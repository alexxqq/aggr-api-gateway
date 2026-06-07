"""Unit tests for auth dependency (get_auth_context)."""

import pytest
import respx
import httpx
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.api.deps import AuthContext, get_auth_context
from app.core.config import Settings


# ---------------------------------------------------------------------------
# Minimal app fixture that exercises get_auth_context
# ---------------------------------------------------------------------------

def make_app(settings: Settings) -> FastAPI:
    """Create a minimal FastAPI app that exposes the auth context."""
    app = FastAPI()

    @app.get("/probe")
    async def probe(auth: AuthContext = Depends(get_auth_context)) -> dict:
        return {
            "firebase_uid": auth.firebase_uid,
            "merchant_id": auth.merchant_id,
            "email": auth.email,
        }

    app.dependency_overrides[Settings] = lambda: settings  # type: ignore[assignment]
    # Override get_settings so deps pick up our test settings
    from app.core import config as cfg_mod
    from app.api import deps as deps_mod
    app.dependency_overrides[cfg_mod.get_settings] = lambda: settings
    app.dependency_overrides[deps_mod.get_settings] = lambda: settings  # type: ignore[assignment]
    return app


def _settings(**kwargs) -> Settings:
    base = dict(
        dev_bypass_token="test-bypass",
        user_service_url="http://user-service-mock",
        payment_service_url="http://payment-service-mock",
        internal_api_secret="secret",
        firebase_credentials_path=None,
    )
    base.update(kwargs)
    return Settings(**base)


# ---------------------------------------------------------------------------
# Tests: dev bypass
# ---------------------------------------------------------------------------

@respx.mock
def test_dev_bypass_resolves_merchant():
    """Dev bypass token skips Firebase; merchant_id comes from User Service."""
    settings = _settings()
    app = make_app(settings)

    respx.post("http://user-service-mock/internal/merchant/init").mock(
        return_value=httpx.Response(200, json={"merchant_id": "merchant-abc", "created": False})
    )

    with TestClient(app) as client:
        resp = client.get(
            "/probe",
            headers={
                "Authorization": "Bearer test-bypass",
                "X-Dev-Firebase-Uid": "uid-123",
                "X-Dev-Email": "test@example.com",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["firebase_uid"] == "uid-123"
    assert data["merchant_id"] == "merchant-abc"
    assert data["email"] == "test@example.com"


@respx.mock
def test_dev_bypass_uses_fallback_uid_when_header_missing():
    """Dev bypass with no X-Dev-Firebase-Uid falls back to 'dev-uid'."""
    settings = _settings()
    app = make_app(settings)

    respx.post("http://user-service-mock/internal/merchant/init").mock(
        return_value=httpx.Response(200, json={"merchant_id": "merchant-xyz", "created": True})
    )

    with TestClient(app) as client:
        resp = client.get("/probe", headers={"Authorization": "Bearer test-bypass"})

    assert resp.status_code == 200
    assert resp.json()["firebase_uid"] == "dev-uid"


# ---------------------------------------------------------------------------
# Tests: real token path (Firebase disabled / bad token)
# ---------------------------------------------------------------------------

def test_invalid_token_returns_401():
    """When no dev bypass is set, any token triggers Firebase verification which fails."""
    settings = _settings(dev_bypass_token=None)
    app = make_app(settings)

    with TestClient(app) as client:
        resp = client.get("/probe", headers={"Authorization": "Bearer bad-token"})

    assert resp.status_code == 401


def test_wrong_bypass_token_returns_401():
    """A token that does not match DEV_BYPASS_TOKEN falls through to Firebase → 401."""
    settings = _settings(dev_bypass_token="correct-bypass")
    app = make_app(settings)

    with TestClient(app) as client:
        resp = client.get("/probe", headers={"Authorization": "Bearer wrong-bypass"})

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: User Service errors
# ---------------------------------------------------------------------------

@respx.mock
def test_user_service_error_returns_502():
    """Non-200 from User Service bootstrap → 502."""
    settings = _settings()
    app = make_app(settings)

    respx.post("http://user-service-mock/internal/merchant/init").mock(
        return_value=httpx.Response(500, json={"detail": "internal error"})
    )

    with TestClient(app) as client:
        resp = client.get("/probe", headers={"Authorization": "Bearer test-bypass"})

    assert resp.status_code == 502


@respx.mock
def test_user_service_unreachable_returns_502():
    """Connection error to User Service → 502."""
    settings = _settings()
    app = make_app(settings)

    respx.post("http://user-service-mock/internal/merchant/init").mock(
        side_effect=httpx.ConnectError("refused")
    )

    with TestClient(app) as client:
        resp = client.get("/probe", headers={"Authorization": "Bearer test-bypass"})

    assert resp.status_code == 502
