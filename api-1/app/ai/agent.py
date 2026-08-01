import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from app.ai.tools import tools
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if redis_url:
    import redis
    from langgraph.checkpoint.redis import RedisSaver
    redis_pool = redis.ConnectionPool.from_url(redis_url)
    redis_conn = redis.Redis(connection_pool=redis_pool)
    memory = RedisSaver(redis_client=redis_conn)
else:
    redis_conn = None
    memory = MemorySaver()

llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), 
    model="llama-3.1-8b-instant",
    max_retries=2, temperature=0.2,
    temperature=0
)
SYSTEM_PROMPT = """You are a helpful assistant.

EMAIL EXECUTION POLICY & SAFEGUARDS:
1. NEVER call `send_email` directly on the first user request. Always use `draft_email` first to create a draft.
2. Present the drafted email to the user in chat displaying:
   - Recipient Address
   - Subject Line
   - Body Preview
3. Ask the user for explicit confirmation before triggering `send_email`.

4. CONFIRMATION DETECTION & MATCHING RULES:
   - VALID CONFIRMATION PHRASES: Trigger `send_email` ONLY IF the user's explicit authorization response contains phrases like:
     ["haan", "ok bhej do", "send it", "looks good", "confirm", "go ahead", "yes send", "proceed"]
   
   - AMBIGUOUS OR CONDITIONAL RESPONSES: If the user gives a vague or uncertain reply such as:
     ["maybe", "shayad theek hai", "dekh lo", "wait", "let me think", "edit this"]
     DO NOT execute `send_email`. Ask for explicit clarification instead: "Kripya 'Confirm' ya 'Haan bhej do' bol kar confirm karein."
"""

# 2. Agent banate waqt usko memory (checkpointer) assign kar dein
agent_executor = create_react_agent(llm, tools, checkpointer=memory, prompt=SYSTEM_PROMPT)