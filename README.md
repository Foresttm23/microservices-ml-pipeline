# 🚀 ML Microservices Quiz Pipeline

An asynchronous, high-performance microservices system for ML-powered quiz generation and real-time result delivery.

**Status:** ✅ End-to-end pipeline fully operational  
**Last Updated:** May 2026

---

## 📋 Quick Links

- **[WORKFLOW.md](./WORKFLOW.md)** — Complete end-to-end data flow, schemas, and service details
- **[ARCH_GUIDE.md](./ARCH_GUIDE.md)** — Architecture blueprint and design principles
- **[AGENTS.md](./AGENTS.md)** — Development guidelines and agent workflows

Service-specific documentation:

- **[Gateway README](./gateway/README.md)** — HTTP proxy & WebSocket bridge
- **[Orchestrator README](./orchestrator/README.md)** — Task orchestration & state management
- **[ML Worker README](./ml_worker/README.md)** — Inference engine & task processor
- **[Auth README](./auth/README.md)** — JWT auth & refresh tokens
- **[Shared README](./shared/README.md)** — Common utilities & messaging abstractions

---

## 🔄 System Overview

A **4-service microservices architecture** that processes ML quiz tasks asynchronously:

```
┌─────────────────────────────────────────────────────────────────┐
│  Client Request (HTTP)                                          │
│  POST /pipelines/{pipeline_id}/run                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │ GATEWAY (Port 8081)  │
         │ - HTTP Proxy         │
         │ - Context Headers    │
         │ - WebSocket Bridge   │
         └────────┬─────────────┘
                  │ Forward to Orchestrator
                  ▼
         ┌──────────────────────────┐
         │ ORCHESTRATOR (Port 8083) │
         │ - Task Creation (PENDING)│
         │ - DB State Machine       │
         │ - Result Processing      │
         └────────┬─────────────────┘
                  │ Save & Enqueue
    ┌─────────────┘
    │
    ├─ PostgreSQL (Queries table)
    └─ Redis task_queue
       │
       ▼
    ┌──────────────────────────┐
    │  ML WORKER (Port 8084)   │
    │  - Task Consumption      │
    │  - Gemini Inference      │
    │  - Result Publishing     │
    └────────┬─────────────────┘
             │ Publish to result_queue
             ▼
         Redis result_queue
         │
         ├─ Consumed by Orchestrator ResultProcessor
         ├─ Updates QueryModel state to COMPLETED/FAILED
         └─ Publishes to results:{user_id} channel
            │
            ▼
         ┌──────────────────────┐
         │ GATEWAY WEBSOCKET    │
         │ - Subscribes to      │
         │   results:{user_id}  │
         └────────┬─────────────┘
                  │ Push to client
                  ▼
             Client (Browser)
            Receives Result
```

---

## 🛠️ Tech Stack

| Component        | Technology              | Version                                |
|------------------|-------------------------|----------------------------------------|
| Web Framework    | FastAPI                 | 0.100+                                 |
| Message Broker   | Redis                   | 7 (Alpine)                             |
| Database         | PostgreSQL              | 16 (Alpine) + SQLAlchemy 2.0 + Alembic |
| ML Model         | Google Gemini API       | 2.0-flash                              |
| Task Processing  | Python asyncio          | 3.13+                                  |
| Package Manager  | uv                      | Latest                                 |
| Containerization | Docker & Docker Compose | Latest                                 |

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose** (easiest full-stack setup)
- **OR** Python 3.13+, `uv`, local PostgreSQL, local Redis
- **Gemini API Key** (for ML inference)

### Quick Start: Docker Compose

```powershell
# Clone and navigate to project
cd Coursework-ML-Microservices

# Start all services
docker compose up --build

# Expected output:
# - redis        : Ready to accept connections
# - postgres     : database system is ready
# - orchestrator : Migrations applied, FastAPI running on 0.0.0.0:8003
# - gateway      : FastAPI running on 0.0.0.0:8001
# - ml_worker    : Starting queue consumer loop
```

The system is ready when you see all services healthy.

### Local Development (Without Docker)

**Terminal 1: Gateway**

```powershell
$env:ORCHESTRATOR_URL = "http://localhost:8003"
$env:AUTH_URL = "http://localhost:8002"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:PORT = "8001"
uv run python -m gateway.main
```

**Terminal 2: Orchestrator**

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

**Terminal 3: ML Worker**

```powershell
$env:GEMINI_API_KEY = "your-api-key"
$env:ML_WORKER_DRY_RUN = "false"
$env:REDIS_URL = "redis://localhost:6379/0"
uv run python -m ml_worker.main
```

**Terminal 4: Auth**

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:POSTGRES_DB = "auth_db"
$env:POSTGRES_USER = "ml_user"
$env:POSTGRES_PASSWORD = "change_me_in_local_dev"
$env:PORT = "8002"
uv run python -m auth.main
```

**Terminal 5: Test**

```powershell
curl -X POST http://localhost:8081/pipelines/quiz_v1/run `
  -H "Content-Type: application/json" `
  -H "X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000" `
  -H "X-User-ID: user_123" `
  -d '{"message": "What is machine learning?"}'
```

---

## 📊 Complete Request Flow

```
1. CLIENT REQUEST
   POST /pipelines/{pipeline_id}/run
   Headers: X-Correlation-ID, X-User-ID
   Body: { "message": "What is machine learning?" }
   
   ↓ (HTTP via Gateway proxy)

2. ORCHESTRATOR RECEIVES
   POST /api/run/{pipeline_id}
   - Creates QueryModel with state=PENDING
   - Builds TaskMessage with metadata
   - Enqueues to Redis task_queue
   - Returns 202 Accepted with query_id
   
   ↓ (Async via Redis)

3. ML WORKER PROCESSES
   - Dequeues TaskMessage from task_queue
   - Calls Gemini API with prompt
   - Creates ResultMessage with output
   - Publishes to Redis result_queue
   
   ↓ (Background via Result Consumer)

4. ORCHESTRATOR RESULT CONSUMER
   - Dequeues ResultMessage from result_queue
   - Updates QueryModel state to COMPLETED
   - Saves ResponseEntity to DB
   - Publishes to results:{user_id} Redis channel
   
   ↓ (WebSocket push)

5. CLIENT RECEIVES (WebSocket)
   GET /ws/results/{user_id}
   Receives: ResultMessage (JSON)
```

---

## 🔌 Key Endpoints

### Gateway (Port 8081)

| Method | Endpoint                       | Purpose                               |
|--------|--------------------------------|---------------------------------------|
| POST   | `/pipelines/{pipeline_id}/run` | Submit task (proxied to orchestrator) |
| GET    | `/ws/results/{user_id}`        | WebSocket subscription for results    |

### Orchestrator (Port 8003)

| Method | Endpoint                 | Purpose                |
|--------|--------------------------|------------------------|
| POST   | `/api/run/{pipeline_id}` | Task creation endpoint |
| GET    | `/`                      | Health check           |

### ML Worker (Port 8084)

| Method | Endpoint     | Purpose                                |
|--------|--------------|----------------------------------------|
| N/A    | Async worker | Consumes from queue, no HTTP endpoints |

---

## 📨 Message Schemas

### Request (HTTP → Gateway → Orchestrator)

```json
{
  "message": "What is machine learning?"
}
```

### Response (202 Accepted)

```json
{
  "status": "accepted",
  "query_id": "550e8400-e29b-41d4-a716-446655440001",
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Task enqueued"
}
```

### Task Message (Redis Queue)

```json
{
  "prompt": "What is machine learning?",
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "model": null,
  "metadata": {
    "query_id": "550e8400-e29b-41d4-a716-446655440001",
    "pipeline_id": "quiz_v1"
  }
}
```

### Result Message (Redis Channel)

```json
{
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "model": "gemini-2.0-flash",
  "output_text": "Machine learning is a subset of artificial intelligence...",
  "tokens_used": 156,
  "error": null,
  "user_id": "user_123",
  "created_at": "2026-05-10T14:32:15.123456+00:00",
  "metadata": {
    "query_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

---

## 🔍 Testing the Pipeline

### 1. Submit a Task

```powershell
curl -X POST http://localhost:8081/pipelines/quiz_v1/run `
  -H "Content-Type: application/json" `
  -H "X-Correlation-ID: $(New-Guid)" `
  -H "X-User-ID: user_123" `
  -d '{"message": "Explain neural networks in 2 sentences"}'
```

### 2. Connect WebSocket

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8081/ws/results/user_123');
ws.onopen = () => console.log('Connected to results stream');
ws.onmessage = (event) => {
    const result = JSON.parse(event.data);
    console.log('Result received:', result);
};
ws.onerror = (error) => console.error('WebSocket error:', error);
```

### 3. Check Database

```powershell
docker compose exec postgres psql -U ml_user -d ml_db

# View queries
SELECT id, user_id, state, created_at FROM queries;

# View responses
SELECT query_id, content, tokens_used FROM responses;
```

### 4. Monitor Redis

```powershell
docker compose exec redis redis-cli

# Check queue depths
LLEN task_queue
LLEN result_queue

# Monitor Pub/Sub (in separate terminal)
SUBSCRIBE "results:user_123"
```

### 5. View Logs

```powershell
# Gateway logs
docker compose logs gateway -f

# Orchestrator logs
docker compose logs orchestrator -f

# ML Worker logs
docker compose logs ml_worker -f
```

---

## 📁 Project Structure

```
Coursework-ML-Microservices/
├── README.md                  # This file
├── WORKFLOW.md                # Complete workflow documentation
├── ARCH_GUIDE.md              # Architecture blueprint
├── AGENTS.md                  # Development guidelines
├── docker-compose.yml         # Service orchestration
├── pyproject.toml             # Workspace manifest
│
├── gateway/                   # HTTP API & WebSocket bridge
│   ├── main.py
│   ├── api/v1/
│   │   ├── health.py
│   │   ├── query.py           # POST /pipelines/{pipeline_id}/run
│   │   └── websocket.py       # WS /ws/results/{user_id}
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── httpx_client.py
│   └── README.md
│
├── orchestrator/              # Task orchestration & DB state
│   ├── main.py                # FastAPI + result consumer lifespan
│   ├── api/v1/
│   │   └── run.py             # POST /api/run/{pipeline_id}
│   ├── services/
│   │   ├── query_service.py   # create_and_enqueue_task()
│   │   └── result_processor.py# ResultProcessor (background)
│   ├── repositories/          # Data access layer (DDD)
│   ├── db/
│   │   ├── models.py          # QueryModel, ResponseModel, LogModel
│   │   └── session.py
│   ├── migrations/            # Alembic schema versions
│   └── README.md
│
├── ml_worker/                 # Inference engine
│   ├── main.py                # asyncio + QueueConsumer
│   ├── runner.py              # InferenceRunner
│   ├── task_processor.py      # TaskProcessor
│   ├── loader.py              # GeminiModelLoader
│   ├── infrastructure/
│   │   └── gemini_adapter.py  # Gemini API wrapper
│   └── README.md
│
└── shared/                    # Cross-service utilities
    ├── messaging/
    │   ├── queue.py           # RedisQueue abstractions
    │   ├── pubsub.py          # RedisPubSub abstractions
    │   ├── consumer.py        # QueueConsumer[T] generic
    │   └── names.py           # Queue/channel name constants
    ├── schemas/               # Pydantic models
    │   ├── task.py            # TaskMessage
    │   ├── result.py          # ResultMessage
    │   └── query.py           # PipelineRequest/Response
    ├── core/
    │   ├── logging/           # LoggingContextMiddleware
    │   └── exception_handlers.py
    └── README.md
```

---

## 🌐 Environment Variables

### Root `.env`

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_DECODE_RESPONSES=False
DEBUG=True
```

### `gateway/.env`

```bash
PORT=8001
ORCHESTRATOR_URL=http://orchestrator:8003
AUTH_URL=http://auth:8002
HTTPX_TIMEOUT_SECONDS=60
HTTPX_MAX_CONNECTIONS=100
HTTPX_MAX_KEEPALIVE_CONNECTIONS=20
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
JWT_ENABLED=true
JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
JWT_ISSUER=
JWT_AUDIENCE=
JWT_USER_ID_CLAIM=sub
JWT_LEEWAY_SECONDS=0
JWT_PUBLIC_PATHS=["/","/health","/docs","/openapi.json","/auth/register","/auth/login","/auth/refresh","/auth/logout"]
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### `orchestrator/.env`

```bash
PORT=8003
DB_HOST=orchestrator-db
DB_PORT=5432
POSTGRES_DB=orchestrator_db
POSTGRES_USER=ml_user
POSTGRES_PASSWORD=change_me_in_local_dev
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
```

### `ml_worker/.env`

```bash
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1
GEMINI_TIMEOUT_SECONDS=30
ML_WORKER_DRY_RUN=false
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
```

### `auth/.env`

```bash
PORT=8002
DB_HOST=auth-db
DB_PORT=5432
POSTGRES_DB=auth_db
POSTGRES_USER=ml_user
POSTGRES_PASSWORD=change_me_in_local_dev
JWT_ENABLED=true
JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
JWT_ISSUER=
JWT_AUDIENCE=
JWT_USER_ID_CLAIM=sub
JWT_LEEWAY_SECONDS=0
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=14
```

---

## 🐛 Troubleshooting

### Services won't start in Docker Compose

**Issue:** Migrations fail or service exits with error.

```powershell
# View logs
docker compose logs orchestrator

# Restart with rebuild
docker compose down
docker compose up --build
```

### WebSocket not receiving results

**Issue:** Connected to `/ws/results/{user_id}` but no messages arrive.

```powershell
# Verify result consumer is running
docker compose logs orchestrator | grep -i "result"

# Check Redis is working
docker compose exec redis redis-cli LLEN result_queue
```

### Gemini API key not working

**Issue:** ML Worker logs "Invalid API key" errors.

```powershell
# Verify environment variable is set
docker compose exec ml_worker env | grep GEMINI_API_KEY

# Verify API key is valid by testing directly
# (check your Google Cloud project)
```

### Gateway can't reach Orchestrator

**Issue:** 503 Service Unavailable when calling `/pipelines/...`

```powershell
# Check orchestrator is running
docker compose logs orchestrator | head -20

# Verify network connectivity
docker compose exec gateway ping orchestrator
```

---

## 📚 Documentation

For detailed information, see:

- **[WORKFLOW.md](./WORKFLOW.md)** — Complete data flow, message schemas, state transitions
- **[ARCH_GUIDE.md](./ARCH_GUIDE.md)** — System design, DDD principles, coding standards
- **[AGENTS.md](./AGENTS.md)** — Development patterns, service patterns, roadmap
- **Service READMEs** — Service-specific setup and configuration

---

## 🛣️ Roadmap

### ✅ Completed (May 2026)

- ✅ Gateway HTTP proxying & request context middleware
- ✅ Orchestrator API endpoints & DDD layer (services, repos, entities)
- ✅ ML Worker task consumption & inference
- ✅ Redis task queue & result queue integration
- ✅ Result consumer (background service updating DB & publishing)
- ✅ WebSocket pub/sub bridge

### 🔮 Upcoming

1. **Error Handling & Resilience** — Dead-letter queues, retry logic, circuit breakers
2. **Monitoring & Observability** — Health endpoints, metrics, structured logging, tracing
3. **Advanced Features** — Multi-model support, caching, batch processing, analytics

---

## 📝 Development

### Running Tests

```powershell
# (Tests not yet implemented; use integration tests in Docker)
docker compose up --build  # Full integration test
```

### Code Quality

```powershell
# Type checking
basedpyright

# Linting
ruff check .

# Formatting
ruff format .
```

### Migrations (Orchestrator)

```powershell
# Generate new migration
uv run alembic -c orchestrator/alembic.ini revision --autogenerate -m "add new column"

# Apply migrations (automatic on startup)
uv run alembic -c orchestrator/alembic.ini upgrade head
```

---

## 📄 License

[Add license info here]

---

**Questions?** See [WORKFLOW.md](./WORKFLOW.md) for architecture details, or [AGENTS.md](./AGENTS.md) for development
guidelines.

