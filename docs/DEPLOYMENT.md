# Running and Deploying

## Local development

Backend:
```bash
cd api-1
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env    # fill in GROQ_API_KEY, DATABASE_URL, JWT_SECRET_KEY, ENCRYPTION_KEY
uvicorn app.main:app --reload --port 10000
```
Frontend:
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Open http://localhost:5173, register, log in. Swagger: http://localhost:10000/docs.

Quick local Postgres with pgvector:
```bash
docker run -d --name agentos-db -e POSTGRES_PASSWORD=pw -p 5432:5432 pgvector/pgvector:pg16
```
then `DATABASE_URL=postgresql://postgres:pw@localhost:5432/postgres`.

## Production (Render + Vercel + Neon)

**Database (Neon)**: create a project; the pooled connection string works (`prepare_threshold=0` is set).
pgvector is available on Neon (`CREATE EXTENSION vector` runs at startup).

**Backend (Render, Web Service)**
- Root directory `api-1`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Env: everything marked required in [CONFIGURATION.md](CONFIGURATION.md), plus
  `CORS_ORIGINS=https://<your-vercel-domain>`, `FRONTEND_URL=https://<your-vercel-domain>`, `DEFAULT_TIMEZONE`.
- Uploaded images live on local disk (`UPLOAD_DIR`); on Render free tier they vanish on redeploy (text is still in memory).
  Attach a persistent disk and point `UPLOAD_DIR` at it if you need them.

**Frontend (Vercel)**: root `frontend`, build `npm run build`, output `dist`, env `VITE_API_BASE_URL=https://<render-backend>`.

## Google OAuth (Gmail + Calendar), per user

1. Google Cloud console → enable **Gmail API** and **Google Calendar API**.
2. OAuth consent screen: add scopes `https://mail.google.com/` and `https://www.googleapis.com/auth/calendar`;
   while in "Testing", add each user's Google address as a test user.
3. Credentials → OAuth client ID → **Web application**; authorized redirect URI =
   `https://<backend>/api/v1/integrations/google/callback` (local: `http://localhost:10000/api/v1/integrations/google/callback`).
4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `ENCRYPTION_KEY`, `FRONTEND_URL`.
5. In the dashboard click **Connect Google** → consent → redirected back with `?google=connected`.

Fallback for the owner without OAuth configured: `python generate_token.py` (needs `credentials.json`, desktop client),
then `python migrate_token.py --email you@example.com`.

## Upgrading from v1.0 (before the security fixes)

- **Logins keep working** (same `users` table, emails now matched case-insensitively). Set `JWT_SECRET_KEY` so sessions survive restarts.
- **Old conversations are not visible**: they were stored under the shared `default_user` thread key, which no user can access now.
- **Google token**: v1.0 stored it under `user_id="default_user"`, which is no longer used. Reconnect with
  **Connect Google** (or `migrate_token.py --email ...`). The old row can be deleted:
  `DELETE FROM user_tokens WHERE user_id = 'default_user';`
- **Code interpreter is now off** — set `ENABLE_CODE_INTERPRETER=true` only after reading [SECURITY.md](SECURITY.md).
- **Checkpoints move to Postgres** automatically when `DATABASE_URL` is set (tables created on startup).
- Set `GROQ_VISION_MODEL` if the default vision model is not available on your Groq account.
- Old long-term memories have no `user_id` and are therefore not returned to anyone.
