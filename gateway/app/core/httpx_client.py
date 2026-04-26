from typing import Any

from app.core.exceptions import SessionNotInitializedException
from httpx import AsyncClient


class HTTPXClientManager:
    def __init__(self):
        self._client: AsyncClient | None = None

    def start(self, **client_kwargs: Any) -> None:
        """Initialize the client."""
        if self._client is None:
            self._client = AsyncClient(**client_kwargs)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def client(self) -> AsyncClient:
        if self._client is None:
            raise SessionNotInitializedException(session_name="HTTPX_Client")
        return self._client


httpx_client_manager = HTTPXClientManager()
