"""Unit tests for the proxy forwarding layer."""

import pytest
import respx
import httpx
from fastapi import FastAPI, Request, Response

from app.api.deps import AuthContext
from app.api.proxy import forward
from app.core.config import Settings


def _auth() -> AuthContext:
    return AuthContext(
        firebase_uid="uid-test",
        merchant_id="merchant-test",
        email="a@b.com",
        display_name=None,
    )


def _settings(**kwargs) -> Settings:
    base = dict(
        internal_api_secret="secret",
        downstream_timeout=5.0,
        user_service_url="http://user-mock",
        payment_service_url="http://payment-mock",
    )
    base.update(kwargs)
    return Settings(**base)


# ---------------------------------------------------------------------------
# Helper: call forward() through a real TestClient request
# ---------------------------------------------------------------------------

def make_proxy_app(target_url: str, settings: Settings) -> FastAPI:
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "DELETE"])
    async def proxy(request: Request) -> Response:
        return await forward(request, target_url, _auth(), settings)

    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@respx.mock
def test_internal_headers_injected():
    """X-Internal-Secret, X-Merchant-Id, X-Firebase-Uid must be present downstream."""
    settings = _settings()

    captured_headers = {}

    def capture(req: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(req.headers))
        return httpx.Response(200, json={"ok": True})

    respx.get("http://user-mock/v1/me").mock(side_effect=capture)

    from fastapi.testclient import TestClient
    app = make_proxy_app("http://user-mock", settings)
    with TestClient(app) as client:
        resp = client.get("/v1/me", headers={"Authorization": "Bearer some-token"})

    assert resp.status_code == 200
    assert captured_headers.get("x-internal-secret") == "secret"
    assert captured_headers.get("x-merchant-id") == "merchant-test"
    assert captured_headers.get("x-firebase-uid") == "uid-test"


@respx.mock
def test_authorization_header_stripped():
    """Authorization header must NOT be forwarded to downstream services."""
    settings = _settings()

    captured_headers = {}

    def capture(req: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(req.headers))
        return httpx.Response(200, json={})

    respx.get("http://user-mock/v1/me").mock(side_effect=capture)

    from fastapi.testclient import TestClient
    app = make_proxy_app("http://user-mock", settings)
    with TestClient(app) as client:
        client.get("/v1/me", headers={"Authorization": "Bearer firebase-token"})

    assert "authorization" not in captured_headers


@respx.mock
def test_downstream_response_passed_through():
    """Status code and body from downstream are returned transparently."""
    settings = _settings()

    respx.get("http://user-mock/v1/me").mock(
        return_value=httpx.Response(202, json={"data": "hello"})
    )

    from fastapi.testclient import TestClient
    app = make_proxy_app("http://user-mock", settings)
    with TestClient(app) as client:
        resp = client.get("/v1/me")

    assert resp.status_code == 202
    assert resp.json() == {"data": "hello"}


@respx.mock
def test_downstream_timeout_returns_504():
    """Timeout from downstream → 504."""
    settings = _settings()

    respx.get("http://user-mock/v1/me").mock(side_effect=httpx.TimeoutException("timeout"))

    from fastapi.testclient import TestClient
    app = make_proxy_app("http://user-mock", settings)
    with TestClient(app) as client:
        resp = client.get("/v1/me")

    assert resp.status_code == 504


@respx.mock
def test_downstream_unreachable_returns_502():
    """Connection error from downstream → 502."""
    settings = _settings()

    respx.get("http://user-mock/v1/me").mock(side_effect=httpx.ConnectError("refused"))

    from fastapi.testclient import TestClient
    app = make_proxy_app("http://user-mock", settings)
    with TestClient(app) as client:
        resp = client.get("/v1/me")

    assert resp.status_code == 502
