from uuid import uuid4

from ..models.loader import GeminiModelLoader
from shared.schemas.result import ResultMessage
from shared.schemas.task import TaskMessage


class InferenceRunner:
	def __init__(self, loader: GeminiModelLoader):
		self._loader = loader

	async def run(self, task: TaskMessage) -> ResultMessage:
		interaction_id = task.interaction_id or str(uuid4())

		try:
			output_text, model_name, is_mocked = await self._loader.generate_text(
				prompt=task.prompt,
				interaction_id=interaction_id,
				model=task.model,
			)
			return ResultMessage(
				interaction_id=interaction_id,
				status="mocked" if is_mocked else "completed",
				model=model_name,
				output_text=output_text,
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

