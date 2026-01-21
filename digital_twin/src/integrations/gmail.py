"""
Gmail API integration for polling inbox and creating drafts.
Requires OAuth2 credentials from Google Cloud Console.
"""
import os
import base64
import json
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import requests

load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Configuration
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080/callback")
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class GmailIntegration:
    """Gmail API integration for digital twin."""
    
    def __init__(self):
        """Initialize Gmail service."""
        self.service = None
        self.credentials = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.
        
        Returns:
            True if authentication successful
        """
        creds = None
        
        # Load existing token
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # If no valid credentials, do OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file not found: {CREDENTIALS_FILE}\n"
                        "Download from Google Cloud Console: "
                        "https://console.cloud.google.com/apis/credentials"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save credentials
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def get_unread_messages(self, max_results: int = 10) -> List[Dict]:
        """
        Get unread messages from inbox.
        
        Args:
            max_results: Maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        results = self.service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=max_results
        ).execute()
        
        messages = []
        for msg in results.get('messages', []):
            msg_data = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
            
            # Extract body
            body = self._extract_body(msg_data['payload'])
            
            messages.append({
                'id': msg['id'],
                'thread_id': msg_data['threadId'],
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'date': headers.get('Date', ''),
                'body': body,
                'snippet': msg_data.get('snippet', '')
            })
        
        return messages
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract message body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def create_draft(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict:
        """
        Create a draft email.
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            thread_id: Optional thread ID for replies
        
        Returns:
            Draft object
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        message = f"To: {to}\r\n"
        message += f"Subject: {subject}\r\n"
        if thread_id:
            message += f"In-Reply-To: {thread_id}\r\n"
        message += "\r\n" + body
        
        encoded_message = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
        
        draft = {
            'message': {
                'raw': encoded_message
            }
        }
        
        if thread_id:
            draft['message']['threadId'] = thread_id
        
        created_draft = self.service.users().drafts().create(
            userId='me',
            body=draft
        ).execute()
        
        return created_draft
    
    def generate_and_draft(self, message: Dict, api_url: str = None) -> Optional[Dict]:
        """
        Generate reply using digital twin API and create draft.
        
        Args:
            message: Message dictionary from get_unread_messages()
            api_url: Base URL for digital twin API
        
        Returns:
            Created draft or None if failed
        """
        api_url = api_url or API_BASE_URL
        
        # Build context from message
        context = f"Subject: {message['subject']}\n\nFrom: {message['from']}\n\n{message['body']}"
        
        # Call API to generate reply
        try:
            response = requests.post(
                f"{api_url}/generate",
                json={
                    "context": context,
                    "use_rag": True,
                    "max_length": 1000
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            reply_body = result['reply']
        except Exception as e:
            print(f"Failed to generate reply: {e}")
            return None
        
        # Create draft
        try:
            draft = self.create_draft(
                to=message['from'],
                subject=f"Re: {message['subject']}",
                body=reply_body,
                thread_id=message.get('thread_id')
            )
            return draft
        except Exception as e:
            print(f"Failed to create draft: {e}")
            return None
    
    def poll_and_draft(self, max_messages: int = 5, api_url: str = None):
        """
        Poll inbox for unread messages and create drafts.
        
        Args:
            max_messages: Maximum messages to process
            api_url: Base URL for digital twin API
        """
        if not self.service:
            self.authenticate()
        
        messages = self.get_unread_messages(max_results=max_messages)
        
        print(f"Found {len(messages)} unread messages")
        
        for msg in messages:
            print(f"\nProcessing message: {msg['subject']}")
            draft = self.generate_and_draft(msg, api_url)
            if draft:
                print(f"✅ Created draft: {draft['id']}")
            else:
                print("❌ Failed to create draft")


def main():
    """Example usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gmail integration for digital twin")
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Poll inbox and create drafts"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=5,
        help="Maximum messages to process"
    )
    
    args = parser.parse_args()
    
    gmail = GmailIntegration()
    
    if args.poll:
        gmail.poll_and_draft(max_messages=args.max)
    else:
        print("Use --poll to poll inbox and create drafts")


if __name__ == "__main__":
    main()