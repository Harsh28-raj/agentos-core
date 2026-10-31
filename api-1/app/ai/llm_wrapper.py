import json
import re
import uuid
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

_NAME_RE = re.compile(r'\{.*"name"\s*:\s*".*?.*\}', re.DOTALL | re.IGNORECASE)
_FUNCTION_RE = re.compile(r'\{.*"type"\s*:\s*"function".*\}', re.DOTALL | re.IGNORECASE)


def parse_fallback_json(ai_message: AIMessage) -> AIMessage:
    """Small Llama models sometimes print a tool call as JSON text instead of a native tool call.
    Converts that text into a real tool call so the ReAct loop can execute it."""
    if ai_message.tool_calls or not ai_message.content or not isinstance(ai_message.content, str):
        return ai_message
    match = _NAME_RE.search(ai_message.content) or _FUNCTION_RE.search(ai_message.content)
    if not match:
        return ai_message
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return ai_message
    # Sometimes Groq outputs {"type": "function", "function": {"name": "...", "arguments": "{...}"}}
    if isinstance(parsed.get("function"), dict):
        parsed = parsed["function"]
    if "name" not in parsed:
        return ai_message

    args = parsed.get("parameters", parsed.get("arguments", parsed.get("args", {})))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    # Unique ids: a fixed id made every fallback call collide in the message history
    ai_message.tool_calls = [{"name": parsed["name"], "args": args or {}, "id": f"call_{uuid.uuid4().hex[:24]}"}]
    ai_message.content = ""  # so the raw JSON does not leak into the UI
    return ai_message


class FallbackBoundModel(Runnable):
    def __init__(self, bound_model: Any):
        self.bound_model = bound_model

    def invoke(self, *args, **kwargs) -> AIMessage:
        res = self.bound_model.invoke(*args, **kwargs)
        return parse_fallback_json(res) if isinstance(res, AIMessage) else res

    async def ainvoke(self, *args, **kwargs) -> AIMessage:
        res = await self.bound_model.ainvoke(*args, **kwargs)
        return parse_fallback_json(res) if isinstance(res, AIMessage) else res

    def __getattr__(self, name: str) -> Any:
        return getattr(self.bound_model, name)


class FallbackLLMWrapper(Runnable):
    def __init__(self, model: BaseChatModel, **kwargs):
        super().__init__(**kwargs)
        self.inner_model = model

    def invoke(self, *args, **kwargs):
        res = self.inner_model.invoke(*args, **kwargs)
        return parse_fallback_json(res) if isinstance(res, AIMessage) else res

    async def ainvoke(self, *args, **kwargs):
        res = await self.inner_model.ainvoke(*args, **kwargs)
        return parse_fallback_json(res) if isinstance(res, AIMessage) else res

    def bind_tools(self, tools, **kwargs):
        return FallbackBoundModel(self.inner_model.bind_tools(tools, **kwargs))

    def with_structured_output(self, *args, **kwargs):
        return self.inner_model.with_structured_output(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner_model, name)
