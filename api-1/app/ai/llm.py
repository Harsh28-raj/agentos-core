"""Single place that builds chat models and the per-turn prompt context."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core import config


def get_llm(model: str | None = None, **overrides) -> ChatGroq:
    params = dict(
        model=model or config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        max_retries=5,
        temperature=0.0,
        timeout=60.0,
    )
    params.update(overrides)
    return ChatGroq(**params)


def get_vision_llm() -> ChatGroq:
    return get_llm(model=config.GROQ_VISION_MODEL)


def _tz() -> ZoneInfo:
    try:
        return ZoneInfo(config.DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def now_context() -> str:
    """Models have no clock: without this, 'tomorrow at 4pm' resolves to a random date."""
    now = datetime.now(_tz())
    return (
        f"Current date and time: {now.strftime('%A, %Y-%m-%d %H:%M')} "
        f"(timezone {now.tzname()}, ISO {now.isoformat(timespec='seconds')}). "
        f"Interpret relative dates such as 'today' or 'tomorrow' from this, and always write "
        f"timestamps in ISO 8601 with an explicit UTC offset."
    )


def context_window(messages: list[BaseMessage], limit: int | None = None) -> list[BaseMessage]:
    """Returns the tail of the history that is sent to the model.

    The window always starts at a HumanMessage, so an AIMessage with tool_calls is never
    separated from its ToolMessages (Groq rejects orphaned tool messages). The latest
    human message and everything after it are always kept, even past `limit`.
    The stored history is never modified - trimming only affects what the model sees.
    """
    limit = limit or config.CONTEXT_WINDOW_MESSAGES
    messages = list(messages)
    human_idx = [i for i, m in enumerate(messages) if isinstance(m, HumanMessage)]
    if not human_idx:
        return messages[-limit:]
    start = max(len(messages) - limit, 0)
    candidates = [i for i in human_idx if i >= start]
    start = candidates[0] if candidates else human_idx[-1]
    return messages[start:]


def agent_prompt(system_text: str):
    """Builds a create_react_agent prompt callable: system text + clock + safe history window."""
    def _prompt(state) -> list[BaseMessage]:
        system = SystemMessage(content=f"{system_text.strip()}\n\n{now_context()}")
        return [system, *context_window(state["messages"])]
    return _prompt
