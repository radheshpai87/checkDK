"""FastAPI dependencies for JWT authentication."""

from __future__ import annotations

import logging
import os
import secrets
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


def _resolve_jwt_secret() -> str:
    """Return the JWT signing secret.

    If ``JWT_SECRET`` is not set in the environment a random 256-bit hex
    secret is generated at process startup.  This keeps local development
    functional (tokens simply won't survive a server restart) while
    ensuring the app **never** falls back to a publicly-known string.
    """
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        secret = secrets.token_hex(32)  # 256-bit random secret
        logger.warning(
            "JWT_SECRET is not set — generated an ephemeral random secret. "
            "Tokens will NOT survive a server restart. "
            "Set JWT_SECRET in your environment for production use "
            "(e.g. `openssl rand -hex 32`)."
        )
    return secret


JWT_SECRET: str = _resolve_jwt_secret()
JWT_ALGORITHM: str = "HS256"

_bearer_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT; return payload or *None* on any failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT invalid: %s", exc)
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency — raises HTTP 401 if no valid Bearer token is provided.

    Use this on endpoints that *require* authentication.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[dict]:
    """
    FastAPI dependency — returns the decoded JWT payload or *None* for anonymous
    requests.  Never raises; use this on endpoints that work with or without auth.
    """
    if credentials is None:
        return None
    return _decode_token(credentials.credentials)
