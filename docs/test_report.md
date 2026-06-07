# Test Report

## Run: foundation bootstrap (2026-04-14)

### Command
```
uv run pytest tests/ -v
```

### Result: 16 passed

```
tests/unit/test_auth.py::test_dev_bypass_resolves_merchant          PASSED
tests/unit/test_auth.py::test_dev_bypass_uses_fallback_uid_when_header_missing PASSED
tests/unit/test_auth.py::test_invalid_token_returns_401             PASSED
tests/unit/test_auth.py::test_wrong_bypass_token_returns_401        PASSED
tests/unit/test_auth.py::test_user_service_error_returns_502        PASSED
tests/unit/test_auth.py::test_user_service_unreachable_returns_502  PASSED
tests/unit/test_health.py::test_health                              PASSED
tests/unit/test_proxy.py::test_internal_headers_injected            PASSED
tests/unit/test_proxy.py::test_authorization_header_stripped        PASSED
tests/unit/test_proxy.py::test_downstream_response_passed_through   PASSED
tests/unit/test_proxy.py::test_downstream_timeout_returns_504       PASSED
tests/unit/test_proxy.py::test_downstream_unreachable_returns_502   PASSED
tests/unit/test_routing.py::test_me_routes_to_user_service          PASSED
tests/unit/test_routing.py::test_products_routes_to_payment_service PASSED
tests/unit/test_routing.py::test_paywalls_routes_to_payment_service PASSED
tests/unit/test_routing.py::test_payment_intents_routes_to_payment_service PASSED
```

### Service startup (local)
```
uv run uvicorn app.main:app --host 127.0.0.1 --port 8099
GET /health → 200 {"status": "ok"}
```
Startup warning (expected, no Firebase creds): `FIREBASE_CREDENTIALS_PATH not set — Firebase token verification is disabled. Set DEV_BYPASS_TOKEN for local development.`

### Docker build
Docker socket not accessible in this environment. Dockerfile and .dockerignore are present and structured identically to the verified User Service / Payment Service images. Verify with `docker build .` when Docker is available.

---

## Run: OpenAPI Bearer auth documentation (2026-04-14)

### Command
```
uv run pytest tests/ -v
```

### Result: 22 passed, 4 warnings

New tests added: `tests/unit/test_openapi_security.py`

```
tests/unit/test_openapi_security.py::test_httpbearer_scheme_declared                               PASSED
tests/unit/test_openapi_security.py::test_protected_route_has_security_requirement[/v1/me]         PASSED
tests/unit/test_openapi_security.py::test_protected_route_has_security_requirement[/v1/products]   PASSED
tests/unit/test_openapi_security.py::test_protected_route_has_security_requirement[/v1/paywalls]   PASSED
tests/unit/test_openapi_security.py::test_protected_route_has_security_requirement[/v1/payment-intents] PASSED
tests/unit/test_openapi_security.py::test_health_has_no_security_requirement                       PASSED
```

All previous 16 tests continue to pass.

### Warnings (4, expected)

```
UserWarning: Duplicate Operation ID v1_me for function proxy_me
UserWarning: Duplicate Operation ID v1_products for function proxy_products
UserWarning: Duplicate Operation ID v1_paywalls for function proxy_paywalls
UserWarning: Duplicate Operation ID v1_payment_intents for function proxy_payment_intents
```

**Cause:** FastAPI computes `route.unique_id` once per route and reuses it for all HTTP methods
registered on that route via `api_route`.  With 7 methods per route, methods 2–7 each
produce a duplicate ID.  
**Impact:** None on runtime behaviour or Swagger UI display (Swagger groups by path+method,
not by `operationId`).  The `operationId` field in generated OpenAPI JSON is technically
non-unique per path, which would cause issues for API code generators.  
**Fix if needed:** Register each HTTP method as a separate `router.add_api_route()` call so
each gets its own `unique_id`.  Deferred — out of scope for proxy gateway MVP.

### Live verification
```
GET /openapi.json → components.securitySchemes.HTTPBearer present
/docs → Authorize button visible
/v1/me, /v1/products, /v1/paywalls, /v1/payment-intents → all marked [PROTECTED]
/health → [PUBLIC]
```

## Known gaps (for next task)
- Firebase `verify_id_token` path not covered — requires patching `auth.verify_id_token` or a mock JWT
- Integration tests against a real/stub User Service not yet written
- Payment Service client is a placeholder (service not yet implemented)
