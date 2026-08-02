import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.models import Base, EpisodicLog, UserToken
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL", "")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"ssl": "require"}
) if DATABASE_URL else None
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) if engine else None

# Synchronous engine for tools that require blocking DB queries (e.g., Gmail OAuth)
sync_db_url = DATABASE_URL.replace("+asyncpg", "+psycopg") if DATABASE_URL else ""
sync_engine = create_engine(
    sync_db_url,
    connect_args={"sslmode": "require"}
) if sync_db_url else None
SyncSessionLocal = sessionmaker(bind=sync_engine) if sync_engine else None


async def init_db():
    if not engine:
        print("Warning: NEON_DATABASE_URL is not set or invalid. Skipping DB init.")
        return
    try:
        async with engine.begin() as conn:
            # Create pgvector extension if it doesn't exist
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        print("Neon Postgres DB initialized successfully!")
    except Exception as e:
        print(f"Error initializing Neon DB: {e}")

async def log_episodic_event(
    thread_id: str,
    run_id: str,
    status: str,
    tool_name: str = None,
    tool_input: dict = None,
    tool_output: dict = None,
    reasoning_steps: list = None,
    latency_ms: float = None,
    action_taken: str = None,
    original_args: dict = None,
    modified_args: dict = None,
    human_feedback: str = None
):
    if not AsyncSessionLocal:
        return
    
    try:
        async with AsyncSessionLocal() as session:
            log_entry = EpisodicLog(
                thread_id=thread_id,
                run_id=run_id,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                reasoning_steps=reasoning_steps,
                status=status,
                latency_ms=latency_ms,
                action_taken=action_taken,
                original_args=original_args,
                modified_args=modified_args,
                human_feedback=human_feedback
            )
            session.add(log_entry)
            await session.commit()
    except Exception as e:
        print(f"Error logging to postgres: {e}")
