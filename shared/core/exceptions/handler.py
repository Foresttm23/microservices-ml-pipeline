from typing import Mapping

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from shared.core.exceptions.base import ErrorDefinition
from shared.core.exceptions.definitions import GENERAL_ERROR_MAP, SYSTEM_ERROR_MAP


def global_exception_handler(
    app: FastAPI,
    service_error_map: Mapping[type[Exception], ErrorDefinition] | None = None,
) -> None:
    # Service mapping first, since we need the parent lookup to go down the line
    error_map = {**(service_error_map or {}), **GENERAL_ERROR_MAP, **SYSTEM_ERROR_MAP}

    @app.exception_handler(Exception)
    async def unified_handler(request: Request, exc: Exception) -> JSONResponse:
        # 1. Lookup the parent class exception in our maps
        definition = get_error_definition(exc, error_map)

        # 2. If it's a known/mapped error, return a clean response (suppresses traceback)
        if definition:
            status_code = definition.status_code or 500
            detail = definition.detail or "Internal server error"

            # Log as warning for known service errors (no traceback)
            logger.bind(
                error_code=definition.code,
                status_code=status_code,
                path=request.url.path,
            ).warning("Handled service exception: {detail}", detail=detail)

            return JSONResponse(
                status_code=status_code,
                content={"detail": detail},
            )

        # 3. For truly unhandled exceptions, log with traceback and return 500
        logger.bind(
            error_code="unhandled_exception",
            path=request.url.path,
        ).exception("Unhandled exception occurred")

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Register specific handlers for each mapped exception type.
    # This ensures FastAPI treats them as "known" errors and avoids bubbling/logging.
    def create_handler(handler_fn):
        async def _handler(request: Request, exc: Exception) -> JSONResponse:
            return await handler_fn(request, exc)

        return _handler

    for exc_type in error_map.keys():
        app.add_exception_handler(exc_type, create_handler(unified_handler))


def get_error_definition(
    exc: Exception, error_map: Mapping[type[Exception], ErrorDefinition]
) -> ErrorDefinition | None:
    definition = next(
        (defn for exc_type, defn in error_map.items() if isinstance(exc, exc_type)),
        None,
    )
    return definition
