"""FastAPI dependencies: token verification → merchant_id resolution."""

import logging
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients.user_service import UserServiceClient
from app.core.config import Settings, get_settings
from app.core.firebase import verify_firebase_token

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=True)


@dataclass
class AuthContext:
    firebase_uid: str
    merchant_id: str
    email: str | None
    display_name: str | None


async def _resolve_merchant(
    firebase_uid: str,
    email: str | None,
    display_name: str | None,
    settings: Settings,
) -> str:
    client = UserServiceClient(
        base_url=settings.user_service_url,
        internal_secret=settings.internal_api_secret,
        timeout=settings.downstream_timeout,
    )
    try:
        return await client.bootstrap_merchant(firebase_uid, email, display_name)
    except httpx.HTTPStatusError as exc:
        logger.error("User Service bootstrap failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not resolve merchant identity",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("User Service unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User Service unreachable",
        ) from exc


async def get_auth_context(
    request: Request,
    creds: HTTPAuthorizationCredentials = Security(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    """
    1. Verify Firebase ID token (or accept dev bypass token).
    2. Bootstrap merchant_id via User Service.
    3. Return AuthContext used by forwarding routes.

    Dev bypass:
        Set DEV_BYPASS_TOKEN=<value> in .env.
        Send: Authorization: Bearer <value>
        Optionally: X-Dev-Firebase-Uid, X-Dev-Email headers.
    """
    token = creds.credentials

    # Dev bypass — skip Firebase when DEV_BYPASS_TOKEN is set and matches
    if settings.dev_bypass_token and token == settings.dev_bypass_token:
        firebase_uid = request.headers.get("X-Dev-Firebase-Uid", "dev-uid")
        email = request.headers.get("X-Dev-Email") or None
        display_name = None
    else:
        try:
            claims = verify_firebase_token(token)
        except Exception as exc:
            logger.debug("Token verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Firebase token",
            ) from exc
        firebase_uid = claims["uid"]
        email = claims.get("email")
        display_name = claims.get("name")

    merchant_id = await _resolve_merchant(firebase_uid, email, display_name, settings)
    return AuthContext(
        firebase_uid=firebase_uid,
        merchant_id=merchant_id,
        email=email,
        display_name=display_name,
    )
