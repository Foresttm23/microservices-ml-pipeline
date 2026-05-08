from ml_worker.runner import Runner
from shared.messaging import Publisher
from shared.messaging.protocols import Processor
from shared.schemas import ResultMessage, TaskMessage


class TaskProcessor(Processor[TaskMessage, ResultMessage]):
    def __init__(self, runner: Runner, publisher: Publisher[str | bytes]):
        self._runner = runner
        self._publisher = publisher

    async def process(self, task: TaskMessage) -> ResultMessage:
        result = await self._runner.run(task)
        await self._publisher.publish(result.model_dump_json())
        return result
