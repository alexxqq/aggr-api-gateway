"""Gateway routing: maps public path prefixes to downstream services."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import AuthContext, get_auth_context
from app.api.proxy import forward
from app.core.config import Settings, get_settings

router = APIRouter()

_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


# ---------------------------------------------------------------------------
# /v1/me* → User Service
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# /public/* → Payment Service (no auth — customer-facing checkout)
# ---------------------------------------------------------------------------

@router.api_route(
    "/public/{path:path}",
    methods=["GET", "POST", "OPTIONS"],
    summary="Public checkout (proxied to Payment Service, no auth required)",
    include_in_schema=False,
)
async def proxy_public(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    """Forward /public/* to Payment Service without requiring a Firebase token.

    Handles:
    - /public/paywalls/* — paywall checkout
    - /public/checkout-sessions/* — session-based checkout
    - /public/payment-intents/* — payment status polling
    """
    path = request.url.path
    query = request.url.query
    url = f"{settings.payment_service_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in {"host", "authorization", "content-length", "transfer-encoding", "connection"}
    }
    headers["X-Internal-Secret"] = settings.internal_api_secret

    try:
        body = await request.body()
    except (BrokenPipeError, ConnectionResetError):
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
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Downstream unreachable")

    response_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in {"transfer-encoding", "connection"}
    }
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type"),
    )


# ---------------------------------------------------------------------------
# /v1/me* → User Service
# ---------------------------------------------------------------------------

@router.api_route(
    "/v1/me",
    methods=_METHODS,
    summary="User profile (proxied to User Service)",
    description="All `/v1/me` requests are forwarded to User Service with merchant context.",
)
@router.api_route("/v1/me/{path:path}", methods=_METHODS, include_in_schema=False)
async def proxy_me(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> Response:
    return await forward(request, settings.user_service_url, auth, settings)


# ---------------------------------------------------------------------------
# /v1/products* → Payment Service
# ---------------------------------------------------------------------------

@router.api_route(
    "/v1/products",
    methods=_METHODS,
    summary="Products (proxied to Payment Service)",
    description="All `/v1/products` requests are forwarded to Payment Service with merchant context.",
)
@router.api_route("/v1/products/{path:path}", methods=_METHODS, include_in_schema=False)
async def proxy_products(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> Response:
    return await forward(request, settings.payment_service_url, auth, settings)


# ---------------------------------------------------------------------------
# /v1/paywalls* → Payment Service
# ---------------------------------------------------------------------------

@router.api_route(
    "/v1/paywalls",
    methods=_METHODS,
    summary="Paywalls (proxied to Payment Service)",
    description="All `/v1/paywalls` requests are forwarded to Payment Service with merchant context.",
)
@router.api_route("/v1/paywalls/{path:path}", methods=_METHODS, include_in_schema=False)
async def proxy_paywalls(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> Response:
    return await forward(request, settings.payment_service_url, auth, settings)


# ---------------------------------------------------------------------------
# /v1/payment-intents* → Payment Service
# ---------------------------------------------------------------------------

@router.api_route(
    "/v1/payment-intents",
    methods=_METHODS,
    summary="Payment intents (proxied to Payment Service)",
    description="All `/v1/payment-intents` requests are forwarded to Payment Service with merchant context.",
)
@router.api_route("/v1/payment-intents/{path:path}", methods=_METHODS, include_in_schema=False)
async def proxy_payment_intents(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> Response:
    return await forward(request, settings.payment_service_url, auth, settings)


# ---------------------------------------------------------------------------
# /v1/checkout-sessions* → Payment Service
# ---------------------------------------------------------------------------

@router.api_route(
    "/v1/checkout-sessions",
    methods=_METHODS,
    summary="Checkout sessions (proxied to Payment Service)",
    description="All `/v1/checkout-sessions` requests are forwarded to Payment Service with merchant context.",
)
@router.api_route("/v1/checkout-sessions/{path:path}", methods=_METHODS, include_in_schema=False)
async def proxy_checkout_sessions(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> Response:
    return await forward(request, settings.payment_service_url, auth, settings)
