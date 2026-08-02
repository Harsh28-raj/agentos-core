import os
from datetime import datetime
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools.calendar_tools import check_calendar_availability, create_calendar_event

llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=0, temperature=0.0, timeout=60.0)

def get_calendar_system_prompt() -> SystemMessage:
    now = datetime.now()
    current_dt = now.strftime("%Y-%m-%dT%H:%M:%S")
    current_date_str = now.strftime("%A, %B %d, %Y %H:%M")
    return SystemMessage(content=f"""You are the Calendar Agent.
Your role is to check the user's availability and schedule events on their Google Calendar.

CURRENT DATE AND TIME: {current_date_str}
Use this to convert relative dates like "tomorrow", "next Monday", "in 2 hours" into exact ISO 8601 format: YYYY-MM-DDTHH:MM:SS

STRICT EXECUTION RULES:
1. ALWAYS call tools directly using native JSON tool parameters. NEVER emit raw XML like <function=...> or <tool_call>.
2. NEVER ask the user for confirmation before scheduling. Execute directly when you have enough information.
3. NEVER add human confirmation requests inside the function payload or as extra text.
4. If the user says "schedule a meeting tomorrow at 3pm for 1 hour", compute the ISO datetime and call create_calendar_event immediately.
5. Assume IST (UTC+5:30) unless the user specifies otherwise.
6. Default event duration is 1 hour if not specified.
7. Respond only with the tool result — do not add extra conversational text.

You must output tool calls in valid JSON structure only. Do NOT wrap function calls in raw XML tags.
""")

calendar_agent = create_react_agent(
    llm,
    tools=[check_calendar_availability, create_calendar_event],
    prompt=get_calendar_system_prompt(),
    name="calendar_agent"
    # interrupt_before=["tools"] is intentionally DISABLED for local dev
)
