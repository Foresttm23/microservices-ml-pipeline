from loguru import logger

from shared.messaging import RedisQueue
from shared.schemas import ResultMessage


class ResultPublisher:
    def __init__(self, queue: RedisQueue):
        self._queue = queue
        logger.info("ResultPublisher initialized with queue '{}'", queue.name)

    async def publish(self, result: ResultMessage) -> None:
        """Publish a result message to the result queue."""
        try:
            payload = result.model_dump_json()
            await self._queue.enqueue(payload)
            logger.info(
                "Published result to queue interaction_id={} status={}",
                result.interaction_id,
                result.status,
            )
        except Exception as e:
            logger.error(
                "Failed to publish result interaction_id={}: {}",
                result.interaction_id,
                e,
            )
