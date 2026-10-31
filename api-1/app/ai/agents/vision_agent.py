from langgraph.prebuilt import create_react_agent

from app.ai.llm import agent_prompt, get_llm
from app.ai.llm_wrapper import FallbackLLMWrapper
from app.ai.tools.vision import analyze_image

SYSTEM_PROMPT = """You are the Vision Agent.
Your role is to analyze images the user has uploaded. Call analyze_image with the stored file
name from the upload. If you do not know the file name, call it with any name: the error lists
the user's uploaded images.

Use your assigned tools when necessary. Speak naturally to the user and NEVER output JSON/XML payloads in plain text."""


def build_vision_agent(llm=None):
    return create_react_agent(
        llm or FallbackLLMWrapper(get_llm()),
        tools=[analyze_image],
        prompt=agent_prompt(SYSTEM_PROMPT),
        name="vision_agent",
    )
