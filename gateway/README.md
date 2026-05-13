# Gateway Service

The API Gateway is the entry point for HTTP and WebSocket clients. It proxies requests to the Orchestrator and Auth
services, bridges Redis Pub/Sub to WebSockets, and applies shared middleware (logging, JWT, response logs).

## Core Responsibilities

- Proxy pipeline requests to the Orchestrator
- Proxy auth requests to the Auth service
- Stream results over WebSocket from Redis `results:{user_id}` channels
- Apply request context and JWT middleware

## API Endpoints

HTTP:

- `GET /` - Health check
- `POST /pipelines/{pipeline_id}/run` - Proxy to Orchestrator `/api/run/{pipeline_id}`
- `/auth/{path}` - Proxy all auth routes to the Auth service

WebSocket:

- `GET /ws/results/{user_id}` - Subscribe to results for a user

## Runtime Behavior (from `gateway/main.py`)

- **Lifespan**: initializes a shared HTTPX client pool and closes it on shutdown.
- **Middleware stack**:
    - `LoggingContextMiddleware`
    - `JWTAuthMiddleware` (configurable with `JWT_*` settings)
    - `ResponseLogMiddleware`
    - CORS for all origins
- **Routers**: `health`, `query`, `websocket`, and `auth` proxy routes.

## Configuration

These are read by `gateway/core/config.py`. Defaults below reflect `gateway/.env` (Docker Compose).

Service URLs:

- `ORCHESTRATOR_URL` (default: http://orchestrator:8001)
- `AUTH_URL` (default: http://auth:8003)

HTTPX client:

- `HTTPX_TIMEOUT_SECONDS` (default: 60)
- `HTTPX_MAX_CONNECTIONS` (default: 100)
- `HTTPX_MAX_KEEPALIVE_CONNECTIONS` (default: 20)

Redis (WebSocket pub/sub):

- `REDIS_HOST` (default: redis)
- `REDIS_PORT` (default: 6379)
- `REDIS_URL` (default: redis://redis:6379/0)

JWT middleware:

- `JWT_ENABLED` (default: true)
- `JWT_SECRET_KEY` (default: change_me)
- `JWT_ALGORITHM` (default: HS256)
- `JWT_ISSUER` (optional)
- `JWT_AUDIENCE` (optional)
- `JWT_USER_ID_CLAIM` (default: sub)
- `JWT_LEEWAY_SECONDS` (default: 0)
- `JWT_PUBLIC_PATHS` (auto-configured)

Server:

- `PORT` (default: 8000)

## Running The Service

Docker Compose:

```powershell
docker compose up gateway
```

Local development:

```powershell
$env:ORCHESTRATOR_URL = "http://localhost:8001"
$env:AUTH_URL = "http://localhost:8003"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:PORT = "8000"
uv run python -m gateway.main
```

## Request Flow

Pipeline proxy:

1. `POST /pipelines/{pipeline_id}/run`
2. Gateway forwards the request to `{ORCHESTRATOR_URL}/api/run/{pipeline_id}`
3. Response is returned to the client as-is

Auth proxy:

1. `POST /auth/login` (or any `/auth/{path}`)
2. Gateway forwards to `{AUTH_URL}/auth/{path}`

WebSocket bridge:

1. Client connects to `GET /ws/results/{user_id}`
2. Gateway subscribes to Redis `results:{user_id}`
3. Messages are forwarded to the WebSocket client

## Notes

- The proxy layer uses `shared.utils.forward_to_service` with pooled HTTPX clients.
- WebSocket messages are forwarded as raw JSON strings (decoded if Redis yields bytes).
