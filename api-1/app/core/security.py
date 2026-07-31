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
