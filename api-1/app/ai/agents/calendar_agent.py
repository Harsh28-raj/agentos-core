import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools.calendar_tools import check_calendar_availability, create_calendar_event

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), 
    model="llama-3.1-8b-instant",
    max_retries=3,
    temperature=0
)

system_prompt = SystemMessage(content="""You are the Calendar Agent.
Your role is to check the user's availability and schedule events on their Google Calendar.

CALENDAR EXECUTION POLICY & SAFEGUARDS:
1. Always ask the user for confirmation via the supervisor before scheduling an event if details are unclear.
2. The supervisor will handle human-in-the-loop pauses. When you are re-invoked with user confirmation, you may execute `create_calendar_event`.
3. Provide clear and concise summaries of calendar events.
""")

calendar_agent = create_react_agent(
    llm,
    tools=[check_calendar_availability, create_calendar_event],
    prompt=system_prompt,
    name="calendar_agent",
    interrupt_before=["tools"]
)
