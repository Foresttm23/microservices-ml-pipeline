# AGENTS.md

## Purpose and Source of Truth

- Use `ARCH_GUIDE.md` as the target architecture contract.
- Use runtime files (`docker-compose.yml`, `*/start.sh`, `*/main.py`, `*/Dockerfile`) as the current-state truth.
- Service `README.md` files are mostly empty; do not assume undocumented behavior.

## Big Picture (Target + Current)

- Target flow (see `ARCH_GUIDE.md`): HTTP -> Queue -> Pub/Sub -> WebSocket.
- Service intent (target):
    - `gateway`: auth/rate-limit edge + Redis Pub/Sub WebSocket bridge.
    - `orchestrator`: owns DB state, emits tasks, consumes results and updates state.
    - `ml_worker`: consumes `task_queue`, runs inference, emits `result_queue`.

- Current implementation (what's implemented in the repo today):
    - `gateway`:
        - FastAPI app with health, proxy, and WebSocket endpoints. The proxy endpoint forwards pipeline/run requests to
          the
          orchestrator (see `gateway/api/v1/query.py`). WebSocket results are bridged from Redis Pub/Sub (see
          `gateway/api/v1/websocket.py`).
        - Request context middleware and an HTTPX client manager are implemented (`shared/core/logging/middleware.py`,
          `gateway/core/httpx_client.py`) and wired in `gateway/main.py`.
        - The live gateway path today includes HTTP proxying plus Redis/WebSocket bridging.
        - Notes / recent specifics:
            - HTTPX lifecycle helpers are exposed from `gateway/core/httpx_client.py` as `init_httpx` and `close_httpx`
              and are wired in `gateway/main.py` lifespan.
            - Request context helpers live in `gateway/utils/context_helpers.py` (use these from handlers).
    - `orchestrator`:
        - ✅ **COMPLETE:** Full DDD layering implemented with API endpoints, services, repositories, and domain models.
        - ✅ **COMPLETE:** HTTP API surface fully operational - accepts POST requests, creates PENDING tasks in
          PostgreSQL.
        - ✅ **COMPLETE:** Task enqueuing to Redis `task_queue` with proper context headers and metadata.
        - ✅ **COMPLETE:** Transaction management and unit-of-work pattern implemented in service layer.
        - ✅ **COMPLETE:** Result consumer wired in `orchestrator/main.py` using `QueueConsumer` and
          `services/result_processor.py`.
            - `start.sh` waits for Postgres and runs Alembic migrations before launching the FastAPI app.
            - Notes / recent specifics:
                - Orchestrator receives requests via gateway proxy at `POST /api/run/{pipeline_id}`.
                - Creates QueryModel records with PENDING state, enqueues to Redis, returns 202 Accepted with query_id.
                - ResultProcessor updates DB state and publishes to `results:{user_id}` channels.
    - `ml_worker`:
        - An asyncio-based worker is implemented (`ml_worker/main.py`) that initializes a model loader, inference
          runner, and a `QueueConsumer`.
        - Uses shared Redis queue abstractions (`shared/messaging/queue.py`) to read from `task_queue` and publish to
          `result_queue`.
        - The worker `start.sh` waits for Redis before launching the process.
    - `shared`:
        - Messaging primitives for Redis queues and pub/sub exist (`shared/messaging/queue.py`,
          `shared/messaging/pubsub.py`, `shared/messaging/names.py`).
        - Notes / recent specifics:
            - `shared/messaging/__init__.py` re-exports `RedisResource`, `RedisQueue`, `RedisPubSub`, `RedisNamespace`,
              `result_channel`, `get_task_queue`, `get_result_queue`, and `get_redis_client` — prefer importing these
              from the package root.
            - `RedisQueue.dequeue()` returns `str | bytes | None` and `RedisPubSub.listen()` yields `str | bytes`;
              calling
              code is responsible for decoding/deserializing (see `ml_worker/main.py`).

  In short: the repository contains a fully operational end-to-end task submission pipeline, including result
  consumption and Redis/WebSocket bridging. Remaining work focuses on error handling, observability, and configuration.

## Runtime Boundaries and Integration Points

- The container topology and runtime wiring are defined in `docker-compose.yml`:
    - `redis` and `postgres` services are declared and exported (`6379`, `5432`).
    - `gateway` is exposed on host port `8080` -> container `8000`.
    - `orchestrator` is exposed on host port `8081` -> container `8000`.
    - `ml_worker` is exposed on host port `8082` -> container `8000`.

- Start scripts and dependency waits:
    - `orchestrator/start.sh` actively waits for the database (`$DB_HOST:5432`) and runs
      `uv run alembic -c orchestrator/alembic.ini upgrade head` before launching.
    - `ml_worker/start.sh` actively waits for the message broker (`$REDIS_HOST:6379`) prior to starting.
    - `gateway/start.sh` does not wait in its script, but `docker-compose.yml` configures a `depends_on` condition for
      `redis` (service health) which ensures Redis is available when started via Docker Compose.

- Implication: when running with Docker Compose the compose wiring already covers most broker/DB availability checks;
  when running services locally (not in compose) you must ensure `REDIS_HOST`, `DB_HOST` and the backing services are
  reachable.

## Coding Patterns and Conventions to Keep

- Launch services as modules in the start scripts: `uv run python -m <service>.main`.
- Keep ASGI import target style: `uvicorn.run("<service>.main:app", host="0.0.0.0", port=..., reload=True)` inside
  `if __name__ == "__main__"` blocks.
- Root workspace dependency management uses the top-level `pyproject.toml` plus `uv.lock` and the Dockerfiles call
  `uv sync --frozen` in builder stages—preserve that flow.
- Root workspace members are declared in `pyproject.toml` and should not be arbitrarily changed: `gateway`, `ml_worker`,
  `orchestrator`, `shared`.

- Service lifecycle patterns to follow:
    - The gateway uses `init_httpx(...)` and `close_httpx()` inside the FastAPI lifespan (see `gateway/main.py`) —
      new agents should prefer these helpers rather than constructing ad-hoc HTTPX clients.
    - Request context helpers live in `gateway/utils/context_helpers.py` (use these from handlers; middleware is from
      `shared/core/logging/middleware.py`).

## Orchestrator Design Rules (from ARCH_GUIDE) — current status

- The target DDD layering is fully implemented: `api/v1`, `services`, `domain`, `repositories`, `schemas`, `core` under
  `orchestrator/` with all core logic operationally complete.
- Repository rules are in place: repositories return domain entities (not ORM models) and do not call
  `session.commit()`; the service layer manages unit-of-work / transactions and cross-boundary calls.
- ✅ **Completed:** Core API endpoints (task creation, 202 Accepted responses), services (task orchestration), and
  repositories (query persistence) are all implemented and running.
- ✅ **Completed:** Result consumer uses `QueueConsumer` in `orchestrator/main.py` and `ResultProcessor` in
  `orchestrator/services/result_processor.py` to update DB state and publish to `results:{user_id}` channels.

## Practical Agent Workflow / How to run things

- Preferred full-stack bring-up (from repo root):

  ```powershell
  docker compose up --build
  ```

- Local development (run a single service from repo root):

  ```powershell
  # Gateway
  uv run python -m gateway.main

  # Orchestrator
  uv run python -m orchestrator.main

  # ML Worker (worker runs as an asyncio process)
  uv run python -m ml_worker.main
  ```

- When using Docker Compose be mindful that:
    - The compose file defines `depends_on` with health checks: `gateway` depends on `redis`, `orchestrator` depends on
      `postgres` and `redis`, and `ml_worker` depends on `redis`.
    - Orchestrator startup runs migrations; if migrations fail, orchestrator will not complete startup.

- If startup hangs locally, check environment and external services first:
    - `DB_HOST`, `REDIS_HOST`, `POSTGRES_USER/DB/PASSWORD`, and that Postgres and Redis services are reachable.

## Notes for future work / roadmap (align with ARCH_GUIDE)

### ✅ Completed (as of May 2026)

- ✅ Orchestrator API endpoints fully implement the ARCH_GUIDE flow: save PENDING task -> enqueue to Redis -> return 202
  Accepted.
- ✅ Gateway HTTP proxying and request context middleware are fully operational.
- ✅ ML worker task consumption and result publishing to `result_queue` are working end-to-end.
- ✅ Orchestrator result consumer updates DB state and publishes to Redis channels.
- ✅ Gateway WebSocket pub/sub bridge streams results from Redis to clients.
- ✅ All services (gateway, orchestrator, ml_worker) running in Docker Compose with proper health checks and dependency
  ordering.

### 🔮 Next Steps (Priority Order)

1. **Error Handling & Resilience**:
    - Implement FAILED state for tasks that encounter errors or timeouts.
    - Add retry logic for transient failures with exponential backoff.
    - Implement dead-letter queue for permanently failed tasks.
    - Add circuit breaker patterns for external API calls (e.g., Gemini API).

2. **Monitoring & Observability**:
    - Add health check endpoints for all services (currently minimal).
    - Implement metrics collection: queue depth, processing latency, error rates.
    - Add structured logging with correlation IDs across all services.
    - Create alerting for critical failures and performance degradation.

3. **Configuration & Service Discovery**:
    - Replace hardcoded orchestrator URL(s) with environment-driven configuration or service discovery.
    - Add configuration validation at startup with clear error messages.
    - Document all required environment variables per service.

### Commits

- Avoid overly verbose descriptions or unnecessary details.
- When generating feat commits follow 'feat(service name/whats updated): message' principle.