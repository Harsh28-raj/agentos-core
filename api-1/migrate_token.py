import os
import json
import asyncio
from dotenv import load_dotenv

# We need to run init_db first if tables are not created.
from app.db.postgres import init_db, SyncSessionLocal
from app.db.models import UserToken
from app.core.security import encrypt_token

load_dotenv()

async def migrate():
    # Ensure tables exist
    await init_db()
    
    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    if not os.path.exists(token_path):
        token_path = os.path.join(os.path.dirname(__file__), "token.json.bak")
    
    if not os.path.exists(token_path):
        print("token.json or token.json.bak not found. Nothing to migrate.")
        return
        
    with open(token_path, "r") as f:
        token_data = json.load(f)
        
    session = SyncSessionLocal()
    try:
        user_id = "default_user"
        service_name = "google"
        
        encrypted_data = encrypt_token(token_data)
        
        existing = session.query(UserToken).filter_by(user_id=user_id, service_name=service_name).first()
        if existing:
            existing.encrypted_data = encrypted_data
            print("Token updated for default_user.")
        else:
            new_token = UserToken(
                user_id=user_id,
                service_name=service_name,
                encrypted_data=encrypted_data
            )
            session.add(new_token)
        session.commit()
        
        print("Successfully migrated token.json to PostgreSQL for default_user!")
        
        # Optionally, delete or rename token.json
        os.rename(token_path, token_path + ".bak")
        print("Renamed token.json to token.json.bak for safety.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(migrate())
