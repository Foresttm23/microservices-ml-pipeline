# AGENTS.md

## Purpose and Source of Truth

- Use `ARCH_GUIDE.md` as the target architecture contract.
- Use runtime files (`docker-compose.yml`, `*/start.sh`, `*/main.py`, `*/Dockerfile`) as current-state truth.
- Service `README.md` files are empty; do not assume undocumented behavior.

## Big Picture (Target + Current)

- Target flow (`ARCH_GUIDE.md`): HTTP -> Queue -> Pub/Sub -> WebSocket.
- Service intent (`ARCH_GUIDE.md`):
    - `gateway`: auth/rate-limit edge + Redis Pub/Sub WebSocket bridge.
    - `orchestrator`: owns DB state, emits tasks, consumes results.
    - `ml_worker`: consumes `task_queue`, runs inference, emits `result_queue`.
- Current implementation: all 3 services are minimal FastAPI apps with `GET /` (`gateway/app/main.py`,
  `orchestrator/app/main.py`, `ml_worker/app/main.py`).

## Runtime Boundaries and Integration Points

- Container topology is defined only in `docker-compose.yml` (ports `8080`, `8081`, `8082` to container `8000`).
- `orchestrator/start.sh` blocks on `$DB_HOST:5432`, then runs `uv run alembic upgrade head`.
- `ml_worker/start.sh` blocks on `$REDIS_HOST:6379` before launch.
- `gateway/start.sh` launches immediately; no dependency wait is implemented.
- Implication: add DB/broker services and env wiring before relying on orchestrator/worker startup scripts.

## Coding Patterns to Keep

- Launch services as modules: `uv run python -m <service>.main` (all `start.sh`).
- Keep ASGI import target style: `uvicorn.run("app.main:app", host="0.0.0.0", port=..., reload=True)` (`*/main.py`).
- Keep workspace-aware dependency flow: root `pyproject.toml` + `uv.lock`, then `uv sync --frozen` in Docker builder
  stages.
- Root workspace members are fixed in `pyproject.toml`: `gateway`, `ml_worker`, `orchestrator`.

## Orchestrator Design Rules (from ARCH_GUIDE)

- Build layered structure under `orchestrator/app/`: `api/v1`, `services`, `domain`, `repositories`, `schemas`, `core`.
- Repositories return domain entities (not ORM models) and must not call `session.commit()`.
- Service layer owns unit-of-work/transactions and cross-boundary calls (DB + queue/pubsub).

## Practical Agent Workflow

- Prefer full-stack bring-up for integration work:
    - `docker compose up --build`
- Local service runs from repo root:
    - `uv run python -m gateway.main`
    - `uv run python -m orchestrator.main`
    - `uv run python -m ml_worker.main`
- If startup hangs, inspect missing env/dependencies first (`DB_HOST`, `REDIS_HOST`, Postgres, Redis).
