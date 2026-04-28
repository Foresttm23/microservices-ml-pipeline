import json

from shared.messaging import RedisQueue
from shared.schemas import TaskMessage

from ..processors.task_processor import TaskConsumer


class QueueConsumer:
    def __init__(self, task_consumer: TaskConsumer, queue: RedisQueue):
        self._task_consumer = task_consumer
        self._queue = queue

    async def run(self):
        while True:
            message = await self._queue.dequeue(timeout=None)
            if message:
                task_dict = json.loads(message)
                task = TaskMessage(**task_dict)
                await self._task_consumer.consume(task)
