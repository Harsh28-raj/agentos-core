import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.db.postgres import SyncSessionLocal
from app.db.models import UserToken
from app.core.security import encrypt_token, decrypt_token

SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/calendar'
]

def get_calendar_service(user_id: str):
    """Helper function to get the Calendar API service using UserToken from the DB."""
    if not SyncSessionLocal:
        raise Exception("Database connection not configured.")
        
    session = SyncSessionLocal()
    try:
        token_record = session.query(UserToken).filter_by(user_id=user_id, service_name='google').first()
        
        if not token_record:
            raise Exception(f"No Google credentials found for user '{user_id}'. Please authenticate first.")
            
        token_data = decrypt_token(token_record.encrypted_data)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                new_token_data = json.loads(creds.to_json())
                token_record.encrypted_data = encrypt_token(new_token_data)
                session.commit()
            except Exception as e:
                raise Exception(f"Failed to refresh Google credentials: {e}")
                
        return build('calendar', 'v3', credentials=creds)
    finally:
        session.close()

@tool
def check_calendar_availability(start_time: str, end_time: str, config: RunnableConfig = None) -> str:
    """Check availability on the user's primary calendar between start_time and end_time.
    
    Args:
        start_time: ISO format string (e.g., '2026-07-31T10:00:00Z').
        end_time: ISO format string (e.g., '2026-07-31T18:00:00Z').
    """
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"
    try:
        service = get_calendar_service(user_id)
        
        body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "timeZone": "UTC",
            "items": [{"id": "primary"}]
        }
        
        events_result = service.freebusy().query(body=body).execute()
        calendars = events_result.get('calendars', {})
        primary_cal = calendars.get('primary', {})
        busy_slots = primary_cal.get('busy', [])
        
        if not busy_slots:
            return f"The calendar is completely free between {start_time} and {end_time}."
            
        output = [f"Found {len(busy_slots)} busy slots:"]
        for slot in busy_slots:
            start = slot.get('start')
            end = slot.get('end')
            output.append(f"- Busy from {start} to {end}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Calendar API Error: {str(e)}"

from pydantic import Field
@tool
def create_calendar_event(summary: str, start_time: str, end_time: str, attendees: Optional[List[str]] = Field(default_factory=list), description: str = "", config: RunnableConfig = None) -> str:
    """Create a new event on the primary calendar.
    
    Args:
        summary: Title of the event.
        start_time: ISO format string (e.g., '2026-07-31T10:00:00Z').
        end_time: ISO format string (e.g., '2026-07-31T11:00:00Z').
        attendees: List of email addresses to invite.
        description: Description of the event.
    """
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"
    try:
        service = get_calendar_service(user_id)
        
        event_body = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        
        if attendees:
            event_body['attendees'] = [{'email': email} for email in attendees]
            
        event = service.events().insert(calendarId='primary', body=event_body, sendUpdates='all').execute()
        return f"Event created successfully. Event Link: {event.get('htmlLink')}"
    except Exception as e:
        return f"Calendar API Error: {str(e)}"
