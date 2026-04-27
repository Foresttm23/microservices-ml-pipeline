from ...core.dependencies import HTTPXClientDep
from ...middleware import build_context_headers
from fastapi import APIRouter, Request, Response
from loguru import logger

router = APIRouter()


@router.post("/pipelines/{pipeline_id}/run")
async def proxy_to_orchestrator(
    pipeline_id: str, request: Request, client: HTTPXClientDep
):
    logger.info(f"Proxying pipeline {pipeline_id}")

    orchestrator_url = f"http://127.0.0.1:8001/api/run/{pipeline_id}"

    # 1. Get the raw body bytes instead of parsing JSON
    # This prevents the JSONDecodeError if the body is empty
    content = await request.body()

    # 2. Build headers using your middleware helper
    headers = build_context_headers(request)

    # 3. Forward original headers (filtered)
    for key, value in request.headers.items():
        if key.lower() not in ("host", "content-length"):
            headers[key] = value

    # 4. Forward the request using 'content' instead of 'json'
    # This works regardless of whether the body is empty, plain text, or JSON
    response = await client.request(
        method=request.method,
        url=orchestrator_url,
        content=content,
        headers=headers,
        timeout=60.0,  # ML tasks can be slow
    )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers={
            k: v for k, v in response.headers.items() if k.lower() != "content-length"
        },
    )
