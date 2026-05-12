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
    async def unified_handler(request: Request, exc: Exception):
        # Lookup the parent class exception
        definition = get_error_definition(exc, error_map)
        if not definition:
            logger.bind(error_code="unhandled_exception").exception(
                "Unhandled exception"
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        status_code = definition.status_code or 500
        detail = definition.detail or "Internal server error"
        logger.bind(error_code=definition.code).warning(
            "Handled service exception: {detail}", detail=detail
        )
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )


def get_error_definition(
    exc: Exception, error_map: Mapping[type[Exception], ErrorDefinition]
) -> ErrorDefinition | None:
    definition = next(
        (defn for exc_type, defn in error_map.items() if isinstance(exc, exc_type)),
        None,
    )
    return definition
