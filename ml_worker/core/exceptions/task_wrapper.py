import functools
from uuid import UUID, uuid4

from loguru import logger

from ml_worker.core.exceptions.definitions import ML_ERROR_MAP
from shared.core import QueryState
from shared.core.exceptions import get_error_definition
from shared.schemas import ResultMessage


def task_wrapper(func):
    @functools.wraps(func)
    async def wrapper(self, message, *args, **kwargs):
        # 1. Adopt Identity
        # Use .get() or getattr() depending on if message is a dict or Pydantic model
        raw_corr_id = getattr(message, "correlation_id", None) or str(uuid4())
        user_id = getattr(message, "user_id", "anonymous")
        interaction_id = getattr(message, "interaction_id", None) or uuid4()

        # 2. Rehydrate Context
        with logger.contextualize(correlation_id=raw_corr_id, user_id=user_id):
            try:
                result = await func(self, message, *args, **kwargs)
                return result

            except Exception as exc:
                definition = get_error_definition(exc, ML_ERROR_MAP)
                error_code = definition.code if definition else "ml_processing_failed"

                logger.bind(error_code=error_code).exception("Task processing failed")

                # Ensure correlation_id is a valid UUID object for the schema
                try:
                    valid_corr_id = UUID(str(raw_corr_id))
                except ValueError:
                    valid_corr_id = uuid4()

                return ResultMessage(
                    interaction_id=interaction_id,
                    correlation_id=valid_corr_id,
                    user_id=user_id,
                    status=QueryState.FAILED,
                    error=error_code,
                    model="unknown",
                )

    return wrapper
