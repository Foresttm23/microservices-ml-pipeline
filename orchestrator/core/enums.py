from enum import StrEnum


class QueryState(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    MOCKED = "MOCKED"
