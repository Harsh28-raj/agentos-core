import os
import io
import json
import traceback
import asyncio
import PyPDF2
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import Literal, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain & Groq Imports
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Vector DB & AI Agent Imports
from app.db.vector_store import add_to_memory
from app.ai.agents.supervisor import supervisor_graph as agent_executor, redis_conn, memory
from app.db.postgres import init_db, log_episodic_event
from app.routers.logs import router as logs_router
from app.routers.auth import router as auth_router
import base64

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Redis Search Indices are created
    if hasattr(memory, "setup"):
        memory.setup()
    await init_db()
    yield

app = FastAPI(
    title="AgentOS Backend Engine",
    description="The Personal AI Operating System Backend Engine with Multi-Agent Supervisor",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Frontend Development
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs_router)
app.include_router(auth_router)

# Initialize Groq LLM
llm = None
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)
except Exception as e:
    print(f"⚠️ Error initializing Groq LLM: {e}")

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_user"
    user_id: str = "default_user"

class ApproveRequest(BaseModel):
    thread_id: str = "default_user"
    user_id: str = "default_user"
    action: Literal["CONFIRM", "REJECT", "EDIT"]
    updated_args: Optional[Dict[str, Any]] = None
    feedback_message: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "AgentOS Backend is running smoothly! 🚀"}

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [HumanMessage(content=request.message)]
        config = {"configurable": {"thread_id": request.user_id, "user_id": request.user_id}}
        
        # Check if resuming
        current_state = agent_executor.get_state(config)
        is_resuming = len(current_state.next) > 0
        payload = None if is_resuming else {"messages": messages}
        
        
        # Keep only the last 4 messages in history safely
        history = current_state.values.get('messages', [])
        if isinstance(history, list) and len(history) > 4:
            history = history[-4:]
            # We skip aupdate_state here as it causes crashes with RemoveMessage in some versions
            # Let LangGraph handle memory naturally or just trim local payload if necessary.
        
        # Agent Execution with recursion guardrail and timeout
        response = await asyncio.wait_for(agent_executor.ainvoke(payload, config=config, recursion_limit=5), timeout=20.0)
        
        # Check if paused
        final_state = agent_executor.get_state(config)
        if final_state.next:
            return {"reply": f"⏸️ Execution paused. Awaiting human approval to proceed with {final_state.next[0]}."}
            
        final_reply = response["messages"][-1].content
        return {"reply": final_reply}
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Error in /api/v1/chat: {str(e)}")
        logging.error(traceback.format_exc())
        print(traceback.format_exc())
        return {"reply": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"}

@app.post("/api/v1/chat/approve")
async def approve_hitl(request: ApproveRequest):
    """
    Endpoint to confirm, reject, or edit a pending HITL paused action.
    """
    try:
        config = {"configurable": {"thread_id": request.user_id, "user_id": request.user_id}}
        
        # We need to get the subgraph state where the actual tool call is paused
        state = agent_executor.get_state(config, subgraphs=True)
        
        # Check if parent or any subgraph is paused
        parent_state = agent_executor.get_state(config)
        if not parent_state.next and not state.tasks:
            return {"status": "error", "message": "No pending execution paused."}
            
        # Find the paused subgraph task if it's paused in a subgraph
        active_subgraph_task = None
        if state.tasks:
            active_subgraph_task = state.tasks[0]
            
        # Extract pending tool call from subgraph state if available
        original_args = None
        pending_msg = None
        tool_call_id = None
        subgraph_config = None
        
        if active_subgraph_task and active_subgraph_task.state and active_subgraph_task.state.values.get("messages"):
            subgraph_config = active_subgraph_task.state.config
            messages = active_subgraph_task.state.values["messages"]
            if messages:
                pending_msg = messages[-1]
                if getattr(pending_msg, "tool_calls", None) and len(pending_msg.tool_calls) > 0:
                    original_args = pending_msg.tool_calls[0].get("args")
                    tool_call_id = pending_msg.tool_calls[0].get("id")

        if request.action == "EDIT":
            if not request.updated_args:
                return {"status": "error", "message": "updated_args is required for EDIT action"}
            if not pending_msg or not subgraph_config:
                return {"status": "error", "message": "Could not locate a pending tool call to edit."}
                
            # Clone the message and override the args
            new_tool_calls = list(pending_msg.tool_calls)
            new_tool_calls[0]["args"] = request.updated_args
            
            # Create a new AIMessage with the updated tool calls
            from langchain_core.messages import AIMessage
            modified_msg = AIMessage(
                content=pending_msg.content,
                tool_calls=new_tool_calls,
                id=pending_msg.id  # Must use the same ID to overwrite it in LangGraph state
            )
            
            # Update the subgraph state
            agent_executor.update_state(subgraph_config, {"messages": [modified_msg]})
            
            # Log the event
            await log_episodic_event(
                thread_id=request.user_id,
                run_id=tool_call_id or "edit",
                tool_name="HITL_EDIT",
                action_taken="EDIT",
                original_args=original_args,
                modified_args=request.updated_args,
                human_feedback=request.feedback_message,
                status="completed"
            )

            # Resume
            await agent_executor.ainvoke(None, config=config, recursion_limit=5)
            return {"status": "resumed", "message": "Action edited and resumed."}
            
        elif request.action == "CONFIRM":
            # Log the event
            await log_episodic_event(
                thread_id=request.user_id,
                run_id=tool_call_id or "confirm",
                tool_name="HITL_CONFIRM",
                action_taken="CONFIRM",
                original_args=original_args,
                status="completed"
            )
            await agent_executor.ainvoke(None, config=config, recursion_limit=5)
            return {"status": "resumed", "message": "Action approved and resumed."}
            
        else:
            # Inject a rejection message and resume
            agent_executor.update_state(config, {"messages": [HumanMessage(content="The user REJECTED the action. Do not proceed.")]})
            
            # Log the event
            await log_episodic_event(
                thread_id=request.user_id,
                run_id=tool_call_id or "reject",
                tool_name="HITL_REJECT",
                action_taken="REJECT",
                original_args=original_args,
                status="completed"
            )
            
            await agent_executor.ainvoke(None, config=config, recursion_limit=5)
            return {"status": "rejected", "message": "Action rejected and graph updated."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streams Agent execution events (Thought, Routing, Tool Start/End, Tokens)
    using LangGraph's astream_events engine over Server-Sent Events (SSE).
    """
    async def event_generator():
        try:
            thread_id = request.thread_id if request.thread_id else "default_user"
            user_id = request.user_id if request.user_id else "default_user"
            messages = [HumanMessage(content=request.message)]
            config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
            
            # 1. State check to see if we are resuming from a HITL pause
            current_state = agent_executor.get_state(config)
            is_resuming = len(current_state.next) > 0
            
            payload_input = None if is_resuming else {"messages": messages}

            # Emit Initial Thinking State
            init_event = json.dumps({
                "type": "thinking",
                "content": "Analyzing query and planning multi-agent steps..."
            })
            yield f"data: {init_event}\n\n"

            total_input_tokens = 0
            total_output_tokens = 0

            # 2. Consume LangGraph v2 Event Stream
            async for event in agent_executor.astream_events(
                payload_input,
                config=config,
                version="v2",
                recursion_limit=5
            ):
                try:
                    event_type = event.get("event")
                    node_name = event.get("name", "")
                    
                    if event_type == "on_chain_start" and node_name in ["research_agent", "coder_agent", "vision_agent", "gmail_agent"]:
                        payload = json.dumps({
                            "type": "route",
                            "content": f"Routing task to {node_name.replace('_', ' ').title()}"
                        })
                        yield f"data: {payload}\n\n"
                    
                    elif event_type == "on_tool_start":
                        tool_name = event.get("name", "unknown_tool")
                        tool_input = event.get("data", {}).get("input", {})
                        payload = json.dumps({
                            "type": "tool_start",
                            "tool": tool_name,
                            "content": f"Executing tool: {tool_name}",
                            "input": tool_input
                        })
                        asyncio.create_task(log_episodic_event(
                            thread_id=thread_id,
                            run_id=event.get("run_id", "unknown"),
                            status="started",
                            tool_name=tool_name,
                            tool_input=tool_input
                        ))
                        yield f"data: {payload}\n\n"
                        
                    elif event_type == "on_tool_end":
                        tool_name = event.get("name", "unknown_tool")
                        tool_output = str(event.get("data", {}).get("output", ""))
                        payload = json.dumps({
                            "type": "tool_end",
                            "tool": tool_name,
                            "content": f"Finished executing {tool_name}",
                            "output": tool_output[:150]
                        })
                        asyncio.create_task(log_episodic_event(
                            thread_id=thread_id,
                            run_id=event.get("run_id", "unknown"),
                            status="completed",
                            tool_name=tool_name,
                            tool_output={"output": tool_output}
                        ))
                        yield f"data: {payload}\n\n"
                        
                    elif event_type == "on_chat_model_end":
                        output = event.get("data", {}).get("output", {})
                        content = getattr(output, "content", "")
                        
                        # Token tracking logic
                        usage = getattr(output, "usage_metadata", {})
                        if usage:
                            total_input_tokens += usage.get("input_tokens", 0)
                            total_output_tokens += usage.get("output_tokens", 0)
                            
                        if content:
                            asyncio.create_task(log_episodic_event(
                                thread_id=thread_id,
                                run_id=event.get("run_id", "unknown"),
                                status="completed",
                                reasoning_steps=[{"content": content}]
                            ))
                            
                    elif event_type == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            payload = json.dumps({
                                "type": "token",
                                "content": chunk.content
                            })
                            yield f"data: {payload}\n\n"
                except Exception as inner_e:
                    error_payload = json.dumps({"type": "error", "content": str(inner_e)})
                    yield f"data: {error_payload}\n\n"

            # Check if graph paused due to HITL
            final_state = agent_executor.get_state(config, subgraphs=True)
            parent_state = agent_executor.get_state(config)
            
            is_paused = False
            paused_agent = None
            pending_tool = None
            pending_args = None
            
            if parent_state.next:
                is_paused = True
                paused_agent = str(parent_state.next)
            elif final_state.tasks:
                is_paused = True
                subgraph_task = final_state.tasks[0]
                paused_agent = subgraph_task.name
                
                # Extract pending args
                if subgraph_task.state and subgraph_task.state.values.get("messages"):
                    msgs = subgraph_task.state.values["messages"]
                    if msgs and getattr(msgs[-1], "tool_calls", None) and len(msgs[-1].tool_calls) > 0:
                        pending_tool = msgs[-1].tool_calls[0].get("name")
                        pending_args = msgs[-1].tool_calls[0].get("args")

            if is_paused:
                hitl_payload = json.dumps({
                    "type": "hitl_pause",
                    "content": f"Execution paused. Awaiting human approval for {paused_agent}.",
                    "agent": paused_agent,
                    "tool": pending_tool,
                    "pending_args": pending_args
                })
                yield f"data: {hitl_payload}\n\n"
            else:
                done_payload = json.dumps({
                    "type": "done",
                    "tokens": {
                        "input": total_input_tokens,
                        "output": total_output_tokens,
                        "total": total_input_tokens + total_output_tokens
                    }
                })
                yield f"data: {done_payload}\n\n"
                
        except Exception as e:
            import logging
            import traceback
            logging.error(f"Error in /api/v1/chat/stream: {str(e)}")
            logging.error(traceback.format_exc())
            print(traceback.format_exc())
            error_payload = json.dumps({"type": "error", "content": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/v1/chat/history/{thread_id}")
def get_chat_history(thread_id: str):
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent_executor.get_state(config)
        
        if not state or not getattr(state, "values", None):
            return {"history": []}
        values = state.values
        messages = values.get("messages") or []
        
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                role_val = msg.get("role") or msg.get("type", "user")
                content_val = msg.get("content", "")
            else:
                role_val = getattr(msg, "type", "user")
                content_val = getattr(msg, "content", "")
            role = "user" if str(role_val).lower() in ["human", "user"] else "assistant"
            if content_val:
                formatted_messages.append({"role": role, "content": str(content_val)})
        return {"history": formatted_messages}
    except Exception as e:
        print("History Fetch Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/chat/history/{thread_id}")
async def delete_chat_history(thread_id: str):
    try:
        if redis_conn is None:
            return {"status": "success", "message": f"Simulated delete for thread {thread_id} (MemorySaver active)"}
            
        cursor = 0
        keys_deleted = 0
        while True:
            cursor, keys = redis_conn.scan(cursor=cursor, match=f"*{thread_id}*")
            if keys:
                redis_conn.delete(*keys)
                keys_deleted += len(keys)
            if cursor == 0:
                break
                
        return {"status": "success", "message": f"Deleted {keys_deleted} keys for thread {thread_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        extracted_text = ""
        
        if file.filename.lower().endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            base64_image = base64.b64encode(file_content).decode('utf-8')
            mime_type = file.content_type or "image/jpeg"
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable is missing.")

            vision_llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)
            msg = vision_llm.invoke(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract and summarize the text and visual content of this image."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                        ]
                    }
                ]
            )
            extracted_text = msg.content
        else:
            raise HTTPException(status_code=400, detail="Only PDF and Image files (PNG, JPG, WEBP) are supported.")
            
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text/content found in the file.")
            
        add_to_memory(text=extracted_text, metadata={"source": file.filename})
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' processed and saved to memory!",
            "content_length": len(extracted_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)