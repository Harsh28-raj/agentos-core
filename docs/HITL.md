# Human-in-the-Loop (approvals)

Risky tools — `send_email` and `create_calendar_event` — never act without explicit human approval.

## Mechanism

```python
# inside the tool (gmail.py / calendar_tools.py)
approved, edits = resolve_approval(interrupt({
    "message": "...", "tool": "send_email", "action": "send_email",
    "recipient": ..., "subject": ..., "body": ..., "draft_id": ...,
}))
if not approved:
    return "Email sending was cancelled by the user."
# apply edits, then perform the side effect
```

1. `interrupt(payload)` stops the graph; the checkpointer stores the paused state (Postgres → survives restarts).
2. The API detects it with `pending_interrupts(graph, cfg)` (walks `aget_state(cfg, subgraphs=True)`).
3. The client gets `hitl_interrupt: true` + `interrupt_data` (= payload) or an SSE `hitl_pause` event.
4. The user answers; the API resumes with `Command(resume=value)`. LangGraph **re-runs the tool from the top**
   and `interrupt()` now returns `value`. Therefore everything before `interrupt()` must be read-only
   (e.g. `send_email` re-reads the draft for the preview — harmless).
5. If several tools paused in parallel, `resume_command` answers all of them (`{interrupt_id: value}`).

## Resume values (`resolve_approval`)

| Value | Meaning |
|---|---|
| `"CONFIRM"` | approve as shown |
| `"REJECT"` (or any other string) | cancel; the tool returns a cancellation message and the agent tells the user |
| `{"decision": "EDIT", "args": {...}}` | approve with changed fields (only keys present are changed) |

`send_email` + edit of `recipient`/`subject`/`body` sends a **new message** with the edited content instead of the stale draft.

## Three ways to answer

| Channel | How |
|---|---|
| Buttons (UI `ApprovalCard`) | `POST /api/v1/chat/approve {thread_id, action, updated_args?}` |
| Chat text, non-streaming | `POST /api/v1/chat {message: "yes"}` |
| Chat text, streaming | `POST /api/v1/chat/stream {message: "no"}` |

### Chat text parsing — `classify_approval()` in `app/core/hitl.py`

Whole-word matching, in this order:
1. Any **negative** word (`no, not, don't, never, cancel, reject, stop, abort, deny, nahi, mat, …`) → `REJECT`.
2. Any **hesitant** word (`maybe, wait, later, edit, change, but, ?, shayad, …`) → `None` (re-ask).
3. Any **affirmative** word/phrase (`yes, confirm, approve, ok, sure, haan, go ahead, do it, send it, bhej do, …`) → `CONFIRM`.
4. Otherwise → `None` (re-ask; the action stays paused, state is untouched).

Examples: "no, don't do it" → REJECT · "eyes on it later" → re-ask · "yes but change the subject" → re-ask · "ok bhej do" → CONFIRM.

## Invariants (do not break)

- **Never call `update_state` / `aupdate_state` while a thread is paused** — it discards the pending interrupt
  (verified). Answer only with `Command(resume=...)`.
- Never trim stored history with `RemoveMessage`; trim only the model's view (`context_window`).
- Every decision is audited: `episodic_logs` row with `tool_name=HITL_<DECISION>`, `action_taken`,
  `original_args` (the payload), `modified_args`, `human_feedback`, keyed by the user-scoped thread key.
- A paused tool's `tool_start` is logged as `awaiting_approval`; the resumed run logs its own start/end.
- Approvals are per user: another user can neither see nor resume the thread (`409`).

## Tested in `tests/test_api.py`

`test_negative_reply_rejects_and_never_calls_google`, `test_ambiguous_reply_keeps_waiting`,
`test_yes_in_chat_confirms`, `test_approve_endpoint_confirm_returns_reply_and_audits`,
`test_approve_endpoint_edit_changes_args`, `test_approve_endpoint_reject`,
`test_stream_resumes_pending_approval`, `test_users_cannot_see_or_approve_each_other`.
