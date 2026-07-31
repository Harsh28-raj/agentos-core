import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.db.models import Base, EpisodicLog, UserToken

# Explicitly load from api-1/.env and override
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path, override=True)

db_url = os.getenv('NEON_DATABASE_URL')
print("Loaded NEON_DATABASE_URL:", db_url)

if '?' in db_url:
    db_url = db_url.split('?')[0]
db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
print("Processed Engine URL:", db_url)

engine = create_async_engine(db_url, connect_args={'ssl': 'require'}, echo=True)

async def check():
    async with engine.begin() as conn:
        print("Engine URL internally:", str(engine.url))
        
        # Force create tables
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        
        res = await conn.execute(text("SELECT current_database();"))
        print('Current DB:', res.scalar())
        
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = res.scalars().all()
        print('Tables:', tables)

asyncio.run(check())
