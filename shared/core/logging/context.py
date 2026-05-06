from contextlib import contextmanager
from uuid import UUID

from loguru import logger


@contextmanager
def logging_context(correlation_id: UUID, user_id: str | None):
    with logger.contextualize(correlation_id=correlation_id, user_id=user_id):
        yield
