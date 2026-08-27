# 🚀 ML Microservices Chat Pipeline

This project was built to explore and understand the internals of modern, high-performance asynchronous AI chat pipelines. With AI chat interfaces becoming mainstream, designing and implementing this architecture from scratch provides deep insights into microservices coordination, asynchronous task queues, real-time WebSocket communication, and distributed state management. This implementation serves as a robust, production-ready blueprint that can easily be expanded into a full-scale, feature-rich chat system if needed.

The system is an asynchronous, high-performance microservices architecture for ML-powered chat processing and real-time result delivery.

**Status:** ✅ End-to-end pipeline fully operational  
**Last Updated:** May 2026

---

## 📋 Quick Links

- **[AGENTS.md](./AGENTS.md)** — Development guidelines and agent workflows

Service-specific documentation:

- **[Gateway README](./gateway/README.md)** — HTTP proxy & WebSocket bridge
- **[Orchestrator README](./orchestrator/README.md)** — Task orchestration & state management
- **[ML Worker README](./ml_worker/README.md)** — Inference engine & task processor
- **[Auth README](./auth/README.md)** — JWT auth & refresh tokens
- **[Shared README](./shared/README.md)** — Common utilities & messaging abstractions

---

## 🔄 System Overview

A **5-service microservices architecture** with dedicated Auth and ML processing pipelines:

```
┌─────────────────────────────────────────────────────────────────┐
│              CLIENT (Frontend) (Port 8080)                      │
│        React Dashboard for Submission & Visualization           │
└──────┬─────────────────────────────────────────────▲────────────┘
       │                                             │
       │ 1. Request                                  │ 6. WS Result
       ▼                                             │
┌──────────────┐                                     │
│   GATEWAY    │─────────────────────────────────────┘
│ (Port 8081)  │────────▶┌────────────────────────────────────────┐
│ - Edge Proxy │◀────────│       AUTH SERVICE (Port 8082)         │
│ - WS Bridge  │ 2. Auth │   - JWT Issuance & Token Rotation      │
└──────┬───────┘  Check  │   - User Identity Management           │
       │                 └─────────────┬──────────────────────────┘
       │                               ▼
       │ 3. Forward              ┌──────────────────────────┐
       │    Request              │     AUTH DB (Postgres)   │
       ▼                         └──────────────────────────┘
┌──────────────────────────┐
│ ORCHESTRATOR (Port 8083) │◀──────────────────────────────┐
│ - Task Logic & State     │                               │
│ - Result Consumption     │────────┐                      │ 5. Results
└──────┬───────────────────┘        │                      │
       │                            ▼                      │
       │ 4. Enqueue         ┌──────────────────────────┐   │
       │    Task            │   ORCHESTRATOR DB (PG)   │   │
       ▼                    └──────────────────────────┘   │
┌──────────────┐                                           │
│    REDIS     │───────────────────────────────────────────┘
│ (Queues/Pub) │◀──────────────┐
└──────┬───────┘               │
       │                       │
       │ Dequeue               │ Results
       ▼                       │
┌──────────────┐               │
│  ML WORKER   │───────────────┘
│ (Port 8084)  │──────▶┌──────────────────────────┐
│ - LangGraph  │       │    GOOGLE GEMINI API     │
│   Workflow   │       │   (Inference Engine)     │
│ - ChromaDB   │       └──────────────────────────┘
│   RAG Search │
└──────────────┘
```

**Workflow Summary:**

1. **Frontend** sends requests through the **Gateway**.
2. **Gateway** validates identity with the **Auth Service** (backed by its own DB).
3. **Gateway** proxies valid requests to the **Orchestrator**.
4. **Orchestrator** saves task state to **Orchestrator DB** and enqueues the task to **Redis**.
5. **ML Worker** consumes the task, executes a **LangGraph StateGraph** with semantic query routing, queries **ChromaDB** for knowledge context, and synthesizes grounded answers with **Google Gemini**.
6. **ML Worker** returns results to **Redis**, which are consumed by the **Orchestrator**.
7. **Gateway** (via WebSocket) retrieves the results from **Redis Pub/Sub** and streams them live to the **Frontend**.

---

## 🧠 Agentic RAG & LangGraph Architecture

The ML Worker uses **LangGraph** to execute a stateful, decision-driven RAG pipeline:
- **Semantic Query Routing (`route_query`)**: Classifies whether a prompt requires knowledge retrieval (`retrieve`) or general conversation (`direct_chat`).
- **In-Process Vector Store (`retrieve`)**: Performs cosine similarity search over local **ChromaDB** collections using embedded `all-MiniLM-L6-v2` ONNX models (zero external embedding API overhead).
- **Grounded Answer Synthesis (`generate_grounded_answer`)**: Augments prompts with retrieved context chunks, cites source documents, and invokes Google Gemini.

---

## 🛠️ Tech Stack

| Component        | Technology                          | Version                                |
|------------------|-------------------------------------|----------------------------------------|
| Frontend         | HTML/JS (Vanilla/React)             | Modern                                 |
| Web Framework    | FastAPI                             | 0.100+                                 |
| Agent Framework  | LangGraph & LangChain               | 1.2+ / Core 1.6+                       |
| Vector Database  | ChromaDB (all-MiniLM-L6-v2 ONNX)    | 1.5+                                   |
| Message Broker   | Redis                               | 7 (Alpine)                             |
| Database         | PostgreSQL                          | 16 (Alpine) + SQLAlchemy 2.0 + Alembic |
| ML Model         | Google Gemini API                   | 2.0-flash / 2.5-flash                  |
| Task Processing  | Python asyncio                      | 3.13+                                  |
| Package Manager  | uv                                  | Latest                                 |
| Containerization | Docker & Docker Compose             | Latest                                 |

---

## 🚀 Getting Started


### Prerequisites

- **Docker & Docker Compose** (Recommended)
- **OR** Python 3.13+, `uv`, local PostgreSQL, local Redis
- **Gemini API Key** (Required for ML Worker)

### Quick Start: Docker Compose

```powershell
# Clone and navigate to project
cd Coursework-ML-Microservices

# Create .env from sample
copy .env.sample .env

# Start all services
docker compose up --build
```

**Exposed Ports (Host):**

- **Frontend:** [http://localhost:8080](http://localhost:8080)
- **Gateway:** [http://localhost:8081](http://localhost:8081)
- **Auth:** [http://localhost:8082](http://localhost:8082)
- **Orchestrator:** [http://localhost:8083](http://localhost:8083)
- **ML Worker:** [http://localhost:8084](http://localhost:8084) (Internal only)
- **Postgres:** `localhost:5432` (Auth), `localhost:5433` (Orchestrator)
- **Redis:** `localhost:6379`

### Local Development (Without Docker)

**Terminal 1: Redis & Postgres**
Ensure Redis is running on `6379` and Postgres on `5432`/`5433`.

**Terminal 2: Auth Service (Port 8002)**

```powershell
$env:PORT = "8002"
$env:DB_HOST = "localhost"
uv run python -m auth.main
```

**Terminal 3: Orchestrator (Port 8003)**

```powershell
$env:PORT = "8003"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5433"
uv run python -m orchestrator.main
```

**Terminal 4: Gateway (Port 8001)**

```powershell
$env:PORT = "8001"
$env:ORCHESTRATOR_URL = "http://localhost:8003"
$env:AUTH_URL = "http://localhost:8002"
uv run python -m gateway.main
```

**Terminal 5: ML Worker**

```powershell
$env:GEMINI_API_KEY = "your-api-key"
uv run python -m ml_worker.main
```

---

## 📊 Complete Request Flow

1. **CLIENT REQUEST**: `POST /pipelines/{pipeline_id}/run` to Gateway (Port 8081).
2. **GATEWAY**: Validates JWT, adds context headers, and proxies to Orchestrator.
3. **ORCHESTRATOR**: Creates `PENDING` query in DB, enqueues `TaskMessage` to Redis, returns `202 Accepted`.
4. **ML WORKER**: Dequeues task, calls Gemini API, publishes `ResultMessage` to Redis.
5. **ORCHESTRATOR CONSUMER**: Dequeues result, updates DB to `COMPLETED`, publishes to `results:{user_id}` channel.
6. **GATEWAY WEBSOCKET**: Pushes result to connected client via `ws://localhost:8081/ws/results/{user_id}`.

---

## 🔌 Key Endpoints

### Gateway (Port 8081)

| Method | Endpoint                       | Purpose                               |
|--------|--------------------------------|---------------------------------------|
| POST   | `/pipelines/{pipeline_id}/run` | Submit task (proxied to orchestrator) |
| GET    | `/ws/results/{user_id}`        | WebSocket subscription for results    |
| POST   | `/auth/login`                  | User authentication                   |

### Orchestrator (Port 8083)

| Method | Endpoint                 | Purpose                |
|--------|--------------------------|------------------------|
| POST   | `/api/run/{pipeline_id}` | Task creation endpoint |
| GET    | `/health`                | Health check           |

---

## 📁 Project Structure

```
Coursework-ML-Microservices/
├── gateway/                   # HTTP API & WebSocket bridge
│   ├── api/v1/                # Routes (query, websocket, auth)
│   ├── core/                  # Lifespan, Config, HTTPX client
│   └── utils/                 # Context & Proxy helpers
│
├── orchestrator/              # Task orchestration & DB state
│   ├── api/v1/                # Task submission endpoints
│   ├── services/              # QueryService & ResultProcessor
│   ├── repositories/          # DDD Repositories (Query, Response, Log)
│   ├── db/                    # SQLAlchemy Models & Migrations
│   └── schemas/               # Domain entities (Pydantic)
│
├── ml_worker/                 # Inference engine
│   ├── worker/                # InferenceRunner logic
│   ├── services/              # TaskProcessor (queue logic)
│   ├── infra/                 # Gemini API Adapter
│   └── main.py                # Async worker entry point
│
├── auth/                      # Identity service
│   ├── api/v1/                # JWT & User endpoints
│   └── db/                    # User models & migrations
│
├── shared/                    # Cross-service library
│   ├── messaging/             # Redis Queue/PubSub abstractions
│   ├── schemas/               # Shared Pydantic messages
│   └── core/                  # Logging & Exception handlers
│
└── frontend/                  # React/Vite dashboard
```

---

## 🧪 Testing

The project uses `pytest` for unit and integration testing.

```powershell
# Run all tests
uv run pytest

# Run specific service tests
uv run pytest orchestrator/tests
uv run pytest gateway/tests
uv run pytest ml_worker/tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

