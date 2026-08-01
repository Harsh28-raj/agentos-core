import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools.vision import analyze_image

llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), 
    model="llama-3.1-8b-instant",
    max_retries=3,
    request_timeout=30.0,
    temperature=0
)

system_prompt = SystemMessage(content="""You are the Vision Agent.
Your role is to analyze images, perform OCR, and extract insights from visual data.
Be highly descriptive and accurate.
""")

vision_agent = create_react_agent(
    llm,
    tools=[analyze_image],
    prompt=system_prompt,
    name="vision_agent"
)
