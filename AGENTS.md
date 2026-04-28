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
    - FastAPI app with health and proxy endpoints. The proxy endpoint forwards pipeline/run requests to the orchestrator (see `gateway/app/api/v1/query.py`).
    - Request context middleware and an HTTPX client manager are implemented (`gateway/app/middleware.py`, `gateway/app/core/httpx_client.py`).
    - Some WebSocket/pubsub bridge modules exist as scaffolding (schemas and service placeholders), but the fully working WebSocket Redis subscriber/connection manager are minimal/partial.
  - `orchestrator`:
    - Project layout follows the intended layered structure (folders under `orchestrator/app/` are present).
    - `start.sh` waits for Postgres and runs Alembic migrations before launching the FastAPI app.
    - The HTTP API surface is minimal today (root GET), and higher-level endpoints and service logic are still to be implemented.
  - `ml_worker`:
    - An asyncio-based worker is implemented (`ml_worker/app/main.py`) that initializes a model loader, inference runner, and a `QueueConsumer`.
    - Uses shared Redis queue abstractions (`shared/messaging/queue.py`) to read from `task_queue` and publish to `result_queue`.
    - The worker `start.sh` waits for Redis before launching the process.
  - `shared`:
    - Messaging primitives for Redis queues and pub/sub exist (`shared/messaging/queue.py`, `shared/messaging/pubsub.py`, `shared/messaging/names.py`).

  In short: the repository contains a working ML worker and shared messaging layer; the gateway implements HTTP proxying and middleware; orchestrator scaffolding and DB migration steps exist, but full orchestrator application logic (task creation, result consumption, DB repositories/services) is still in progress.

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
- Keep ASGI import target style: `uvicorn.run("<service>.app.main:app", host="0.0.0.0", port=..., reload=True)` inside `if __name__ == "__main__"` blocks.
- Root workspace dependency management uses the top-level `pyproject.toml` plus `uv.lock` and the Dockerfiles call `uv sync --frozen` in builder stages—preserve that flow.
- Root workspace members are declared in `pyproject.toml` and should not be arbitrarily changed: `gateway`, `ml_worker`, `orchestrator`, `shared`.

## Orchestrator Design Rules (from ARCH_GUIDE) — current status

- The target DDD layering remains the contract: `api/v1`, `services`, `domain`, `repositories`, `schemas`, `core` under `orchestrator/app/` — the directory layout exists in the repo.
- Repository rules still apply: repositories should return domain entities (not ORM models) and must not call `session.commit()`; the service layer should manage unit-of-work / transactions and cross-boundary calls (DB + queue/pubsub).
- Current gap: concrete repository implementations, service orchestration logic, and API endpoints that implement the ARCH_GUIDE flow (save PENDING task -> enqueue task -> return 202) are still TODO. Use the existing layout to implement these behaviors.

## Practical Agent Workflow / How to run things

- Preferred full-stack bring-up (from repo root):

  ```powershell
  docker compose up --build
  ```

- Local development (run a single service from repo root):

  ```powershell
  # Gateway
  uv run python -m gateway.app.main

  # Orchestrator
  uv run python -m orchestrator.app.main

  # ML Worker (worker runs as an asyncio process)
  uv run python -m ml_worker.app.main
  ```

- When using Docker Compose be mindful that:
  - The compose file defines `depends_on` with health checks: `gateway` depends on `redis`, `orchestrator` depends on `postgres` and `redis`, and `ml_worker` depends on `redis`.
  - Orchestrator startup runs migrations; if migrations fail, orchestrator will not complete startup.

- If startup hangs locally, check environment and external services first:
  - `DB_HOST`, `REDIS_HOST`, `POSTGRES_USER/DB/PASSWORD`, and that Postgres and Redis services are reachable.

## Notes for future work / roadmap (align with ARCH_GUIDE)

- Implement Orchestrator API endpoints and services to:
  - Create task records (PENDING) in Postgres via repositories and return `202 Accepted`.
  - Push tasks to the `task_queue` using `shared/messaging/RedisQueue`.
  - Run a result listener that consumes `result_queue`, updates DB records to `COMPLETED`, and publishes to result channels (e.g., `results:{user_id}`).

- Complete Gateway WebSocket Pub/Sub bridge:
  - Wire the gateway to use `shared/messaging/RedisPubSub` or the repo's pubsub utilities to subscribe to `results:{user_id}` channels and route messages to connected WebSocket clients.

- Harden configuration & networking:
  - Replace hardcoded orchestrator URL(s) with environment-driven service discovery (or use compose service names when running inside Docker).
  - Add graceful shutdown handling and health endpoints for long-running worker loops.

---

If you want, I can:
- open a PR that implements a small end-to-end smoke path (orchestrator endpoint that enqueues a trivial task, a short-lived ml_worker consumer that returns a canned result, and gateway proxy+websocket demo), or
- implement the missing gateway pub/sub subscriber and connection manager wiring to exercise `results:{user_id}` publishes.
