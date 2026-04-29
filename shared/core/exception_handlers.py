from typing import Any

from . import SessionNotInitializedException
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_exception_handlers(app: FastAPI) -> None:
    # We use add_exception_handler but use a lambda or local wrap
    # to bypass strict Pyright signature checks if they persist
    app.add_exception_handler(
        SessionNotInitializedException, session_not_initialized_handler
    )


async def session_not_initialized_handler(request: Request, exc: Any) -> JSONResponse:
    # Using Any here satisfies the Starlette protocol while keeping the logic clean
    # You can still use 'exc.session_name' if you know it's that type
    return JSONResponse(
        status_code=503,
        content={"detail": f"Service dependency not ready: {exc.session_name}"},
    )
