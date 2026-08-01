import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools import get_weather, web_search_tool, remember_fact, recall_fact

llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2, timeout=60.0)

system_prompt = SystemMessage(content="""You are the Research Agent.
Your role is to gather information, search the live web, and store/recall facts from long-term memory.
Always provide clear and accurate summaries of your findings.

You must output tool calls in valid JSON structure only. Do not wrap function calls in raw XML tags like <function>.
""")

research_agent = create_react_agent(
    llm,
    tools=[get_weather, web_search_tool, remember_fact, recall_fact],
    prompt=system_prompt,
    name="research_agent"
)
