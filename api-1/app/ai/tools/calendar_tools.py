from typing import List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import interrupt

from app.ai.tools.google_auth import calendar_service, user_id_from
from app.core import config as app_config
from app.core.hitl import resolve_approval


def _when(value: str) -> dict:
    # timeZone is required by Google when the timestamp has no UTC offset.
    return {"dateTime": value, "timeZone": app_config.DEFAULT_TIMEZONE}


@tool
def check_calendar_availability(start_time: str, end_time: str, config: RunnableConfig = None) -> str:
    """Check busy slots on the user's primary calendar between start_time and end_time.

    Args:
        start_time: ISO 8601 timestamp with offset (e.g., '2026-07-31T10:00:00+05:30').
        end_time: ISO 8601 timestamp with offset (e.g., '2026-07-31T18:00:00+05:30').
    """
    try:
        service = calendar_service(user_id_from(config))
        result = service.freebusy().query(body={
            "timeMin": start_time,
            "timeMax": end_time,
            "timeZone": app_config.DEFAULT_TIMEZONE,
            "items": [{"id": "primary"}],
        }).execute()
        busy = result.get("calendars", {}).get("primary", {}).get("busy", [])
        if not busy:
            return f"The calendar is completely free between {start_time} and {end_time}."
        lines = [f"Found {len(busy)} busy slots:"]
        lines += [f"- Busy from {slot.get('start')} to {slot.get('end')}" for slot in busy]
        return "\n".join(lines)
    except Exception as e:
        return f"Calendar API Error: {e}"


@tool
def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: Optional[List[str]] = None,
    description: str = "",
    config: RunnableConfig = None,
) -> str:
    """Create a new event on the primary calendar. Requires human approval before it is created.

    Args:
        summary: Title of the event.
        start_time: ISO 8601 timestamp with offset (e.g., '2026-07-31T10:00:00+05:30').
        end_time: ISO 8601 timestamp with offset (e.g., '2026-07-31T11:00:00+05:30').
        attendees: List of email addresses to invite.
        description: Description of the event.
    """
    attendees = list(attendees or [])
    approved, edits = resolve_approval(interrupt({
        "message": "Awaiting approval for calendar event creation",
        "tool": "create_calendar_event",
        "action": "create_event",
        "summary": summary,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "description": description,
    }))
    if not approved:
        return "Calendar event creation was cancelled by the user."

    summary = edits.get("summary", summary)
    start_time = edits.get("start_time", start_time)
    end_time = edits.get("end_time", end_time)
    attendees = edits.get("attendees", attendees) or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in attendees.split(",") if a.strip()]
    description = edits.get("description", description)

    try:
        service = calendar_service(user_id_from(config))
        event_body = {
            "summary": summary,
            "description": description,
            "start": _when(start_time),
            "end": _when(end_time),
        }
        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]
        event = service.events().insert(calendarId="primary", body=event_body, sendUpdates="all").execute()
        return f"Event created successfully. Event Link: {event.get('htmlLink')}"
    except Exception as e:
        return f"Calendar API Error: {e}"
