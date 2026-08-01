import os
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY) if ENCRYPTION_KEY else None

def encrypt_token(data: dict) -> str:
    """Encrypts a token dictionary into a string using Fernet."""
    if not fernet:
        raise ValueError("ENCRYPTION_KEY is not set. Cannot encrypt token.")
    json_data = json.dumps(data)
    return fernet.encrypt(json_data.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted_str: str) -> dict:
    """Decrypts a Fernet encrypted string back into a token dictionary."""
    if not fernet:
        raise ValueError("ENCRYPTION_KEY is not set. Cannot decrypt token.")
    decrypted_data = fernet.decrypt(encrypted_str.encode("utf-8")).decode("utf-8")
    return json.loads(decrypted_data)

from datetime import datetime, timedelta
import bcrypt
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
