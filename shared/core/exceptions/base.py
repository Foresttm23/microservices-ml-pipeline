from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorDefinition:
    code: str
    status_code: int | None = None
    detail: str | None = None
