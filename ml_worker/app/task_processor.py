from shared.schemas import ResultMessage
from shared.schemas.task import TaskMessage

from inference.runner import InferenceRunner
from publishers.queue_publisher import ResultPublisher


class TaskProcessor:
    def __init__(self, runner: InferenceRunner, publisher: ResultPublisher):
        self._runner = runner
        self._publisher = publisher

    async def process(self, task: TaskMessage) -> ResultMessage:
        result = await self._runner.run(task)
        await self._publisher.publish(result)
        return result
