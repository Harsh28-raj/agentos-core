import asyncio
import os
from langchain_core.messages import HumanMessage
from app.ai.agents.supervisor import supervisor_graph

async def main():
    config = {"configurable": {"thread_id": "test_thread", "user_id": "default_user"}}
    messages = [HumanMessage(content="Check my Google Calendar...")]
    
    print("Invoking graph...")
    response = supervisor_graph.invoke({"messages": messages}, config=config, recursion_limit=10)
    print("Graph response:", response)
    print("Final reply:", response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
