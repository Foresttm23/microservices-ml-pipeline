from shared.schemas import BaseSchema


class GenerationResult(BaseSchema):
    text: str
    model: str
    is_dry_run: bool = False
    tokens_used: int | None = None
