from langgraph.prebuilt import create_react_agent

from app.ai.llm import agent_prompt, get_llm
from app.ai.llm_wrapper import FallbackLLMWrapper
from app.ai.tools.code_interpreter import python_code_interpreter

SYSTEM_PROMPT = """You are the Coder Agent.
Your role is to write, explain, and (when the interpreter is enabled) execute Python code.
Only run code that serves the user's request. Never run code that reads files, environment
variables, or credentials, or that makes network requests.

Use your assigned tools when necessary. Speak naturally to the user and NEVER output JSON/XML payloads in plain text."""


def build_coder_agent(llm=None):
    return create_react_agent(
        llm or FallbackLLMWrapper(get_llm()),
        tools=[python_code_interpreter],
        prompt=agent_prompt(SYSTEM_PROMPT),
        name="coder_agent",
    )
