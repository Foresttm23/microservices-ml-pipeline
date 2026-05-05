# Project Blueprint: Microservice ML Quiz System

**Context for AI Agents & Development Sprint**

## Implementation Status (May 2026)

**Current State:** ✅ End-to-end task submission pipeline is fully operational and deployed in Docker Compose.

### Completed Components
- ✅ Gateway: HTTP proxying with request context middleware
- ✅ Orchestrator: Full DDD implementation with API endpoints, services, and repositories
- ✅ ML Worker: Task consumption and inference with result publishing
- ✅ Messaging: Redis queues (`task_queue`, `result_queue`) fully integrated
- ✅ Database: PostgreSQL with Alembic migrations and query state tracking

### Next Priority Items
1. **Result Consumer**: Background service to consume `result_queue` and update query state to COMPLETED
2. **WebSocket Bridge**: Gateway WebSocket endpoint for real-time result streaming to clients
3. **Error Handling**: Implement FAILED state and retry logic
4. **Monitoring**: Add health endpoints and metrics collection

See `COMPLETION_SUMMARY.md` for detailed flow and current service status.

---

## 1. System Overview

A high-performance, asynchronous ML pipeline for quiz management and real-time result delivery.

* **Architecture:** Modular Monolith (transitioning to Microservices).
* **Communication:** Async Request-Reply (HTTP -> Queue -> Pub/Sub -> WebSocket).
* **Standards:** Domain-Driven Design (DDD), Repository Pattern, Unit of Work.

## 2. Service Definitions

### A. API Gateway (The Bouncer)

* **Tech:** FastAPI, Redis Pub/Sub.
* **Role:** Handles Auth (JWT), Rate Limiting, and WebSocket connections.
* **WebSocket Logic:** Subscribes to Redis channel `results:{user_id}` on connection. Pushes incoming data to client.

### B. Orchestrator (The Brain)

* **Tech:** FastAPI, PostgreSQL (SQLAlchemy 2.0), Redis/RabbitMQ.
* **Role:** Owns the State.
* **Layers:**
    * `api/`: HTTP endpoints.
    * `services/`: Orchestrates Repositories and external notifications.
    * `domain/`: Pure Entities (Business Objects).
    * `repositories/`: Database persistence logic (ID-only referencing).

### C. ML Worker (The Muscle)

* **Tech:** Python, Gemini API (or configurable ML provider), asyncio.
* **Role:** Consumes tasks from `task_queue`, executes inference, pushes result to `result_queue`.

## 3. Data Flow (The "Queue Conversation")

1. ✅ **Client POST /quiz** -> Gateway forwards to Orchestrator (with context headers).
2. ✅ **Orchestrator** -> Saves record to Postgres (`PENDING`) -> Pushes task to **Redis Queue**.
3. ✅ **Orchestrator** -> Returns `202 Accepted` to Gateway -> Gateway returns to Client.
4. ✅ **ML Worker** -> Consumes task -> Runs model (Gemini API) -> Pushes JSON to `result_queue`.
5. 🔄 **Orchestrator Result Listener** -> Consumes from `result_queue`:
     * Updates query record: `status='COMPLETED', result=...`
     * Publishes to Redis: `REDIS.PUBLISH("results:{user_id}", data)`
     * *(Currently in implementation; background consumer service needed)*
6. 🔄 **Gateway WebSocket** -> Hears Redis Publish -> Sends result to Client.
     * *(Currently in implementation; WebSocket bridge needed)*

## 4. Coding Standards (DDD Enforcement)

### General Rules

* Absolute imports across the project.
* Blank __init__.py files except for the /shared/ directory, which acts as a common library for other services.

### Repository Layer Rules

* Methods must return **Domain Entities**, not SQLAlchemy models.
* No `session.commit()` inside the Repository.
* Use specialized methods (e.g., `get_detailed_report`) instead of generic filters to avoid N+1 problems.

### Service Layer Rules

* Responsible for the **Unit of Work** (transaction management).
* Handles cross-domain logic (e.g., Calling DB and then calling the Queue).
* Returns **Pydantic Schemas** for the API layer.
