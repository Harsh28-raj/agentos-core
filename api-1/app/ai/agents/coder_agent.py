import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.ai.tools.code_interpreter import python_code_interpreter

llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)

system_prompt = SystemMessage(content="""You are the Coder Agent.
Your role is to write, debug, and execute Python code.

CRITICAL INSTRUCTIONS:
1. When invoking a tool, do NOT generate commentary, markdown code blocks, or text preambles before the tool call. Output ONLY the structured tool call.
2. If a user simply asks to "write a function" or generate code, provide the code directly in markdown format. DO NOT unnecessarily trigger `python_code_interpreter` unless the user explicitly requests code execution, running the script, or testing the output.
3. Provide clean code and clear explanations of the output.

You must output tool calls in valid JSON structure only. Do not wrap function calls in raw XML tags like <function>.
""")

coder_agent = create_react_agent(
    llm,
    tools=[python_code_interpreter],
    prompt=system_prompt,
    name="coder_agent"
)
