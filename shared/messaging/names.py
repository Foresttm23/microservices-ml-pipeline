from enum import StrEnum


class RedisNamespace(StrEnum):
    TASK_QUEUE = "task_queue"
    RESULT_QUEUE = "result_queue"
    RESULT_CHANNEL_PREFIX = "results:"


def result_channel(user_id: str) -> str:
    return f"{RedisNamespace.RESULT_CHANNEL_PREFIX.value}{user_id}"
