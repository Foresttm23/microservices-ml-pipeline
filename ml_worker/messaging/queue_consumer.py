import asyncio
from typing import Protocol

from loguru import logger
from pydantic import ValidationError

from ml_worker.task_processor import Processor
from shared.core.logging import logging_context
from shared.messaging import RedisQueue
from shared.schemas import TaskMessage


class Consumer(Protocol):
    async def run(self) -> None: ...


class QueueConsumer:
    def __init__(self, task_processor: Processor, queue: RedisQueue):
        self._task_processor = task_processor
        self._queue = queue

    async def run(self) -> None:
        logger.info("Starting queue consumer loop on queue '{}'", self._queue.name)
        while True:
            try:
                message = await self._queue.dequeue()
                if not message:
                    continue

                try:
                    task = TaskMessage.model_validate_json(message)
                    await self._run_task(task)

                except ValidationError as e:
                    logger.error("Invalid task format or malformed JSON: {}", e)
                except Exception as e:
                    logger.error("Error processing task: {}", e)
            except Exception as e:
                logger.error("Error in queue consumer loop: {}", e)
                await asyncio.sleep(1)  # Back off on errors

    async def _run_task(self, task: TaskMessage) -> None:
        with logging_context(task.correlation_id, task.user_id):
            logger.info("Received task")
            result = await self._task_processor.process(task)
            logger.info("Task completed status={}", result.status)
