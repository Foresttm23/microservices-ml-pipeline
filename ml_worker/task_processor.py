from typing import Protocol

from ml_worker.messaging.queue_publisher import Publisher
from ml_worker.runner import Runner
from shared.schemas import ResultMessage, TaskMessage


class Processor(Protocol):
    async def process(self, task: TaskMessage) -> ResultMessage: ...


class TaskProcessor(Processor):
    def __init__(self, runner: Runner, publisher: Publisher):
        self._runner = runner
        self._publisher = publisher

    async def process(self, task: TaskMessage) -> ResultMessage:
        result = await self._runner.run(task)
        await self._publisher.publish(result)
        return result
