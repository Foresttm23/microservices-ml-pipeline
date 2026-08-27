from uuid import UUID
from typing import Protocol

from ml_worker.core.config import GeminiSettings
from ml_worker.infra.gemini_adapter import TextGenerator
from ml_worker.schemas.text_generator import GenerationResult


class ModelLoader(Protocol):
    async def generate_text(
        self, prompt: str, interaction_id: UUID
    ) -> GenerationResult: ...


class GeminiModelLoader(ModelLoader):
    def __init__(self, settings: GeminiSettings, generator: TextGenerator):
        self._settings = settings
        self._generator = generator


    async def generate_text(
        self,
        prompt: str,
        interaction_id: UUID,
    ) -> GenerationResult:
        result = await self._generator.generate(prompt, interaction_id)
        return result
