import time

from loguru import logger
from starlette.types import ASGIApp, Receive, Scope, Send


class ResponseLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only log HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        # We use a list or a dict to store the status code so the
        # inner send_wrapper can modify it (closure behavior)
        response_info = {"status": None}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_info["status"] = message["status"]

            await send(message)

        # Process the request
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Calculate duration even if an exception occurred
            process_time = (time.perf_counter() - start_time) * 1000
            status_code = response_info["status"]

            # Log Success (only if status exists and is < 400)
            if status_code and status_code < 400:
                method = scope.get("method", "")
                path = scope.get("path", "")

                logger.info(
                    f"SUCCESS | Method: {method} | "
                    f"Path: {path} | "
                    f"Status: {status_code} | "
                    f"Duration: {process_time:.2f}ms"
                )
