import httpx
from fastapi import Request, Response
from loguru import logger

from gateway.utils.context_helpers import build_context_headers


async def forward_to_service(
    request: Request, client: httpx.AsyncClient, target_url: str, timeout: int = 30
) -> Response:
    """A reusable engine to move a request from A to B with context."""

    logger.debug("Forwarding request to {}", target_url)

    # 1. Prepare Headers (The logic we perfected)
    outbound_headers = httpx.Headers()
    excluded = ("host", "content-length", "connection", "accept-encoding")
    for key, value in request.headers.items():
        if key.lower() not in excluded:
            outbound_headers[key] = value

    outbound_headers.update(build_context_headers(request))

    # 2. Execute
    response = await client.request(
        method=request.method,
        url=target_url,
        content=await request.body(),
        headers=outbound_headers,
        timeout=timeout,
    )

    logger.info(
        "Forwarded response from {} status_code={}", target_url, response.status_code
    )

    # 3. Return Clean Response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers={
            k: v for k, v in response.headers.items() if k.lower() != "content-length"
        },
    )
