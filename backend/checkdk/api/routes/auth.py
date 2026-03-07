"""OAuth routes (GitHub + Google) and user-profile / history endpoints."""

from __future__ import annotations

import logging
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from ...auth.dependencies import JWT_ALGORITHM, JWT_SECRET, get_current_user
from ...db.dynamodb import get_history, get_patterns, upsert_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Environment ────────────────────────────────────────────────────────────────
# Base URL of the *backend* service as seen by OAuth providers.
# Production:  https://checkdk.app  (CloudFront → App Runner rewrite)
# Local dev:   http://localhost:3000 (Vite/nginx proxies /api → backend)
APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:3000")

# The base used to construct OAuth redirect_uri values.
# Defaults to APP_BASE_URL + "/api" so the proxy layer strips /api before
# it reaches FastAPI.  Set to APP_BASE_URL alone when running backend-only
# (no proxy in front), e.g. OAUTH_CALLBACK_BASE=http://localhost:8000
OAUTH_CALLBACK_BASE: str = os.getenv("OAUTH_CALLBACK_BASE", f"{APP_BASE_URL}/api")

# Where the frontend lives (used for post-auth redirects).
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

# GitHub OAuth
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

# Google OAuth
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

JWT_EXPIRY_DAYS: int = 7


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_jwt(user: dict) -> str:
    """Issue a signed JWT with a 7-day expiry."""
    payload = {
        "sub": user["userId"],
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "avatarUrl": user.get("avatarUrl", ""),
        "provider": user.get("provider", ""),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _redirect_success(token: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/callback#token={token}",
        status_code=status.HTTP_302_FOUND,
    )


def _redirect_error(reason: str) -> RedirectResponse:
    encoded = urllib.parse.quote(reason)
    return RedirectResponse(
        url=f"{FRONTEND_URL}/login?error={encoded}",
        status_code=status.HTTP_302_FOUND,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GitHub OAuth
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/auth/github", tags=["Auth"])
async def github_login():
    """Redirect the browser to GitHub's OAuth authorisation page."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    callback_url = f"{OAUTH_CALLBACK_BASE}/auth/github/callback"
    params = urllib.parse.urlencode({
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": callback_url,
        "scope": "read:user user:email",
    })
    return RedirectResponse(
        url=f"https://github.com/login/oauth/authorize?{params}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/auth/github/callback", tags=["Auth"])
async def github_callback(code: Optional[str] = Query(None), error: Optional[str] = Query(None)):
    """Handle the OAuth callback from GitHub."""
    if error or not code:
        return _redirect_error(error or "github_auth_denied")

    callback_url = f"{OAUTH_CALLBACK_BASE}/auth/github/callback"

    async with httpx.AsyncClient(timeout=15) as client:
        # 1 – Exchange code for access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": callback_url,
            },
            headers={"Accept": "application/json"},
        )
        token_data: dict[str, Any] = token_resp.json()
        access_token: Optional[str] = token_data.get("access_token")
        if not access_token:
            logger.error("GitHub token exchange failed: %s", token_data)
            return _redirect_error("github_token_exchange_failed")

        # 2 – Fetch profile
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        profile_resp = await client.get("https://api.github.com/user", headers=headers)
        if profile_resp.status_code != 200:
            return _redirect_error("github_profile_fetch_failed")
        profile: dict[str, Any] = profile_resp.json()

        # 3 – Fetch primary verified email if not public
        email: Optional[str] = profile.get("email")
        if not email:
            emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            if emails_resp.status_code == 200:
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break

    # 4 – Upsert in DynamoDB
    try:
        user = upsert_user(
            provider="github",
            provider_id=str(profile["id"]),
            email=email,
            name=profile.get("name") or profile.get("login"),
            avatar_url=profile.get("avatar_url"),
        )
    except Exception:
        logger.exception("Failed to upsert GitHub user %s", profile.get("id"))
        return _redirect_error("db_error")

    return _redirect_success(_make_jwt(user))


# ═══════════════════════════════════════════════════════════════════════════════
# Google OAuth
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/auth/google", tags=["Auth"])
async def google_login():
    """Redirect the browser to Google's OAuth authorisation page."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    callback_url = f"{OAUTH_CALLBACK_BASE}/auth/google/callback"
    params = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
    })
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/auth/google/callback", tags=["Auth"])
async def google_callback(code: Optional[str] = Query(None), error: Optional[str] = Query(None)):
    """Handle the OAuth callback from Google."""
    if error or not code:
        return _redirect_error(error or "google_auth_denied")

    callback_url = f"{OAUTH_CALLBACK_BASE}/auth/google/callback"

    async with httpx.AsyncClient(timeout=15) as client:
        # 1 – Exchange code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": callback_url,
            },
        )
        token_data: dict[str, Any] = token_resp.json()
        access_token: Optional[str] = token_data.get("access_token")
        if not access_token:
            logger.error("Google token exchange failed: %s", token_data)
            return _redirect_error("google_token_exchange_failed")

        # 2 – Fetch profile via userinfo endpoint
        profile_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_resp.status_code != 200:
            return _redirect_error("google_profile_fetch_failed")
        profile: dict[str, Any] = profile_resp.json()

    # 3 – Upsert in DynamoDB
    try:
        user = upsert_user(
            provider="google",
            provider_id=profile["sub"],
            email=profile.get("email"),
            name=profile.get("name"),
            avatar_url=profile.get("picture"),
        )
    except Exception:
        logger.exception("Failed to upsert Google user %s", profile.get("sub"))
        return _redirect_error("db_error")

    return _redirect_success(_make_jwt(user))


# ═══════════════════════════════════════════════════════════════════════════════
# User profile & history
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/auth/me", tags=["Auth"])
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile extracted from the JWT."""
    return {
        "userId": current_user["sub"],
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "avatarUrl": current_user.get("avatarUrl"),
        "provider": current_user.get("provider"),
    }


@router.post("/auth/cli-token", tags=["Auth"])
async def cli_token_validate(current_user: dict = Depends(get_current_user)):
    """Validate a JWT issued by OAuth and return the user profile.

    Used by ``checkdk auth login`` to verify a pasted token before saving it
    to ``~/.checkdk/.env``.  The token must be supplied as a Bearer token in
    the ``Authorization`` header.
    """
    return {
        "userId": current_user["sub"],
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "avatarUrl": current_user.get("avatarUrl"),
        "provider": current_user.get("provider"),
    }


@router.get("/user/history", tags=["User"])
async def get_user_history(current_user: dict = Depends(get_current_user)):
    """Return the user's last 10 analysis history items."""
    items = get_history(current_user["sub"])
    return {"history": items}


@router.get("/user/patterns", tags=["User"])
async def get_user_patterns(current_user: dict = Depends(get_current_user)):
    """Return the user's top recurring issue categories."""
    patterns = get_patterns(current_user["sub"])
    return {"patterns": patterns}
