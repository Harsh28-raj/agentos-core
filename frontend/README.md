# AgentOS Frontend

React 19 + TypeScript + Vite + Tailwind CSS 4 single-page app for AgentOS (landing page, auth, dashboard with
streaming chat, approval card, live tool status, tool activity and episodic memory).

```bash
npm install
cp .env.example .env.local    # VITE_API_BASE_URL=http://127.0.0.1:10000
npm run dev                   # http://localhost:5173
npm run check                 # lint + typecheck + build
```

File map, data flow and conventions: [`../docs/FRONTEND.md`](../docs/FRONTEND.md). API reference: [`../docs/API.md`](../docs/API.md).
