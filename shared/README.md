# shared

Cross-service contracts and utilities used by `gateway`, `orchestrator`, and `ml_worker`.

## Redis helpers

The `shared.redis` module provides a single Redis client with queue and pub/sub helpers
that share the same connection context.

```python
from shared.messaging import RedisClient

redis = RedisClient("messaging://localhost:6379/0", decode_responses=True)
await redis.task_queue.enqueue("payload")
message = await redis.task_queue.dequeue(timeout=1)
channel = redis.results_pubsub.channel_for("user-123")
await redis.results_pubsub.publish(channel, "result")
```

## Examples

Run the optional smoke example after setting `REDIS_URL`.

```bash
python -m shared.examples.redis_smoke
```
