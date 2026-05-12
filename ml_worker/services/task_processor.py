from loguru import logger

from ml_worker.core.exceptions.task_wrapper import task_wrapper
from ml_worker.worker.runner import Runner
from shared.messaging import Publisher
from shared.messaging.protocols import Processor
from shared.schemas import ResultMessage, TaskMessage


class TaskProcessor(Processor[TaskMessage, ResultMessage]):
    def __init__(self, runner: Runner, publisher: Publisher[str | bytes]):
        self._runner = runner
        self._publisher = publisher

    # Since the processor is the last step before publishing results,
    # we can wrap the entire process in a try-except to catch any unhandled exceptions and log them with structured error codes.
    # We also have the correlation_id and user_id available in the context, so we can add them to the structured log.
    @task_wrapper
    async def process(self, task: TaskMessage) -> ResultMessage:
        logger.debug("Processing task")
        result = await self._runner.run(task)
        logger.info("Task processed: status={} model={}", result.status, result.model)
        await self._publisher.publish(result.model_dump_json())
        logger.info(
            "Task result published: status={} model={}",
            result.status,
            result.model,
        )
        return result
