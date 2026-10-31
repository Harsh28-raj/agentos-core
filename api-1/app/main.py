import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.checkpointer import open_checkpointer
from app.core import config
from app.db.postgres import init_db
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.integrations import router as integrations_router
from app.routers.logs import router as logs_router
from app.routers.system import router as system_router
from app.routers.upload import router as upload_router

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("agentos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with open_checkpointer() as (saver, kind):
        app.state.checkpointer_kind = kind
        try:
            from app.ai.agents.supervisor import build_supervisor_graph
            app.state.graph = build_supervisor_graph(checkpointer=saver)
        except Exception as e:
            # Keep auth/health endpoints up; chat endpoints answer 503
            logger.error(f"Could not build the agent graph: {e}")
            app.state.graph = None
        yield


app = FastAPI(
    title="AgentOS Backend Engine",
    description="The Personal AI Operating System Backend Engine with Multi-Agent Supervisor",
    version="1.1.0",
    lifespan=lifespan,
)

# Auth uses bearer tokens in the Authorization header, never cookies, so credentials
# are not needed cross-origin. Restrict origins in production with CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(logs_router)
app.include_router(integrations_router)
app.include_router(system_router)


@app.get("/")
async def root():
    return {"status": "AgentOS Backend is running smoothly! 🚀"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
