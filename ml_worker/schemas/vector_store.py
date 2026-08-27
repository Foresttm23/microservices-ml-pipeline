from typing import Any
from shared.schemas import BaseSchema


class RetrievedDoc(BaseSchema):
    content: str
    metadata: dict[str, Any] = {}
    score: float | None = None
