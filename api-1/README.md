# AgentOS Backend (`api-1`)

FastAPI + LangGraph backend for AgentOS: a supervisor agent routes requests to research, coder, vision,
Gmail and Calendar agents; risky actions pause for human approval.

```bash
pip install -r requirements-dev.txt
cp .env.example .env          # fill in the required values
uvicorn app.main:app --reload --port 10000
pytest                        # 46 tests, no API keys needed
```

Documentation lives in [`../docs`](../docs/README.md):
[file map](../docs/BACKEND.md) · [API](../docs/API.md) · [agents & tools](../docs/AGENTS_AND_TOOLS.md) ·
[approvals](../docs/HITL.md) · [data & state](../docs/DATA_AND_STATE.md) · [configuration](../docs/CONFIGURATION.md) ·
[deployment](../docs/DEPLOYMENT.md) · [security](../docs/SECURITY.md) · [testing](../docs/TESTING.md)
