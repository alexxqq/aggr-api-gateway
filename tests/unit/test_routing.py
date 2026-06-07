"""Unit tests: verify path prefixes route to the correct downstream service."""

import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core import config as cfg_mod
from app.api import deps as deps_mod
from app.api.deps import AuthContext
from app.core.config import Settings


def _settings() -> Settings:
    return Settings(
        dev_bypass_token="test-bypass",
        user_service_url="http://user-svc",
        payment_service_url="http://payment-svc",
        internal_api_secret="secret",
        firebase_credentials_path=None,
    )


def _override_settings(test_app, settings: Settings):
    test_app.dependency_overrides[cfg_mod.get_settings] = lambda: settings
    test_app.dependency_overrides[deps_mod.get_settings] = lambda: settings


@pytest.fixture
def client():
    settings = _settings()
    _override_settings(app, settings)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _bypass_headers() -> dict:
    return {
        "Authorization": "Bearer test-bypass",
        "X-Dev-Firebase-Uid": "uid-test",
    }


@respx.mock
def test_me_routes_to_user_service(client):
    route = respx.get("http://user-svc/v1/me").mock(
        return_value=httpx.Response(200, json={"merchant": "data"})
    )
    # Also mock User Service bootstrap
    respx.post("http://user-svc/internal/merchant/init").mock(
        return_value=httpx.Response(200, json={"merchant_id": "m1", "created": False})
    )

    resp = client.get("/v1/me", headers=_bypass_headers())

    assert resp.status_code == 200
    assert route.called


@respx.mock
def test_products_routes_to_payment_service(client):
    route = respx.get("http://payment-svc/v1/products").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.post("http://user-svc/internal/merchant/init").mock(
        return_value=httpx.Response(200, json={"merchant_id": "m1", "created": False})
    )

    resp = client.get("/v1/products", headers=_bypass_headers())

    assert resp.status_code == 200
    assert route.called


@respx.mock
def test_paywalls_routes_to_payment_service(client):
    route = respx.get("http://payment-svc/v1/paywalls").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.post("http://user-svc/internal/merchant/init").mock(
        return_value=httpx.Response(200, json={"merchant_id": "m1", "created": False})
    )

    resp = client.get("/v1/paywalls", headers=_bypass_headers())

    assert resp.status_code == 200
    assert route.called


@respx.mock
def test_payment_intents_routes_to_payment_service(client):
    route = respx.get("http://payment-svc/v1/payment-intents").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.post("http://user-svc/internal/merchant/init").mock(
        return_value=httpx.Response(200, json={"merchant_id": "m1", "created": False})
    )

    resp = client.get("/v1/payment-intents", headers=_bypass_headers())

    assert resp.status_code == 200
    assert route.called
