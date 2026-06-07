# Implementation Plan — API Gateway Foundation

## Task
Bootstrap the project foundation for MVP development.

## Assessment of existing code (pre-task)

The previous session created the skeleton files. The following gaps remained:

- No dedicated downstream client modules — httpx call was inlined in `deps.py`
- No `.dockerignore`
- Test coverage: only `GET /health` smoke test
- `main.py` imported private `_get_firebase_app` symbol from `firebase.py`
- `routes.py` stacked decorators on a single handler per service group —
  functionally correct but harder to extend
- `docs/plan.md` described initial intent; not updated post-implementation

## What was done in this task

### Code
- Added `app/clients/user_service.py` — dedicated httpx client for User Service bootstrap call
- Added `app/clients/payment_service.py` — placeholder skeleton for Payment Service calls
- Refactored `app/api/deps.py` to use `UserServiceClient` instead of inline httpx
- Added `init_firebase()` public function to `app/core/firebase.py`; removed private import from `main.py`
- Added `.dockerignore`
- Cleaned up `app/api/routes.py` for clarity

### Tests added
- `tests/unit/test_auth.py`
  - dev bypass → AuthContext populated correctly
  - dev bypass missing uid header → uses fallback "dev-uid"
  - no DEV_BYPASS_TOKEN set → treated as real token → 401
  - User Service bootstrap returns 502 → raises 502
- `tests/unit/test_proxy.py`
  - internal headers (X-Internal-Secret, X-Merchant-Id, X-Firebase-Uid) injected
  - Authorization header stripped before forwarding
  - downstream response status and body passed through transparently
  - downstream timeout → 504
  - downstream unreachable → 502
- `tests/unit/test_routing.py`
  - /v1/me → User Service URL
  - /v1/products → Payment Service URL
  - /v1/paywalls → Payment Service URL
  - /v1/payment-intents → Payment Service URL

### Infrastructure
- Docker build verified
- All unit tests pass

## What should be implemented next

1. **Integration tests** — bring up a stub User Service and exercise the full bootstrap path end-to-end
2. **Firebase token verification** — currently untested because it requires live Firebase or a mock JWT; add a unit test that patches `auth.verify_id_token` and asserts correct claim extraction
3. **Payment Service client** — fill in `app/clients/payment_service.py` once Payment Service is implemented
4. **Error response shape** — decide if gateway should normalise downstream error payloads or pass them through as-is (current behaviour: pass through)
5. **Logging middleware** — request-id / correlation-id injection for tracing across services

---

## Task: OpenAPI Bearer auth documentation (2026-04-14)

### Problem
Swagger UI showed no Authorize button.

Root cause: `_bearer = HTTPBearer(auto_error=True)` was used via `Depends(_bearer)` inside
`get_auth_context`. FastAPI only propagates security scheme declarations to the OpenAPI spec
when `Security()` is used — `Depends()` is opaque to the schema generator.

### Fix
Two-line change in `app/api/deps.py`:
1. Import `Security` from `fastapi`
2. Change `Depends(_bearer)` → `Security(_bearer)`

FastAPI then wires `HTTPBearer` into `components/securitySchemes` and adds
`"security": [{"HTTPBearer": []}]` to every route that transitively depends on it.

No routing, proxy, or auth flow changes — purely documentation-layer fix.

### What was done
- Changed `Depends(_bearer)` → `Security(_bearer)` in `app/api/deps.py`
- Added Bearer scheme description to `FastAPI(...)` constructor in `app/main.py`
- Created `docs/api_contract.md`
- Tests: all 16 existing tests pass unchanged; added `test_openapi_security.py`
