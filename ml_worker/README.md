# ⚙️ ML Worker Service

The **ML Worker** is the inference engine. It consumes tasks from Redis, executes ML inference via Google Gemini API,
and publishes results back to Redis for the Orchestrator to process.

**Port:** 8082 (host) → 8002 (container)  
**Language:** Python (asyncio)  
**ML Provider:** Google Gemini API  
**Status:** ✅ Complete

---

## 🎯 Responsibilities

1. **Task Consumption**
    - Connect to Redis and block-wait on `task_queue`
    - Deserialize `TaskMessage` from JSON
    - Extract prompt, user context, and metadata

2. **Inference Execution**
    - Initialize Gemini model (real or mock)
    - Send prompt to Gemini API
    - Collect response text and token usage

3. **Result Publishing**
    - Create `ResultMessage` with status, output, tokens
    - Serialize to JSON
    - Publish to Redis `result_queue`
    - Handle errors and dry-run modes

4. **Task Processing Loop**
    - Run indefinitely (until shutdown)
    - Log all actions with correlation context
    - Graceful error handling (don't crash on single task failure)

---

## 📁 Directory Structure

```
ml_worker/
├── main.py                          # asyncio main + initialization
├── loader.py                        # GeminiModelLoader
├── runner.py                        # InferenceRunner (Runner protocol)
├── task_processor.py                # TaskProcessor
├── core/
│   ├── config.py                    # GeminiSettings
│   └── exceptions.py                # Custom exceptions
├── infrastructure/
│   └── gemini_adapter.py            # GeminiTextGenerator, MockTextGenerator
├── schemas/
│   └── text_generator.py            # GenerationResult
├── utils/
│   └── gemini.py                    # Gemini API helpers
├── Dockerfile
├── start.sh                         # Entry script
├── pyproject.toml                   # Service dependencies
└── README.md                        # This file
```

---

## ⚙️ Configuration

### Environment Variables

```bash
PORT=8002                              # Unused (no HTTP endpoints)
GEMINI_API_KEY=abc123...               # Required for live inference
GEMINI_MODEL=gemini-2.0-flash          # Model name (default)
GEMINI_API_BASE=https://...            # API base URL (optional)
GEMINI_TIMEOUT_SECONDS=30              # Request timeout (default: 30)
ML_WORKER_DRY_RUN=false                # true = mock inference, false = real
REDIS_HOST=redis                       # Redis hostname
REDIS_PORT=6379                        # Redis port
```

---

## 🚀 Quick Start

### Docker Compose

```powershell
docker compose up ml_worker
```

**Note:** Service runs as an infinite worker process (no web interface).

### Local Development

```powershell
$env:GEMINI_API_KEY = "your-api-key"
$env:REDIS_HOST = "localhost"
$env:ML_WORKER_DRY_RUN = "false"
uv run python -m ml_worker.main
```

**Prerequisites:**

- Redis running locally (port 6379)
- Orchestrator running (to enqueue tasks)
- Gemini API key set

---

## 📊 Processing Flow

### Task Processing Pipeline

```
1. QueueConsumer waits for message
   BLPOP task_queue 0  (blocking)
   ├─ Deserialize: TaskMessage.model_validate_json(raw_bytes)

2. TaskProcessor.process(task: TaskMessage)
   ├─ Set correlation context
   ├─ Call runner.run(task)
   │  ├─ Load model (lazy, cached)
   │  ├─ Call generator.generate(prompt, model)
   │  ├─ Receive GenerationResult {text, model, tokens}
   │  └─ Create ResultMessage
   ├─ Publisher.publish(result.model_dump_json())
   │  └─ RPUSH result_queue [ResultMessage JSON]
   └─ Log: "Task completed"

3. Loop continues
```

---

## 📨 Message Formats

### Task Message (Input from Redis)

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

### Result Message (Output to Redis)

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

## 🛠️ Development

### Dependencies

Key packages (see `pyproject.toml`):

- **google-generativeai** — Gemini API client
- **redis** — Redis client
- **loguru** — Structured logging
- **pydantic** — Validation
- **asyncio** — Native Python async

### Dry-Run Testing

```powershell
$env:ML_WORKER_DRY_RUN = "true"
uv run python -m ml_worker.main
```

This returns mock responses without calling Gemini API.

### Running Standalone

```powershell
# Ensure Redis is running
uv run python -m ml_worker.main

# In another terminal, publish test task
redis-cli RPUSH task_queue '{"prompt":"Test","correlation_id":"123...","user_id":"user_123"}'

# Monitor result_queue
redis-cli BLPOP result_queue 0
```

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY not set" error

```powershell
$env:GEMINI_API_KEY = "your-key"
echo $env:GEMINI_API_KEY
```

### "Redis connection refused"

```powershell
# Start Redis
redis-server
# Or in Docker
docker compose up redis
```

### "model_id not supported" error

```powershell
# Use valid model (check Gemini API docs)
$env:GEMINI_MODEL = "gemini-2.0-flash"
```

### Worker consumes task but doesn't produce result

```powershell
# Check logs
docker compose logs ml_worker | tail -50

# Increase timeout
$env:GEMINI_TIMEOUT_SECONDS = "60"
```

---

## 📈 Performance Tuning

### Model Caching

Model is cached in `GeminiModelLoader.load_model()` (lazy initialization).

---

## 📚 Related Services

- **Orchestrator** (`/orchestrator/README.md`) — Enqueues tasks, processes results
- **Gateway** (`/gateway/README.md`) — Routes client requests
- **Shared** (`/shared/README.md`) — Common schemas and messaging

---

**See Also:** [WORKFLOW.md](../WORKFLOW.md) for complete data flow and message schemas.
