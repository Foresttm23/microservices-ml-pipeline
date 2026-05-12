# 🔗 Shared Library

Common utilities, message schemas, and abstractions used by **Gateway**, **Orchestrator**, and **ML Worker** services.

**Language:** Python (Pydantic + asyncio)  
**Status:** ✅ Complete

---

## 🎯 Purpose

Serve as a **shared package** across the microservices monorepo, providing:

- Cross-service **message schemas** (TaskMessage, ResultMessage)
- **Redis abstractions** (queues, pub/sub)
- **Exception handling** and logging middleware
- Common **service interfaces** (repositories, services)
- **Configuration** management

---

## 📁 Directory Structure

```
shared/
├── core/
│   ├── config.py                    # Shared settings base
│   ├── exceptions.py                # Custom exception classes
│   ├── exception_handlers.py        # FastAPI exception middleware
│   └── logging/
│       ├── context.py               # LoggingContext, context_var
│       └── middleware.py            # LoggingContextMiddleware
├── messaging/
│   ├── base.py                      # RedisResource (base class)
│   ├── queue.py                     # RedisQueue (enqueue, dequeue)
│   ├── pubsub.py                    # RedisPubSub (publish, listen)
│   ├── consumer.py                  # QueueConsumer[T, R] generic
│   ├── publisher.py                 # QueuePublisher[T] generic
│   ├── protocols.py                 # Processor, Publisher, Consumer protocols
│   ├── names.py                     # RedisNamespace enum, result_channel()
│   └── __init__.py                  # Re-exports public APIs
├── schemas/
│   ├── base.py                      # BaseSchema (Pydantic v2)
│   ├── query.py                     # PipelineRequest, PipelineResponse
│   ├── task.py                      # TaskMessage
│   ├── result.py                    # ResultMessage
│   └── __init__.py                  # Re-exports
├── services/
│   └── base.py                      # BaseService[T, R] generic interface
├── utils/
│   └── forward_to_service.py        # forward_to_service() helper
├── __init__.py                      # Package-level re-exports
├── pyproject.toml                   # Shared package dependencies
└── README.md                        # This file
```

---

## 📦 Public API

### Import Reference

All public APIs are exported from `shared/__init__.py`:

```python
# Messaging
from shared import (
    RedisQueue,
    RedisPubSub,
    RedisResource,
    QueueConsumer,
    QueuePublisher,
    get_task_queue,
    get_result_queue,
    get_redis_client,
    result_channel,
    RedisNamespace,
)

# Schemas
from shared import (
    TaskMessage,
    ResultMessage,
    PipelineRequest,
    PipelineResponse,
    BaseSchema,
)

# Core utilities
from shared.core.exceptions import register_exception_handlers
from shared.core.logging import (
    LoggingContextMiddleware,
    setup_logging,
    get_context,
)
```

---

## 🔌 Message Schemas

### TaskMessage

Represents a task to be processed by ML Worker.

```python
from shared.schemas import TaskMessage

task = TaskMessage(
    prompt="What is ML?",
    correlation_id=uuid4(),
    interaction_id=uuid4(),
    user_id="user_123",
    metadata={"query_id": "550e..."}
)

# Serialize to JSON for Redis
json_bytes = task.model_dump_json().encode()

# Deserialize from Redis
task = TaskMessage.model_validate_json(json_bytes)
```

---

### ResultMessage

Represents a result from ML inference.

```python
from shared.schemas import ResultMessage

result = ResultMessage(
    correlation_id=...,
    status="completed",
    output_text="Machine learning is...",
    tokens_used=156,
    user_id="user_123",
    metadata={"query_id": "..."}
)
```

---

## 📨 Redis Queue Operations

```python
from shared.messaging import RedisQueue, get_task_queue, get_result_queue

# Get predefined queues
task_queue = get_task_queue()
result_queue = get_result_queue()

# Enqueue (push to tail)
await task_queue.enqueue(json_bytes)

# Dequeue (blocking pop from head)
message = await task_queue.dequeue()  # Blocks until message available

# Queue size
size = await task_queue.size()
```

**Operations:**

- `enqueue(payload: str | bytes)` → int (queue length)
- `dequeue() → str | bytes | None` (blocking)
- `size() → int` (current queue length)

---

## 🔊 Pub/Sub Operations

```python
from shared.messaging import RedisPubSub, get_redis_client, result_channel

# Create pub/sub client
pubsub = RedisPubSub(get_redis_client())

# Publish (fire-and-forget)
channel = result_channel("user_123")  # "results:user_123"
await pubsub.publish(channel, json_message)

# Subscribe and listen
async for message in pubsub.listen(channel):
    if isinstance(message, bytes):
        message = message.decode()
    result = json.loads(message)
```

---

## 🔄 Generic Consumers & Processors

### QueueConsumer[MessageT, ResultT]

Generic consumer that reads from a queue and processes messages.

```python
from shared.messaging import QueueConsumer
from shared.schemas import TaskMessage, ResultMessage

consumer = QueueConsumer[TaskMessage, ResultMessage](
    processor=my_processor,
    queue=task_queue,
    message_factory=TaskMessage.model_validate_json,
)

# Run forever (infinite loop)
await consumer.run()
```

---

### Processor Protocol

Interface for custom processors:

```python
from shared.messaging.protocols import Processor


class MyProcessor(Processor[TaskMessage, ResultMessage]):
    async def process(self, task: TaskMessage) -> ResultMessage:
# Implement processing logic
# Return ResultMessage
```

---

## 🏢 Logging Context

### LoggingContextMiddleware

FastAPI middleware that extracts request context and stores it for logging.

```python
from shared.core.logging import LoggingContextMiddleware, setup_logging

app = FastAPI(...)
setup_logging()
app.add_middleware(LoggingContextMiddleware)

# In handlers:
from shared.core.logging import get_context


@app.post("/endpoint")
async def handler():
    context = get_context()
    # context.correlation_id → UUID | None
    # context.user_id → str | None
```

---

## ⚙️ Configuration

All services use Pydantic `BaseSettings`:

```python
from pydantic_settings import BaseSettings


class SharedSettings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        env_file = ".env"
```

---

## 🛠️ Development

### Adding a New Schema

1. Create file in `schemas/`
2. Define Pydantic model inheriting from `BaseSchema`
3. Export from `schemas/__init__.py`

### Adding a New Redis Abstraction

1. Create in `messaging/`
2. Inherit from `RedisResource`
3. Implement async methods
4. Export from `messaging/__init__.py`

---

## 📚 Examples

### Task Submission

```python
from shared.schemas import TaskMessage
from shared.messaging import QueuePublisher, get_task_queue
from uuid import uuid4

task = TaskMessage(
    prompt="Generate a quiz question",
    correlation_id=uuid4(),
    interaction_id=uuid4(),
    user_id="user_123",
    metadata={"query_id": "550e8400..."}
)

publisher = QueuePublisher(get_task_queue())
await publisher.publish(task.model_dump_json())
```

### Result Subscription

```python
from shared.messaging import RedisPubSub, get_redis_client, result_channel
from shared.schemas import ResultMessage
import json

pubsub = RedisPubSub(get_redis_client())
channel = result_channel("user_123")

async for message in pubsub.listen(channel):
    if isinstance(message, bytes):
        message = message.decode()

    result = ResultMessage.model_validate_json(message)
    print(f"Result: {result.output_text}")
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'shared'"

```powershell
# From repo root
uv sync
```

### Redis connection errors

```powershell
# Check Redis is running
redis-cli ping

# Verify REDIS_HOST/REDIS_PORT
echo $env:REDIS_HOST
echo $env:REDIS_PORT
```

---

## 📚 Related Documentation

- **[WORKFLOW.md](../WORKFLOW.md)** — How services use shared schemas
- **[ARCH_GUIDE.md](../ARCH_GUIDE.md)** — Architecture principles
- **Service READMEs** — Gateway, Orchestrator, ML Worker

---

**Package Version:** 0.1.0  
**Python:** 3.13+  
**Key Dependencies:** pydantic, redis, loguru

