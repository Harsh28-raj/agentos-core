import asyncio
import os
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

@tool
def dummy_tool(arg: str):
    """Dummy tool"""
    return f"Dummy result for {arg}"

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

sub_agent = create_react_agent(llm, tools=[dummy_tool])
# we can set interrupt_before on it? No, create_react_agent accepts it.
sub_agent = create_react_agent(llm, tools=[dummy_tool], interrupt_before=["tools"])

class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage], add_messages]
    next: str

def supervisor_node(state: AgentState):
    return {"next": "sub_agent"}

builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("sub_agent", sub_agent)
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "sub_agent")
builder.add_edge("sub_agent", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

async def test():
    config = {"configurable": {"thread_id": "test_2"}}
    print("Invoking parent graph...")
    res = await graph.ainvoke({"messages": [HumanMessage(content="Use the dummy tool with arg 'world'")]}, config=config)
    print("Parent invoked.")
    
    state = graph.get_state(config, subgraphs=True)
    print("Is paused?", len(state.next) > 0)
    print("Next:", state.next)
    
    print("Tasks:", state.tasks)
    
    # If paused, let's resume
    if state.next:
        print("Resuming...")
        res = await graph.ainvoke(None, config=config)
        print("Final result:", res["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(test())
