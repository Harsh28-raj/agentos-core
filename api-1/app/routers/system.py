"""Real tool/integration status for the dashboard (replaces the hardcoded 'ONLINE' list)."""
from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool

from app.ai.tools.google_auth import is_connected
from app.core import config
from app.core.deps import CurrentUser, get_current_user
from app.db import postgres
from app.routers.integrations import oauth_configured

router = APIRouter(prefix="/api/v1/system", tags=["System"])


def _tool(name: str, ok: bool, detail: str) -> dict:
    return {"name": name, "status": "ONLINE" if ok else "OFFLINE", "detail": detail}


@router.get("/status")
async def system_status(request: Request, user: CurrentUser = Depends(get_current_user)):
    llm_ok = bool(config.GROQ_API_KEY) and getattr(request.app.state, "graph", None) is not None
    google = await run_in_threadpool(is_connected, user.id)
    google_detail = "Connected" if google else ("Click 'Connect Google'" if oauth_configured() else "OAuth not configured")
    tools = [
        _tool("Web Search", bool(config.TAVILY_API_KEY), "Tavily" if config.TAVILY_API_KEY else "TAVILY_API_KEY missing"),
        _tool("Weather API", True, "wttr.in"),
        _tool("Calculator", True, "Built-in"),
        _tool("Long-term Memory", postgres.PGVECTOR_AVAILABLE,
              "PGVector" if postgres.PGVECTOR_AVAILABLE else "Needs Postgres with the pgvector extension"),
        _tool("Code Interpreter", config.ENABLE_CODE_INTERPRETER,
              "Enabled" if config.ENABLE_CODE_INTERPRETER else "Disabled (ENABLE_CODE_INTERPRETER)"),
        _tool("Vision", llm_ok, config.GROQ_VISION_MODEL),
        _tool("Gmail Agent", google, google_detail),
        _tool("Calendar Agent", google, google_detail),
    ]
    return {
        "llm": {"status": "ONLINE" if llm_ok else "OFFLINE", "model": config.GROQ_MODEL},
        "checkpointer": getattr(request.app.state, "checkpointer_kind", "unknown"),
        "tools": tools,
        "active_tools": sum(t["status"] == "ONLINE" for t in tools),
    }
