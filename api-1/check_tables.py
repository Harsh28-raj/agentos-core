import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()
db_url = os.getenv('NEON_DATABASE_URL')
if '?' in db_url:
    db_url = db_url.split('?')[0]
db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
engine = create_async_engine(db_url, connect_args={'ssl': 'require'})

async def check():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT current_database();"))
        print('Current DB:', res.scalar())
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = res.scalars().all()
        print('Tables:', tables)

asyncio.run(check())
