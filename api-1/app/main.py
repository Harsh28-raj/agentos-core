import os
import io
import asyncio
import PyPDF2
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
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
    title="AgentOS Backend",
    description="The Personal AI Operating System Backend",
    version="1.0.0"
)

# Initialize Groq LLM (Streaming endpoint ke liye)
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


# --- FEATURE 3 & 4: LANGGRAPH AGENT WITH MEMORY ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [HumanMessage(content=request.message)]
        
        # Config set karna: User ki memory track karne ke liye
        config = {"configurable": {"thread_id": request.user_id}}
        
        # Agent call
        response = agent_executor.invoke({"messages": messages}, config=config)
        
        final_reply = response["messages"][-1].content
        return {"reply": final_reply}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- FEATURE 2: STREAMING LLM CHAT ENDPOINT (SSE) ---
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM service is not initialized. Check API Key.")

    async def event_generator():
        try:
            messages = [HumanMessage(content=request.message)]
            
            # Chunk-by-chunk stream generate karna
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- FEATURE 6: PDF / FILE UPLOAD ENDPOINT ---
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
            
        # Memory mein store karna
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
