# API Gateway Acceptance Checklist

## Boundaries
- [x] Gateway contains no business logic from User Service
- [x] Gateway contains no business logic from Payment Service
- [x] Gateway contains no blockchain logic

## Auth
- [x] Firebase token verification exists (`app/core/firebase.py` — `verify_firebase_token`)
- [x] firebase_uid is extracted correctly (from Firebase claims or dev bypass header)
- [x] merchant_id is resolved via User Service (`app/clients/user_service.py` — `bootstrap_merchant`)
- [x] X-Merchant-Id is attached to downstream requests (`app/api/proxy.py`)
- [x] X-Internal-Secret is attached to downstream requests (`app/api/proxy.py`)

## Routing
- [x] /v1/me* routes to User Service
- [x] /v1/products* routes to Payment Service
- [x] /v1/paywalls* routes to Payment Service
- [x] /v1/payment-intents* routes to Payment Service

## Quality
- [x] unit tests pass (16/16)
- [ ] integration tests pass (not yet written)
- [ ] docker startup works (Docker socket unavailable in dev environment — Dockerfile is ready)
- [x] docs are updated

## Dev bypass
- [x] DEV_BYPASS_TOKEN documented in .env.example and docs/plan.md
- [x] bypass tested (test_auth.py)

## OpenAPI / Swagger
- [x] Swagger UI shows Authorize button (HTTPBearer scheme in components/securitySchemes)
- [x] /v1/me, /v1/products, /v1/paywalls, /v1/payment-intents marked as protected
- [x] /health has no security requirement
- [x] docs/api_contract.md created
