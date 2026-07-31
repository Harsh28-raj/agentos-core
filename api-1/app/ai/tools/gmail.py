import os
import base64
from email.message import EmailMessage
from typing import List, Dict, Optional
from langchain_core.tools import tool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Helper function to get the Gmail API service."""
    creds = None
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    token_path = os.path.join(base_dir, 'token.json')
    creds_path = os.path.join(base_dir, 'credentials.json')

    # If modifying this to production, token generation should be handled explicitly.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                raise Exception("Failed to refresh Gmail credentials. Please re-authenticate.")
        else:
            if not os.path.exists(creds_path):
                raise Exception("credentials.json not found. Gmail API is not configured.")
            # Note: In a headless environment, InstalledAppFlow will block waiting for a browser. 
            # We assume for this implementation that the token is either generated locally or will be.
            # Raising an error gracefully if no valid token is present and it requires interactive auth.
            raise Exception("No valid Gmail token found. Please run a local script to generate token.json first.")
            
    return build('gmail', 'v1', credentials=creds)


@tool
def search_emails(query: str, max_results: int = 5) -> str:
    """Search unread/recent messages in Gmail.
    
    Args:
        query: The search query (e.g., 'is:unread', 'from:boss@example.com').
        max_results: Maximum number of emails to return.
    """
    try:
        service = get_gmail_service()
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
def read_email_content(message_id: str) -> str:
    """Fetch and extract full body text and headers for a given email.
    
    Args:
        message_id: The ID of the email to read.
    """
    try:
        service = get_gmail_service()
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
def draft_email(recipient: str, subject: str, body: str) -> str:
    """Create an email draft in Gmail.
    
    Args:
        recipient: The email address of the recipient.
        subject: The subject of the email.
        body: The body content of the email.
    """
    try:
        service = get_gmail_service()
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
def send_email(draft_id: Optional[str] = None, recipient: Optional[str] = None, subject: Optional[str] = None, body: Optional[str] = None) -> str:
    """Send an email, preferably by sending an existing draft ID.
    
    Args:
        draft_id: The ID of the draft to send (preferred).
        recipient: The email address of the recipient (if not using draft_id).
        subject: The subject of the email (if not using draft_id).
        body: The body content of the email (if not using draft_id).
    """
    try:
        service = get_gmail_service()
        
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
