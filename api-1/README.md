# 🤖 AgentOS Backend Engine (`api-1`)

A production-ready, asynchronous **FastAPI** backend powering **AgentOS** — a Personal AI Operating System. Built on a **LangGraph ReAct Agent Architecture** that runs dynamic reasoning loops, calls real-time tools, and serves responses over both standard HTTP and high-speed Server-Sent Events (SSE).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688)
![LangGraph](https://img.shields.io/badge/LangGraph-ReAct%20Agent-purple)
![Status](https://img.shields.io/badge/Status-Live-brightgreen)

**🔗 Live API:** [agentos-lr9e.onrender.com](https://agentos-lr9e.onrender.com) &nbsp;•&nbsp; **📘 Docs:** [/docs](https://agentos-lr9e.onrender.com/docs)

---

## 🌟 Key Capabilities

| Capability | Description |
|---|---|
| 🧠 **ReAct Reasoning Engine** | Built on **LangGraph**, powered by **LLaMA 3.3 70B** via Groq LPUs for fast, multi-step reasoning |
| 🌐 **Live Web Search** | Integrates the **Tavily API** for real-time facts, news, and current events |
| 📦 **Long-Term Vector Memory** | Persistent, user-isolated memory via **ChromaDB** + **FastEmbed** |
| ⚡ **SSE Streaming** | Token-by-token streaming at `/api/chat/stream`, ChatGPT-style |
| 📄 **Document Ingestion** | Built-in PDF parsing (`PyPDF2`) — auto-extracts and vectorizes uploaded docs |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn (ASGI) |
| LLM Engine | LangChain + LangGraph + `langchain-groq` (LLaMA 3.3 70B) |
| Vector Store | ChromaDB + FastEmbed (`BAAI/bge-small-en-v1.5`) |
| Search | Tavily Python SDK |
| Deployment | Render (Linux, Free-Tier Container) |

---

## 📂 Project Structure

```text
api-1/
├── app/
│   ├── ai/
│   │   ├── agent.py          # LangGraph ReAct Agent definition & tool binding
│   │   └── tools.py          # Custom tools (Tavily Search, Weather, Chroma Memory)
│   ├── db/
│   │   ├── chroma_db/        # Persistent local ChromaDB files
│   │   └── vector_store.py   # FastEmbed & memory CRUD operations
│   └── main.py               # FastAPI routes, SSE generators, exception handlers
├── requirements.txt          # Locked production dependencies
└── README.md
```

---

## 🚀 Local Setup

### 1. Prerequisites
Python **3.10+** installed on your system.

### 2. Environment Variables
Create a `.env` file in the `api-1/` root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Install & Run

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI available at → `http://localhost:8000/docs`

---

## 📡 API Endpoints

| Method | Endpoint | Description | Payload |
|---|---|---|---|
| `GET` | `/` | Server health check | — |
| `POST` | `/api/chat` | Synchronous agent chat | `{"message": "...", "user_id": "..."}` |
| `POST` | `/api/chat/stream` | Token streaming (SSE) | `{"message": "...", "user_id": "..."}` |
| `POST` | `/api/upload` | PDF → memory upload | Multipart form (`file`: `.pdf`) |

Full request/response schemas, error formats, and frontend integration examples → see [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md).

---

## ⚡ Notes for Contributors

- **Render Cold Start:** Free tier spins down after 15 min idle — first request after that can take 30–40s.
- **CORS:** For local frontend dev (`localhost:3000` / `:5173`), ensure `CORSMiddleware` origins are updated in `main.py`.

---

## 🗺️ Roadmap

- [x] **Feature 1** — Core ReAct engine, SSE streaming, live tools, PDF ingestion
- [ ] **Feature 2** — Structured SSE events (thought / tool_start / tool_end) for live "thinking" UI
- [ ] **Feature 3** — Redis short-term memory + PostgreSQL episodic logging

---

## 🔗 Live Deployment

- **Base URL:** `https://agentos-lr9e.onrender.com`
- **Swagger Docs:** `https://agentos-lr9e.onrender.com/docs`
