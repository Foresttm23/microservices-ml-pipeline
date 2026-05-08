import asyncio
from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from loguru import logger
from pydantic import ValidationError

from shared.core.logging import logging_context
from shared.messaging.protocols import Processor
from shared.messaging.queue import RedisQueue


class ConsumerMessage(Protocol):
    correlation_id: UUID
    user_id: str


class QueueConsumer[MessageT: ConsumerMessage, ResultT]:
    """Consumes messages from a Redis queue and processes them."""

    def __init__(
        self,
        processor: Processor[MessageT, ResultT],
        queue: RedisQueue,
        message_factory: Callable[[str | bytes], MessageT],
    ):
        """

        :param processor:
        :param queue:
        :param message_factory: example: MessageT.model_validate_json
        """
        self._processor = processor
        self._queue = queue
        self._message_factory = message_factory

    async def run(self) -> None:
        while True:
            try:
                message = await self._queue.dequeue()
                if not message:
                    continue

                try:
                    task = self._message_factory(message)
                except ValidationError:
                    logger.exception(
                        "Failed to deserialize message from queue '{}'",
                        self._queue.name,
                    )
                    continue

                await self._run_task(task)
            except Exception as e:
                logger.error("Error in queue consumer loop: {}", e)
                await asyncio.sleep(1)  # Back off on errors

    async def _run_task(self, task: MessageT) -> None:
        with logging_context(task.correlation_id, task.user_id):
            logger.info("Received task")
            try:
                await self._processor.process(task)
                logger.info("Task completed")
            except Exception:
                logger.exception("Error processing task")
                raise
