import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={"ssl": "require"}
) if DATABASE_URL else None
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) if engine else None
Base = declarative_base()

class EpisodicLog(Base):
    __tablename__ = "episodic_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(String, index=True, nullable=False)
    run_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    reasoning_steps = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="started")
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_db():
    if not engine:
        print("Warning: NEON_DATABASE_URL is not set or invalid. Skipping DB init.")
        return
    try:
        async with engine.begin() as conn:
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
    latency_ms: float = None
):
    if not AsyncSessionLocal:
        return
    
    try:
        async with AsyncSessionLocal() as session:
            new_log = EpisodicLog(
                thread_id=thread_id,
                run_id=run_id,
                status=status,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                reasoning_steps=reasoning_steps,
                latency_ms=latency_ms
            )
            session.add(new_log)
            await session.commit()
    except Exception as e:
        print(f"Error logging episodic event: {e}")
