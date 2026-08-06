import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from app.ai.llm_wrapper import FallbackLLMWrapper

from app.ai.tools.calendar_tools import check_calendar_availability, create_calendar_event

llm = FallbackLLMWrapper(ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=5, temperature=0.0, timeout=60.0))

system_prompt = SystemMessage(content="""You are the Calendar Agent.
Your role is to manage calendar events, check schedules, and create new events.

CALENDAR EXECUTION POLICY & SAFEGUARDS:
1. Present the event details to the user in chat.
2. The supervisor will handle human-in-the-loop pauses before event creation.

CRITICAL: You have access to external tools. You MUST invoke them using the internal tool calling API (tool_calls). NEVER write tool payloads, JSON structures, or XML (like <function...>) in your plain text response. If you are calling a tool, your text content should be empty or just a natural language transition, while the tool is invoked natively.
""")

calendar_agent = create_react_agent(
    llm,
    tools=[check_calendar_availability, create_calendar_event],
    prompt=system_prompt,
    name="calendar_agent"
)
