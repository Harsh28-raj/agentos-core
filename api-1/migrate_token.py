"""Stores a local token.json (from generate_token.py) for one AgentOS user.

The normal way to connect Google is the "Connect Google" button in the dashboard.
This script is a fallback for the account owner, e.g. before OAuth is configured:

    python migrate_token.py --email you@example.com
"""
import argparse
import asyncio
import json
import os

from app.core.security import encrypt_token
from app.db.models import User, UserToken
from app.db.postgres import SyncSessionLocal, init_db


async def migrate(email: str):
    await init_db()

    base = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(base, "token.json")
    if not os.path.exists(token_path):
        token_path = os.path.join(base, "token.json.bak")
    if not os.path.exists(token_path):
        print("token.json or token.json.bak not found. Run generate_token.py first.")
        return

    with open(token_path, "r") as f:
        token_data = json.load(f)

    session = SyncSessionLocal()
    try:
        user = session.query(User).filter(User.email.ilike(email.strip())).first()
        if not user:
            print(f"No AgentOS user with email {email}. Register in the app first.")
            return
        user_id = str(user.id)
        encrypted = encrypt_token(token_data)
        record = session.query(UserToken).filter_by(user_id=user_id, service_name="google").first()
        if record:
            record.encrypted_data = encrypted
        else:
            session.add(UserToken(user_id=user_id, service_name="google", encrypted_data=encrypted))
        session.commit()
        print(f"Stored Google token for {user.email} (user id {user_id}).")

        if token_path.endswith("token.json"):
            os.rename(token_path, token_path + ".bak")
            print("Renamed token.json to token.json.bak for safety.")
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True, help="Email of the AgentOS account that owns this Google token")
    asyncio.run(migrate(parser.parse_args().email))
