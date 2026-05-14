import asyncio

from loguru import logger

from ml_worker.core.config import GeminiSettings, get_gemini_settings
from ml_worker.core.loader import GeminiModelLoader
from ml_worker.infra.gemini_adapter import (
    GeminiTextGenerator,
    MockTextGenerator,
    TextGenerator,
)
from ml_worker.services.task_processor import TaskProcessor
from ml_worker.worker.runner import InferenceRunner, Runner
from shared.core.logging import setup_logging
from shared.messaging import (
    Processor,
    QueueConsumer,
    QueuePublisher,
    RedisQueue,
    get_result_queue,
    get_task_queue,
)
from shared.schemas import ResultMessage, TaskMessage


def _init_processor(
    *,
    runner: Runner,
    result_queue: RedisQueue,
) -> Processor[TaskMessage, ResultMessage]:
    """
    Initialize the task processor with an inference runner and result publisher.
    """
    publisher = QueuePublisher(result_queue)
    task_processor = TaskProcessor(runner=runner, publisher=publisher)

    return task_processor


def _init_generator(
    settings: GeminiSettings,
) -> TextGenerator:
    """
    Strategy Pattern: Returns a real or mock generator based on settings.py.
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
    queue_consumer = QueueConsumer[TaskMessage, ResultMessage](
        processor=task_processor,
        queue=task_queue,
        message_factory=TaskMessage.model_validate_json,
    )

    logger.info("Starting queue consumer loop")

    await queue_consumer.run()


if __name__ == "__main__":
    with logger.contextualize(service="ml_worker"):
        asyncio.run(main())
