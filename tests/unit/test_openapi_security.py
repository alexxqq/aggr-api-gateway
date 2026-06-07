"""Verify the OpenAPI schema declares Bearer auth and marks routes as protected."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def schema():
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200
    return resp.json()


def test_httpbearer_scheme_declared(schema):
    """components/securitySchemes must contain an HTTPBearer entry."""
    schemes = schema.get("components", {}).get("securitySchemes", {})
    assert "HTTPBearer" in schemes, f"securitySchemes: {list(schemes)}"
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"


@pytest.mark.parametrize("path", [
    "/v1/me",
    "/v1/products",
    "/v1/paywalls",
    "/v1/payment-intents",
])
def test_protected_route_has_security_requirement(schema, path):
    """Each public gateway route must declare the HTTPBearer security requirement."""
    paths = schema.get("paths", {})
    assert path in paths, f"Path {path!r} not found in schema"
    for method, operation in paths[path].items():
        if method == "parameters":
            continue
        security = operation.get("security", [])
        scheme_names = [name for req in security for name in req]
        assert "HTTPBearer" in scheme_names, (
            f"{method.upper()} {path} missing HTTPBearer in security: {security}"
        )


def test_health_has_no_security_requirement(schema):
    """/health must NOT require auth."""
    health_op = schema["paths"]["/health"]["get"]
    # Either no 'security' key, or an explicit empty list (public override)
    security = health_op.get("security")
    assert not security, f"/health should be public but has security={security}"
