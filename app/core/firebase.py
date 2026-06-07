"""Firebase Admin SDK initialisation and token verification."""

import logging
from functools import lru_cache
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _init_app() -> Optional[firebase_admin.App]:
    """Lazily initialise the Firebase app singleton. Returns None if creds not configured."""
    settings = get_settings()
    if not settings.firebase_credentials_path:
        logger.warning(
            "FIREBASE_CREDENTIALS_PATH not set — Firebase token verification is disabled. "
            "Set DEV_BYPASS_TOKEN for local development."
        )
        return None
    cred = credentials.Certificate(settings.firebase_credentials_path)
    return firebase_admin.initialize_app(cred)


def init_firebase() -> None:
    """Call at application startup to surface credential warnings early."""
    _init_app()


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.

    Raises firebase_admin.auth.InvalidIdTokenError (or subclass) on failure.
    Raises RuntimeError if Firebase was not initialised (no credentials configured
    and no dev bypass in effect).
    """
    _init_app()
    return auth.verify_id_token(id_token)
