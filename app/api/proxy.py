"""Generic reverse-proxy forwarding to downstream services."""

import logging

import httpx
from fastapi import HTTPException, Request, Response, status

from app.core.config import Settings
from app.api.deps import AuthContext

logger = logging.getLogger(__name__)

# Headers that must not be forwarded upstream (hop-by-hop + internal)
_DROP_REQUEST_HEADERS = {
    "host",
    "authorization",
    "content-length",
    "transfer-encoding",
    "connection",
}

_DROP_RESPONSE_HEADERS = {
    "transfer-encoding",
    "connection",
}


async def forward(
    request: Request,
    target_base_url: str,
    auth: AuthContext,
    settings: Settings,
) -> Response:
    """
    Forward the incoming request to *target_base_url* + original path+query,
    injecting internal auth headers.  Returns a FastAPI Response.
    """
    # Build target URL
    path = request.url.path
    query = request.url.query
    url = f"{target_base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"

    # Filter and copy request headers
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _DROP_REQUEST_HEADERS
    }
    headers["X-Internal-Secret"] = settings.internal_api_secret
    headers["X-Merchant-Id"] = auth.merchant_id
    headers["X-Firebase-Uid"] = auth.firebase_uid

    try:
        body = await request.body()
    except (BrokenPipeError, ConnectionResetError):
        logger.debug("Client disconnected before request body was read")
        return Response(status_code=499)

    try:
        async with httpx.AsyncClient(timeout=settings.downstream_timeout) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Downstream timeout")
    except httpx.RequestError as exc:
        logger.error("Downstream request error: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Downstream unreachable")

    response_headers = {
        k: v
        for k, v in resp.headers.items()
        if k.lower() not in _DROP_RESPONSE_HEADERS
    }
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type"),
    )
