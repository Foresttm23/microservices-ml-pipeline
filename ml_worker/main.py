import asyncio

from infrastructure.gemini_adapter import GeminiTextGenerator
from loguru import logger

from ml_worker.core.config import GeminiSettings, get_gemini_settings
from ml_worker.infrastructure.gemini_adapter import MockTextGenerator, TextGenerator
from ml_worker.loader import GeminiModelLoader
from ml_worker.messaging.queue_consumer import QueueConsumer
from ml_worker.messaging.queue_publisher import ResultPublisher
from ml_worker.runner import InferenceRunner, Runner
from ml_worker.task_processor import TaskProcessor, Processor
from shared.core import setup_logging
from shared.messaging import (
    RedisQueue,
    get_result_queue,
    get_task_queue,
)


def _init_processor(
    *,
    runner: Runner,
    result_queue: RedisQueue,
) -> Processor:
    """
    Initialize task processor with inference runner and result publisher.
    """
    publisher = ResultPublisher(queue=result_queue)
    task_processor = TaskProcessor(runner=runner, publisher=publisher)

    return task_processor


def _init_generator(
    settings: GeminiSettings,
) -> TextGenerator:
    """
    Strategy Pattern: Returns a real or mock generator based on settings.
    """
    if settings.ML_WORKER_DRY_RUN:
        logger.warning("Initializing ML Worker in DRY_RUN mode")
        return MockTextGenerator()

    return GeminiTextGenerator(settings)


async def main():
    setup_logging()
    logger.info("Starting ML Worker service")

    settings = get_gemini_settings()

    # Initialize model loader and runner
    generator = _init_generator(settings)
    loader = GeminiModelLoader(settings, generator)
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
