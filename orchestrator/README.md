# Orchestrator Service

The Orchestrator owns query state, enqueues tasks to Redis, and consumes results back into PostgreSQL. It exposes a
single HTTP API for task creation and runs a background result consumer in its FastAPI lifespan.

## Core Responsibilities

- Create query records with PENDING state
- Enqueue task messages to Redis `task_queue`
- Consume `result_queue` messages and update DB state
- Publish results to Redis Pub/Sub `results:{user_id}` channels

## API Endpoint

`POST /api/run/{pipeline_id}`

```json
{
  "message": "What is machine learning?"
}
```

Response (202 Accepted):

```json
{
  "status": "accepted",
  "query_id": "550e8400-e29b-41d4-a716-446655440001",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task enqueued"
}
```

## Runtime Behavior (from `orchestrator/main.py`)

- **Lifespan**:
    - Initialize async DB engine (shared `init_db`)
    - Start a background `QueueConsumer` for `result_queue`
    - On shutdown: cancel consumer and close DB
- **Middleware stack**:
    - `LoggingContextMiddleware`
    - `ResponseLogMiddleware`
    - CORS for all origins

## Configuration

These are read by `orchestrator/core/config.py`. Defaults below reflect `orchestrator/.env` (Docker Compose).

Server:

- `PORT` (default: 8003)

Database:

- `DB_HOST` (default: orchestrator-db)
- `DB_PORT` (default: 5432)
- `POSTGRES_DB` (default: orchestrator_db)
- `POSTGRES_USER` (default: ml_user)
- `POSTGRES_PASSWORD` (default: change_me_in_local_dev)

Redis:

- `REDIS_HOST` (default: redis)
- `REDIS_PORT` (default: 6379)
- `REDIS_URL` (default: redis://redis:6379/0)

Derived:

- `DATABASE_URL` is constructed from the DB variables above.

## Running The Service

Docker Compose:

```powershell
docker compose up orchestrator
```

Local development:

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:POSTGRES_DB = "orchestrator_db"
$env:POSTGRES_USER = "ml_user"
$env:POSTGRES_PASSWORD = "change_me_in_local_dev"
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:PORT = "8003"
uv run python -m orchestrator.main
```

## Startup Script Notes

The container entrypoint `orchestrator/start.sh` waits for Postgres and Redis, runs Alembic migrations, then starts the
service:

```text
uv run alembic -c orchestrator/alembic.ini upgrade head
uv run python -m orchestrator.main
```

## Data Flow Summary

- **Task creation**: API request -> QueryService -> DB insert -> Redis `task_queue`
- **Result processing**: Redis `result_queue` -> ResultProcessor -> DB update -> Redis `results:{user_id}`

