from typing import Protocol
from uuid import uuid4

from loguru import logger

from ml_worker.core.exceptions.definitions import ML_ERROR_MAP
from ml_worker.core.loader import ModelLoader
from ml_worker.schemas.text_generator import GenerationResult
from shared.core.enums import QueryState
from shared.core.exceptions import get_error_definition
from shared.schemas import ResultMessage, TaskMessage


class Runner(Protocol):
    async def run(self, task: TaskMessage) -> ResultMessage: ...


class InferenceRunner(Runner):
    def __init__(self, loader: ModelLoader):
        self._loader = loader

    async def run(self, task: TaskMessage) -> ResultMessage:
        interaction_id = task.interaction_id or uuid4()
        logger.info("Starting inference: interaction_id={}", interaction_id)

        try:
            result: GenerationResult = await self._loader.generate_text(
                prompt=task.prompt,
                interaction_id=interaction_id,
            )
            status = QueryState.MOCKED if result.is_dry_run else QueryState.COMPLETED
            logger.info("Inference completed: status={} model={}", status, result.model)
            return ResultMessage(
                correlation_id=task.correlation_id,
                interaction_id=interaction_id,
                status=status,
                model=result.model,
                output_text=result.text,
                tokens_used=result.tokens_used,
                user_id=task.user_id,
                metadata=task.metadata,
            )
        except Exception as exc:
            definition = get_error_definition(exc, ML_ERROR_MAP)
            error_code = definition.code if definition else "ml_processing_failed"
            logger.bind(error_code=error_code).exception("Inference failed")
            return ResultMessage(
                correlation_id=task.correlation_id,
                interaction_id=interaction_id,
                status=QueryState.FAILED,
                model=task.model or "unknown",
                error=error_code,
                user_id=task.user_id,
                metadata=task.metadata,
            )
        finally:
            logger.info("Inference finished: interaction_id={}", interaction_id)
