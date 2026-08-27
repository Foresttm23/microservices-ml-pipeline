from typing import Protocol


class ModelSettingsProtocol(Protocol):
    """Generic AI / ML provider settings protocol to allow easy model swapping."""

    API_KEY: str | None
    MODEL: str
    API_BASE: str
    TIMEOUT_SECONDS: float
    ML_WORKER_DRY_RUN: bool
