import asyncio

from loguru import logger
from redis.asyncio import Redis

from shared.core import setup_logging
from shared.messaging import RedisNamespace, RedisQueue

from . import GeminiModelLoader, InferenceRunner, TaskProcessor
from .core import GeminiSettings, get_gemini_settings
from .messaging import QueueConsumer, ResultPublisher


def _init_queues(
    settings: GeminiSettings,
) -> tuple[RedisQueue, RedisQueue]:
    """
    Initialize Redis queues for task and result messaging.
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
    task_queue, result_queue = _init_queues(settings)

    # Initialize publisher and processor
    task_processor = _init_processor(runner=runner, result_queue=result_queue)

    # Initialize and start queue consumer
    queue_consumer = QueueConsumer(task_processor=task_processor, queue=task_queue)

    logger.info("Starting queue consumer loop")
    await queue_consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
