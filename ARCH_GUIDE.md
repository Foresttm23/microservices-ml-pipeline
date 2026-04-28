# Project Blueprint: Microservice ML Quiz System

**Context for AI Agents & Development Sprint**

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

* **Tech:** Python, Pytorch/Transformers, RabbitMQ.
* **Role:** Consumes tasks from `task_queue`, executes inference, pushes result to `result_queue`.

## 3. Data Flow (The "Queue Conversation")

1. **Client POST /quiz** -> Gateway forwards to Orchestrator.
2. **Orchestrator** -> Saves record to Postgres (`PENDING`) -> Pushes task to **Redis Queue**.
3. **Orchestrator** -> Returns `202 Accepted` to Gateway -> Gateway returns to Client.
4. **ML Worker** -> Consumes task -> Runs model -> Pushes JSON to `result_queue`.
5. **Orchestrator Result Listener** -> Consumes from `result_queue`:
    * `UPDATE queries SET status='COMPLETED', result=...`
    * `REDIS.PUBLISH("results:{user_id}", data)`
6. **Gateway WebSocket** -> Hears Redis Publish -> Sends result to Client.

## 4. Coding Standards (DDD Enforcement)

### Repository Layer Rules

* Methods must return **Domain Entities**, not SQLAlchemy models.
* No `session.commit()` inside the Repository.
* Use specialized methods (e.g., `get_detailed_report`) instead of generic filters to avoid N+1 problems.

### Service Layer Rules

* Responsible for the **Unit of Work** (transaction management).
* Handles cross-domain logic (e.g., Calling DB and then calling the Queue).
* Returns **Pydantic Schemas** for the API layer.

### Directory Structure example

```text
/orchestrator
├── /app
│   ├── /api/v1      # FastAPI Routers
│   ├── /services    # Business Logic / Orchestration
│   ├── /domain      # Entities & Value Objects
│   ├── /repositories# Database Access
│   ├── /schemas     # Pydantic DTOs
│   └── /core        # Config, Exceptions, Logging