import os
import io
import json
import traceback
import asyncio
import PyPDF2
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain & Groq Imports
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Vector DB & AI Agent Imports
from app.db.vector_store import add_to_memory
from app.ai.agent import agent_executor, redis_conn, memory
from app.db.postgres import init_db, log_episodic_event
from app.routers.logs import router as logs_router
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
    description="The Personal AI Operating System Backend Engine",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(logs_router)

# Enable CORS for Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production mein exact frontend domain se replace kar sakte ho
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq LLM
llm = None
try:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0.7,
        max_tokens=1024
    )
except Exception as e:
    print(f"⚠️ Error initializing Groq LLM: {e}")


# Pydantic Model for incoming chat requests
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_user"


# --- HEALTH CHECK ---
@app.get("/")
async def root():
    return {"status": "AgentOS Backend is running smoothly! 🚀"}


# --- STANDARD SYNCHRONOUS CHAT ENDPOINT ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [HumanMessage(content=request.message)]
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Agent Execution
        response = agent_executor.invoke({"messages": messages}, config=config)
        
        final_reply = response["messages"][-1].content
        return {"reply": final_reply}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# FEATURE 2: EVENT-DRIVEN SSE STREAMING ENDPOINT (astream_events v2)
# =====================================================================
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streams Agent execution events (Thought, Tool Start/End, Tokens)
    using LangGraph's astream_events engine over Server-Sent Events (SSE).
    """
    async def event_generator():
        try:
            thread_id = request.thread_id if request.thread_id else "default_user"
            messages = [HumanMessage(content=request.message)]
            config = {"configurable": {"thread_id": thread_id}}

            # 1. Emit Initial Thinking State
            init_event = json.dumps({
                "type": "thought",
                "content": "Analyzing query and planning steps..."
            })
            yield f"data: {init_event}\n\n"

            # 2. Consume LangGraph v2 Event Stream
            async for event in agent_executor.astream_events(
                {"messages": messages},
                config=config,
                version="v2"
            ):
                try:
                    event_type = event.get("event")
                    if event_type == "on_tool_start":
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
                        content = ""
                        if hasattr(output, "content") and output.content:
                            content = output.content
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
                    else:
                        continue
                except Exception as inner_e:
                    error_payload = json.dumps({"type": "error", "content": str(inner_e)})
                    yield f"data: {error_payload}\n\n"

            # --- EVENT D: STREAM COMPLETED ---
            done_payload = json.dumps({"type": "done"})
            yield f"data: {done_payload}\n\n"
        except Exception as e:
            if str(e):
                error_payload = json.dumps({"type": "error", "content": str(e)})
                yield f"data: {error_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- HISTORY ENDPOINTS ---







@app.get("/api/chat/history/{thread_id}")
def get_chat_history(thread_id: str):
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent_executor.get_state(config)
        
        # Debug logs in terminal
        print("\n--- DEBUG CHAT HISTORY ---")
        print("Thread ID:", thread_id)
        print("State exists:", state is not None)
        if state and hasattr(state, "values"):
            print("State values keys:", list(state.values.keys()) if isinstance(state.values, dict) else "Not a dict")
            print("Raw state values:", state.values)
        print("---------------------------\n")
        
        if not state or not getattr(state, "values", None):
            return {"history": []}
        values = state.values
        messages = values.get("messages") or values.get("chat_history") or []
        
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                role_val = msg.get("role") or msg.get("type", "user")
                content_val = msg.get("content", "")
            else:
                role_val = getattr(msg, "type", "user")
                content_val = getattr(msg, "content", "")
            role = "user" if str(role_val).lower() in ["human", "user"] else "assistant"
            formatted_messages.append({"role": role, "content": str(content_val)})
        return {"history": formatted_messages}
    except Exception as e:
        print("History Fetch Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))





@app.delete("/api/chat/history/{thread_id}")
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


# --- DOCUMENT UPLOAD ENDPOINT ---
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        extracted_text = ""
        
        if file.filename.lower().endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            # Process image with Vision LLM
            base64_image = base64.b64encode(file_content).decode('utf-8')
            mime_type = file.content_type or "image/jpeg"
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable is missing.")

            vision_llm = ChatGroq(
                model="qwen/qwen3.6-27b", 
                max_tokens=500,
                api_key=groq_api_key
            )
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
            
        # Store in ChromaDB vector memory
        add_to_memory(text=extracted_text, metadata={"source": file.filename})
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' processed and saved to memory!",
            "content_length": len(extracted_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- RENDER PORT RUNNER ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)