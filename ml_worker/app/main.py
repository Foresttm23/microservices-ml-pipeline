import asyncio

from redis.asyncio import Redis

from shared.core.logging import setup_logging
from shared.messaging import RedisQueue
from shared.messaging.names import RedisNamespace

from .consumers.queue_consumer import QueueConsumer
from .processors.task_processor import TaskConsumer
from .core.config import get_settings
from .inference.runner import InferenceRunner
from .models.loader import GeminiModelLoader
from .publishers.queue_publisher import ResultPublisher

# TODO initialize the queue


setup_logging()

settings = get_settings()
loader = GeminiModelLoader(settings=settings)

runner = InferenceRunner(loader=loader)


#
client = Redis.from_url(settings.REDIS_URL)
task_queue = RedisQueue(client=client, name=RedisNamespace.TASK_QUEUE)

publisher = ResultPublisher()
task_consumer = TaskConsumer(runner=runner, publisher=publisher)

queue_consumer = QueueConsumer(task_consumer=task_consumer, queue=task_queue)
#

asyncio.run(queue_consumer.run())
