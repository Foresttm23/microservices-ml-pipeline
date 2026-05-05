## 🔄 Complete Request Flow

```
Client Request
    ↓
Gateway (Port 8080)
    ├─ Extract headers: X-Correlation-ID, X-User-ID
    ├─ Log context information
    ├─ Proxy POST /pipelines/{pipeline_id}/run
    ↓
Orchestrator (Port 8081 in Docker)
    ├─ Receive POST /api/run/{pipeline_id}
    ├─ Extract context headers
    ├─ Parse message from body
    ├─ Create QueryModel (PENDING state) in PostgreSQL
    ├─ Build TaskMessage with prompt + metadata
    ├─ Enqueue to Redis task_queue
    ├─ Commit transaction
    ├─ Return 202 Accepted with query_id
    ↓
Redis
    ├─ Store task in queue
    ↓
ML Worker
    ├─ Consume task from queue
    ├─ Parse TaskMessage
    ├─ Process with Gemini API
    ├─ Publish result to result_queue
    ├─ Log completion
    ↓
202 Accepted Response to Client
```
