from typing import Protocol
from uuid import uuid4

from loguru import logger

from ml_worker.core.loader import ModelLoader
from ml_worker.schemas.text_generator import GenerationResult
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
            status = "mocked" if result.is_dry_run else "completed"
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
            logger.exception("Inference failed")
            return ResultMessage(
                correlation_id=task.correlation_id,
                interaction_id=interaction_id,
                status="failed",
                model=task.model or "unknown",
                error=str(exc),
                user_id=task.user_id,
                metadata=task.metadata,
            )
