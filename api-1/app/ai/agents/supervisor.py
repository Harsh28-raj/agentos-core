import os
from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel

# Checkpointer
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
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()

# Import sub-agents
from app.ai.agents.research_agent import research_agent
from app.ai.agents.coder_agent import coder_agent
from app.ai.agents.vision_agent import vision_agent
from app.ai.agents.gmail_agent import gmail_agent
from app.ai.agents.calendar_agent import calendar_agent

# The State for the Supervisor Graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str

# Define Routing choices
members = ["research_agent", "coder_agent", "vision_agent", "gmail_agent", "calendar_agent"]
options = ["FINISH"] + members

class RouteResponse(BaseModel):
    next: Literal["FINISH", "research_agent", "coder_agent", "vision_agent", "gmail_agent", "calendar_agent"]

# Supervisor LLM setup
llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=0, temperature=0.0, timeout=60.0)

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the following workers: {members}. "
    "Given the conversation history, respond with the worker to act next. "
    "Each worker will perform a task and respond with their results. "
    "CRITICAL RULE: If a worker has just responded, and their response answers the user, provides information, or asks the user a question, you MUST respond with FINISH so the user can see it! "
    "Do NOT route back to the same worker if they just spoke. ALWAYS route to FINISH when a worker replies to the user. "
    "If the user wants to search the web or remember something, route to research_agent. "
    "If the user wants to write or run code, route to coder_agent. "
    "If the user wants to analyze an image, route to vision_agent. "
    "If the user wants to read or send emails, route to gmail_agent. "
    "If the user wants to check their schedule or create a calendar event, route to calendar_agent. "
    'You must output your response in valid JSON format ONLY. Your JSON MUST contain exactly one key named "next", and its value must be the worker to act next or "FINISH". Example: {{"next": "FINISH"}}'
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Given the conversation above, who should act next? Or should we FINISH? Select one of: {options}"),
]).partial(options=str(options), members=", ".join(members))

def supervisor_node(state: AgentState) -> dict:
    # Force json_mode to bypass Groq's buggy native XML tool parser
    supervisor_chain = prompt | llm.with_structured_output(RouteResponse, method="json_mode")
    res = supervisor_chain.invoke(state)
    print(f"=== SUPERVISOR ROUTING TO: {res.next} ===")
    return {"next": res.next}

# Helper to invoke a sub-graph node
def _invoke_agent(agent, state: AgentState, config: dict = None) -> dict:
    print(f"=== INVOKING AGENT: {agent.name} ===")
    # Pass user_id in config so tools like calendar/gmail can authenticate
    invoke_config = config or {}
    res = agent.invoke(state, config=invoke_config)
    last_msg = res["messages"][-1]
    
    msg_content = last_msg.content if getattr(last_msg, "content", None) else str(last_msg)
    print(f"=== AGENT {agent.name} RETURNED: {msg_content[:100]}... ===")
    
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content=msg_content, name=agent.name)]}
    
def research_node(state: AgentState, config: dict = None):
    return _invoke_agent(research_agent, state, config)

def coder_node(state: AgentState, config: dict = None):
    return _invoke_agent(coder_agent, state, config)

def vision_node(state: AgentState, config: dict = None):
    return _invoke_agent(vision_agent, state, config)

def gmail_node(state: AgentState, config: dict = None):
    return _invoke_agent(gmail_agent, state, config)

def calendar_node(state: AgentState, config: dict = None):
    return _invoke_agent(calendar_agent, state, config)

# Build the Graph
builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("research_agent", research_node)
builder.add_node("coder_agent", coder_node)
builder.add_node("vision_agent", vision_node)
builder.add_node("gmail_agent", gmail_node)
builder.add_node("calendar_agent", calendar_node)

for member in members:
    builder.add_edge(member, END)

builder.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {
        "research_agent": "research_agent",
        "coder_agent": "coder_agent",
        "vision_agent": "vision_agent",
        "gmail_agent": "gmail_agent",
        "calendar_agent": "calendar_agent",
        "FINISH": END
    }
)

builder.add_edge(START, "supervisor")

supervisor_graph = builder.compile(
    checkpointer=memory
)
