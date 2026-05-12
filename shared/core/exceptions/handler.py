
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.core.exceptions.base import BaseAppException


def global_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(BaseAppException)
    async def base_exception_handler(request: Request, exc: BaseAppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
