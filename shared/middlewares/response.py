import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class ResponseLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        # 1. Process the request (this goes into your services)
        response = await call_next(request)

        # 2. Calculate duration
        process_time = (time.perf_counter() - start_time) * 1000

        # 3. Log Success (only if status < 400)
        # Errors are handled by exception_handler
        if response.status_code < 400:
            logger.info(
                f"SUCCESS | Method: {request.method} | "
                f"Path: {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {process_time:.2f}ms"
            )

        return response
