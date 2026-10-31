# Configuration

Backend variables are read once in `api-1/app/core/config.py` (from the environment or `api-1/.env`).
Template: `api-1/.env.example`.

## Backend

| Variable | Default | Required | Purpose |
|---|---|:---:|---|
| `GROQ_API_KEY` | — | ✅ | Groq inference. Without it the graph is not built and chat returns 503 |
| `DATABASE_URL` (or `NEON_DATABASE_URL`) | — | ✅ prod | Postgres URL (any of `postgres://`, `postgresql://`, `+asyncpg`, `+psycopg`; query string ignored; SSL required unless host is localhost). `sqlite:///...` works for tests. Without it auth is unavailable |
| `JWT_SECRET_KEY` | random per process | ✅ prod | JWT signing key (≥32 chars). If unset, every restart logs everyone out |
| `ENCRYPTION_KEY` | — | ✅ for Google | Fernet key encrypting Google tokens (`Fernet.generate_key()`) |
| `TAVILY_API_KEY` | — | | Web search; tool reports itself unavailable without it |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | | Router + worker model |
| `GROQ_VISION_MODEL` | `meta-llama/llama-4-scout-17b-16e-instruct` | | Must be a Groq **vision** model (image upload + `analyze_image`) |
| `CHECKPOINTER` | `auto` | | `auto` \| `postgres` \| `redis` \| `memory` |
| `REDIS_URL` | — | | Only for `CHECKPOINTER=redis` (needs Redis Stack) |
| `CORS_ORIGINS` | `*` | | Comma-separated allowed origins, e.g. `https://app.vercel.app,http://localhost:5173`. Credentials are never allowed |
| `FRONTEND_URL` | `http://localhost:5173` | for OAuth | Where the Google callback redirects (`/dashboard?google=...`) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | — | for Google | OAuth web client |
| `GOOGLE_REDIRECT_URI` | — | for Google | `https://<backend>/api/v1/integrations/google/callback` (must match Google console) |
| `DEFAULT_TIMEZONE` | `UTC` | | IANA zone for "today/tomorrow", calendar events and free/busy (e.g. `Asia/Kolkata`) |
| `ENABLE_CODE_INTERPRETER` | `false` | | Let the coder agent run Python on the server. Read [SECURITY.md](SECURITY.md) first |
| `CODE_TIMEOUT_SECONDS` | `15` | | Wall/CPU limit for interpreter runs |
| `CONTEXT_WINDOW_MESSAGES` | `12` | | History messages sent to models (window always starts at a user message) |
| `MAX_AGENT_HOPS` | `3` | | Max worker runs per user message |
| `RECURSION_LIMIT` | `25` | | LangGraph recursion limit per run |
| `MAX_UPLOAD_MB` | `10` | | Upload size limit |
| `UPLOAD_DIR` | `api-1/uploads` | | Where uploaded images are stored (per-user folders). Use a persistent disk in production |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `7` | | JWT lifetime |
| `LOG_LEVEL` | `INFO` | | Python logging level |
| `PORT` | `10000` | | Only when running `python -m app.main` |

Generate secrets:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Frontend

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:10000` | Backend origin; `/api/v1` is appended automatically. Set it in Vercel project settings |

Template: `frontend/.env.example` (copy to `.env.local`, which is git-ignored).
