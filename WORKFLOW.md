# Workflow Documentation: ML Microservices Quiz Pipeline

**Purpose:** This document provides a comprehensive guide to the end-to-end data flow, schemas, service
responsibilities, and deployment architecture of the ML Microservices system.

**Last Updated:** May 2026
**Status:** ✅ End-to-end pipeline operational

---

## Table of Contents

1. [System Overview](#system-overview)
2. [End-to-End Data Flow](#end-to-end-data-flow)
3. [Service Architecture](#service-architecture)
4. [Message Schemas](#message-schemas)
5. [Query State Lifecycle](#query-state-lifecycle)
6. [Redis Messaging](#redis-messaging)
7. [Deployment Topology](#deployment-topology)
8. [Running the System](#running-the-system)

---

## System Overview

### Core Principles

- **Asynchronous Request-Reply Pattern:** Clients submit tasks via HTTP and receive results via WebSocket pub/sub.
- **Microservices Architecture:** Four independent services communicate via HTTP (gateway → orchestrator) and async
  messaging (Redis queues/channels).
- **Domain-Driven Design:** Orchestrator uses repository pattern, service layer orchestration, and clear domain entity
  boundaries.
- **Request Context Tracking:** All requests carry `correlation_id` and `user_id` headers processed by middleware and
  logged throughout.

### Technology Stack

| Component          | Technology                     | Purpose                                        |
|--------------------|--------------------------------|------------------------------------------------|
| API Layer          | FastAPI 0.100+                 | HTTP endpoints & WebSocket connections         |
| Message Broker     | Redis 7                        | Task queues & pub/sub channels                 |
| Database           | PostgreSQL 16 + SQLAlchemy 2.0 | Query state persistence & migrations (Alembic) |
| ML Model           | Google Gemini API              | Inference engine for text generation           |
| Task Processor     | Python asyncio                 | Concurrent task consumption & processing       |
| Dependency Manager | `uv` (Python package manager)  | Workspace management & lock file               |

---

## End-to-End Data Flow

### Stage-by-Stage Pipeline

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ POST /pipelines/{pipeline_id}/run
       │ Body: { message: "..." }
       │ Headers: X-Correlation-ID, X-User-ID
       ▼
┌──────────────────────────────────────────────────┐
│ 1. GATEWAY (Port 8080)                           │
│    - FastAPI HTTP endpoint                       │
│    - Extract context headers (correlation_id,    │
│      user_id) from client request               │
│    - Validate & forward to Orchestrator URL     │
└──────┬───────────────────────────────────────────┘
       │ Forward POST to http://orchestrator:8081/api/run/{pipeline_id}
       ▼
┌──────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR (Port 8081)                      │
│    - FastAPI HTTP endpoint                       │
│    - Create QueryModel(PENDING) in PostgreSQL    │
│    - Enqueue TaskMessage to Redis task_queue    │
│    - Return 202 Accepted with query_id          │
└──────┬────────────────────────────────────────────┘
       │ 202 Accepted → Gateway → Client
       │ (Query status stored as PENDING)
       │
       ├─────────────────────────────────────┐
       │ Parallel Async Processing            │
       ▼                                      ▼
┌──────────────────────┐         ┌─────────────────────────┐
│ 3. DATABASE (Postgres)        │ 4. TASK QUEUE (Redis)   │
│    - QueryModel table          │    - Queue: task_queue  │
│    - State: PENDING            │    - Consumption: FIFO  │
│    - Linked responses/logs     │    - Message: TaskMsg   │
│    - Created/Updated timestamps│       (JSON serialized) │
└──────────────────────┘         └────────────┬────────────┘
                                              │
                                              ▼
                            ┌─────────────────────────────────┐
                            │ 5. ML WORKER (Port 8082)        │
                            │    - asyncio QueueConsumer      │
                            │    - Dequeues from task_queue   │
                            │    - Runs Gemini inference      │
                            │    - Publishes ResultMessage to │
                            │      result_queue               │
                            └────────────┬────────────────────┘
                                         │ ResultMessage (JSON)
                                         ▼
                            ┌─────────────────────────────────┐
                            │ 6. RESULT QUEUE (Redis)         │
                            │    - Queue: result_queue        │
                            │    - Consumer: Orchestrator's   │
                            │      ResultProcessor service    │
                            └────────────┬────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────────────┐
                            │ 7. RESULT CONSUMER (Orchestrator)│
                            │    - Background QueueConsumer   │
                            │    - Parse ResultMessage        │
                            │    - Update QueryModel state to │
                            │      COMPLETED/FAILED           │
                            │    - Save responses/logs to DB  │
                            │    - Publish to Redis channel:  │
                            │      results:{user_id}          │
                            └────────────┬────────────────────┘
                                         │ Publish message to
                                         │ results:user_123
                                         ▼
                            ┌─────────────────────────────────┐
                            │ 8. PUB/SUB CHANNEL (Redis)      │
                            │    - Channel: results:{user_id} │
                            │    - Subscribers: Gateway WS    │
                            │      connections                │
                            └────────────┬────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────────────┐
                            │ 9. GATEWAY WEBSOCKET            │
                            │    - Client connected on        │
                            │      /ws/results               │
                            │    - Subscribed to              │
                            │      results:{user_id} channel  │
                            │    - Push result to client      │
                            └────────────┬────────────────────┘
                                         │ WebSocket message
                                         ▼
                                    ┌──────────┐
                                    │  Client  │
                                    │ Receives │
                                    │ Result   │
                                    └──────────┘
```

### Timeline Summary

| Stage | Service                   | Component                   | Duration | Status     |
|-------|---------------------------|-----------------------------|----------|------------|
| 1     | Gateway                   | HTTP proxy validation       | ~10ms    | ✅ Complete |
| 2     | Orchestrator              | Create DB record & enqueue  | ~50ms    | ✅ Complete |
| 3 & 4 | Async messaging           | Task published to Redis     | ~5ms     | ✅ Complete |
| 5     | ML Worker                 | Inference (Gemini API call) | ~3-10s   | ✅ Complete |
| 6     | Async messaging           | Result published to queue   | ~5ms     | ✅ Complete |
| 7     | Orchestrator              | Result consumed & processed | ~30ms    | ✅ Complete |
| 8 & 9 | Redis Pub/Sub → WebSocket | Result delivered to client  | ~10ms    | ✅ Complete |

**Total latency:** ~3-10 seconds (dominated by ML inference).

---

## Service Architecture

### 1. Gateway Service (`gateway/`)

**Purpose:** HTTP API frontman; handles request routing, context propagation, and WebSocket connections.

**Port:** 8080 (host) → 8000 (container)

**Directory Structure:**

```
gateway/
├── main.py                          # FastAPI app + lifespan
├── api/v1/
│   ├── health.py                    # GET /health
│   ├── query.py                     # POST /pipelines/{pipeline_id}/run (proxy)
│   └── websocket.py                 # WS /ws/results (Pub/Sub bridge)
├── core/
│   ├── config.py                    # Settings (ORCHESTRATOR_URL, HTTPX_TIMEOUT)
│   ├── dependencies.py              # FastAPI Depends factories
│   └── httpx_client.py              # HTTPX lifecycle management
├── utils/
│   └── context_helpers.py           # build_context_headers(), extract headers
└── start.sh                         # Entry point script
```

**Key Responsibilities:**

1. **HTTP Proxying** (`api/v1/query.py`):
    - Accept `POST /pipelines/{pipeline_id}/run` with `PipelineRequest` body
    - Extract request context (correlation_id, user_id) from headers using middleware
    - Forward to Orchestrator at `{ORCHESTRATOR_URL}/api/run/{pipeline_id}`
    - Return orchestrator's response (202 Accepted with query_id)

2. **Context Propagation** (`utils/context_helpers.py`):
    - Generate/extract `X-Correlation-ID` and `X-User-ID` headers
    - Store in request state via `LoggingContextMiddleware`
    - Pass downstream to orchestrator via `build_context_headers()`

3. **HTTPX Lifecycle** (`core/httpx_client.py`):
    - Initialize connection pool at FastAPI startup
    - Configure timeouts and max connections
    - Gracefully close at shutdown

4. **WebSocket Bridge** (`api/v1/websocket.py`, *in-progress*):
    - Accept WebSocket connections at `GET /ws/results`
    - Subscribe to `results:{user_id}` Redis channel
    - Forward pub/sub messages to connected WebSocket clients

**Dependencies:**

- FastAPI, httpx, loguru, pydantic
- Shared utilities: `PipelineRequest`, context helpers

---

### 2. Orchestrator Service (`orchestrator/`)

**Purpose:** Central state machine; owns query lifecycle and coordinates task flow.

**Port:** 8081 (host) → 8001 (container)

**Directory Structure:**

```
orchestrator/
├── main.py                          # FastAPI app + lifespan w/ result consumer
├── api/v1/
│   ├── health.py                    # GET /health
│   └── run.py                       # POST /api/run/{pipeline_id} (task creation)
├── core/
│   ├── config.py                    # OrchestratorSettings
│   ├── dependencies.py              # FastAPI Depends factories
│   ├── enums.py                     # QueryState enum
│   └── exceptions.py                # Custom exceptions
├── db/
│   ├── models.py                    # SQLAlchemy ORM: QueryModel, ResponseModel, LogModel
│   ├── base.py                      # Base class + CreatedAtMixin, UpdatedAtMixin
│   ├── session.py                   # AsyncSession lifecycle
│   └── migrations/                  # Alembic migrations (auto-generated)
├── repositories/
│   ├── query_repository.py          # QueryRepository(get_by_id, save, etc.)
│   ├── response_repository.py       # ResponseRepository for responses
│   └── log_repository.py            # LogRepository for error logs
├── schemas/
│   ├── query.py                     # QueryEntity, QueryCreate, QueryResponse
│   ├── response.py                  # ResponseEntity, ResponseResponse
│   └── log.py                       # LogEntity, LogResponse
├── services/
│   ├── query_service.py             # QueryService: create_and_enqueue_task(), handle_result()
│   └── result_processor.py          # ResultProcessor: process() → DB update + pub/sub
├── alembic.ini                      # Migration config
└── start.sh                         # Entry point (runs migrations)
```

**Key Responsibilities:**

1. **Task Creation & Enqueuing** (`services/query_service.py::create_and_enqueue_task`):
   ```
   Input:  correlation_id, user_id, message, pipeline_id
   |
   ├─ 1. Create QueryEntity with state=PENDING
   ├─ 2. Save to PostgreSQL via QueryRepository
   ├─ 3. Commit transaction
   ├─ 4. Construct TaskMessage from query data
   ├─ 5. Enqueue TaskMessage (JSON) to Redis task_queue
   └─ Output: query_id UUID
   ```

2. **Result Processing** (`services/result_processor.py::process`):
    - Background consumer (started in `lifespan`)
    - Listen on `result_queue`
    - For each `ResultMessage`:
        1. Extract query_id from metadata
        2. Fetch QueryModel from DB
        3. Call `QueryService.handle_result()` to:
            - Transition state PENDING → COMPLETED/FAILED
            - Save ResponseEntity or LogEntity
            - Commit DB transaction
        4. Publish to Redis channel `results:{user_id}` with result JSON

3. **Database State Management** (`db/models.py`, `repositories/`):
    - QueryModel: maps to `queries` table (user_id, correlation_id, state, timestamps)
    - ResponseModel: maps to `responses` table (query_id FK, content, tokens_used)
    - LogModel: maps to `logs` table (query_id FK, message, metadata JSONB)
    - Repository layer returns **domain entities** (not ORM models)
    - Service layer manages transactions and commits

4. **Migrations** (`alembic.ini`, `migrations/`):
    - Auto-generated via `alembic revision --autogenerate -m "..."`
    - Applied at startup by `orchestrator/start.sh` before FastAPI launch

**Dependencies:**

- FastAPI, SQLAlchemy 2.0, Alembic, asyncpg, redis
- Shared: `TaskMessage`, `ResultMessage`, messaging abstractions

---

### 3. ML Worker Service (`ml_worker/`)

**Purpose:** Inference engine; processes tasks and publishes results.

**Port:** 8082 (host) → 8000 (container)

**Directory Structure:**

```
ml_worker/
├── main.py                          # asyncio main + initialization
├── loader.py                        # GeminiModelLoader
├── runner.py                        # InferenceRunner (Protocol/impl)
├── task_processor.py                # TaskProcessor: consumes + publishes
├── core/
│   ├── config.py                    # GeminiSettings
│   └── exceptions.py                # Custom exceptions
├── infrastructure/
│   └── gemini_adapter.py            # GeminiTextGenerator, MockTextGenerator
├── schemas/
│   └── text_generator.py            # GenerationResult
├── utils/
│   └── gemini.py                    # Gemini API helpers
└── start.sh                         # Entry point (waits for Redis)
```

**Key Responsibilities:**

1. **Model Initialization** (`loader.py`):
    - `GeminiModelLoader`: lazy-loads Gemini credentials & config
    - Instantiates TextGenerator (real or mock based on `ML_WORKER_DRY_RUN`)

2. **Inference Execution** (`runner.py`):
    - `InferenceRunner`: implements `Runner` protocol
    - Takes `TaskMessage` input
    - Calls `TextGenerator.generate(prompt, model)` → `GenerationResult`
    - Returns `ResultMessage` with status, output_text, tokens_used

3. **Task Processing** (`task_processor.py`):
    - `TaskProcessor`: implements `Processor[TaskMessage, ResultMessage]`
    - Receives `TaskMessage` from queue
    - Calls `runner.run(task)` for inference
    - Publishes `ResultMessage` (JSON) to result_queue
    - Logs errors with correlation context

4. **Queue Consumption** (`main.py`):
    - Initialize Redis queues: `task_queue`, `result_queue`
    - Start `QueueConsumer[TaskMessage, ResultMessage]`:
        - Dequeues from task_queue (blocking)
        - Deserializes JSON → TaskMessage
        - Calls processor.process()
        - Logs with correlation_id/user_id context
    - Run forever (until shutdown)

**Dependencies:**

- google-generativeai (Gemini API)
- redis, asyncio, loguru, pydantic
- Shared: `TaskMessage`, `ResultMessage`, `QueueConsumer`, queue abstractions

---

### 4. Shared Utilities (`shared/`)

**Purpose:** Common libraries and abstractions shared by all services.

**Directory Structure:**

```
shared/
├── core/
│   ├── config.py                    # Shared settings (REDIS_HOST, DB_HOST, etc.)
│   ├── exceptions.py                # CustomException, ValidationError
│   ├── exception_handlers.py        # FastAPI exception handlers
│   └── logging/
│       ├── context.py               # LoggingContext, context_var
│       └── middleware.py            # LoggingContextMiddleware
├── messaging/
│   ├── base.py                      # RedisResource (connection pool)
│   ├── names.py                     # RedisNamespace enum, result_channel()
│   ├── queue.py                     # RedisQueue (enqueue, dequeue)
│   ├── pubsub.py                    # RedisPubSub (publish, listen)
│   ├── consumer.py                  # QueueConsumer[MessageT, ResultT]
│   ├── publisher.py                 # QueuePublisher
│   ├── protocols.py                 # Processor, Publisher, Consumer protocols
│   └── __init__.py                  # Re-exports all public APIs
├── schemas/
│   ├── base.py                      # BaseSchema (Pydantic v2 base class)
│   ├── query.py                     # PipelineRequest, PipelineResponse
│   ├── task.py                      # TaskMessage
│   ├── result.py                    # ResultMessage
│   └── __init__.py                  # Re-exports all schemas
├── services/
│   └── base.py                      # BaseService (generic CRUD interface)
├── utils/
│   └── forward_to_service.py        # forward_to_service() helper (for proxy)
└── pyproject.toml                   # Shared package dependencies
```

**Key Exports:**

From `shared/__init__.py`:

- `RedisQueue`, `RedisPubSub`, `RedisResource`
- `QueueConsumer`, `QueuePublisher`
- `TaskMessage`, `ResultMessage`
- `PipelineRequest`, `PipelineResponse`

---

## Message Schemas

### 1. HTTP Request/Response

#### PipelineRequest (Client → Gateway → Orchestrator)

```json
{
  "message": "What is machine learning?"
}
```

**Schema:** `shared/schemas/query.py`

```python
class PipelineRequest(BaseSchema):
    message: str
```

---

#### PipelineResponse (Orchestrator → Gateway → Client)

```json
{
  "status": "accepted",
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Task enqueued"
}
```

**Schema:** `shared/schemas/query.py`

```python
class PipelineResponse(BaseSchema):
    status: str
    query_id: UUID
    correlation_id: UUID
    message: str
```

**HTTP Status:** `202 Accepted` (async processing initiated)

---

### 2. Redis Task Queue Message

#### TaskMessage (Orchestrator → ML Worker via `task_queue`)

```json
{
  "prompt": "What is machine learning?",
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "model": null,
  "metadata": {
    "query_id": "550e8400-e29b-41d4-a716-446655440001",
    "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
    "pipeline_id": "quiz_v1"
  }
}
```

**Schema:** `shared/schemas/task.py`

```python
class TaskMessage(BaseSchema):
    prompt: str  # ML input
    correlation_id: UUID  # Trace across services
    interaction_id: UUID | None  # Gemini conversation ID
    user_id: str  # User identifier
    model: str | None  # Optional model override
    metadata: dict[str, Any]  # Extra context (query_id, pipeline_id)
```

**Serialization:** `task_payload.model_dump_json()` → UTF-8 bytes

---

### 3. Redis Result Queue Message

#### ResultMessage (ML Worker → Orchestrator via `result_queue`)

```json
{
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "model": "gemini-1.5-pro",
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

**Schema:** `shared/schemas/result.py`

```python
class ResultMessage(BaseSchema):
    correlation_id: UUID
    interaction_id: UUID
    status: Literal["completed", "failed", "mocked"]  # Query state
    model: str  # Model used
    output_text: str | None  # Generated response
    tokens_used: int | None  # API token count
    error: str | None  # Error message
    user_id: str
    created_at: datetime  # Timestamp
    metadata: dict[str, Any]  # Extra context
```

**Serialization:** `result.model_dump_json()` → UTF-8 bytes

---

### 4. Domain Entities (Orchestrator Internal)

#### QueryEntity

```python
class QueryEntity(BaseSchema):
    id: UUID  # Auto-generated
    user_id: str
    correlation_id: UUID
    interaction_id: UUID
    message: str
    state: QueryState  # PENDING, COMPLETED, FAILED, MOCKED
    created_at: datetime | None
    updated_at: datetime | None
```

**Persistence:** Mapped to `queries` table in PostgreSQL

---

#### ResponseEntity

```python
class ResponseEntity(BaseSchema):
    id: UUID
    query_id: UUID  # FK to QueryModel
    content: str  # Generated text
    tokens_used: int | None
    created_at: datetime | None
    updated_at: datetime | None
```

**Persistence:** Mapped to `responses` table in PostgreSQL

---

### Schema Mapping Across Pipeline

```
Client Request
  │
  ├─ PipelineRequest { message }
  │
  ▼ (Gateway)
  
Orchestrator HTTP Endpoint
  │
  ├─ PipelineRequest { message }
  ├─ context headers (correlation_id, user_id)
  │
  ├─ Create QueryEntity { user_id, correlation_id, message, state=PENDING }
  ├─ Create TaskMessage { prompt, correlation_id, interaction_id, user_id, metadata }
  │
  ├─ Enqueue TaskMessage (JSON) to task_queue
  │
  ├─ Response: PipelineResponse { status, query_id, correlation_id }
  │
  ▼
  
ML Worker Process
  │
  ├─ Dequeue from task_queue
  ├─ Deserialize JSON → TaskMessage
  ├─ Extract { prompt, user_id, model, metadata }
  ├─ Call Gemini API → GenerationResult { text, model, tokens_used }
  ├─ Create ResultMessage { correlation_id, status, output_text, tokens_used, user_id, metadata }
  ├─ Publish ResultMessage (JSON) to result_queue
  │
  ▼
  
Result Consumer (Orchestrator)
  │
  ├─ Dequeue from result_queue
  ├─ Deserialize JSON → ResultMessage
  ├─ Fetch QueryModel by query_id (from metadata)
  ├─ Call service.handle_result() to:
  │  ├─ Create ResponseEntity { query_id, content, tokens_used }
  │  ├─ Update QueryModel { state=COMPLETED }
  ├─ Commit DB transaction
  ├─ Publish to Redis channel results:{user_id} → ResultMessage (JSON)
  │
  ▼
  
Gateway WebSocket Subscriber
  │
  ├─ Listen on results:{user_id} channel
  ├─ Receive ResultMessage (JSON)
  ├─ Deserialize → send to WebSocket client
  │
  ▼
  
Client (Browser)
  ├─ Receive ResultMessage on WebSocket
  └─ Display result to user
```

---

## Query State Lifecycle

### State Enum Definition

**File:** `orchestrator/core/enums.py`

```python
class QueryState(StrEnum):
    PENDING = "PENDING"  # Initial state after task creation
    COMPLETED = "COMPLETED"  # Inference succeeded; response saved
    FAILED = "FAILED"  # Inference failed; error logged
    MOCKED = "MOCKED"  # Dry-run mode (dev/testing)
```

### State Transitions

```
┌──────────┐
│ PENDING  │  (Initial)
└────┬─────┘
     │
     ├─ ML Worker inference succeeds
     │  ├─ status = "completed"
     │  │
     │  ▼
     │  ┌──────────┐
     │  │COMPLETED │ (Result saved to DB)
     │  └──────────┘
     │
     ├─ ML Worker dry-run mode
     │  ├─ status = "mocked"
     │  │
     │  ▼
     │  ┌────────┐
     │  │MOCKED  │ (Test response)
     │  └────────┘
     │
     └─ ML Worker inference fails
        ├─ status = "failed"
        │
        ▼
        ┌────────┐
        │ FAILED │ (Error logged to DB)
        └────────┘
```

### Transition Rules

**Defined in:** `orchestrator/schemas/query.py::QueryEntity.transition_to()`

1. **PENDING → COMPLETED:** Triggered by ResultMessage with status="completed" or "mocked"
2. **PENDING → FAILED:** Triggered by ResultMessage with status="failed" or any exception
3. **COMPLETED/FAILED → (same state only):** Idempotent; reprocessing same result is safe
4. **COMPLETED → FAILED (or vice versa):** Not allowed; raises ValueError

### Side Effects Per Transition

| From    | To        | Action              | Database                                    | Redis                                      |
|---------|-----------|---------------------|---------------------------------------------|--------------------------------------------|
| PENDING | COMPLETED | Save ResponseEntity | QueryModel.state ← COMPLETED                | Publish ResultMessage to results:{user_id} |
| PENDING | FAILED    | Save LogEntity      | QueryModel.state ← FAILED, LogModel created | Publish error to results:{user_id}         |
| PENDING | MOCKED    | Save ResponseEntity | QueryModel.state ← COMPLETED                | Publish mocked result to results:{user_id} |

---

## Redis Messaging

### Queue Architecture

#### Task Queue (`task_queue`)

**Location:** Redis list at key `task_queue`

**Purpose:** Hold pending tasks for ML Worker consumption

**Operations:**

```
Orchestrator: RPUSH task_queue [TaskMessage JSON]   (Enqueue)
ML Worker:   BLPOP task_queue 0                     (Blocking dequeue)
```

**Characteristics:**

- FIFO (First In, First Out)
- Blocking dequeue: waits indefinitely for next task
- No message TTL (persists until consumed)
- Used by: `shared/messaging/queue.py::RedisQueue`

**Example Sequence:**

```
Time T0:  Orchestrator creates task
          Task JSON = '{"prompt": "...", "correlation_id": "...", ...}'
          RPUSH task_queue [Task JSON]
          
Time T0+1ms: ML Worker blocking on BLPOP
          Receives task immediately
          Processes inference
          
Time T0+5s: ML Worker finishes
          Publishes to result_queue
```

---

#### Result Queue (`result_queue`)

**Location:** Redis list at key `result_queue`

**Purpose:** Hold results from ML Worker for Orchestrator result consumer

**Operations:**

```
ML Worker:     RPUSH result_queue [ResultMessage JSON]  (Publish result)
Orchestrator:  BLPOP result_queue 0                     (Blocking consume)
```

**Characteristics:**

- FIFO consumption
- Blocking dequeue with timeout=0 (wait forever)
- Deserialization happens on dequeue
- Used by: `orchestrator/services/result_processor.py::ResultProcessor` (via QueueConsumer)

---

### Pub/Sub Channel Architecture

#### Results Broadcast Channel (`results:{user_id}`)

**Pattern:** `results:user_123`, `results:user_456`, etc.

**Purpose:** Deliver completed results to connected WebSocket clients

**Operations:**

```
Result Consumer:  PUBLISH results:{user_id} [ResultMessage JSON]  (Broadcast)
Gateway WS:       SUBSCRIBE results:{user_id}                    (Listen)
```

**Characteristics:**

- Multiple subscribers per channel (multiple browser tabs)
- Fire-and-forget (no persistence; if no subscribers, message is lost)
- Used by: `shared/messaging/pubsub.py::RedisPubSub`

**Example Sequence:**

```
Time T0: Orchestrator result consumer finishes processing
         PUBLISH results:user_123 [ResultMessage JSON]
         
Time T0+1ms: Gateway receives publish event
          Extracts ResultMessage JSON
          Sends to all WebSocket clients subscribed to user_123
          
Client receives: '{"status": "completed", "output_text": "...", ...}'
```

---

### Message Serialization

| Phase                 | Format            | Method                          | Deserialization                          |
|-----------------------|-------------------|---------------------------------|------------------------------------------|
| Redis Queue (enqueue) | JSON string UTF-8 | `TaskMessage.model_dump_json()` | `TaskMessage.model_validate_json(bytes)` |
| Redis Queue (dequeue) | Raw bytes         | Redis native                    | Automatic by consumer                    |
| Pub/Sub channel       | JSON string       | `result.model_dump_json()`      | Client-side parsing                      |

**Code Example (ML Worker):**

```python
# Deserialize from queue
raw_bytes = await task_queue.dequeue()
task: TaskMessage = TaskMessage.model_validate_json(raw_bytes)

# Process
result = await runner.run(task)

# Re-serialize & publish
await result_queue.enqueue(result.model_dump_json())
```

---

## Deployment Topology

### Docker Compose Services

**File:** `docker-compose.yml`

#### Service Matrix

| Service          | Port (Host:Container) | Image               | Health Check                   | Dependencies              | Key Environment                                        |
|------------------|-----------------------|---------------------|--------------------------------|---------------------------|--------------------------------------------------------|
| **redis**        | 6379:6379             | redis:7-alpine      | `redis-cli ping`               | None                      | N/A                                                    |
| **postgres**     | 5432:5432             | postgres:16-alpine  | `pg_isready -U $POSTGRES_USER` | None                      | POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB          |
| **gateway**      | 8080:8000             | gateway:latest      | None                           | redis (healthy)           | ORCHESTRATOR_URL, HTTPX_TIMEOUT_SECONDS                |
| **orchestrator** | 8081:8001             | orchestrator:latest | None                           | postgres, redis (healthy) | DB_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB |
| **ml_worker**    | 8082:8000             | ml_worker:latest    | None                           | redis (healthy)           | ML_WORKER_DRY_RUN, GEMINI_API_KEY                      |

---

### Startup Sequence

```
1. docker compose up --build

2. Start dependency services first:
   ├─ Redis starts (health check: redis-cli ping)
   ├─ Postgres starts (health check: pg_isready)

3. Once health checks pass:
   ├─ Orchestrator starts
   │  └─ orchestrator/start.sh waits for $DB_HOST:5432 (pg_isready)
   │  └─ Runs: uv run alembic -c orchestrator/alembic.ini upgrade head
   │  └─ Launches: uv run python -m orchestrator.main
   │  └─ Initializes result consumer in lifespan
   │
   ├─ Gateway starts
   │  └─ gateway/start.sh (no wait in script; depends_on handles it)
   │  └─ Launches: uv run python -m gateway.main
   │
   └─ ML Worker starts
      └─ ml_worker/start.sh waits for $REDIS_HOST:6379
      └─ Launches: uv run python -m ml_worker.main
      └─ Starts infinite QueueConsumer loop

4. All services healthy → pipeline ready for requests
```

---

### Environment Variables

#### Root `.env`

```bash
# Shared
REDIS_HOST=redis
REDIS_PORT=6379
DB_HOST=postgres
POSTGRES_USER=ml_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=ml_db
```

#### `gateway/.env`

```bash
PORT=8000
ORCHESTRATOR_URL=http://orchestrator:8001
HTTPX_TIMEOUT_SECONDS=60
HTTPX_MAX_CONNECTIONS=100
HTTPX_MAX_KEEPALIVE_CONNECTIONS=20
```

#### `orchestrator/.env`

```bash
PORT=8001
DATABASE_URL=postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:5432/{POSTGRES_DB}
REDIS_HOST=redis
REDIS_PORT=6379
```

#### `ml_worker/.env`

```bash
PORT=8000
REDIS_HOST=redis
REDIS_PORT=6379
ML_WORKER_DRY_RUN=false
GEMINI_API_KEY=your_gemini_key_here
```

---

### Network Communication

```
┌─────────────────────────────┐
│   Docker Compose Network    │
├─────────────────────────────┤
│                             │
│  Client (Host) ─────┐       │
│                     │       │
│  Host 8080 ────────► ┌──────────────┐
│                    │  Gateway     │
│                     │ Port 8000    │
│                     └──────┬───────┘
│                            │ Internal http://orchestrator:8001
│                            │
│                     ┌──────▼──────┐
│                    │ Orchestrator │
│  Host 8081 ◄───────┤ Port 8001    │
│                     └──────┬───────┘
│                            │ SQL queries
│                            │ Redis interactions
│                            │
│                   ┌────────┴────────┐
│                   │                 │
│                ┌──▼──────┐      ┌──▼─────┐
│              │ Postgres  │    │  Redis   │
│              │ Port 5432 │    │ Port 6379│
│              └───────────┘    └─────┬────┘
│                                     │ task_queue/result_queue
│                                     │
│                              ┌──────▼─────┐
│                             │  ML Worker  │
│                             │ Port 8000   │
│  Host 8082 ◄──────────────┤ (HTTPX OK)  │
│                             └─────────────┘
│                             
└─────────────────────────────┘
```

---

## Running the System

### Prerequisites

- Docker & Docker Compose
- Python 3.13+
- `uv` package manager
- Gemini API key (for ML inference; set `GEMINI_API_KEY`)

### Full Stack (Docker Compose)

```powershell
# From repo root
docker compose up --build

# Expected output:
# redis_1         | ...Ready to accept connections
# postgres_1      | ...database system is ready to accept connections
# orchestrator_1  | ...Alembic upgrade head (migrations applied)
# orchestrator_1  | ...Starting FastAPI app on 0.0.0.0:8001
# gateway_1       | ...Starting FastAPI app on 0.0.0.0:8000
# ml_worker_1     | ...Starting queue consumer loop
```

### Testing the Pipeline

#### 1. Create a task (via Gateway → Orchestrator)

```bash
curl -X POST http://localhost:8080/pipelines/quiz_v1/run \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-User-ID: user_123" \
  -d '{"message": "What is machine learning?"}'
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

#### 2. Query task status

```bash
curl http://localhost:8081/api/queries/550e8400-e29b-41d4-a716-446655440001
# (Not yet implemented; placeholder for next phase)
```

#### 3. Connect WebSocket client (when WS bridge is ready)

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/results');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Result:', JSON.parse(e.data));
```

#### 4. Check database (`docker exec`)

```powershell
# Access postgres container
docker compose exec postgres psql -U ml_user -d ml_db

# Query tasks
SELECT id, user_id, state, created_at FROM queries;

# Query responses
SELECT query_id, content, tokens_used FROM responses;
```

#### 5. Check Redis queues (`docker exec`)

```powershell
# Access redis container
docker compose exec redis redis-cli

# Check queue depth
LLEN task_queue
LLEN result_queue

# Peek at a message (raw JSON)
LRANGE task_queue 0 0
```

#### 6. Inspect logs

```powershell
# Gateway logs
docker compose logs gateway -f

# Orchestrator logs
docker compose logs orchestrator -f

# ML Worker logs
docker compose logs ml_worker -f
```

### Local Development (Without Docker)

**Requirement:** Redis and Postgres running locally, and environment variables set.

```powershell
# Terminal 1: Gateway
$env:ORCHESTRATOR_URL = "http://localhost:8001"
uv run python -m gateway.main

# Terminal 2: Orchestrator
$env:DATABASE_URL = "postgresql+asyncpg://ml_user:password@localhost:5432/ml_db"
uv run python -m orchestrator.main

# Terminal 3: ML Worker
uv run python -m ml_worker.main

# Terminal 4: Test
curl -X POST http://localhost:8080/pipelines/quiz_v1/run ...
```

---

## Troubleshooting

### Issue: Service won't start (port conflict)

**Solution:** Change ports in `docker-compose.yml` or kill existing process on the port.

```powershell
# Find process on port 8080
lsof -i :8080

# Kill process
taskkill /PID <pid> /F
```

### Issue: Orchestrator fails to apply migrations

**Solution:** Check PostgreSQL is healthy and DATABASE_URL is correct.

```bash
# Test DB connection
docker compose exec orchestrator psql $DATABASE_URL -c "\dt"
```

### Issue: ML Worker can't reach Gemini API

**Solution:** Verify `GEMINI_API_KEY` environment variable and API quota.

```bash
# Check in ml_worker container
docker compose exec ml_worker env | grep GEMINI
```

### Issue: WebSocket doesn't receive results

**Solution:** Result consumer may not be running; check orchestrator logs for errors.

```bash
docker compose logs orchestrator | grep -i "result"
```

---

## Next Steps (Roadmap)

### Immediate

- ✅ Task creation & enqueueing operational
- ✅ ML Worker inference & result publishing operational
- ✅ Result consumer updating DB & publishing to channels

### Phase 2: WebSocket Real-Time Results

- [ ] Implement `gateway/api/v1/websocket.py::ws_results_endpoint`
- [ ] Subscribe to `RedisPubSub` on connection
- [ ] Route messages to WebSocket client
- [ ] Handle reconnection & graceful disconnect

### Phase 3: Error Handling & Resilience

- [ ] Implement dead-letter queue for permanently failed tasks
- [ ] Add retry logic with exponential backoff
- [ ] Implement circuit breaker for Gemini API

### Phase 4: Monitoring & Observability

- [ ] Add structured logging with correlation IDs to all services
- [ ] Implement health endpoints (ready, live, detailed)
- [ ] Add metrics collection: queue depth, latency, error rates
- [ ] Create OpenTelemetry tracing across services

### Phase 5: Advanced Features

- [ ] Multi-model support (GPT, Claude, etc.)
- [ ] Caching layer for common queries
- [ ] Query history & analytics endpoints
- [ ] Batch task processing

---

## References

- **ARCH_GUIDE.md** — System design and architectural decisions
- **AGENTS.md** — Implementation guidelines and service patterns
- **Orchestrator API/v1** — Task creation endpoint logic
- **shared/messaging/** — Queue and pub/sub abstractions
- **docker-compose.yml** — Deployment configuration

---

**Document Version:** 1.0  
**Last Updated:** May 10, 2026  
**Status:** Complete & Operational ✅

