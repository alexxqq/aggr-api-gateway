"""HTTP client skeleton for Payment Service internal API.

Payment Service is not yet implemented.  This module is a placeholder that
documents the expected call interface.  Fill in concrete methods once the
Payment Service internal contract is defined.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class PaymentServiceClient:
    """Thin httpx wrapper for Payment Service internal endpoints (stub)."""

    def __init__(self, base_url: str, internal_secret: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret = internal_secret
        self._timeout = timeout

    def _headers(self, merchant_id: str) -> dict[str, str]:
        return {
            "X-Internal-Secret": self._secret,
            "X-Merchant-Id": merchant_id,
        }

    # TODO: add concrete methods once Payment Service contract is finalised
    # Example shape (not yet implemented):
    #
    # async def list_products(self, merchant_id: str) -> list[dict]:
    #     ...
