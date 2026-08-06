import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from app.ai.llm_wrapper import FallbackLLMWrapper

from app.ai.tools.vision import analyze_image

llm = FallbackLLMWrapper(ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=5, temperature=0.0, timeout=60.0))

system_prompt = SystemMessage(content="""You are the Vision Agent.
Your role is to analyze images when provided.

You are a helpful assistant. Use your assigned tools when necessary. Speak naturally to the user and NEVER output JSON/XML payloads in plain text.
""")

vision_agent = create_react_agent(
    llm,
    tools=[analyze_image],
    prompt=system_prompt,
    name="vision_agent"
)
