"""Chooses the LangGraph checkpointer that stores conversation + paused-approval state.

The API is fully async (ainvoke / astream_events), so only async savers work: the old sync
RedisSaver raised NotImplementedError on every async call.

CHECKPOINTER=auto (default) picks Postgres when DATABASE_URL is Postgres, else Redis when
REDIS_URL is set, else in-memory (state is lost on restart - development only).
"""
import logging
from contextlib import asynccontextmanager

from langgraph.checkpoint.memory import MemorySaver

from app.core import config
from app.db.postgres import IS_POSTGRES, PSYCOPG_URL

logger = logging.getLogger(__name__)


def _choice() -> str:
    if config.CHECKPOINTER != "auto":
        return config.CHECKPOINTER
    if IS_POSTGRES:
        return "postgres"
    if config.REDIS_URL:
        return "redis"
    return "memory"


@asynccontextmanager
async def open_checkpointer():
    """Yields (saver, kind). Falls back to memory with an error log if the store is unreachable."""
    kind = _choice()
    if kind == "postgres" and PSYCOPG_URL:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg.rows import dict_row
            from psycopg_pool import AsyncConnectionPool

            pool = AsyncConnectionPool(
                conninfo=PSYCOPG_URL,
                max_size=10,
                open=False,
                # prepare_threshold=0 is required behind PgBouncer (Neon pooled endpoints)
                kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            )
            await pool.open(wait=True, timeout=30)
            saver = AsyncPostgresSaver(pool)
            await saver.setup()
        except Exception as e:
            logger.error(f"Postgres checkpointer unavailable, falling back to memory: {e}")
            if "pool" in locals():
                await pool.close()
        else:
            try:
                logger.info("Checkpointer: Postgres")
                yield saver, "postgres"
                return
            finally:
                await pool.close()
    elif kind == "redis" and config.REDIS_URL:
        try:
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver
            cm = AsyncRedisSaver.from_conn_string(config.REDIS_URL)
            saver = await cm.__aenter__()
            await saver.asetup()
        except Exception as e:
            logger.error(f"Redis checkpointer unavailable, falling back to memory: {e}")
        else:
            try:
                logger.info("Checkpointer: Redis")
                yield saver, "redis"
                return
            finally:
                await cm.__aexit__(None, None, None)

    logger.warning("Checkpointer: in-memory. Conversations and pending approvals are lost on restart.")
    yield MemorySaver(), "memory"
