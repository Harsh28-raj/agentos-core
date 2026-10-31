import json
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from conftest import route, tool_call

EVENT = {"summary": "Sync with Rahul", "start_time": "2026-11-01T16:00:00+05:30",
         "end_time": "2026-11-01T17:00:00+05:30", "attendees": ["rahul@example.com"]}


@pytest.fixture
def calendar(monkeypatch):
    """Fake Google Calendar service; fails the test if called unexpectedly."""
    service = MagicMock()
    service.events.return_value.insert.return_value.execute.return_value = {"htmlLink": "https://cal/evt"}
    monkeypatch.setattr("app.ai.tools.calendar_tools.calendar_service", lambda user_id: service)
    return service


def start_calendar_request(client, llms, user, thread="t1"):
    router_llm, worker_llm = llms
    router_llm.script += [route("calendar_agent")]
    worker_llm.script += [tool_call("create_calendar_event", EVENT)]
    res = client.post("/api/v1/chat", json={"message": "Schedule a sync with Rahul tomorrow 4pm", "thread_id": thread},
                      headers=user["headers"]).json()
    assert res["hitl_interrupt"] is True
    assert res["interrupt_data"]["summary"] == "Sync with Rahul"
    return res


# ------------------------------------------------------------ auth

def test_endpoints_require_auth(client):
    for method, path in [("post", "/api/v1/chat"), ("post", "/api/v1/chat/approve"), ("post", "/api/v1/chat/stream"),
                         ("get", "/api/v1/chat/history/t1"), ("delete", "/api/v1/chat/history/t1"),
                         ("get", "/api/v1/logs/t1"), ("get", "/api/logs/t1"), ("post", "/api/v1/upload"),
                         ("get", "/api/v1/system/status"), ("post", "/api/v1/integrations/google/authorize")]:
        assert getattr(client, method)(path).status_code == 401, path
    bad = {"Authorization": "Bearer not-a-token"}
    assert client.get("/api/v1/auth/me", headers=bad).status_code == 401


def test_register_login_flow(client, make_user):
    user = make_user("Mixed.Case@Example.com")
    assert user["email"] == "Mixed.Case@Example.com"
    # Login is case-insensitive, duplicate registration is rejected with a readable error
    assert client.post("/api/v1/auth/login", json={"email": "mixed.case@example.com", "password": "password123"}).status_code == 200
    dup = client.post("/api/v1/auth/register", json={"email": "mixed.case@example.com", "password": "password123"})
    assert dup.status_code == 400 and dup.json()["detail"] == "Email already registered"
    assert client.post("/api/v1/auth/register", json={"email": "s@example.com", "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={"email": "l@example.com", "password": "x" * 73}).status_code == 422
    assert client.post("/api/v1/auth/login", json={"email": "mixed.case@example.com", "password": "wrong-pass"}).status_code == 401


# ------------------------------------------------------------ chat + routing

def test_simple_chat_routes_and_finishes(client, llms, make_user):
    router_llm, worker_llm = llms
    user = make_user()
    router_llm.script += [route("research_agent"), route("FINISH")]
    worker_llm.script += ["Hello! How can I help?"]
    res = client.post("/api/v1/chat", json={"message": "hi", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res == {"reply": "Hello! How can I help?"}

    history = client.get("/api/v1/chat/history/t1", headers=user["headers"]).json()
    assert history["history"] == [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello! How can I help?"}]
    assert history["pending"] is None


def test_supervisor_chains_agents_with_hop_limit(client, llms, make_user, monkeypatch):
    router_llm, worker_llm = llms
    user = make_user()
    # A confused router keeps picking workers: the hop cap (3) must stop it
    router_llm.script += [route("research_agent"), route("coder_agent"), route("research_agent")]
    worker_llm.script += ["step 1", "step 2", "step 3"]
    res = client.post("/api/v1/chat", json={"message": "do many things", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["reply"] == "step 3"
    assert router_llm.script == [] and worker_llm.script == []


def test_router_cannot_reroute_same_worker(client, llms, make_user):
    router_llm, worker_llm = llms
    user = make_user()
    router_llm.script += [route("research_agent"), route("research_agent")]
    worker_llm.script += ["done"]
    res = client.post("/api/v1/chat", json={"message": "hi", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["reply"] == "done"


def test_unparseable_route_falls_back(client, llms, make_user):
    router_llm, worker_llm = llms
    user = make_user()
    router_llm.script += ["not json at all", "garbage"]
    worker_llm.script += ["fallback answer"]
    res = client.post("/api/v1/chat", json={"message": "hi", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["reply"] == "fallback answer"


# ------------------------------------------------------------ human in the loop

def test_negative_reply_rejects_and_never_calls_google(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)

    worker_llm.script += ["Okay, I did not create the event."]
    router_llm.script += [route("FINISH")]
    res = client.post("/api/v1/chat", json={"message": "no, don't do it", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["reply"] == "Okay, I did not create the event."
    calendar.events.return_value.insert.assert_not_called()
    tool_result = [m for m in worker_llm.calls[-1] if m.type == "tool"][-1]
    assert "cancelled" in tool_result.content


def test_ambiguous_reply_keeps_waiting(client, llms, make_user, calendar):
    user = make_user()
    start_calendar_request(client, llms, user)
    for message in ["maybe", "eyes on it later", "what time is it?"]:
        res = client.post("/api/v1/chat", json={"message": message, "thread_id": "t1"}, headers=user["headers"]).json()
        assert res["hitl_interrupt"] is True, message
    calendar.events.return_value.insert.assert_not_called()
    # Reloading the page shows the pending approval
    assert client.get("/api/v1/chat/history/t1", headers=user["headers"]).json()["pending"]["hitl_interrupt"] is True


def test_yes_in_chat_confirms(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)
    worker_llm.script += ["Your event is booked."]
    router_llm.script += [route("FINISH")]
    res = client.post("/api/v1/chat", json={"message": "yes", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["reply"] == "Your event is booked."
    body = calendar.events.return_value.insert.call_args.kwargs["body"]
    assert body["summary"] == "Sync with Rahul" and body["start"]["timeZone"]


def test_approve_endpoint_confirm_returns_reply_and_audits(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)
    worker_llm.script += ["Booked!"]
    router_llm.script += [route("FINISH")]
    res = client.post("/api/v1/chat/approve", json={"thread_id": "t1", "action": "CONFIRM"}, headers=user["headers"]).json()
    assert res["status"] == "resumed" and res["reply"] == "Booked!"
    calendar.events.return_value.insert.assert_called_once()

    logs = client.get("/api/v1/logs/t1", headers=user["headers"]).json()["logs"]
    assert any(log["action_taken"] == "CONFIRM" and log["original_args"]["summary"] == "Sync with Rahul" for log in logs)
    # Nothing left to approve
    assert client.post("/api/v1/chat/approve", json={"thread_id": "t1", "action": "CONFIRM"}, headers=user["headers"]).status_code == 409


def test_approve_endpoint_edit_changes_args(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)
    worker_llm.script += ["Booked with the new title."]
    router_llm.script += [route("FINISH")]
    res = client.post("/api/v1/chat/approve", json={"thread_id": "t1", "action": "EDIT",
                                                    "updated_args": {"summary": "Renamed"}}, headers=user["headers"]).json()
    assert res["status"] == "resumed"
    assert calendar.events.return_value.insert.call_args.kwargs["body"]["summary"] == "Renamed"


def test_approve_endpoint_reject(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)
    worker_llm.script += ["Cancelled."]
    router_llm.script += [route("FINISH")]
    res = client.post("/api/v1/chat/approve", json={"thread_id": "t1", "action": "REJECT"}, headers=user["headers"]).json()
    assert res["status"] == "rejected" and res["reply"] == "Cancelled."
    calendar.events.return_value.insert.assert_not_called()


def test_stream_resumes_pending_approval(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)
    worker_llm.script += ["Streamed booking done."]
    router_llm.script += [route("FINISH")]
    with client.stream("POST", "/api/v1/chat/stream", json={"message": "go ahead", "thread_id": "t1"},
                       headers=user["headers"]) as response:
        events = [json.loads(line[6:]) for line in response.iter_lines() if line.startswith("data: ")]
    kinds = [e["type"] for e in events]
    assert "tool_end" in kinds and kinds[-1] == "done", kinds
    assert events[-1]["reply"] == "Streamed booking done."
    calendar.events.return_value.insert.assert_called_once()
    # Routing JSON is never streamed as tokens
    assert not any('"next"' in e.get("content", "") for e in events if e["type"] == "token")


def test_stream_new_request_pauses(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    router_llm.script += [route("calendar_agent")]
    worker_llm.script += [tool_call("create_calendar_event", EVENT)]
    with client.stream("POST", "/api/v1/chat/stream", json={"message": "book it", "thread_id": "t9"},
                       headers=user["headers"]) as response:
        events = [json.loads(line[6:]) for line in response.iter_lines() if line.startswith("data: ")]
    assert events[-1]["type"] == "hitl_pause"
    assert events[-1]["tool"] == "create_calendar_event"
    assert any(e["type"] == "route" and "Calendar" in e["content"] for e in events)


# ------------------------------------------------------------ isolation

def test_users_cannot_see_or_approve_each_other(client, llms, make_user, calendar):
    alice, bob = make_user(), make_user()
    start_calendar_request(client, llms, alice, thread="shared")
    assert client.get("/api/v1/chat/history/shared", headers=bob["headers"]).json() == {"history": [], "pending": None}
    assert client.post("/api/v1/chat/approve", json={"thread_id": "shared", "action": "CONFIRM"},
                       headers=bob["headers"]).status_code == 409
    assert client.get("/api/v1/logs/shared", headers=bob["headers"]).json()["logs"] == []
    calendar.events.return_value.insert.assert_not_called()


def test_tools_receive_authenticated_user_id(client, llms, make_user, monkeypatch):
    seen = []
    service = MagicMock()
    service.events.return_value.insert.return_value.execute.return_value = {"htmlLink": "x"}
    monkeypatch.setattr("app.ai.tools.calendar_tools.calendar_service", lambda uid: seen.append(uid) or service)
    router_llm, worker_llm = llms
    user = make_user()
    start_calendar_request(client, llms, user)
    worker_llm.script += ["ok"]
    router_llm.script += [route("FINISH")]
    client.post("/api/v1/chat/approve", json={"thread_id": "t1", "action": "CONFIRM"}, headers=user["headers"])
    assert seen == [user["id"]]


def test_delete_history_only_removes_own_thread(client, llms, make_user):
    router_llm, worker_llm = llms
    alice, bob = make_user(), make_user()
    for u in (alice, bob):
        router_llm.script += [route("research_agent"), route("FINISH")]
        worker_llm.script += ["hello"]
        client.post("/api/v1/chat", json={"message": "hi", "thread_id": "t1"}, headers=u["headers"])
    assert client.delete("/api/v1/chat/history/t1", headers=alice["headers"]).status_code == 200
    assert client.get("/api/v1/chat/history/t1", headers=alice["headers"]).json()["history"] == []
    assert len(client.get("/api/v1/chat/history/t1", headers=bob["headers"]).json()["history"]) == 2
    # Glob characters are not valid thread ids
    assert client.delete("/api/v1/chat/history/*", headers=alice["headers"]).status_code == 422


def test_invalid_thread_id_rejected(client, make_user):
    user = make_user()
    assert client.post("/api/v1/chat", json={"message": "hi", "thread_id": "a*b"}, headers=user["headers"]).status_code == 422


# ------------------------------------------------------------ upload / status

def test_upload_validation(client, make_user):
    user = make_user()
    res = client.post("/api/v1/upload", files={"file": ("notes.txt", b"hello", "text/plain")}, headers=user["headers"])
    assert res.status_code == 400  # was turned into 500 before
    res = client.post("/api/v1/upload", files={"file": ("big.pdf", b"0" * (11 * 1024 * 1024), "application/pdf")},
                      headers=user["headers"])
    assert res.status_code == 413


def test_upload_reports_memory_failure(client, make_user, monkeypatch):
    user = make_user()
    monkeypatch.setattr("app.routers.upload._extract_pdf", lambda data: "some text")
    res = client.post("/api/v1/upload", files={"file": ("doc.pdf", b"%PDF", "application/pdf")}, headers=user["headers"])
    # SQLite test DB has no pgvector: must fail loudly instead of claiming success
    assert res.status_code == 503


def test_system_status(client, make_user):
    user = make_user()
    status = client.get("/api/v1/system/status", headers=user["headers"]).json()
    names = {t["name"]: t["status"] for t in status["tools"]}
    assert names["Code Interpreter"] == "OFFLINE" and names["Gmail Agent"] == "OFFLINE"
    assert status["active_tools"] == sum(1 for s in names.values() if s == "ONLINE")


def test_recovers_after_a_crashed_run(client, llms, make_user):
    router_llm, worker_llm = llms
    user = make_user()

    def boom(messages):
        raise RuntimeError("Groq exploded")
    router_llm.script += [route("research_agent")]
    worker_llm.script += [boom]
    res = client.post("/api/v1/chat", json={"message": "first", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["error"] is True and "PYTHON ERROR" not in res["reply"]

    # The stale half-finished run must not be mistaken for a pending approval
    router_llm.script += [route("research_agent"), route("FINISH")]
    worker_llm.script += ["second answer"]
    res = client.post("/api/v1/chat", json={"message": "second", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res == {"reply": "second answer"}
