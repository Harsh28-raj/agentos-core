import asyncio
import os
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()

@tool
def dummy_tool(arg: str):
    """Dummy tool"""
    return "Dummy result"

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

sub_agent = create_react_agent(llm, tools=[dummy_tool], interrupt_before=["tools"])

def supervisor_node(state):
    return {"next": "sub_agent"}

builder = StateGraph(dict)
builder.add_node("supervisor", supervisor_node)
builder.add_node("sub_agent", sub_agent)
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "sub_agent")
builder.add_edge("sub_agent", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

async def test():
    config = {"configurable": {"thread_id": "test_1"}}
    res = await graph.ainvoke({"messages": [HumanMessage(content="Use the dummy tool with arg 'hello'")]}, config=config)
    print("Graph output:", res)
    state = graph.get_state(config)
    print("Next:", state.next)
    print("Last Message:", state.values["messages"][-1])

if __name__ == "__main__":
    asyncio.run(test())
