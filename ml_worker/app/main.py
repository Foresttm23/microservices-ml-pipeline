import asyncio

from loguru import logger

from shared.core import setup_logging
from shared.messaging import (
    RedisQueue,
    get_result_queue,
    get_task_queue,
)

from .loader import GeminiModelLoader
from .runner import InferenceRunner
from .task_processor import TaskProcessor
from .core.config import get_gemini_settings
from .messaging.queue_consumer import QueueConsumer
from .messaging.queue_publisher import ResultPublisher


def _init_processor(
    *,
    runner: InferenceRunner,
    result_queue: RedisQueue,
) -> TaskProcessor:
    """
    Initialize task processor with inference runner and result publisher.
    """
    publisher = ResultPublisher(queue=result_queue)
    task_processor = TaskProcessor(runner=runner, publisher=publisher)

    return task_processor


async def main():
    setup_logging()
    logger.info("Starting ML Worker service")

    settings = get_gemini_settings()

    # Initialize model loader and runner
    loader = GeminiModelLoader(settings=settings)
    runner = InferenceRunner(loader=loader)

    # Initialize Redis client and queues
    task_queue = get_task_queue()
    result_queue = get_result_queue()

    # Initialize publisher and processor
    task_processor = _init_processor(runner=runner, result_queue=result_queue)

    # Initialize and start queue consumer
    queue_consumer = QueueConsumer(task_processor=task_processor, queue=task_queue)

    logger.info("Starting queue consumer loop")
    await queue_consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
