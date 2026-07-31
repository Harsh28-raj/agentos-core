import asyncio
from app.db.postgres import init_db, SyncSessionLocal
from app.db.models import UserToken
from app.core.security import encrypt_token, decrypt_token
import json

async def verify_encryption():
    print("Initializing Database...")
    await init_db()
    
    print("\n--- Testing Multi-Tenant Encrypted OAuth Token Storage ---")
    
    dummy_token = {
        "token": "ya29.a0AfB_byC...",
        "refresh_token": "1//04...",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "dummy.apps.googleusercontent.com",
        "client_secret": "dummy-secret",
        "scopes": ["https://mail.google.com/"]
    }
    
    print(f"Original Dummy Token Payload: {dummy_token}")
    
    encrypted_str = encrypt_token(dummy_token)
    print(f"\nEncrypted String (Fernet): {encrypted_str}")
    
    decrypted_token = decrypt_token(encrypted_str)
    print(f"\nDecrypted Payload: {decrypted_token}")
    
    if dummy_token == decrypted_token:
        print("\n✅ Verification Successful: Fernet encryption and decryption cycle works perfectly!")
    else:
        print("\n❌ Verification Failed: Decrypted payload does not match original.")
        return
        
    print("\nVerifying Postgres UserToken table configuration...")
    session = SyncSessionLocal()
    try:
        # Check if table exists by doing a test query
        count = session.query(UserToken).count()
        print(f"Table 'user_tokens' is active and contains {count} records.")
        print("\n✅ Verification Successful: Neon Postgres DB is properly configured for Multi-Tenant Encrypted Storage!")
    except Exception as e:
        print(f"\n❌ Verification Failed: Database query error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(verify_encryption())
