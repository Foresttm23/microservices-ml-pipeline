# 🧠 Orchestrator Service

The **Orchestrator** is the brain of the system. It owns query state, orchestrates task execution, and coordinates
result consumption. Built with Domain-Driven Design (DDD) principles.

**Port:** 8001 (host) → 8001 (container)  
**Language:** Python (FastAPI + SQLAlchemy)  
**Database:** PostgreSQL 16 (Alembic migrations)  
**Status:** ✅ Complete

---

## 🎯 Responsibilities

1. **Task Creation & State Management**
    - Receive HTTP POST requests from Gateway
    - Create QueryModel records with PENDING state
    - Validate and enqueue tasks to Redis
    - Return 202 Accepted responses

2. **Background Result Processing**
    - Consume ResultMessage from result_queue
    - Update QueryModel states (COMPLETED/FAILED)
    - Persist ResponseEntity or LogEntity records
    - Publish results to Redis pub/sub channel

3. **Database Persistence**
    - Manage PostgreSQL schema (Alembic migrations)
    - Implement DDD repository pattern (entity-based)
    - Handle transactions and unit-of-work pattern
    - Maintain data consistency

4. **Health & Lifecycle**
    - Apply migrations on startup
    - Initialize result consumer background task
    - Graceful shutdown handling

---

## 📁 Directory Structure

```
orchestrator/
├── main.py                          # FastAPI app + lifespan
├── api/v1/
│   ├── __init__.py
│   ├── health.py                    # GET / (empty)
│   └── run.py                       # POST /api/run/{pipeline_id}
├── core/
│   ├── config.py                    # OrchestratorSettings
│   ├── dependencies.py              # FastAPI Depends factories
│   ├── enums.py                     # QueryState enum
│   └── exceptions.py                # Custom exceptions
├── db/
│   ├── base.py                      # Base ORM class + mixins
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── session.py                   # AsyncSession lifecycle
│   └── migrations/                  # Alembic (auto-generated)
├── repositories/
│   ├── __init__.py
│   ├── query_repository.py          # QueryRepository
│   ├── response_repository.py       # ResponseRepository
│   └── log_repository.py            # LogRepository
├── schemas/
│   ├── __init__.py
│   ├── query.py                     # QueryEntity
│   ├── response.py                  # ResponseEntity
│   └── log.py                       # LogEntity
├── services/
│   ├── __init__.py
│   ├── query_service.py             # QueryService
│   └── result_processor.py          # ResultProcessor
├── alembic.ini                      # Migration config
├── Dockerfile
├── start.sh                         # Entry script (runs migrations)
├── pyproject.toml                   # Service dependencies
└── README.md                        # This file
```

---

## 🔌 Endpoints

#### `POST /api/run/{pipeline_id}`

**Purpose:** Create and enqueue a task for processing.

**Request:**

```json
{
  "message": "What is machine learning?"
}
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

---

## ⚙️ Configuration

### Environment Variables

```bash
PORT=8001
DATABASE_URL=postgresql+asyncpg://ml_user:password@localhost:5432/ml_db
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## 🚀 Quick Start

### Docker Compose

```powershell
docker compose up orchestrator
```

### Local Development

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://ml_user:password@localhost:5432/ml_db"
$env:PORT = "8001"
uv run python -m orchestrator.main
```

---

## 📊 Data Flow

### Task Creation

1. Extract headers (correlation_id, user_id)
2. Validate PipelineRequest { message }
3. Create QueryEntity with state=PENDING
4. Save to PostgreSQL via QueryRepository
5. Commit transaction
6. Build TaskMessage with metadata
7. Enqueue TaskMessage to Redis task_queue
8. Return PipelineResponse with query_id

### Result Processing (Background)

1. ResultProcessor started in main.py lifespan
2. Listen for messages on result_queue (blocking)
3. For each ResultMessage:
    - Extract query_id from metadata
    - Fetch QueryModel from PostgreSQL
    - Call QueryService.handle_result()
    - Update state to COMPLETED/FAILED
    - Save ResponseEntity or LogEntity
    - Commit transaction
    - Publish to results:{user_id} Redis channel

---

## 🔄 State Machine

**States:**

- `PENDING` — Initial state after task creation
- `COMPLETED` — Inference succeeded; response saved
- `FAILED` — Inference failed; error logged
- `MOCKED` — Dry-run mode (dev/testing)

**Transitions:**

- PENDING → COMPLETED (on successful inference)
- PENDING → FAILED (on error)
- PENDING → MOCKED (on dry-run)

---

## 🛠️ Migrations

**Auto-generate migration after schema changes:**

```bash
uv run alembic -c orchestrator/alembic.ini revision --autogenerate -m "migration message"
```

**Apply migrations manually:**

```bash
uv run alembic -c orchestrator/alembic.ini upgrade head
```

**Note:** `start.sh` automatically applies migrations on startup.

---

## 🗄️ Database Schema

**tables:**

- `queries` — Task records (id, user_id, correlation_id, state, timestamps)
- `responses` — Generated responses (query_id FK, content, tokens_used)
- `logs` — Error logs (query_id FK, message, metadata JSONB)

---

## 📚 Related Services

- **Gateway** (`/gateway/README.md`) — Sends HTTP requests here
- **ML Worker** (`/ml_worker/README.md`) — Consumes tasks, publishes results
- **Shared** (`/shared/README.md`) — Common DDD utilities

---

**See Also:** [WORKFLOW.md](../WORKFLOW.md) for complete data flow and state transitions.

