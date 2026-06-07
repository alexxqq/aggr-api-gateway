# API Gateway Development Rules

## Project context

This repository contains only the API Gateway of the thesis system.

The API Gateway is the single public entry point for frontend requests.

Its responsibilities are:
- verify Firebase ID tokens
- extract firebase_uid
- bootstrap or resolve merchant_id through User Service
- forward authenticated requests to downstream services
- attach internal headers
- provide a basic security boundary
- keep routing logic simple and explicit

The API Gateway must NOT:
- own merchant data as source of truth
- implement product or payment business logic
- implement blockchain execution logic
- store private keys
- become a monolith with domain logic

## Architecture constraints

- Use FastAPI
- Use httpx for downstream calls
- Use Firebase Admin SDK for token verification
- Keep routing logic explicit
- Keep authentication and forwarding logic separate
- Prefer minimal and testable code

## Downstream dependencies

The gateway depends on:
- User Service
- Payment Service

For MVP, downstream calls use:
- X-Internal-Secret
- X-Merchant-Id where needed

## Expected behavior

For authenticated frontend requests:
1. verify Firebase token
2. resolve firebase_uid
3. call User Service bootstrap or lookup endpoint
4. obtain merchant_id
5. forward request to appropriate downstream service
6. return downstream response transparently where possible

## Workflow rules

For every task:
1. Read spec/service_scope.md and spec/acceptance_checklist.md
2. Inspect existing code before changing anything
3. Write a short implementation plan to docs/plan.md
4. Implement the smallest correct change
5. Add or update tests
6. Run validation
7. Update docs/test_report.md
8. Update spec/acceptance_checklist.md

## Safety rules

- Do not duplicate User Service logic
- Do not duplicate Payment Service logic
- Do not move business logic into the gateway
- If something is ambiguous, record it in docs/open_questions.md and proceed with the safest MVP assumption

## Definition of done

A task is done only if:
- code is implemented
- tests pass
- docker startup works
- docs are updated
- acceptance checklist is updated