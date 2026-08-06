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
    llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=5, temperature=0.0, timeout=60.0)
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
        session_id = f"agentos_new:{request.user_id}_{request.thread_id}"
        config = {"configurable": {"thread_id": session_id, "user_id": request.user_id}}
        
        # Check if a tool-level interrupt is pending (inside a tool via interrupt())
        current_state = agent_executor.get_state(config, subgraphs=True)
        current_state_parent = agent_executor.get_state(config)
        
        # A tool-level interrupt means tasks exist AND those tasks have .interrupts populated
        is_tool_interrupted = (
            bool(current_state.tasks) and 
            any(bool(t.interrupts) for t in current_state.tasks)
        )
        # A node-level pause means .next is set but NO tool-level interrupt
        is_node_paused = len(current_state_parent.next) > 0 and not is_tool_interrupted
        is_resuming = is_node_paused  # Only treat as resuming for node-level pauses
        
        # HITL Natural Language Resolution (only for node-level pauses)
        if is_resuming:
            msg_lower = request.message.strip().lower()
            affirmative_keywords = ["confirm", "approved", "yes", "proceed", "do it"]
            negative_keywords = ["reject", "cancel", "no", "stop", "abort"]
            
            if any(k in msg_lower for k in negative_keywords):
                agent_executor.update_state(config, {"messages": [HumanMessage(content="The user REJECTED the action. Do not proceed.")]})
            elif any(k in msg_lower for k in affirmative_keywords):
                pass # Proceed normally
            else:
                agent_executor.update_state(config, {"messages": [HumanMessage(content=request.message)]})
        
        # Handle tool-level interrupts (from interrupt() inside tools like create_calendar_event)
        if is_tool_interrupted:
            from langgraph.types import Command
            interrupt_data = current_state.tasks[0].interrupts[0].value if current_state.tasks[0].interrupts else {}
            msg_lower = request.message.strip().lower()
            
            affirmative_keywords = ["confirm", "approved", "yes", "proceed", "do it", "go ahead"]
            negative_keywords = ["reject", "cancel", "no", "stop", "abort", "deny"]
            
            if any(k in msg_lower for k in affirmative_keywords):
                # Resume the interrupted tool with CONFIRM
                print(f"[HITL] Resuming tool interrupt with CONFIRM")
                config["recursion_limit"] = 15
                response = await agent_executor.ainvoke(Command(resume="CONFIRM"), config=config)
                
                # Extract final response after tool execution completes
                if isinstance(response, dict) and "messages" in response and response["messages"]:
                    final_reply = response["messages"][-1].content
                else:
                    final_reply = "Action completed successfully."
                return {"reply": final_reply}
                
            elif any(k in msg_lower for k in negative_keywords):
                # Resume the interrupted tool with REJECT
                print(f"[HITL] Resuming tool interrupt with REJECT")
                config["recursion_limit"] = 15
                response = await agent_executor.ainvoke(Command(resume="REJECT"), config=config)
                
                if isinstance(response, dict) and "messages" in response and response["messages"]:
                    final_reply = response["messages"][-1].content
                else:
                    final_reply = "Action was cancelled."
                return {"reply": final_reply}
            else:
                # First time seeing this interrupt — show the approval prompt to the user
                return {
                    "reply": f"⏸️ Awaiting your approval before executing: **{interrupt_data.get('action', 'action')}**",
                    "hitl_interrupt": True,
                    "interrupt_data": interrupt_data
                }
                
        payload = None if is_resuming else {"messages": messages}
        
        # Safe History Slicing (DO NOT assign directly to memory.messages)
        if hasattr(memory, "chat_memory"):
            raw_msgs = memory.chat_memory.messages
        elif hasattr(memory, "messages"):
            raw_msgs = memory.messages
        else:
            raw_msgs = current_state.values.get('messages', [])
            
        trimmed_msgs = raw_msgs[-4:] if len(raw_msgs) > 4 else raw_msgs
        
        # In LangGraph v0.2.x, we must carefully update state to trim history without mutating frozen objects.
        # If removing messages causes crashes, we will just rely on the payload or let it grow if RemoveMessage fails.
        if len(raw_msgs) > 4:
            try:
                from langchain_core.messages import RemoveMessage
                msgs_to_remove = raw_msgs[:-4]
                remove_payload = {"messages": [RemoveMessage(id=m.id) for m in msgs_to_remove if hasattr(m, 'id') and m.id]}
                agent_executor.update_state(config, remove_payload)
            except Exception:
                pass
        
        # Ensure recursion_limit is inside config dictionary for LangGraph
        config["recursion_limit"] = 15
        
        # Agent Execution with recursion guardrail (No arbitrary asyncio timeout, let recursion_limit handle safety)
        response = await agent_executor.ainvoke(payload, config=config)

        
        # Check if paused after execution
        final_state_with_sub = agent_executor.get_state(config, subgraphs=True)
        final_state = agent_executor.get_state(config)
        
        # Only show pause if it's a tool-level interrupt (inside a tool)
        final_is_tool_interrupted = (
            bool(final_state_with_sub.tasks) and
            any(bool(t.interrupts) for t in final_state_with_sub.tasks)
        )
        if final_is_tool_interrupted:
            interrupt_data = final_state_with_sub.tasks[0].interrupts[0].value if final_state_with_sub.tasks[0].interrupts else {}
            return {
                "reply": f"⏸️ Awaiting your approval before executing: **{interrupt_data.get('action', 'action')}**",
                "hitl_interrupt": True,
                "interrupt_data": interrupt_data
            }
            
        # Safe Output Extraction
        if isinstance(response, dict):
            final_reply = response.get("output") or response.get("result")
            if not final_reply and "messages" in response and response["messages"]:
                final_reply = response["messages"][-1].content
            elif not final_reply:
                final_reply = str(response)
        else:
            final_reply = str(response)
            
        return {"reply": final_reply}
    except Exception as e:
        import traceback
        error_msg = str(e)
        print("CHAT ROUTER ERROR:", traceback.format_exc())
        
        if "Rate limit reached" in error_msg or "rate_limit_exceeded" in error_msg:
            return {"reply": "⚠️ Groq rate limit reached for this model. Please wait a moment and try again."}
        elif "tool call validation failed" in error_msg:
            return {"reply": "I got a bit confused while trying to use my tools. Could you please rephrase your request?"}
        elif "recursion" in error_msg.lower():
            return {"reply": "I tried to process your request but needed too many steps. Could you be more specific?"}
        
        return {"reply": f"PYTHON ERROR: {type(e).__name__} - {error_msg}"}
@app.post("/api/v1/chat/approve")
async def approve_hitl(request: ApproveRequest):
    """
    Endpoint to confirm, reject, or edit a pending HITL paused action.
    """
    try:
        session_id = f"agentos_new:{request.user_id}_{request.thread_id}"
        config = {"configurable": {"thread_id": session_id, "user_id": request.user_id}}
        
        state = agent_executor.get_state(config, subgraphs=True)
        parent_state = agent_executor.get_state(config)
        
        is_tool_interrupt = False
        if state.tasks and state.tasks[0].interrupts:
            is_tool_interrupt = True

        if not parent_state.next and not state.tasks:
            return {"status": "error", "message": "No pending execution paused."}
            
        active_subgraph_task = None
        if state.tasks:
            active_subgraph_task = state.tasks[0]
            
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

        if is_tool_interrupt:
            interrupt_payload = active_subgraph_task.interrupts[0].value
            if isinstance(interrupt_payload, dict):
                original_args = interrupt_payload

        from langgraph.types import Command
        
        if request.action == "EDIT":
            if not request.updated_args:
                return {"status": "error", "message": "updated_args is required for EDIT action"}
            
            if is_tool_interrupt:
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
                await agent_executor.ainvoke(Command(resume=f"EDIT:{request.updated_args}"), config=config, recursion_limit=5)
                return {"status": "resumed", "message": "Action edited and resumed."}
            else:
                if not pending_msg or not subgraph_config:
                    return {"status": "error", "message": "Could not locate a pending tool call to edit."}
                    
                new_tool_calls = list(pending_msg.tool_calls)
                new_tool_calls[0]["args"] = request.updated_args
                
                from langchain_core.messages import AIMessage
                modified_msg = AIMessage(
                    content=pending_msg.content,
                    tool_calls=new_tool_calls,
                    id=pending_msg.id
                )
                agent_executor.update_state(subgraph_config, {"messages": [modified_msg]})
                
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
                await agent_executor.ainvoke(None, config=config, recursion_limit=5)
                return {"status": "resumed", "message": "Action edited and resumed."}
            
        elif request.action == "CONFIRM":
            await log_episodic_event(
                thread_id=request.user_id,
                run_id=tool_call_id or "confirm",
                tool_name="HITL_CONFIRM",
                action_taken="CONFIRM",
                original_args=original_args,
                status="completed"
            )
            if is_tool_interrupt:
                await agent_executor.ainvoke(Command(resume="CONFIRM"), config=config, recursion_limit=5)
            else:
                await agent_executor.ainvoke(None, config=config, recursion_limit=5)
            return {"status": "resumed", "message": "Action approved and resumed."}
            
        else:
            if is_tool_interrupt:
                await log_episodic_event(
                    thread_id=request.user_id,
                    run_id=tool_call_id or "reject",
                    tool_name="HITL_REJECT",
                    action_taken="REJECT",
                    original_args=original_args,
                    status="completed"
                )
                await agent_executor.ainvoke(Command(resume="REJECT"), config=config, recursion_limit=5)
            else:
                agent_executor.update_state(config, {"messages": [HumanMessage(content="The user REJECTED the action. Do not proceed.")]})
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
            thread_id = request.thread_id if request.thread_id else "default_thread"
            user_id = request.user_id if request.user_id else "default_user"
            messages = [HumanMessage(content=request.message)]
            session_id = f"agentos_new:{user_id}_{thread_id}"
            config = {"configurable": {"thread_id": session_id, "user_id": user_id}}
            
            # 1. State check to see if we are resuming from a HITL pause
            current_state = agent_executor.get_state(config)
            
            # Keep only the last 4 messages in history safely
            history = current_state.values.get('messages', [])
            if isinstance(history, list) and len(history) > 4:
                try:
                    from langchain_core.messages import RemoveMessage
                    msgs_to_remove = history[:-4]
                    remove_payload = {"messages": [RemoveMessage(id=m.id) for m in msgs_to_remove if hasattr(m, 'id') and m.id]}
                    agent_executor.update_state(config, remove_payload)
                    current_state = agent_executor.get_state(config)
                except Exception as e:
                    import logging
                    logging.warning(f"Could not remove old messages: {e}")
                    
            is_resuming = len(current_state.next) > 0
            
            # HITL Natural Language Resolution for streaming
            if is_resuming:
                msg_lower = request.message.strip().lower()
                affirmative_keywords = ["confirm", "approved", "yes", "proceed", "do it"]
                negative_keywords = ["reject", "cancel", "no", "stop", "abort"]
                
                if any(k in msg_lower for k in negative_keywords):
                    agent_executor.update_state(config, {"messages": [HumanMessage(content="The user REJECTED the action. Do not proceed.")]})
                elif any(k in msg_lower for k in affirmative_keywords):
                    pass # Proceed normally
                else:
                    agent_executor.update_state(config, {"messages": [HumanMessage(content=request.message)]})
            
            payload_input = None if is_resuming else {"messages": messages}

            # Emit Initial Thinking State
            init_event = json.dumps({
                "type": "thinking",
                "content": "Analyzing query and planning multi-agent steps..."
            })
            yield f"data: {init_event}\n\n"

            total_input_tokens = 0
            total_output_tokens = 0

            config["recursion_limit"] = 15
            # 2. Consume LangGraph v2 Event Stream
            async for event in agent_executor.astream_events(
                payload_input,
                config=config,
                version="v2"
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
                
                if subgraph_task.interrupts:
                    interrupt_data = subgraph_task.interrupts[0].value
                    if isinstance(interrupt_data, dict):
                        pending_tool = interrupt_data.get("action", "unknown_action")
                        pending_args = interrupt_data
                elif subgraph_task.state and subgraph_task.state.values.get("messages"):
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
            error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/v1/chat/history/{thread_id}")
def get_chat_history(thread_id: str, user_id: str = "default_user"):
    try:
        session_id = f"agentos_new:{user_id}_{thread_id}"
        config = {"configurable": {"thread_id": session_id}}
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
async def delete_chat_history(thread_id: str, user_id: str = "default_user"):
    session_id = f"agentos_new:{user_id}_{thread_id}"
    try:
        if redis_conn is None:
            return {"status": "success", "message": f"Simulated delete for thread {thread_id} (MemorySaver active)"}
            
        cursor = 0
        keys_deleted = 0
        while True:
            cursor, keys = redis_conn.scan(cursor=cursor, match=f"*{session_id}*")
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

            vision_llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=5, temperature=0.0, timeout=60.0)
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