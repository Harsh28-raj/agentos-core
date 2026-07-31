import os
import base64
import json
from email.message import EmailMessage
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

def get_gmail_service(user_id: str):
    """Helper function to get the Gmail API service using UserToken from the DB."""
    if not SyncSessionLocal:
        raise Exception("Database connection not configured.")
        
    session = SyncSessionLocal()
    try:
        token_record = session.query(UserToken).filter_by(user_id=user_id, service_name='google').first()
        
        if not token_record:
            # Fallback for dev environment or if OAuth flow hasn't run
            raise Exception(f"No Gmail credentials found for user '{user_id}'. Please authenticate first.")
            
        token_data = decrypt_token(token_record.encrypted_data)
        
        # In a real app, client_id and client_secret should be in ENV, but they are stored in token_data
        # typically, or we can use credentials.json if we still want local secrets for the app identity.
        # Assuming token_data contains the full credentials dict.
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update DB with new refreshed token
                new_token_data = json.loads(creds.to_json())
                token_record.encrypted_data = encrypt_token(new_token_data)
                session.commit()
            except Exception as e:
                raise Exception(f"Failed to refresh Gmail credentials: {e}")
                
        return build('gmail', 'v1', credentials=creds)
    finally:
        session.close()


@tool
def search_emails(query: str, max_results: int = 5, config: RunnableConfig = None) -> str:
    """Search unread/recent messages in Gmail.
    
    Args:
        query: The search query (e.g., 'is:unread', 'from:boss@example.com').
        max_results: Maximum number of emails to return.
    """
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"
    try:
        service = get_gmail_service(user_id)
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return "No messages found matching the query."
            
        output = []
        for msg in messages:
            msg_id = msg['id']
            msg_data = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject', 'From']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            snippet = msg_data.get('snippet', '')
            output.append(f"ID: {msg_id}\nFrom: {sender}\nSubject: {subject}\nSnippet: {snippet}\n---")
            
        return "\n".join(output)
    except Exception as e:
        return f"Gmail API Error: {str(e)}"

@tool
def read_email_content(message_id: str, config: RunnableConfig = None) -> str:
    """Fetch and extract full body text and headers for a given email.
    
    Args:
        message_id: The ID of the email to read.
    """
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"
    try:
        service = get_gmail_service(user_id)
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        body = ""
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in msg['payload']:
            data = msg['payload']['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                
        return f"From: {sender}\nDate: {date}\nSubject: {subject}\n\nBody:\n{body}"
    except Exception as e:
        return f"Gmail API Error: {str(e)}"

@tool
def draft_email(recipient: str, subject: str, body: str, config: RunnableConfig = None) -> str:
    """Create an email draft in Gmail.
    
    Args:
        recipient: The email address of the recipient.
        subject: The subject of the email.
        body: The body content of the email.
    """
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"
    try:
        service = get_gmail_service(user_id)
        message = EmailMessage()
        message.set_content(body)
        message['To'] = recipient
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        return f"Draft created successfully. Draft ID: {draft['id']}"
    except Exception as e:
        return f"Gmail API Error: {str(e)}"

@tool
def send_email(draft_id: Optional[str] = None, recipient: Optional[str] = None, subject: Optional[str] = None, body: Optional[str] = None, config: RunnableConfig = None) -> str:
    """Send an email, preferably by sending an existing draft ID.
    
    Args:
        draft_id: The ID of the draft to send (preferred).
        recipient: The email address of the recipient (if not using draft_id).
        subject: The subject of the email (if not using draft_id).
        body: The body content of the email (if not using draft_id).
    """
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"
    try:
        service = get_gmail_service(user_id)
        
        if draft_id:
            sent_message = service.users().drafts().send(userId='me', body={'id': draft_id}).execute()
            return f"Draft {draft_id} sent successfully. Message ID: {sent_message['id']}"
        elif recipient and subject and body:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = recipient
            message['Subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': encoded_message}
            
            sent_message = service.users().messages().send(userId='me', body=send_message).execute()
            return f"Email sent successfully to {recipient}. Message ID: {sent_message['id']}"
        else:
            return "Error: Must provide either draft_id OR recipient, subject, and body."
    except Exception as e:
        return f"Gmail API Error: {str(e)}"
