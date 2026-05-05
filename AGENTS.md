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
    - FastAPI app with health and proxy endpoints. The proxy endpoint forwards pipeline/run requests to the orchestrator (see `gateway/api/v1/query.py`).
    - Request context middleware and an HTTPX client manager are implemented (`gateway/middleware.py`, `gateway/core/httpx_client.py`).
    - The live gateway path today is HTTP proxying plus request-context/header helpers; the Redis/WebSocket bridge is still only target-architecture work.
    - Notes / recent specifics:
      - HTTPX lifecycle helpers are exposed from `gateway/core/httpx_client.py` as `init_httpx` and `close_httpx` and are wired in `gateway/main.py` lifespan.
      - The middleware module re-exports `build_context_headers` for backward compatibility but the canonical helpers live in `gateway/utils/context_helpers.py` (see the deprecation comment in `gateway/middleware.py`).
  - `orchestrator`:
    - ✅ **COMPLETE:** Full DDD layering implemented with API endpoints, services, repositories, and domain models.
    - ✅ **COMPLETE:** HTTP API surface fully operational - accepts POST requests, creates PENDING tasks in PostgreSQL.
    - ✅ **COMPLETE:** Task enqueuing to Redis `task_queue` with proper context headers and metadata.
    - ✅ **COMPLETE:** Transaction management and unit-of-work pattern implemented in service layer.
    - `start.sh` waits for Postgres and runs Alembic migrations before launching the FastAPI app.
    - Notes / recent specifics:
      - Orchestrator receives requests via gateway proxy at `POST /api/run/{pipeline_id}`.
      - Creates QueryModel records with PENDING state, enqueues to Redis, returns 202 Accepted with query_id.
      - Ready for result consumer implementation (see roadmap below).
  - `ml_worker`:
    - An asyncio-based worker is implemented (`ml_worker/main.py`) that initializes a model loader, inference runner, and a `QueueConsumer`.
    - Uses shared Redis queue abstractions (`shared/messaging/queue.py`) to read from `task_queue` and publish to `result_queue`.
    - The worker `start.sh` waits for Redis before launching the process.
  - `shared`:
    - Messaging primitives for Redis queues and pub/sub exist (`shared/messaging/queue.py`, `shared/messaging/pubsub.py`, `shared/messaging/names.py`).
    - Notes / recent specifics:
      - `shared/messaging/__init__.py` re-exports `RedisResource`, `RedisQueue`, `RedisPubSub`, `RedisNamespace`, `result_channel`, `get_task_queue`, `get_result_queue`, and `get_redis_client` — prefer importing these from the package root.
      - `RedisQueue.dequeue()` returns raw bytes (or None) and `RedisPubSub.listen()` yields str|bytes; calling code is responsible for decoding/deserializing (see `ml_worker/app/messaging/queue_consumer.py`).

   In short: the repository contains a fully operational end-to-end task submission pipeline. Gateway HTTP proxying, Orchestrator API endpoints and services, ML worker task consumption, and Redis queue integration are all complete and running. Remaining work focuses on result consumption, WebSocket pub/sub bridging, and advanced error handling.

## Runtime Boundaries and Integration Points

- The container topology and runtime wiring are defined in `docker-compose.yml`:
  - `redis` and `postgres` services are declared and exported (`6379`, `5432`).
  - `gateway` is exposed on host port `8080` -> container `8000`.
  - `orchestrator` is exposed on host port `8081` -> container `8000`.
  - `ml_worker` is exposed on host port `8082` -> container `8000`.

- Start scripts and dependency waits:
  - `orchestrator/start.sh` actively waits for the database (`$DB_HOST:5432`) and runs `uv run alembic -c orchestrator/alembic.ini upgrade head` before launching.
  - `ml_worker/start.sh` actively waits for the message broker (`$REDIS_HOST:6379`) prior to starting.
  - `gateway/start.sh` does not wait in its script, but `docker-compose.yml` configures a `depends_on` condition for `redis` (service health) which ensures Redis is available when started via Docker Compose.

- Implication: when running with Docker Compose the compose wiring already covers most broker/DB availability checks; when running services locally (not in compose) you must ensure `REDIS_HOST`, `DB_HOST` and the backing services are reachable.

## Coding Patterns and Conventions to Keep

- Launch services as modules in the start scripts: `uv run python -m <service>.app.main`.
- Launch services as modules in the start scripts: `uv run python -m <service>.main`.
- Keep ASGI import target style: `uvicorn.run("<service>.main:app", host="0.0.0.0", port=..., reload=True)` inside `if __name__ == "__main__"` blocks.
- Root workspace dependency management uses the top-level `pyproject.toml` plus `uv.lock` and the Dockerfiles call `uv sync --frozen` in builder stages—preserve that flow.
- Root workspace members are declared in `pyproject.toml` and should not be arbitrarily changed: `gateway`, `ml_worker`, `orchestrator`, `shared`.

- Service lifecycle patterns to follow:
  - The gateway uses `init_httpx(...)` and `close_httpx()` inside the FastAPI lifespan (see `gateway/app/main.py`) — new agents should prefer these helpers rather than constructing ad-hoc HTTPX clients.
  - The request context helpers moved into `gateway/app/utils/context_helpers.py`; the older `gateway/app/middleware.py` exports are kept for backward compatibility but prefer the utils module.

## Orchestrator Design Rules (from ARCH_GUIDE) — current status

- The target DDD layering is fully implemented: `api/v1`, `services`, `domain`, `repositories`, `schemas`, `core` under `orchestrator/` with all core logic operationally complete.
- Repository rules are in place: repositories return domain entities (not ORM models) and do not call `session.commit()`; the service layer manages unit-of-work / transactions and cross-boundary calls.
- ✅ **Completed:** Core API endpoints (task creation, 202 Accepted responses), services (task orchestration), and repositories (query persistence) are all implemented and running.
- Current gap: Result consumer service (consumes `result_queue`, updates DB status to COMPLETED, publishes to `results:{user_id}` channels) is still TODO.

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
  - The compose file defines `depends_on` with health checks: `gateway` depends on `redis`, `orchestrator` depends on `postgres` and `redis`, and `ml_worker` depends on `redis`.
  - Orchestrator startup runs migrations; if migrations fail, orchestrator will not complete startup.

- If startup hangs locally, check environment and external services first:
  - `DB_HOST`, `REDIS_HOST`, `POSTGRES_USER/DB/PASSWORD`, and that Postgres and Redis services are reachable.

## Notes for future work / roadmap (align with ARCH_GUIDE)

### ✅ Completed (as of May 2026)
- ✅ Orchestrator API endpoints fully implement the ARCH_GUIDE flow: save PENDING task -> enqueue to Redis -> return 202 Accepted.
- ✅ Gateway HTTP proxying and request context middleware are fully operational.
- ✅ ML worker task consumption and result publishing to `result_queue` are working end-to-end.
- ✅ All services (gateway, orchestrator, ml_worker) running in Docker Compose with proper health checks and dependency ordering.

### 🔮 Next Steps (Priority Order)

1. **Result Consumer Service** (Orchestrator):
   - Implement a background service/listener in the orchestrator that consumes from `result_queue`.
   - Parse result messages and update corresponding QueryModel records from PENDING to COMPLETED.
   - Publish completed results to Redis channel `results:{user_id}` for WebSocket subscribers.

2. **Gateway WebSocket Pub/Sub Bridge**:
   - Wire the gateway to use `shared/messaging/RedisPubSub` for subscribing to `results:{user_id}` channels.
   - Implement WebSocket endpoint that subscribes to user's result channel on connection.
   - Route incoming messages from Redis to connected WebSocket clients in real-time.
   - Handle graceful connection lifecycle (on-connect, on-disconnect, reconnect logic).

3. **Error Handling & Resilience**:
   - Implement FAILED state for tasks that encounter errors or timeouts.
   - Add retry logic for transient failures with exponential backoff.
   - Implement dead-letter queue for permanently failed tasks.
   - Add circuit breaker patterns for external API calls (e.g., Gemini API).

4. **Monitoring & Observability**:
   - Add health check endpoints for all services (currently minimal).
   - Implement metrics collection: queue depth, processing latency, error rates.
   - Add structured logging with correlation IDs across all services.
   - Create alerting for critical failures and performance degradation.

5. **Configuration & Service Discovery**:
   - Replace hardcoded orchestrator URL(s) with environment-driven configuration or service discovery.
   - Add configuration validation at startup with clear error messages.
   - Document all required environment variables per service.
