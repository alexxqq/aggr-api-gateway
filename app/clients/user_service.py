"""HTTP client skeleton for User Service internal API."""

import logging

import httpx

logger = logging.getLogger(__name__)


class UserServiceClient:
    """Thin httpx wrapper for User Service internal endpoints."""

    def __init__(self, base_url: str, internal_secret: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret = internal_secret
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"X-Internal-Secret": self._secret}

    async def bootstrap_merchant(
        self,
        firebase_uid: str,
        email: str | None,
        display_name: str | None,
    ) -> str:
        """
        Call POST /internal/merchant/init (idempotent).
        Returns merchant_id as a string.
        Raises httpx.HTTPStatusError if the service returns a non-200 response.
        """
        url = f"{self._base_url}/internal/merchant/init"
        payload = {
            "firebase_uid": firebase_uid,
            "email": email,
            "display_name": display_name,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
        resp.raise_for_status()
        return str(resp.json()["merchant_id"])
