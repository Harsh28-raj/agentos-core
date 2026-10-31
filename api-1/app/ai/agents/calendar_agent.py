from langgraph.prebuilt import create_react_agent

from app.ai.llm import agent_prompt, get_llm
from app.ai.llm_wrapper import FallbackLLMWrapper
from app.ai.tools.calendar_tools import check_calendar_availability, create_calendar_event

SYSTEM_PROMPT = """You are the Calendar Agent.
Your role is to check the user's schedule and create new events.

CALENDAR EXECUTION POLICY & SAFEGUARDS:
1. Resolve relative dates ("tomorrow at 4pm") using the current date given below.
2. When asked to schedule something, check availability first if the user asked "am I free".
3. `create_calendar_event` always pauses for an explicit human approval before the event is created.
4. Always pass timestamps in ISO 8601 with an explicit offset.

If Google is not connected, tell the user to click "Connect Google" in the dashboard.
CRITICAL: Invoke tools through the native tool-calling API. NEVER write tool payloads, JSON, or XML in your plain text response."""


def build_calendar_agent(llm=None):
    return create_react_agent(
        llm or FallbackLLMWrapper(get_llm()),
        tools=[check_calendar_availability, create_calendar_event],
        prompt=agent_prompt(SYSTEM_PROMPT),
        name="calendar_agent",
    )
