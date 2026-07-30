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

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)
# 2. Agent banate waqt usko memory (checkpointer) assign kar dein
agent_executor = create_react_agent(llm, tools, checkpointer=memory)