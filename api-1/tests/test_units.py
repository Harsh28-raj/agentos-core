import base64

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.ai.llm import context_window
from app.ai.tools.calculator import calculator_tool
from app.ai.tools.code_interpreter import run_python
from app.ai.tools.gmail import extract_body
from app.ai.tools.vision import analyze_image
from app.core import config
from app.core.hitl import classify_approval, resolve_approval


@pytest.mark.parametrize("message,expected", [
    ("yes", "CONFIRM"),
    ("Confirm", "CONFIRM"),
    ("go ahead", "CONFIRM"),
    ("ok bhej do", "CONFIRM"),
    ("looks good, send it", "CONFIRM"),
    # Bug #9: these were approved by the old substring matching
    ("no, don't do it", "REJECT"),
    ("stop, do not proceed", "REJECT"),
    ("don’t send it", "REJECT"),
    ("cancel", "REJECT"),
    ("eyes on it later", None),
    ("I don't know", "REJECT"),
    ("now", None),
    ("maybe", None),
    ("yes but change the subject", None),
    ("what's the weather?", None),
    ("", None),
])
def test_classify_approval(message, expected):
    assert classify_approval(message) == expected


def test_resolve_approval():
    assert resolve_approval("CONFIRM") == (True, {})
    assert resolve_approval("REJECT") == (False, {})
    assert resolve_approval("anything else") == (False, {})
    assert resolve_approval({"decision": "EDIT", "args": {"subject": "x"}}) == (True, {"subject": "x"})
    assert resolve_approval({"decision": "REJECT"}) == (False, {})


def test_context_window_never_orphans_tool_messages():
    history = [
        HumanMessage("q1"),
        AIMessage("", tool_calls=[{"name": "t", "args": {}, "id": "a"}]),
        ToolMessage("r", tool_call_id="a"),
        AIMessage("answer 1"),
        HumanMessage("q2"),
        AIMessage("answer 2"),
    ]
    window = context_window(history, limit=4)
    assert isinstance(window[0], HumanMessage)
    assert [m.content for m in window] == ["q2", "answer 2"]
    # The latest request and its tool calls are always kept, even past the limit
    long_turn = [HumanMessage("q"), *[AIMessage("", tool_calls=[{"name": "t", "args": {}, "id": str(i)}]) for i in range(5)]]
    assert context_window(long_turn, limit=2) == long_turn


def test_calculator_guards():
    assert calculator_tool.invoke({"expression": "4 * (3 + 2)"}) == "Result: 20"
    assert "too large" in calculator_tool.invoke({"expression": "9 ** 9 ** 9"})
    assert "Division by zero" in calculator_tool.invoke({"expression": "1/0"})
    assert "Unsupported" in calculator_tool.invoke({"expression": "__import__('os')"})


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def test_extract_body_nested_multipart():
    payload = {"mimeType": "multipart/mixed", "parts": [
        {"mimeType": "multipart/alternative", "parts": [
            {"mimeType": "text/plain", "body": {"data": _b64("Hello plain")}},
            {"mimeType": "text/html", "body": {"data": _b64("<p>Hello html</p>")}},
        ]},
        {"mimeType": "application/pdf", "body": {"attachmentId": "x"}},
    ]}
    assert extract_body(payload) == "Hello plain"
    html_only = {"mimeType": "text/html", "body": {"data": _b64("<div>Hi <b>there</b></div><script>x()</script>")}}
    assert extract_body(html_only) == "Hi there"


def test_code_interpreter_disabled_by_default():
    assert "disabled" in run_python("print(1)")


def test_code_interpreter_has_no_secrets(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_CODE_INTERPRETER", True)
    monkeypatch.setenv("SUPER_SECRET", "hunter2")
    out = run_python("import os; print(os.environ.get('SUPER_SECRET'), os.environ.get('GROQ_API_KEY'))")
    assert "None None" in out
    assert "timed out" in run_python("while True: pass") or "Error" in run_python("while True: pass")


def test_analyze_image_rejects_paths_outside_user_folder():
    cfg = {"configurable": {"user_id": "42"}}
    for name in ["../../etc/passwd", "/etc/passwd", "secret.txt"]:
        result = analyze_image.invoke({"file_name": name}, config=cfg)
        assert result.startswith("Error")
    assert "no authenticated user" in analyze_image.invoke({"file_name": "a.png"})
