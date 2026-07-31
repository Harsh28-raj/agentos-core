from fastapi import APIRouter, HTTPException
from app.db.postgres import AsyncSessionLocal, EpisodicLog
from sqlalchemy import select

router = APIRouter()

@router.get("/api/logs/{thread_id}")
async def get_episodic_logs(thread_id: str):
    if not AsyncSessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured.")
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(EpisodicLog)
                .where(EpisodicLog.thread_id == thread_id)
                .order_by(EpisodicLog.created_at.asc())
            )
            logs = result.scalars().all()
            
            return {
                "thread_id": thread_id,
                "logs": [
                    {
                        "id": log.id,
                        "run_id": log.run_id,
                        "tool_name": log.tool_name,
                        "tool_input": log.tool_input,
                        "tool_output": log.tool_output,
                        "reasoning_steps": log.reasoning_steps,
                        "status": log.status,
                        "latency_ms": log.latency_ms,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    for log in logs
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
