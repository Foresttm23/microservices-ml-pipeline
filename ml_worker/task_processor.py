from shared.schemas import ResultMessage, TaskMessage

from ml_worker.messaging.queue_publisher import ResultPublisher
from ml_worker.runner import InferenceRunner


class TaskProcessor:
    def __init__(self, runner: InferenceRunner, publisher: ResultPublisher):
        self._runner = runner
        self._publisher = publisher

    async def process(self, task: TaskMessage) -> ResultMessage:
        result = await self._runner.run(task)
        await self._publisher.publish(result)
        return result
