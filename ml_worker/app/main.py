import asyncio

from loguru import logger
from redis.asyncio import Redis

from shared.core.logging import setup_logging
from shared.messaging import RedisQueue
from shared.messaging.names import RedisNamespace

from .consumers.queue_consumer import QueueConsumer
from .core.config import Settings, get_settings
from .inference.runner import InferenceRunner
from .models.loader import GeminiModelLoader
from .processors.task_processor import TaskProcessor
from .publishers.queue_publisher import ResultPublisher


async def main():
    """Main entrypoint for ml_worker service."""
    setup_logging()
    logger.info("Starting ML Worker service")

    settings = get_settings()

    # Initialize model loader and runner
    loader = GeminiModelLoader(settings=settings)
    runner = InferenceRunner(loader=loader)

    # Initialize Redis client and queues
    task_queue, result_queue = _init_queues(settings)

    # Initialize publisher and processor
    task_processor = _init_processor(runner=runner, result_queue=result_queue)

    # Initialize and start queue consumer
    queue_consumer = QueueConsumer(task_processor=task_processor, queue=task_queue)

    logger.info("Starting queue consumer loop")
    await queue_consumer.run()


if __name__ == "__main__":
    asyncio.run(main())


def _init_queues(
    settings: Settings,
) -> tuple[RedisQueue, RedisQueue]:
    """
    :param settings:
    :return: task_queue, result_queue
    """
    redis_client = Redis.from_url(settings.REDIS_URL)
    task_queue = RedisQueue(client=redis_client, name=RedisNamespace.TASK_QUEUE)
    result_queue = RedisQueue(client=redis_client, name=RedisNamespace.RESULT_QUEUE)

    return task_queue, result_queue


def _init_processor(
    *,
    runner: InferenceRunner,
    result_queue: RedisQueue,
) -> TaskProcessor:
    """
    :param runner:
    :param result_queue:
    :return: task_processor
    """
    publisher = ResultPublisher(queue=result_queue)
    task_processor = TaskProcessor(runner=runner, publisher=publisher)

    return task_processor
