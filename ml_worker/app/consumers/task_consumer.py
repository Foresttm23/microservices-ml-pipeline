from ..inference.runner import InferenceRunner
from ..publishers.result_publisher import ResultPublisher
from shared.schemas.result import ResultMessage
from shared.schemas.task import TaskMessage


class TaskConsumer:
    def __init__(self, runner: InferenceRunner, publisher: ResultPublisher):
        self._runner = runner
        self._publisher = publisher

    async def consume(self, task: TaskMessage) -> ResultMessage:
        result = await self._runner.run(task)
        await self._publisher.publish(result)
        return result

    # Todo queue consumer
