import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

# Database functions ko import karein
from app.db.vector_store import add_to_memory, search_memory

# Environment variables load karna
load_dotenv()

# Safety check for Tavily API Key
tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    print("⚠️ WARNING: TAVILY_API_KEY is missing in environment variables!")

# --- 1. Weather Tool (Dummy/Test Tool) ---
@tool
def get_weather(location: str) -> str:
    """Gets the current weather for a given location."""
    return f"The weather in {location} is 28°C and sunny."

# --- 2. Live Web Search Tool (Tavily) ---
web_search_tool = TavilySearchResults(
    max_results=3,
    description="Useful for when you need to answer questions about current events, real-time info, or live web data."
)

# --- 3. Long-Term Memory: Save Tool ---
@tool
def remember_fact(fact: str) -> str:
    """Useful to save important information, user preferences, or facts permanently into vector memory."""
    try:
        add_to_memory(text=fact, metadata={"source": "user_chat_memory"})
        return f"Successfully remembered: '{fact}'"
    except Exception as e:
        return f"Failed to save memory: {str(e)}"

# --- 4. Long-Term Memory: Recall Tool ---
@tool
def recall_fact(query: str) -> str:
    """Useful to search for past facts, user preferences, or saved memories in vector database."""
    try:
        results = search_memory(query)
        if results:
            return f"Found relevant memories: {', '.join(results)}"
        return "No relevant memories found."
    except Exception as e:
        return f"Failed to search memory: {str(e)}"

# --- AGENT TOOLS LIST ---
# Agent in sabhi tools ka use karke decisions lega
tools = [get_weather, web_search_tool, remember_fact, recall_fact]
