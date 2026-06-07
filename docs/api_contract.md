# API Contract — API Gateway

## Base URL
`http://localhost:8000` (local)

## Authentication

All `/v1/*` endpoints require a Firebase ID token in the `Authorization` header:

```
Authorization: Bearer <firebase-id-token>
```

The gateway verifies the token, resolves `merchant_id` via User Service, then forwards
the request downstream with `X-Internal-Secret` and `X-Merchant-Id` headers.

### Dev bypass (local development only)

Set `DEV_BYPASS_TOKEN=<value>` in `.env`.  Then send:

```
Authorization: Bearer <value>
X-Dev-Firebase-Uid: <any-uid>      # optional; defaults to "dev-uid"
X-Dev-Email: <email>               # optional
```

Firebase verification is skipped.  The `firebase_uid` from `X-Dev-Firebase-Uid` is
used to bootstrap the merchant via User Service.

---

## Endpoints

### GET /health
Public.  Returns `{"status": "ok"}`.

---

### /v1/me  (+ sub-paths)
Proxied to **User Service** (`USER_SERVICE_URL`, default `http://user-service:8002`).

Accepted methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD

Internal headers injected:
- `X-Internal-Secret`
- `X-Merchant-Id`
- `X-Firebase-Uid`

---

### /v1/products  (+ sub-paths)
### /v1/paywalls  (+ sub-paths)
### /v1/payment-intents  (+ sub-paths)

Proxied to **Payment Service** (`PAYMENT_SERVICE_URL`, default `http://payment-service:8001`).

Accepted methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD

Internal headers injected:
- `X-Internal-Secret`
- `X-Merchant-Id`
- `X-Firebase-Uid`

---

## Error codes produced by the gateway itself

| Code | Condition |
|------|-----------|
| 401  | Missing or invalid Firebase token |
| 502  | User Service bootstrap failed or unreachable |
| 504  | Downstream service timed out |

All other status codes are passed through transparently from the downstream service.

---

## OpenAPI / Swagger UI

Available at `/docs` when the service is running.

The Authorize button accepts a Firebase ID token (or `DEV_BYPASS_TOKEN` for local dev).
All `/v1/*` routes are documented as requiring `HTTPBearer` authentication.
