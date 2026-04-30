from functools import lru_cache

from redis.asyncio import Redis

from shared.core import get_shared_settings
from shared.messaging.base import RedisResource
from shared.messaging.names import RedisNamespace, result_channel
from shared.messaging.pubsub import RedisPubSub
from shared.messaging.queue import RedisQueue

__all__ = [
    "RedisPubSub",
    "RedisQueue",
    "RedisResource",
    "RedisNamespace",
    "result_channel",
    "get_task_queue",
    "get_result_queue",
    "get_redis_client",
]


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    shared_settings = get_shared_settings()
    redis_client = Redis.from_url(shared_settings.REDIS_URL)
    return redis_client


@lru_cache(maxsize=1)
def get_task_queue() -> RedisQueue:
    redis_client = get_redis_client()
    task_queue = RedisQueue(client=redis_client, name=RedisNamespace.TASK_QUEUE)
    return task_queue


@lru_cache(maxsize=1)
def get_result_queue() -> RedisQueue:
    redis_client = get_redis_client()
    result_queue = RedisQueue(client=redis_client, name=RedisNamespace.RESULT_QUEUE)
    return result_queue
