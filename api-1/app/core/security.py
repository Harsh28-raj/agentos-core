import json
import logging
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.fernet import Fernet

from app.core import config

logger = logging.getLogger(__name__)

fernet = Fernet(config.ENCRYPTION_KEY) if config.ENCRYPTION_KEY else None


def encrypt_token(data: dict) -> str:
    """Encrypts a token dictionary into a string using Fernet."""
    if not fernet:
        raise ValueError("ENCRYPTION_KEY is not set. Cannot encrypt token.")
    return fernet.encrypt(json.dumps(data).encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_str: str) -> dict:
    """Decrypts a Fernet encrypted string back into a token dictionary."""
    if not fernet:
        raise ValueError("ENCRYPTION_KEY is not set. Cannot decrypt token.")
    return json.loads(fernet.decrypt(encrypted_str.encode("utf-8")).decode("utf-8"))


# Never fall back to a well-known secret: anyone could forge tokens with it.
# A random per-process secret is safe; sessions just reset when the server restarts.
if config.JWT_SECRET_KEY:
    SECRET_KEY = config.JWT_SECRET_KEY
else:
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("JWT_SECRET_KEY is not set: using a random secret. All sessions end on restart.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = config.ACCESS_TOKEN_EXPIRE_DAYS
# bcrypt only looks at the first 72 bytes and bcrypt>=5 raises on longer input.
MAX_PASSWORD_BYTES = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodes a JWT. Raises jwt.PyJWTError when invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
