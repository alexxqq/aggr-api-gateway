# API Gateway Scope

## Purpose

API Gateway is the single public entry point for frontend requests.

## Responsibilities
- verify Firebase ID token
- extract firebase_uid
- resolve merchant_id via User Service
- forward requests to User Service and Payment Service
- attach internal auth headers
- enforce a basic security boundary

## Uses downstream services
- User Service
- Payment Service

## Must not own
- merchant source-of-truth data
- products
- paywalls
- invoices
- blockchain transactions
- private keys

## MVP endpoints / behavior
- GET /health

Authenticated forwarding behavior for:
- /v1/me*
- /v1/products*
- /v1/paywalls*
- /v1/payment-intents*

## Auth flow
- frontend sends Firebase token
- gateway verifies token
- gateway calls User Service internal bootstrap/lookup
- gateway forwards request with X-Merchant-Id and X-Internal-Secret

## Done criteria
- gateway verifies tokens or supports a documented dev bypass
- gateway forwards requests to User Service and Payment Service
- downstream headers are attached correctly
- tests cover routing/auth flow
- docker startup works
