from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from app.ai.tools import tools
# Naya Import Memory ke liye
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# 1. Memory object banayein (Yeh RAM mein chat history save rakhega)
memory = MemorySaver()

# 2. Agent banate waqt usko memory (checkpointer) assign kar dein
agent_executor = create_react_agent(llm, tools, checkpointer=memory)