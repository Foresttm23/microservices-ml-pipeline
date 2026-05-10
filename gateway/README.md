# 🚪 Gateway Service

The **API Gateway** is the entry point for client requests. It handles HTTP endpoint routing, request context
extraction, and WebSocket subscription management for real-time result delivery.

**Port:** 8080 (host) → 8000 (container)  
**Language:** Python (FastAPI)  
**Status:** ✅ Complete

---

## 🎯 Responsibilities

1. **HTTP Endpoint Routing**
    - Accept `POST /pipelines/{pipeline_id}/run` requests from clients
    - Extract request headers (`X-Correlation-ID`, `X-User-ID`)
    - Forward to Orchestrator via HTTP proxy
    - Return response to client

2. **Request Context Propagation**
    - Extract and validate `X-Correlation-ID` header (or generate if missing)
    - Extract and validate `X-User-ID` header
    - Store context in middleware for logging pipeline
    - Pass headers downstream to Orchestrator

3. **WebSocket Pub/Sub Bridge**
    - Accept WebSocket connections at `GET /ws/results/{user_id}`
    - Subscribe to Redis channel `results:{user_id}`
    - Push incoming messages to connected clients
    - Handle graceful disconnection

4. **Health Endpoint**
    - Expose `GET /` or `GET /health` for liveness/readiness checks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│ Client (HTTP + WebSocket)                   │
├─────────────────────────────────────────────┤
│                                             │
│  POST /pipelines/{pipeline_id}/run          │
│  └─ query.py:proxy_to_orchestrator()        │
│                                             │
│  GET /ws/results/{user_id}                  │
│  └─ websocket.py:results_socket()           │
│                                             │
│  GET /                                      │
│  └─ health.py:root()                        │
│                                             │
├─────────────────────────────────────────────┤
│ Middleware Stack                            │
│ - LoggingContextMiddleware (correlation_id)│
│ - CORSMiddleware                            │
├─────────────────────────────────────────────┤
│ Dependencies (FastAPI)                      │
│ - HTTPXClient (for HTTP proxying)           │
│ - Request context extraction                │
├─────────────────────────────────────────────┤
│ External Services                           │
│ - Orchestrator API (HTTP)                   │
│ - Redis (Pub/Sub)                           │
└─────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
gateway/
├── main.py                          # FastAPI app + lifespan (startup/shutdown)
├── api/v1/
│   ├── __init__.py
│   ├── health.py                    # GET / endpoint
│   ├── query.py                     # POST /pipelines/{pipeline_id}/run (HTTP proxy)
│   └── websocket.py                 # GET /ws/results/{user_id} (WebSocket bridge)
├── core/
│   ├── config.py                    # Settings (GatewaySettings)
│   ├── dependencies.py              # FastAPI Depends factories
│   └── httpx_client.py              # HTTPX client lifecycle management
├── utils/
│   └── context_helpers.py           # build_context_headers(), extract headers
├── Dockerfile
├── start.sh                         # Entry point script
├── pyproject.toml                   # Service dependencies
└── README.md                        # This file
```

---

## 🔌 Endpoints

### HTTP Endpoints

#### `POST /pipelines/{pipeline_id}/run`

**Purpose:** Submit a quiz task for processing.

**Request:**

```json
{
  "message": "What is machine learning?"
}
```

**Headers (Optional; auto-generated if missing):**

```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
X-User-ID: user_123
```

**Response (202 Accepted):**

```json
{
  "status": "accepted",
  "query_id": "550e8400-e29b-41d4-a716-446655440001",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task enqueued"
}
```

**Processing:**

1. Extract headers (correlation_id, user_id)
2. Validate `PipelineRequest` body
3. Forward `POST /api/run/{pipeline_id}` to Orchestrator
4. Return orchestrator's response to client

---

#### `GET /`

**Purpose:** Health check endpoint.

**Response:**

```json
{
  "message": "I am healthy!"
}
```

---

### WebSocket Endpoints

#### `GET /ws/results/{user_id}`

**Purpose:** Subscribe to real-time result delivery for a user.

**Parameters:**

- `user_id` (path): User ID to subscribe to results for

**Connection Behavior:**

1. Client connects via WebSocket
2. Gateway subscribes to Redis channel `results:{user_id}`
3. For each message published to the channel, gateway pushes to client
4. On disconnect, gateway closes Redis subscription

**Example (JavaScript):**

```javascript
const userId = 'user_123';
const ws = new WebSocket(`ws://localhost:8080/ws/results/${userId}`);

ws.onopen = () => {
    console.log(`Connected to results stream for ${userId}`);
};

ws.onmessage = (event) => {
    const result = JSON.parse(event.data);
    console.log('Result received:', result);
    // result = {
    //   "correlation_id": "...",
    //   "status": "completed",
    //   "output_text": "Machine learning is...",
    //   ...
    // }
};

ws.onclose = () => {
    console.log('Disconnected from results stream');
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

---

## ⚙️ Configuration

### Environment Variables

**File:** `.env` or `gateway/.env`

```bash
# Server
PORT=8000                                      # FastAPI port (default: 8000)

# Orchestrator (required for proxy)
ORCHESTRATOR_URL=http://orchestrator:8001     # Orchestrator HTTP URL

# HTTP Client
HTTPX_TIMEOUT_SECONDS=60                       # Request timeout (default: 60)
HTTPX_MAX_CONNECTIONS=100                      # Max connections in pool (default: 100)
HTTPX_MAX_KEEPALIVE_CONNECTIONS=20             # Keepalive connections (default: 20)

# Redis (for WebSocket pub/sub)
REDIS_HOST=redis                               # Redis hostname (default: redis)
REDIS_PORT=6379                                # Redis port (default: 6379)
```

### FastAPI Settings

**File:** `core/config.py`

```python
class GatewaySettings(BaseSettings):
    PORT: int = 8000
    ORCHESTRATOR_URL: str  # Must be set
    HTTPX_TIMEOUT_SECONDS: float = 60
    HTTPX_MAX_CONNECTIONS: int = 100
    HTTPX_MAX_KEEPALIVE_CONNECTIONS: int = 20
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
```

---

## 🚀 Quick Start

### Docker Compose

```powershell
docker compose up gateway
```

Accessible at: `http://localhost:8080`

### Local Development

```powershell
# Set environment variables
$env:ORCHESTRATOR_URL = "http://localhost:8001"
$env:PORT = "8000"

# Install and run
uv run python -m gateway.main
```

---

## 📊 Request Flow

### HTTP Proxy Flow (POST /pipelines/{pipeline_id}/run)

```
1. Client sends HTTP POST request
   POST /pipelines/{pipeline_id}/run
   Headers: { X-Correlation-ID, X-User-ID }
   Body: { message }
   
   ↓
   
2. Gateway middleware (LoggingContextMiddleware)
   - Extract or generate X-Correlation-ID
   - Extract or generate X-User-ID
   - Store in request context
   - Log request metadata
   
   ↓
   
3. query.py:proxy_to_orchestrator()
   - Extract headers via context_helpers.build_context_headers()
   - Validate PipelineRequest schema
   - Create full orchestrator URL: {ORCHESTRATOR_URL}/api/run/{pipeline_id}
   - Call orchestrator via HTTPX client (pooled connection)
   
   ↓
   
4. Orchestrator processes request
   - Creates QueryModel (PENDING)
   - Enqueues TaskMessage to Redis
   - Returns 202 Accepted with query_id
   
   ↓
   
5. Gateway returns response to client
   - 202 Accepted with { status, query_id, correlation_id, message }
```

### WebSocket Pub/Sub Flow (GET /ws/results/{user_id})

```
1. Client opens WebSocket connection
   GET /ws/results/user_123
   
   ↓
   
2. websocket.py:results_socket()
   - Accept WebSocket connection
   - Create RedisPubSub client
   - Subscribe to results:user_123 channel
   
   ↓
   
3. Orchestrator result processor publishes result
   - ResultMessage received from ml_worker
   - QueryModel state updated to COMPLETED
   - Message published to results:user_123 channel
   
   ↓
   
4. Gateway receives publish event
   - RedisPubSub.listen() yields the message
   - Decode JSON if needed
   - Send to WebSocket client
   
   ↓
   
5. Client receives message
   - ws.onmessage event fires
   - Parse JSON ResultMessage
   - Update UI
   
   ↓
   
6. On disconnect
   - WebSocketDisconnect exception caught
   - Cleanup and log disconnect
```

---

## 🔧 Development

### Dependencies

See `pyproject.toml` for full list. Key dependencies:

- **FastAPI** — Web framework
- **httpx** — HTTP client for proxying
- **redis** — Redis Pub/Sub (via shared)
- **loguru** — Structured logging
- **pydantic** — Request validation
- **uvicorn** — ASGI server

### Code Structure

**main.py:**

- FastAPI app initialization
- Middleware setup (CORS, logging, context)
- Router includes (`health`, `query`, `websocket`)
- Lifespan context manager (HTTPX lifecycle)

**api/v1/query.py:**

- `proxy_to_orchestrator()` endpoint
- Validates `PipelineRequest`
- Calls `forward_to_service()` helper (in shared)

**api/v1/websocket.py:**

- `results_socket()` WebSocket endpoint
- Subscribes to Redis channel dynamically
- Pushes messages to client

**core/dependencies.py:**

- Dependency injection factories (HTTPXClient, request context)

**utils/context_helpers.py:**

- `build_context_headers()` — Create headers dict from context
- Header extraction utilities

---

## 🐛 Troubleshooting

### Proxy returns 503 Service Unavailable

**Cause:** Orchestrator service not reachable.

```powershell
# Verify Orchestrator is running
docker compose logs orchestrator | head -20

# Test connectivity from Gateway container
docker compose exec gateway curl http://orchestrator:8001/

# Check ORCHESTRATOR_URL environment variable
docker compose exec gateway env | grep ORCHESTRATOR_URL
```

### WebSocket connection fails or doesn't receive messages

**Cause:** Redis not reachable or result consumer not publishing.

```powershell
# Check Redis is running
docker compose logs redis | tail -10

# Verify result consumer is active
docker compose logs orchestrator | grep -i "result"

# Test Redis manually
docker compose exec redis redis-cli PING
docker compose exec redis redis-cli SUBSCRIBE "results:test"
```

### Request headers not being propagated

**Cause:** Context extraction issue.

```python
# In request handler, verify context is set
from shared.core.logging import get_context

context = get_context()
print(context.correlation_id)  # Should not be None
```

### HTTPX connection pool exhausted

**Cause:** Max connections limit reached.

**Solution:** Increase limits in `.env`:

```bash
HTTPX_MAX_CONNECTIONS=200
HTTPX_MAX_KEEPALIVE_CONNECTIONS=50
```

---

## 📈 Performance Tuning

### HTTPX Client Pool

```python
# gateway/core/httpx_client.py

init_httpx(
    timeout=httpx.Timeout(60),
    limits=httpx.Limits(
        max_connections=100,  # Increase for high concurrency
        max_keepalive_connections=20  # Reuse connections
    ),
)
```

### Middleware Ordering

The middleware stack matters for performance:

1. **LoggingContextMiddleware** (earliest) — Extract context
2. **CORSMiddleware** — Handle CORS (if enabled)
3. FastAPI routing → handlers

---

## 🔒 Security Notes

### Request Validation

- `PipelineRequest` validated via Pydantic
- `pipeline_id` path parameter treated as-is (forwarded to Orchestrator)
- No authentication currently implemented (add JWT/OAuth as needed)

### WebSocket Security

- User ID in path; vulnerable to enumeration (add auth tokens)
- No TLS/SSL by default in Docker Compose
- Should use WSS (WebSocket Secure) in production

---

## 📚 Related Services

- **Orchestrator** (`/orchestrator/README.md`) — Receives proxied requests
- **Shared** (`/shared/README.md`) — Common messaging and utilities
- **ML Worker** (`/ml_worker/README.md`) — Processes tasks (indirectly via Orchestrator)

---

**See Also:** [WORKFLOW.md](../WORKFLOW.md) for complete data flow.
