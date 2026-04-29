from typing import Annotated

from fastapi import Depends
from httpx import AsyncClient

from . import httpx_client_manager


async def get_httpx_client() -> AsyncClient:
    return await httpx_client_manager.client()


HTTPXClientDep = Annotated[AsyncClient, Depends(get_httpx_client)]
