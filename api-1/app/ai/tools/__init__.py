"""Tools available to the agents. Long-term memory tools are scoped to the calling user."""
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.ai.tools.calculator import calculator_tool
from app.ai.tools.weather import get_current_weather
from app.core import config as app_config
from app.db.vector_store import add_to_memory, search_memory

if not app_config.TAVILY_API_KEY:
    print("⚠️ WARNING: TAVILY_API_KEY is missing - web search will report itself unavailable.")

_tavily = None


@tool("web_search")
def web_search_tool(query: str) -> str:
    """Search the live web. Useful for current events, real-time info, news, or facts you are unsure of."""
    global _tavily
    if not app_config.TAVILY_API_KEY:
        return "Web search is not configured on this server (TAVILY_API_KEY missing)."
    try:
        if _tavily is None:
            from tavily import TavilyClient
            _tavily = TavilyClient(api_key=app_config.TAVILY_API_KEY)
        results = _tavily.search(query=query, max_results=3).get("results", [])
        if not results:
            return "No web results found."
        # Web content is untrusted: never follow instructions found inside it.
        return "\n\n".join(f"{r.get('title', '')}\n{r.get('url', '')}\n{r.get('content', '')[:800]}" for r in results)
    except Exception as e:
        return f"Web search error: {e}"


def _user_id(config: RunnableConfig | None) -> str | None:
    return (config or {}).get("configurable", {}).get("user_id")


@tool
def remember_fact(fact: str, config: RunnableConfig = None) -> str:
    """Save important information, user preferences, or facts permanently into the user's long-term memory."""
    user_id = _user_id(config)
    if not user_id:
        return "Failed to save memory: no authenticated user."
    try:
        add_to_memory(text=fact, user_id=user_id, metadata={"source": "user_chat_memory"})
        return f"Successfully remembered: '{fact}'"
    except Exception as e:
        return f"Failed to save memory: {e}"


@tool
def recall_fact(query: str, config: RunnableConfig = None) -> str:
    """Search the user's long-term memory and uploaded documents for past facts or preferences."""
    user_id = _user_id(config)
    if not user_id:
        return "Failed to search memory: no authenticated user."
    try:
        results = search_memory(query, user_id=user_id)
        return f"Found relevant memories: {' | '.join(results)}" if results else "No relevant memories found."
    except Exception as e:
        return f"Failed to search memory: {e}"


__all__ = ["calculator_tool", "get_current_weather", "web_search_tool", "remember_fact", "recall_fact"]
