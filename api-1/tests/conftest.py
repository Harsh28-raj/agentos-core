"""Test fixtures. Environment is set before the app is imported: SQLite database,
in-memory checkpointer, and scripted fake LLMs instead of Groq."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="agentos_tests_")
os.environ.update({
    "GROQ_API_KEY": "test-key",
    "DATABASE_URL": f"sqlite+aiosqlite:///{_TMP}/test.db",
    "JWT_SECRET_KEY": "test-secret-that-is-long-enough-for-hs256",
    "CHECKPOINTER": "memory",
    "UPLOAD_DIR": f"{_TMP}/uploads",
    "TAVILY_API_KEY": "",
    "ENABLE_CODE_INTERPRETER": "false",
})
os.environ.pop("REDIS_URL", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from typing import Any, Callable  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.language_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402
from langchain_core.outputs import ChatGeneration, ChatResult  # noqa: E402
from pydantic import Field  # noqa: E402


class ScriptedChatModel(BaseChatModel):
    """Returns queued responses in order. An item may be an AIMessage, a string, or a
    callable(messages) -> AIMessage | str. Records every prompt it received."""
    script: list[Any] = Field(default_factory=list)
    calls: list[Any] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.calls.append(messages)
        if not self.script:
            raise AssertionError(f"ScriptedChatModel ran out of responses (call #{len(self.calls)})")
        item = self.script.pop(0)
        if callable(item):
            item = item(messages)
        if isinstance(item, str):
            item = AIMessage(content=item)
        return ChatResult(generations=[ChatGeneration(message=item)])

    def bind_tools(self, tools, **kwargs):
        return self


def route(name: str) -> str:
    return '{"next": "%s"}' % name


def tool_call(name: str, args: dict, call_id: str = "call_1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


@pytest.fixture
def llms():
    return ScriptedChatModel(), ScriptedChatModel()


@pytest.fixture
def client(llms):
    from langgraph.checkpoint.memory import MemorySaver

    from app.ai.agents.supervisor import build_supervisor_graph
    from app.main import app

    router_llm, worker_llm = llms
    with TestClient(app) as c:
        app.state.graph = build_supervisor_graph(MemorySaver(), llm=router_llm, worker_llm=worker_llm)
        yield c


_counter = {"n": 0}


@pytest.fixture
def make_user(client) -> Callable[..., dict]:
    def _make(email: str | None = None, password: str = "password123") -> dict:
        _counter["n"] += 1
        email = email or f"user{_counter['n']}@example.com"
        assert client.post("/api/v1/auth/register", json={"email": email, "password": password}).status_code == 201
        token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        return {"email": email, "id": me["id"], "headers": {"Authorization": f"Bearer {token}"}}
    return _make
