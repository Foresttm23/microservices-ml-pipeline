# ML Worker Service

Asynchronous inference worker powered by **LangGraph** and **ChromaDB RAG**. It consumes task requests from Redis `task_queue`, executes an agentic state-machine retrieval-augmented generation workflow, and publishes `ResultMessage` payloads to `result_queue`.

---

## 🧠 Core Architecture & Workflow

The worker executes a multi-node **LangGraph `StateGraph`** with built-in semantic query routing:

```
                      ┌─────────────────┐
                      │   User Query    │
                      └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ 1. route_query  │
                      └────────┬────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
       [route == 'retrieve']         [route == 'direct_chat']
                │                             │
                ▼                             ▼
       ┌─────────────────┐           ┌─────────────────┐
       │   2. retrieve   │           │ 4. direct_chat  │
       │   (ChromaDB)    │           │ (General Gemini)│
       └────────┬────────┘           └────────┬────────┘
                │                             │
                ▼                             │
       ┌─────────────────────────┐            │
       │ 3. generate_grounded_   │            │
       │         answer          │            │
       └────────┬────────────────┘            │
                │                             │
                └──────────────┬──────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   ResultMessage │
                      │ (to Redis Queue)│
                      └─────────────────┘
```

### LangGraph Nodes
1. **`route_query`**: Analyzes the query intent using structured classification to decide whether to query knowledge documents (`retrieve`) or perform casual conversation (`direct_chat`).
2. **`retrieve`**: Searches local **ChromaDB** using ONNX-based `all-MiniLM-L6-v2` embeddings for relevant knowledge base documents.
3. **`generate_grounded_answer`**: Synthesizes an accurate, citation-backed answer grounded strictly in the retrieved context using Google Gemini.
4. **`direct_chat`**: Direct conversational LLM response for greetings and general questions.

---

## 🗄️ Knowledge Base & Vector Store
- **Vector DB**: ChromaDB with cosine similarity search.
- **Embeddings**: Local in-process `all-MiniLM-L6-v2` ONNX embeddings (no external embedding API dependency, zero-cost, <10ms latency).
- **Knowledge Sources**: Automatically loaded from `ml_worker/knowledge/` (e.g. `about_creator.md`).

---

## ⚙️ Configuration

Settings are managed via `ml_worker/core/config.py` conforming to `ModelSettingsProtocol`.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `API_KEY` | Google Gemini API Key | `None` (triggers dry-run) |
| `MODEL` | Model name / ID | `gemini-2.0-flash` |
| `API_BASE` | Gemini API Base URL | `https://generativelanguage.googleapis.com/v1beta` |
| `TIMEOUT_SECONDS` | HTTP request timeout | `30.0` |
| `ML_WORKER_DRY_RUN`| Force mock execution without API calls | `false` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |

---

## 🚀 Running The Service

### Via Docker Compose (Recommended)
```powershell
docker compose up --build ml_worker
```

### Local Development
```powershell
$env:API_KEY = "your-gemini-api-key"
$env:MODEL = "gemini-2.0-flash"
$env:REDIS_URL = "redis://localhost:6379/0"
uv run python -m ml_worker.main
```

### Dry-run Mode (No API calls)
```powershell
$env:ML_WORKER_DRY_RUN = "true"
uv run python -m ml_worker.main
```
