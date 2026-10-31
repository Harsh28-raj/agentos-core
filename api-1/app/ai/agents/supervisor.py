"""Supervisor graph: routes each request to a specialised worker agent.

    START -> supervisor -> <worker> -> supervisor -> ... -> FINISH (END)

Workers report back to the supervisor so multi-step requests ("check my calendar, then
email Rahul") can chain. A hop counter caps the chain at MAX_AGENT_HOPS worker runs per
user message so a confused model can never loop.

gmail_agent and calendar_agent are registered as *direct* subgraph nodes so LangGraph
checkpoints their internal interrupt() state: Command(resume=...) continues at the exact
interrupt() call. The other workers are wrapped and only contribute their final answer.
"""
import json
import logging
import re
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.ai.agents.calendar_agent import build_calendar_agent
from app.ai.agents.coder_agent import build_coder_agent
from app.ai.agents.gmail_agent import build_gmail_agent
from app.ai.agents.research_agent import build_research_agent
from app.ai.agents.vision_agent import build_vision_agent
from app.ai.llm import context_window, get_llm, now_context
from app.core import config

logger = logging.getLogger(__name__)

MEMBERS = ["research_agent", "coder_agent", "vision_agent", "gmail_agent", "calendar_agent"]
OPTIONS = ["FINISH", *MEMBERS]


class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str
    hops: int


SYSTEM_PROMPT = f"""You are a supervisor managing these workers: {", ".join(MEMBERS)}.
Given the conversation, decide which worker acts next, or FINISH.
- research_agent: web search, weather, arithmetic, remembering/recalling facts, greetings and general chat.
- coder_agent: writing or running Python code.
- vision_agent: analyzing an uploaded image.
- gmail_agent: searching, reading, drafting or sending emails.
- calendar_agent: checking the schedule or creating calendar events.
Rules:
1. If the latest message is from the user, pick the worker for it.
2. If a worker has replied and the user's whole request is answered, or the worker asked the user a question, respond FINISH.
3. Only pick another worker if part of the user's request is still not done (e.g. "check my calendar, then email Rahul").
4. Never pick the worker that just replied.
Respond with JSON only, exactly one key "next": {{"next": "<one of {OPTIONS}>"}}"""


def _router_view(messages: Sequence[BaseMessage]) -> list[BaseMessage]:
    """Plain-text transcript for the router: tool calls and tool results are dropped so the
    router never sends tool-call history to a model that has no tools bound."""
    view: list[BaseMessage] = []
    for m in context_window(list(messages)):
        if isinstance(m, HumanMessage):
            view.append(HumanMessage(content=str(m.content)))
        elif isinstance(m, AIMessage) and m.content:
            speaker = m.name or "assistant"
            view.append(AIMessage(content=f"[{speaker}] {m.content}"))
    return view


def _parse_route(text: str) -> str | None:
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0)).get("next")
    except (json.JSONDecodeError, AttributeError):
        return None
    return value if value in OPTIONS else None


def build_supervisor_graph(checkpointer=None, llm=None, worker_llm=None):
    """Compiles the graph. `llm`/`worker_llm` are injectable for tests (default: Groq)."""
    router_llm = (llm or get_llm()).bind(response_format={"type": "json_object"})

    async def supervisor_node(state: AgentState, config: RunnableConfig) -> dict:
        messages = list(state.get("messages", []))
        new_request = bool(messages) and isinstance(messages[-1], HumanMessage)
        hops = 0 if new_request else state.get("hops", 0) + 1

        if hops >= config_max_hops():
            logger.info("Supervisor: hop limit reached, finishing")
            return {"next": "FINISH", "hops": hops}

        prompt = [SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{now_context()}"), *_router_view(messages),
                  HumanMessage(content=f"Who should act next? Answer with JSON using one of {OPTIONS}.")]
        try:
            result = await router_llm.ainvoke(prompt, config)
            route = _parse_route(result.content)
        except Exception as e:
            logger.warning(f"Supervisor routing failed: {e}")
            route = None

        # `next` still holds the previous route, i.e. the worker that just replied
        last_worker = None if new_request else state.get("next")
        if route is None:
            # Unparseable answer: start with the general agent, or stop after a worker replied
            route = "research_agent" if new_request else "FINISH"
        if route == last_worker:
            route = "FINISH"
        logger.info(f"Supervisor routing to: {route} (hop {hops})")
        return {"next": route, "hops": hops}

    def wrap(agent):
        async def run(state: AgentState, config: RunnableConfig) -> dict:
            result = await agent.ainvoke({"messages": state["messages"]}, config)
            last = result["messages"][-1]
            content = last.content if getattr(last, "content", None) else str(last)
            return {"messages": [AIMessage(content=content, name=agent.name)]}
        return run

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("research_agent", wrap(build_research_agent(worker_llm)))
    builder.add_node("coder_agent", wrap(build_coder_agent(worker_llm)))
    builder.add_node("vision_agent", wrap(build_vision_agent(worker_llm)))
    builder.add_node("gmail_agent", build_gmail_agent(worker_llm))
    builder.add_node("calendar_agent", build_calendar_agent(worker_llm))

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", lambda s: s["next"], {**{m: m for m in MEMBERS}, "FINISH": END})
    for member in MEMBERS:
        builder.add_edge(member, "supervisor")

    return builder.compile(checkpointer=checkpointer)


def config_max_hops() -> int:
    return max(1, config.MAX_AGENT_HOPS)
