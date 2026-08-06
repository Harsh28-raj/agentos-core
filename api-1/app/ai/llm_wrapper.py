import json
import re
from typing import Any, List, Optional
from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

def parse_fallback_json(ai_message: AIMessage) -> AIMessage:
    if not ai_message.tool_calls and ai_message.content and isinstance(ai_message.content, str):
        # Look for a JSON structure containing "name": "..." and optionally "arguments", "parameters" or "args"
        match = re.search(r'\{.*"name"\s*:\s*".*?.*\}', ai_message.content, re.DOTALL | re.IGNORECASE)
        
        # Or look for "type": "function"
        if not match:
            match = re.search(r'\{.*"type"\s*:\s*"function".*\}', ai_message.content, re.DOTALL | re.IGNORECASE)
            
        if match:
            try:
                parsed = json.loads(match.group(0))
                
                # Sometime Groq outputs {"type": "function", "function": {"name": "...", "arguments": "{...}"}}
                if "function" in parsed and isinstance(parsed["function"], dict):
                    parsed = parsed["function"]
                    
                if "name" in parsed:
                    name = parsed["name"]
                    
                    # Extract args
                    args = parsed.get("parameters", parsed.get("arguments", parsed.get("args", {})))
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                            
                    # Inject tool call
                    ai_message.tool_calls = [{
                        "name": name,
                        "args": args,
                        "id": "call_fallback_1"
                    }]
                    # Clear the content so it doesn't leak into UI
                    ai_message.content = ""
            except json.JSONDecodeError:
                pass
    return ai_message

class FallbackBoundModel(Runnable):
    def __init__(self, bound_model: Any):
        self.bound_model = bound_model
        
    def invoke(self, *args, **kwargs) -> AIMessage:
        res = self.bound_model.invoke(*args, **kwargs)
        if isinstance(res, AIMessage):
            res = parse_fallback_json(res)
        return res
        
    async def ainvoke(self, *args, **kwargs) -> AIMessage:
        res = await self.bound_model.ainvoke(*args, **kwargs)
        if isinstance(res, AIMessage):
            res = parse_fallback_json(res)
        return res
        
    # We must proxy stream, astream, etc.
    # Note: For stream events in LangGraph, ainvoke is used by create_react_agent internally inside a node.
    # So intercepting invoke and ainvoke is sufficient.
    def __getattr__(self, name: str) -> Any:
        return getattr(self.bound_model, name)

class FallbackLLMWrapper(Runnable):
    def __init__(self, model: BaseChatModel, **kwargs):
        super().__init__(**kwargs)
        self.inner_model = model
        
    def invoke(self, *args, **kwargs):
        res = self.inner_model.invoke(*args, **kwargs)
        if isinstance(res, AIMessage):
            res = parse_fallback_json(res)
        return res
        
    async def ainvoke(self, *args, **kwargs):
        res = await self.inner_model.ainvoke(*args, **kwargs)
        if isinstance(res, AIMessage):
            res = parse_fallback_json(res)
        return res
        
    def bind_tools(self, tools, **kwargs):
        bound = self.inner_model.bind_tools(tools, **kwargs)
        return FallbackBoundModel(bound)
        
    def with_structured_output(self, *args, **kwargs):
        return self.inner_model.with_structured_output(*args, **kwargs)
        
    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner_model, name)

