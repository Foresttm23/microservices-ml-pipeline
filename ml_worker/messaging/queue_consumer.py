from __future__ import annotations

import asyncio
import json

from loguru import logger

from shared.messaging import RedisQueue
from shared.schemas import TaskMessage

from ml_worker.task_processor import TaskProcessor


class QueueConsumer:
    def __init__(self, task_processor: TaskProcessor, queue: RedisQueue):
        self._task_processor = task_processor
        self._queue = queue

    async def run(self):
        logger.info("Starting queue consumer loop on queue '{}'", self._queue.name)
        while True:
            try:
                message = await self._queue.dequeue(timeout=None)
                if message:
                    try:
                        # Deserialize message to TaskMessage
                        task_dict = json.loads(message)
                        task = TaskMessage(**task_dict)
                        logger.info(
                            "Received task interaction_id={}", task.interaction_id
                        )

                        # Process the task
                        result = await self._task_processor.process(task)
                        logger.info(
                            "Task completed interaction_id={} status={}",
                            result.interaction_id,
                            result.status,
                        )
                    except json.JSONDecodeError as e:
                        logger.error("Failed to deserialize task message: {}", e)
                    except Exception as e:
                        logger.error("Error processing task: {}", e)
            except Exception as e:
                logger.error("Error in queue consumer loop: {}", e)
                await asyncio.sleep(1)  # Back off on errors
