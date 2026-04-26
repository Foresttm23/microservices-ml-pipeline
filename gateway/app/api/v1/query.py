from app.core.dependencies import HTTPXClientDep
from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.post("/pipelines/{pipeline_id}/run")
async def proxy_to_orchestrator(
    pipeline_id: str, request: Request, client: HTTPXClientDep
):
    # 1. Define the target URL (The Orchestrator)
    orchestrator_url = f"https://orchestrator.internal/api/run/{pipeline_id}"

    # 2. Extract payload and headers from incoming request
    body = await request.json()
    headers = dict(request.headers)

    # Remove the 'host' header to avoid handshake conflicts with the orchestrator
    headers.pop("host", None)

    # 3. Forward the request
    # Note: Use a generous timeout for ML triggers
    response = await client.post(
        orchestrator_url, json=body, headers=headers, timeout=30.0
    )

    # 4. Return the orchestrator's response back to the original client
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
