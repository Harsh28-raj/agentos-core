import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools.vision import analyze_image

llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=0, temperature=0.2, timeout=60.0)

system_prompt = SystemMessage(content="""You are the Vision Agent.
Your role is to analyze images, perform OCR, and extract insights from visual data.
Be highly descriptive and accurate.

You must output tool calls in valid JSON structure only. Do not wrap function calls in raw XML tags like <function>.
""")

vision_agent = create_react_agent(
    llm,
    tools=[analyze_image],
    prompt=system_prompt,
    name="vision_agent"
)
