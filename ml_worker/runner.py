from typing import Protocol
from uuid import uuid4

from ml_worker.schemas.text_generator import GenerationResult

from ml_worker.loader import ModelLoader
from shared.schemas import ResultMessage, TaskMessage


class Runner(Protocol):
    async def run(self, task: TaskMessage) -> ResultMessage: ...


class InferenceRunner(Runner):
    def __init__(self, loader: ModelLoader):
        self._loader = loader

    # Todo add logger on failure
    async def run(self, task: TaskMessage) -> ResultMessage:
        interaction_id = task.interaction_id or str(uuid4())

        try:
            result: GenerationResult = await self._loader.generate_text(
                prompt=task.prompt,
                interaction_id=interaction_id,
            )
            return ResultMessage(
                interaction_id=interaction_id,
                status="mocked" if result.is_dry_run else "completed",
                model=result.model,
                output_text=result.text,
                user_id=task.user_id,
                metadata=task.metadata,
            )
        except Exception as exc:
            return ResultMessage(
                interaction_id=interaction_id,
                status="failed",
                model=task.model or "unknown",
                error=str(exc),
                user_id=task.user_id,
                metadata=task.metadata,
            )
