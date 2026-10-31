import logging
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core import config
from app.db.models import Base, EpisodicLog  # noqa: F401  (EpisodicLog is re-exported)

logger = logging.getLogger(__name__)


def _base_postgres_url(url: str) -> str:
    """Returns the URL as plain postgresql://user:pass@host/db, without driver or query string."""
    url = url.split("?")[0]
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg://", "postgresql+psycopg2://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix):]
    return url


def _needs_ssl(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    return host not in {"localhost", "127.0.0.1", "db", "postgres"}


RAW_URL = config.DATABASE_URL
IS_POSTGRES = RAW_URL.startswith(("postgresql", "postgres://"))
IS_SQLITE = RAW_URL.startswith("sqlite")

if IS_POSTGRES:
    _base = _base_postgres_url(RAW_URL)
    _ssl = _needs_ssl(_base)
    ASYNC_URL = _base.replace("postgresql://", "postgresql+asyncpg://", 1)
    SYNC_URL = _base.replace("postgresql://", "postgresql+psycopg://", 1)
    # libpq-style URL used by psycopg directly (checkpointer, PGVector)
    PSYCOPG_URL = _base + ("?sslmode=require" if _ssl else "")
    _async_args = {"ssl": "require"} if _ssl else {}
    _sync_args = {"sslmode": "require"} if _ssl else {}
elif IS_SQLITE:
    # Used by the test-suite and quick local runs.
    ASYNC_URL = RAW_URL if "+aiosqlite" in RAW_URL else RAW_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
    SYNC_URL = ASYNC_URL.replace("+aiosqlite", "")
    PSYCOPG_URL = ""
    _async_args, _sync_args = {}, {}
else:
    ASYNC_URL = SYNC_URL = PSYCOPG_URL = ""
    _async_args, _sync_args = {}, {}

engine = create_async_engine(
    ASYNC_URL, echo=False, pool_pre_ping=True, pool_recycle=300, connect_args=_async_args
) if ASYNC_URL else None
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) if engine else None

# Synchronous engine for tools that run in worker threads (Gmail / Calendar credentials)
sync_engine = create_engine(SYNC_URL, pool_pre_ping=True, connect_args=_sync_args) if SYNC_URL else None
SyncSessionLocal = sessionmaker(bind=sync_engine) if sync_engine else None


# Set by init_db: whether long-term memory (pgvector) can work on this database
PGVECTOR_AVAILABLE = False


async def init_db():
    global PGVECTOR_AVAILABLE
    if not engine:
        logger.warning("DATABASE_URL is not set. Auth, logs and Google tokens are disabled.")
        return
    if IS_POSTGRES:
        # Own transaction: a missing pgvector must not stop the auth/log tables being created
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            PGVECTOR_AVAILABLE = True
        except Exception as e:
            logger.warning(f"pgvector extension unavailable (long-term memory disabled): {e}")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            if IS_POSTGRES:
                # Columns added after the first release (create_all does not alter existing tables)
                for column, kind in (("action_taken", "VARCHAR"), ("original_args", "JSONB"),
                                     ("modified_args", "JSONB"), ("human_feedback", "TEXT")):
                    await conn.execute(text(f"ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS {column} {kind}"))
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


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
    human_feedback: str = None,
):
    """Writes one audit row. `thread_id` is the user-scoped session key (see routers/chat.py)."""
    if not AsyncSessionLocal:
        return
    try:
        async with AsyncSessionLocal() as session:
            session.add(EpisodicLog(
                thread_id=thread_id,
                run_id=str(run_id),
                tool_name=tool_name,
                tool_input=_jsonable(tool_input),
                tool_output=_jsonable(tool_output),
                reasoning_steps=_jsonable(reasoning_steps),
                status=status,
                latency_ms=latency_ms,
                action_taken=action_taken,
                original_args=_jsonable(original_args),
                modified_args=_jsonable(modified_args),
                human_feedback=human_feedback,
            ))
            await session.commit()
    except Exception as e:
        logger.error(f"Error logging to database: {e}")


def _jsonable(value):
    """JSON columns reject arbitrary objects (e.g. LangChain messages) - coerce them to strings."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)
