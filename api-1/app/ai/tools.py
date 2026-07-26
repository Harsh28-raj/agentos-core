from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import os
from dotenv import load_dotenv

# Database functions ko import karein
from app.db.vector_store import add_to_memory, search_memory

# Env variables load karna
load_dotenv()

# Safety check for Tavily API Key
tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    print("⚠️ WARNING: TAVILY_API_KEY is missing in .env file!")

# --- 1. Weather Tool (Dummy) ---
@tool
def get_weather(location: str) -> str:
    """Gets the current weather for a given location."""
    return f"The weather in {location} is 28°C and sunny."

# --- 2. Live Web Search Tool (Tavily) ---
web_search_tool = TavilySearch(
    max_results=3,
    description="Useful for when you need to answer questions about current events, real-time info, or anything you don't know."
)

# --- 3. Long-Term Memory: Save Tool ---
@tool
def remember_fact(fact: str) -> str:
    """Useful to save important information, user preferences, or facts permanently."""
    return add_to_memory(fact)

# --- 4. Long-Term Memory: Recall Tool ---
@tool
def recall_fact(query: str) -> str:
    """Useful to search for past facts, user preferences, or saved memories."""
    results = search_memory(query)
    if results:
        return f"Found memories: {', '.join(results)}"
    return "No relevant memories found."

# --- AGENT TOOLS LIST ---
# Agent in sabhi tools ka use karke khud decisons lega
tools = [get_weather, web_search_tool, remember_fact, recall_fact]