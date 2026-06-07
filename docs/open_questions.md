# Open Questions

## OQ-1: Payment Service internal endpoint contract
**Status:** assumed  
Payment Service is not yet implemented. Gateway currently forwards to `PAYMENT_SERVICE_URL` as-is with X-Merchant-Id + X-Internal-Secret headers. Once Payment Service is up, verify it reads X-Merchant-Id from headers and not from the JWT.

## OQ-2: Firebase token caching
**Status:** deferred  
`verify_id_token` makes a network call to Google on first use (to fetch public keys). Keys are cached by the SDK. No additional caching needed for MVP.

## OQ-3: Rate limiting
**Status:** out of scope for MVP  
Add at nginx/load-balancer layer or as FastAPI middleware later.
