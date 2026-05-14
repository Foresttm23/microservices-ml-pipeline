from collections.abc import Mapping
from typing import Optional, Type

import httpx
from fastapi import Request, Response
from loguru import logger

from shared.core.config import CORRELATION_ID_HEADER, USER_ID_HEADER
from shared.core.exceptions.system import MissingRequestStateException

# Hop-by-hop headers that should not be forwarded
EXCLUDED_HEADERS = {
    "host",
    "content-length",
    "connection",
    "accept-encoding",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


async def proxy_request(
    request: Request,
    client: httpx.AsyncClient,
    base_url: str,
    *,
    timeout: int = 30,
    status_error_map: Optional[Mapping[int, Type[Exception]]] = None,
) -> Response:
    # 1. Header Preparation (Stay with Mapping/Headers)
    try:
        context_headers = {
            CORRELATION_ID_HEADER: request.state.correlation_id,
            USER_ID_HEADER: request.state.user_id,
        }
    except AttributeError:
        raise MissingRequestStateException("Context missing: correlation_id or user_id")

    headers = httpx.Headers(
        {k: v for k, v in request.headers.items() if k.lower() not in EXCLUDED_HEADERS}
    )
    headers.update(context_headers)

    logger.debug("Proxying {method} to {url}", method=request.method, url=base_url)

    # 2. Execute Upstream Request
    # Passing params=request.query_params here handles the merging safely
    response = await client.request(
        method=request.method,
        url=base_url,
        params=request.query_params,
        content=await request.body(),
        headers=headers,
        timeout=timeout,
    )

    # 3. Error Mapping
    if status_error_map and response.status_code in status_error_map:
        raise status_error_map[response.status_code]

    # 4. Return Response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers={
            k: v for k, v in response.headers.items() if k.lower() != "content-length"
        },
    )
