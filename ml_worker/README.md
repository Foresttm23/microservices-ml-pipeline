# ML Worker Service

Async worker that consumes `task_queue`, runs inference (Gemini or mock), and publishes results to `result_queue`.
There is no HTTP API; the worker runs indefinitely.

## Core Responsibilities

- Consume task messages from Redis
- Execute inference (real or dry-run)
- Publish `ResultMessage` back to Redis

## Runtime Behavior (from `ml_worker/main.py`)

- Initializes logging and settings
- Chooses generator:
    - `MockTextGenerator` when `ML_WORKER_DRY_RUN=true`
    - `GeminiTextGenerator` otherwise
- Builds `InferenceRunner` and `TaskProcessor`
- Starts a `QueueConsumer` loop on `task_queue`

## Configuration

These are read by `ml_worker/core/config.py`. Defaults below reflect `ml_worker/.env` (Docker Compose).

Inference:

- `GEMINI_API_KEY` (optional when `ML_WORKER_DRY_RUN=true`)
- `GEMINI_MODEL` (default: gemini-2.5-flash-lite)
- `GEMINI_API_BASE` (default: https://generativelanguage.googleapis.com/v1)
- `GEMINI_TIMEOUT_SECONDS` (default: 30)
- `ML_WORKER_DRY_RUN` (default: false)

Redis:

- `REDIS_HOST` (default: redis)
- `REDIS_PORT` (default: 6379)
- `REDIS_URL` (default: redis://redis:6379/0)

Notes:

- `ml_worker/start.sh` expects `REDIS_HOST` and `REDIS_PORT` for its readiness check.

## Running The Service

Docker Compose:

```powershell
docker compose up ml_worker
```

Local development:

```powershell
$env:GEMINI_API_KEY = "your-api-key"
$env:ML_WORKER_DRY_RUN = "false"
$env:REDIS_URL = "redis://localhost:6379/0"
uv run python -m ml_worker.main
```

Dry-run mode (no external API calls):

```powershell
$env:ML_WORKER_DRY_RUN = "true"
uv run python -m ml_worker.main
```

## Message Flow

1. `QueueConsumer` blocks on `task_queue`
2. `TaskProcessor` invokes the inference runner
3. Result is serialized and published to `result_queue`
