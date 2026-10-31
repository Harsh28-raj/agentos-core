# Frontend (`frontend/`)

React 19 + TypeScript 6 + Vite 8 + Tailwind CSS 4 + react-router 7 + lucide-react. Deployed on Vercel (`vercel.json` rewrites all paths to `index.html`).

Commands: `npm run dev` (port 5173) · `npm run build` · `npm run lint` · `npm run check` (lint + typecheck + build).
API base: `VITE_API_BASE_URL` (default `http://localhost:10000`); `src/env.ts` appends `/api/v1`.

## File map (`src/`)

| Path | Responsibility |
|---|---|
| `main.tsx`, `App.tsx` | Fonts, CSS, `ThemeProvider` → `AuthProvider` → `AppRouter` |
| `routes/AppRouter.tsx` | `/` landing · `/login` `/register` (AuthLayout) · `/dashboard` (ProtectedRoute + AppShell) · `*` → `/` |
| `routes/ProtectedRoute.tsx` | Redirects to `/login` when there is no user |
| `layouts/AuthLayout.tsx` | Auth card; redirects logged-in users to `/dashboard` |
| `layouts/AppShell.tsx` | Header (SystemStatusBar, theme toggle, Sign out) + `<Outlet/>` |
| `contexts/authContextValue.ts` + `AuthContext.tsx` | `AuthProvider`: restores session via `/auth/me`, `login(user, token)`, `logout()`, listens for the global logout event |
| `hooks/useAuth.ts` | `useAuth()` |
| `hooks/useDashboardData.ts` | `useThreadLogs(threadId, refreshKey)`, `useSystemStatus()` (polls every 60 s) |
| `services/apiClient.ts` | `apiClient.get/post/delete`, bearer header, FastAPI `detail` → `ApiError.message`, 401 → dispatches `agentos:logout` |
| `services/authService.ts` | login / register / me |
| `services/chatService.ts` | history, clear, approve, logs, system status, Google status/authorize/disconnect, upload, **`stream()`** (SSE over `fetch` + `ReadableStream`) |
| `types/index.ts`, `types/auth.ts` | API types: `ChatReply`, `InterruptData`, `StreamEvent`, `LogEntry`, `SystemStatus`, `User` |
| `pages/DashboardPage.tsx` | Owns `threadId` (localStorage `agentos_thread_<userId>`) and `refreshKey`; lays out the 4 panels |
| `components/dashboard/ChatPanel.tsx` | Loads history (+ pending approval), streams messages, shows live status, approval card, upload, new/delete conversation |
| `components/dashboard/ApprovalCard.tsx` | Approve / Reject / Edit for `interrupt_data` (edits only changed fields; `draft_id` read-only) |
| `components/dashboard/ToolStatus.tsx` | Real tool status + Connect/Disconnect Google; reads `?google=connected|error` after OAuth |
| `components/dashboard/TaskBoard.tsx` | "Tool activity" from the audit log (paused attempts hidden once resumed) |
| `components/dashboard/MemoryViewer.tsx` | "Episodic memory": approval decisions and tool results from the audit log |
| `components/dashboard/styles.ts` | Shared light/dark class strings for dashboard panels |
| `components/system/SystemStatusBar.tsx` | ONLINE/OFFLINE, `active/total TOOLS ACTIVE`, clock |
| `components/common/*` | `Card`, `Button`, `StatusBadge` (`completed`, `in_progress`, `failed`, `pending`) |
| `components/landing/*`, `pages/LandingPage.tsx` | Marketing page (dark terminal look) |
| `pages/LoginPage.tsx`, `RegisterPage.tsx`, `authStyles.ts` | Auth forms (server error messages shown verbatim) |
| `theme/themeContext.ts`, `ThemeProvider.tsx`, `useTheme.ts` | `light`/`dark` in localStorage, toggles `.dark` on `<html>` |
| `index.css` | Tailwind import, `@custom-variant dark` (class based), color tokens (`paper`, `surface`, `ink`, `slate`, `hairline`, `signal`) |

## Data flow on the dashboard

```
DashboardPage(threadId, refreshKey)
 ├─ ChatPanel ── chatService.history(threadId) on mount/thread change
 │             ── chatService.stream(...)  → events update messages/status/pending
 │             ── chatService.approve(...) → reply + maybe next pending
 │             └─ onActivity() → refreshKey++  (re-fetches logs)
 ├─ ToolStatus ── useSystemStatus(), Google status
 ├─ TaskBoard  ┐
 └─ MemoryViewer┘── useThreadLogs(threadId, refreshKey) (one shared fetch)
```

Stream handling: `token` events are shown live; the `done.reply` replaces them (tokens can include
intermediate worker output). `hitl_pause` shows the pause message and the ApprovalCard.

## Theme

Class-based dark mode. Dashboard/auth use `bg-white dark:bg-[#0d0d0d]`-style pairs (dark = original terminal look).
The landing page shares the theme state but its visuals are dark-only (see [BUG_AUDIT.md](BUG_AUDIT.md)).

## Conventions

- Fetch through `apiClient`/`chatService` only (auth header, error parsing and 401 handling are there).
- Contexts live in `*Value.ts`/`*Context.ts` files separate from provider components (react-refresh lint rule).
- No `any`; lint must pass (`npm run lint`).
