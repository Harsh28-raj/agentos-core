from fastapi import FastAPI, HTTPException, File, UploadFile
import PyPDF2
import io
from app.db.vector_store import add_to_memory
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio

# LangChain & Groq Imports
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Import our LangGraph Agent
from app.ai.agent import agent_executor

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AgentOS Backend",
    description="The Personal AI Operating System Backend",
    version="1.0.0"
)

# Initialize Groq LLM (Sirf Streaming API ke liye abhi zaroorat hai)
try:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0.7,
        max_tokens=1024
    )
except Exception as e:
    print(f"Error initializing LLM: {e}")

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
        
        # Config set karna: Yeh agent ko batayega ki kis user ki memory load karni hai
        config = {"configurable": {"thread_id": request.user_id}}
        
        # Agent ko message aur config dono pass karein
        response = agent_executor.invoke({"messages": messages}, config=config)
        
        final_reply = response["messages"][-1].content
        
        return {"reply": final_reply}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- FEATURE 2: STREAMING LLM CHAT ENDPOINT (SSE) ---
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    async def event_generator():
        try:
            messages = [HumanMessage(content=request.message)]
            
            # LangChain ka astream use karke chunk by chunk data nikalna
            async for chunk in llm.astream(messages):
                if chunk.content:
                    # SSE format: "data: {text}\n\n"
                    yield f"data: {chunk.content}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    # StreamingResponse frontend ko connection open rakhne deta hai
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- FEATURE 6: PDF / FILE UPLOAD ENDPOINT ---
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check agar file PDF hai
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")
        
        # File ko read karna
        file_content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        
        extracted_text = ""
        # PDF ke har page ka text nikalna
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"
            
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the PDF.")
            
        # Text ko apni ChromaDB memory mein hamesha ke liye save karna
        add_to_memory(text=extracted_text, metadata={"source": file.filename})
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' processed and saved to memory!",
            "pages_read": len(pdf_reader.pages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# --- RENDER PORT RUNNER (SABSE NEECHE ISKO ADD KARO) ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)        
        
