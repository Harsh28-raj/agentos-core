"""Chat, streaming, approval (human-in-the-loop) and history endpoints.

Every endpoint is authenticated. The LangGraph thread key is always built from the
authenticated user id, so one user can never read, resume or delete another user's thread.
"""
import asyncio
import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.types import Command
from pydantic import BaseModel, Field
from sqlalchemy import delete

from app.ai.agents.supervisor import MEMBERS
from app.core import config
from app.core.deps import CurrentUser, get_current_user
from app.core.hitl import classify_approval
from app.db.models import EpisodicLog
from app.db.postgres import AsyncSessionLocal, log_episodic_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])

THREAD_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
_background_tasks: set[asyncio.Task] = set()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    thread_id: str = Field("default", pattern=THREAD_ID_PATTERN)


class ApproveRequest(BaseModel):
    thread_id: str = Field("default", pattern=THREAD_ID_PATTERN)
    action: Literal["CONFIRM", "REJECT", "EDIT"]
    updated_args: dict[str, Any] | None = None
    feedback_message: str | None = Field(None, max_length=2000)


# ---------------------------------------------------------------- helpers

def session_key(user: CurrentUser, thread_id: str) -> str:
    return f"agentos_new:{user.id}_{thread_id}"


def graph_config(user: CurrentUser, thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": session_key(user, thread_id), "user_id": user.id},
        "recursion_limit": config.RECURSION_LIMIT,
    }


def get_graph(request: Request):
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="Agent engine is not available (check GROQ_API_KEY).")
    return graph


async def pending_interrupts(graph, cfg: dict) -> list:
    """All interrupt() calls waiting for a human, including ones inside subgraphs."""
    state = await graph.aget_state(cfg, subgraphs=True)
    found = {}
    for item in getattr(state, "interrupts", ()) or ():
        found[item.id] = item
    for task in state.tasks:
        for item in task.interrupts:
            found[item.id] = item
    return list(found.values())


def resume_command(interrupts: list, value: Any) -> Command:
    if len(interrupts) <= 1:
        return Command(resume=value)
    # Several tools paused in parallel: answer every one of them, not just the first
    return Command(resume={item.id: value for item in interrupts})


def pause_payload(interrupts: list, reply: str | None = None) -> dict:
    data = interrupts[0].value if interrupts and isinstance(interrupts[0].value, dict) else {}
    return {
        "reply": reply or f"⏸️ Awaiting your approval before executing: **{data.get('action', 'action')}**",
        "hitl_interrupt": True,
        "interrupt_data": data,
        "pending_count": len(interrupts),
    }


def final_reply(messages: list[BaseMessage]) -> str:
    """Last assistant text produced after the latest user message."""
    last_human = max((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=-1)
    for message in reversed(messages[last_human + 1:]):
        if isinstance(message, AIMessage) and message.content and not message.tool_calls:
            return str(message.content)
    return "I couldn't produce an answer for that. Could you rephrase?"


def friendly_error(error: Exception) -> str:
    text = str(error)
    if "Rate limit reached" in text or "rate_limit_exceeded" in text:
        return "⚠️ Groq rate limit reached for this model. Please wait a moment and try again."
    if "tool call validation failed" in text or "tool_use_failed" in text:
        return "I got a bit confused while trying to use my tools. Could you please rephrase your request?"
    if "recursion" in text.lower():
        return "I tried to process your request but needed too many steps. Could you be more specific?"
    return "⚠️ Something went wrong while processing your request. Please try again."


async def audit_decision(user, thread_id, interrupts, decision, updated_args=None, feedback=None):
    data = interrupts[0].value if interrupts and isinstance(interrupts[0].value, dict) else None
    await log_episodic_event(
        thread_id=session_key(user, thread_id),
        run_id=interrupts[0].id if interrupts else decision.lower(),
        tool_name=f"HITL_{decision}",
        action_taken=decision,
        original_args=data,
        modified_args=updated_args,
        human_feedback=feedback,
        status="completed",
    )


def _log_in_background(**kwargs):
    task = asyncio.create_task(log_episodic_event(**kwargs))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def run_turn(graph, cfg: dict, graph_input) -> dict:
    result = await graph.ainvoke(graph_input, cfg)
    interrupts = await pending_interrupts(graph, cfg)
    if interrupts:
        return pause_payload(interrupts)
    return {"reply": final_reply(list(result.get("messages", [])))}


async def resolve_input(graph, cfg, user, thread_id, message):
    """Returns (graph_input, early_response). A pending approval is answered from the message;
    an unclear answer re-asks instead of guessing. State is never edited while paused."""
    interrupts = await pending_interrupts(graph, cfg)
    if not interrupts:
        return {"messages": [HumanMessage(content=message)]}, None
    decision = classify_approval(message)
    if decision is None:
        return None, pause_payload(
            interrupts,
            '⏸️ An action is waiting for your approval. Reply "yes" to approve or "no" to cancel, '
            "or use the Approve / Reject buttons.",
        )
    await audit_decision(user, thread_id, interrupts, decision, feedback=message)
    return resume_command(interrupts, decision), None


# ---------------------------------------------------------------- endpoints

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user: CurrentUser = Depends(get_current_user),
                        graph=Depends(get_graph)):
    cfg = graph_config(user, request.thread_id)
    try:
        graph_input, early = await resolve_input(graph, cfg, user, request.thread_id, request.message)
        if early:
            return early
        return await run_turn(graph, cfg, graph_input)
    except Exception as e:
        logger.exception("Chat error")
        return {"reply": friendly_error(e), "error": True}


@router.post("/chat/approve")
async def approve_hitl(request: ApproveRequest, user: CurrentUser = Depends(get_current_user),
                       graph=Depends(get_graph)):
    """Confirms, rejects, or edits the arguments of the action that is waiting for approval."""
    cfg = graph_config(user, request.thread_id)
    interrupts = await pending_interrupts(graph, cfg)
    if not interrupts:
        raise HTTPException(status_code=409, detail="No action is waiting for approval.")
    if request.action == "EDIT" and not request.updated_args:
        raise HTTPException(status_code=400, detail="updated_args is required for EDIT action")

    value = {"decision": "EDIT", "args": request.updated_args} if request.action == "EDIT" else request.action
    await audit_decision(user, request.thread_id, interrupts, request.action,
                         updated_args=request.updated_args, feedback=request.feedback_message)
    try:
        result = await run_turn(graph, cfg, resume_command(interrupts, value))
    except Exception as e:
        logger.exception("Approve error")
        raise HTTPException(status_code=500, detail=friendly_error(e))

    status = "rejected" if request.action == "REJECT" else "resumed"
    message = {"CONFIRM": "Action approved and resumed.", "EDIT": "Action edited and resumed.",
               "REJECT": "Action rejected."}[request.action]
    return {"status": status, "message": message, **result}


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, user: CurrentUser = Depends(get_current_user),
                               graph=Depends(get_graph)):
    """Streams execution events over Server-Sent Events:
    thinking, route, tool_start, tool_end, token, hitl_pause, done, error."""
    cfg = graph_config(user, request.thread_id)
    key = session_key(user, request.thread_id)

    def sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, default=str)}\n\n"

    async def event_generator():
        try:
            graph_input, early = await resolve_input(graph, cfg, user, request.thread_id, request.message)
            if early:
                yield sse({"type": "hitl_pause", "content": early["reply"], "tool": early["interrupt_data"].get("tool"),
                           "pending_args": early["interrupt_data"]})
                return

            yield sse({"type": "thinking", "content": "Analyzing query and planning multi-agent steps..."})
            input_tokens = output_tokens = 0
            last_route = None
            async for event in graph.astream_events(graph_input, config=cfg, version="v2"):
                kind = event.get("event")
                name = event.get("name", "")
                node = event.get("metadata", {}).get("langgraph_node")
                if kind == "on_chain_start" and name in MEMBERS and node == name and name != last_route:
                    last_route = name
                    yield sse({"type": "route", "content": f"Routing task to {name.replace('_', ' ').title()}"})
                elif kind == "on_chain_start" and name == "supervisor" and node == name:
                    last_route = None
                elif kind == "on_tool_start":
                    tool_input = event.get("data", {}).get("input", {})
                    _log_in_background(thread_id=key, run_id=event.get("run_id", "unknown"), status="started",
                                       tool_name=name, tool_input=tool_input)
                    yield sse({"type": "tool_start", "tool": name, "content": f"Executing tool: {name}", "input": tool_input})
                elif kind == "on_tool_end":
                    output = str(event.get("data", {}).get("output", ""))
                    _log_in_background(thread_id=key, run_id=event.get("run_id", "unknown"), status="completed",
                                       tool_name=name, tool_output={"output": output[:5000]})
                    yield sse({"type": "tool_end", "tool": name, "content": f"Finished executing {name}", "output": output[:150]})
                elif kind == "on_chat_model_end":
                    usage = getattr(event.get("data", {}).get("output"), "usage_metadata", None) or {}
                    input_tokens += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)
                elif kind == "on_chat_model_stream" and node != "supervisor":
                    # The supervisor's routing JSON is internal - never stream it to the user
                    chunk = event.get("data", {}).get("chunk")
                    if chunk is not None and getattr(chunk, "content", None) and not getattr(chunk, "tool_call_chunks", None):
                        yield sse({"type": "token", "content": chunk.content})

            interrupts = await pending_interrupts(graph, cfg)
            if interrupts:
                pause = pause_payload(interrupts)
                yield sse({"type": "hitl_pause", "content": pause["reply"], "tool": pause["interrupt_data"].get("tool"),
                           "pending_args": pause["interrupt_data"]})
            else:
                state = await graph.aget_state(cfg)
                yield sse({"type": "done", "reply": final_reply(list(state.values.get("messages", []))),
                           "tokens": {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens}})
        except Exception as e:
            logger.exception("Stream error")
            yield sse({"type": "error", "content": friendly_error(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/chat/history/{thread_id}")
async def get_chat_history(thread_id: str, user: CurrentUser = Depends(get_current_user), graph=Depends(get_graph)):
    _validate_thread(thread_id)
    cfg = graph_config(user, thread_id)
    state = await graph.aget_state(cfg)
    history = []
    for message in (state.values or {}).get("messages", []) if state else []:
        # Only what the user actually saw: no tool results, no tool-call stubs
        if isinstance(message, HumanMessage):
            history.append({"role": "user", "content": str(message.content)})
        elif isinstance(message, AIMessage) and message.content and not message.tool_calls:
            history.append({"role": "assistant", "content": str(message.content)})
    interrupts = await pending_interrupts(graph, cfg)
    return {"history": history, "pending": pause_payload(interrupts) if interrupts else None}


@router.delete("/chat/history/{thread_id}")
async def delete_chat_history(thread_id: str, user: CurrentUser = Depends(get_current_user), graph=Depends(get_graph)):
    _validate_thread(thread_id)
    key = session_key(user, thread_id)
    # Deletes exactly this thread (all checkpoints and subgraph namespaces) - no key patterns
    await graph.checkpointer.adelete_thread(key)
    if AsyncSessionLocal:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(EpisodicLog).where(EpisodicLog.thread_id == key))
            await session.commit()
    return {"status": "success", "message": f"Deleted thread {thread_id}"}


def _validate_thread(thread_id: str):
    import re
    if not re.fullmatch(THREAD_ID_PATTERN, thread_id):
        raise HTTPException(status_code=422, detail="Invalid thread_id")
