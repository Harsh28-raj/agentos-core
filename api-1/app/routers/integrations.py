"""Per-user Google OAuth (Gmail + Calendar). Tokens are stored Fernet-encrypted in user_tokens."""
import json
import logging
import os
from datetime import timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select

from app.ai.tools.google_auth import is_connected
from app.core import config
from app.core.deps import CurrentUser, get_current_user
from app.core.security import create_access_token, decode_token, encrypt_token
from app.db.models import UserToken
from app.db.postgres import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/integrations/google", tags=["Integrations"])

STATE_PURPOSE = "google_oauth"
# Google may return a superset of scopes (include_granted_scopes); do not fail on that.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
if (config.GOOGLE_REDIRECT_URI or "").startswith("http://localhost"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def oauth_configured() -> bool:
    return bool(config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET and config.GOOGLE_REDIRECT_URI
                and config.ENCRYPTION_KEY and AsyncSessionLocal)


def _flow():
    from google_auth_oauthlib.flow import Flow

    client_config = {"web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [config.GOOGLE_REDIRECT_URI],
    }}
    # No PKCE verifier: the callback builds a fresh Flow and could not know it.
    return Flow.from_client_config(client_config, scopes=config.GOOGLE_SCOPES,
                                   redirect_uri=config.GOOGLE_REDIRECT_URI, autogenerate_code_verifier=False)


@router.get("/status")
async def google_status(user: CurrentUser = Depends(get_current_user)):
    connected = await run_in_threadpool(is_connected, user.id)
    return {"configured": oauth_configured(), "connected": connected}


@router.post("/authorize")
async def google_authorize(user: CurrentUser = Depends(get_current_user)):
    """Returns the Google consent URL. The frontend redirects the browser to it."""
    if not oauth_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on the server.")
    state = create_access_token({"uid": user.id, "purpose": STATE_PURPOSE}, expires_delta=timedelta(minutes=10))
    url, _ = _flow().authorization_url(access_type="offline", prompt="consent",
                                       include_granted_scopes="true", state=state)
    return {"url": url}


@router.get("/callback", include_in_schema=False)
async def google_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    dashboard = f"{config.FRONTEND_URL}/dashboard"
    if error or not code or not state:
        return RedirectResponse(f"{dashboard}?google=error")
    try:
        claims = decode_token(state)
        if claims.get("purpose") != STATE_PURPOSE or not claims.get("uid"):
            raise jwt.InvalidTokenError("wrong purpose")
    except jwt.PyJWTError:
        return RedirectResponse(f"{dashboard}?google=error")

    try:
        flow = _flow()
        await run_in_threadpool(flow.fetch_token, code=code)
        encrypted = encrypt_token(json.loads(flow.credentials.to_json()))
        user_id = str(claims["uid"])
        async with AsyncSessionLocal() as session:
            record = (await session.execute(
                select(UserToken).where(UserToken.user_id == user_id, UserToken.service_name == "google")
            )).scalars().first()
            if record:
                record.encrypted_data = encrypted
            else:
                session.add(UserToken(user_id=user_id, service_name="google", encrypted_data=encrypted))
            await session.commit()
    except Exception:
        logger.exception("Google OAuth callback failed")
        return RedirectResponse(f"{dashboard}?google=error")
    return RedirectResponse(f"{dashboard}?google=connected")


@router.delete("")
async def google_disconnect(user: CurrentUser = Depends(get_current_user)):
    if not AsyncSessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured.")
    async with AsyncSessionLocal() as session:
        await session.execute(delete(UserToken).where(UserToken.user_id == user.id, UserToken.service_name == "google"))
        await session.commit()
    return {"connected": False}
