"""Loads a user's Google OAuth credentials (stored encrypted in user_tokens)."""
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core import config
from app.core.security import decrypt_token, encrypt_token
from app.db.models import UserToken
from app.db.postgres import SyncSessionLocal

# Only for local development: lets `local_test_user` use a token.json made by generate_token.py.
LOCAL_TEST_USER = "local_test_user"


class GoogleNotConnected(Exception):
    pass


def get_credentials(user_id: str) -> Credentials:
    if not SyncSessionLocal:
        raise GoogleNotConnected("Database connection not configured.")

    session = SyncSessionLocal()
    try:
        record = session.query(UserToken).filter_by(user_id=str(user_id), service_name="google").first()
        if not record:
            if user_id == LOCAL_TEST_USER and os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", config.GOOGLE_SCOPES)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open("token.json", "w") as token_file:
                        token_file.write(creds.to_json())
                return creds
            raise GoogleNotConnected(
                "Google account is not connected. Ask the user to click 'Connect Google' in the dashboard."
            )

        creds = Credentials.from_authorized_user_info(decrypt_token(record.encrypted_data), config.GOOGLE_SCOPES)
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise GoogleNotConnected(f"Failed to refresh Google credentials, please reconnect: {e}")
            record.encrypted_data = encrypt_token(json.loads(creds.to_json()))
            session.commit()
        return creds
    finally:
        session.close()


def gmail_service(user_id: str):
    return build("gmail", "v1", credentials=get_credentials(user_id), cache_discovery=False)


def calendar_service(user_id: str):
    return build("calendar", "v3", credentials=get_credentials(user_id), cache_discovery=False)


def is_connected(user_id: str) -> bool:
    if not SyncSessionLocal:
        return False
    session = SyncSessionLocal()
    try:
        return session.query(UserToken).filter_by(user_id=str(user_id), service_name="google").first() is not None
    finally:
        session.close()


def user_id_from(config_obj) -> str:
    """Tools receive the authenticated user id through RunnableConfig (set in routers/chat.py)."""
    user_id = (config_obj or {}).get("configurable", {}).get("user_id")
    if not user_id:
        raise GoogleNotConnected("No authenticated user for this request.")
    return str(user_id)
