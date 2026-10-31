from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.deps import CurrentUser, get_current_user
from app.db.postgres import AsyncSessionLocal, EpisodicLog
from app.routers.chat import THREAD_ID_PATTERN, _validate_thread, session_key

router = APIRouter(tags=["Logs"])


def _serialize(log: EpisodicLog) -> dict:
    return {
        "id": log.id,
        "run_id": log.run_id,
        "tool_name": log.tool_name,
        "tool_input": log.tool_input,
        "tool_output": log.tool_output,
        "reasoning_steps": log.reasoning_steps,
        "status": log.status,
        "latency_ms": log.latency_ms,
        "action_taken": log.action_taken,
        "original_args": log.original_args,
        "modified_args": log.modified_args,
        "human_feedback": log.human_feedback,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


# /api/logs/... is kept for backwards compatibility with the original README.
@router.get("/api/v1/logs/{thread_id}")
@router.get("/api/logs/{thread_id}", include_in_schema=False)
async def get_episodic_logs(thread_id: str, limit: int = 200, user: CurrentUser = Depends(get_current_user)):
    """Audit trail of one of the caller's threads (tool calls and human approval decisions)."""
    _validate_thread(thread_id)
    if not AsyncSessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured.")
    limit = max(1, min(limit, 1000))
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EpisodicLog)
            .where(EpisodicLog.thread_id == session_key(user, thread_id))
            .order_by(EpisodicLog.created_at.desc(), EpisodicLog.id.desc())
            .limit(limit)
        )
        logs = list(reversed(result.scalars().all()))
    return {"thread_id": thread_id, "logs": [_serialize(log) for log in logs]}


__all__ = ["router", "THREAD_ID_PATTERN"]
