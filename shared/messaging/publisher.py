
from loguru import logger

from shared.messaging.protocols import Publisher
from shared.messaging.queue import RedisQueue


class QueuePublisher(Publisher[str | bytes]):
    """Publishes raw payloads to a Redis queue."""

    def __init__(self, queue: RedisQueue) -> None:
        self._queue = queue

    async def publish(self, payload: str | bytes) -> None:
        """Publish a serialized payload to the queue."""
        try:
            await self._queue.enqueue(payload)
            logger.info("Published payload to queue '{}'", self._queue.name)
        except Exception:
            logger.exception(
                "Failed to publish payload to queue '{}'", self._queue.name
            )
