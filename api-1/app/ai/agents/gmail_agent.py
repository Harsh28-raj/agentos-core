import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools.gmail import search_emails, read_email_content, draft_email, send_email

llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), 
    model="llama-3.1-8b-instant",
    max_retries=2, temperature=0.2
)

system_prompt = SystemMessage(content="""You are the Gmail Agent.
Your role is to search emails, read content, draft emails, and send emails when instructed.

EMAIL EXECUTION POLICY & SAFEGUARDS:
1. NEVER call `send_email` directly on the first user request. Always use `draft_email` first to create a draft.
2. Present the drafted email to the user in chat.
3. The supervisor will handle human-in-the-loop pauses. When you are re-invoked with user confirmation, you may execute `send_email`.
""")

gmail_agent = create_react_agent(
    llm,
    tools=[search_emails, read_email_content, draft_email, send_email],
    prompt=system_prompt,
    name="gmail_agent",
    interrupt_before=["tools"]
)
