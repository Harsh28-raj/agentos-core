import os
import io
import json
import asyncio
import PyPDF2
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain & Groq Imports
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Vector DB & AI Agent Imports
from app.db.vector_store import add_to_memory
from app.ai.agent import agent_executor

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AgentOS Backend Engine",
    description="The Personal AI Operating System Backend Engine",
    version="1.0.0"
)

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
    user_id: str = "default_user"


# --- HEALTH CHECK ---
@app.get("/")
async def root():
    return {"status": "AgentOS Backend is running smoothly! 🚀"}


# --- STANDARD SYNCHRONOUS CHAT ENDPOINT ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [HumanMessage(content=request.message)]
        config = {"configurable": {"thread_id": request.user_id}}
        
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
            user_id = request.user_id if request.user_id else "default_user"
            messages = [HumanMessage(content=request.message)]
            config = {"configurable": {"thread_id": user_id}}

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
                event_type = event.get("event")

                # --- EVENT A: TOOL STARTED ---
                if event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    tool_input = event.get("data", {}).get("input", {})
                    
                    payload = json.dumps({
                        "type": "tool_start",
                        "tool": tool_name,
                        "content": f"Executing tool: {tool_name}",
                        "input": tool_input
                    })
                    yield f"data: {payload}\n\n"

                # --- EVENT B: TOOL COMPLETED ---
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown_tool")
                    tool_output = str(event.get("data", {}).get("output", ""))
                    
                    payload = json.dumps({
                        "type": "tool_end",
                        "tool": tool_name,
                        "content": f"Finished executing {tool_name}",
                        "output": tool_output[:150]  # First 150 chars preview
                    })
                    yield f"data: {payload}\n\n"

                # --- EVENT C: LIVE RESPONSE TOKENS ---
                elif event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload = json.dumps({
                            "type": "token",
                            "content": chunk.content
                        })
                        yield f"data: {payload}\n\n"

            # --- EVENT D: STREAM COMPLETED ---
            done_payload = json.dumps({"type": "done"})
            yield f"data: {done_payload}\n\n"

        except Exception as e:
            error_payload = json.dumps({
                "type": "error", 
                "content": str(e)
            })
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- DOCUMENT UPLOAD ENDPOINT ---
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")
        
        file_content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"
            
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the PDF.")
            
        # Store in ChromaDB vector memory
        add_to_memory(text=extracted_text, metadata={"source": file.filename})
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' processed and saved to memory!",
            "pages_read": len(pdf_reader.pages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- RENDER PORT RUNNER ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
