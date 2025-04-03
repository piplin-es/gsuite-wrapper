from googleapiclient.discovery import build 
from . import gauth
import logging
import base64
import traceback
from email.mime.text import MIMEText
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class GmailAttachment:
    """Represents a Gmail attachment with its metadata."""
    filename: str
    mime_type: str
    attachment_id: str
    part_id: str

@dataclass
class GmailEmail:
    """Represents a Gmail email with all its metadata and content."""
    id: str
    thread_id: str
    history_id: str
    _internal_date: str  # Raw timestamp in milliseconds, use .date property instead
    size_estimate: int
    label_ids: List[str]
    snippet: str
    subject: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: Optional[str] = None
    delivered_to: Optional[str] = None
    body_html: Optional[str] = None
    body_plain: Optional[str] = None
    body: Optional[str] = None  # For backward compatibility, will contain preferred version
    mime_type: Optional[str] = None
    attachments: Dict[str, GmailAttachment] = field(default_factory=dict)

    @property
    def date(self) -> datetime:
        """
        Get the email's receipt date as a datetime object.
        This is when Gmail received the message, not when it was sent.
        """
        try:
            # Convert milliseconds to seconds for datetime
            timestamp = int(self._internal_date) / 1000
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError) as e:
            logging.error(f"Error converting internal date: {str(e)}")
            # Return epoch time if conversion fails
            return datetime.fromtimestamp(0)

    @classmethod
    def from_api_response(cls, txt: dict) -> Optional['GmailEmail']:
        """Create a GmailEmail instance from a Gmail API response."""
        try:
            payload = txt.get('payload', {})
            
            # Create email with required fields
            email = cls._create_with_required_fields(txt)
            
            # Parse headers
            cls._parse_headers(email, payload.get('headers', []))
            
            # Extract attachments from payload
            email.attachments = cls._extract_attachments_from_payload(payload)

            # Extract body
            cls._extract_and_set_body(email, payload)
            
            return email
            
        except Exception as e:
            logging.error(f"Error creating GmailEmail: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    @classmethod
    def _create_with_required_fields(cls, txt: dict) -> 'GmailEmail':
        """Create a GmailEmail instance with required fields from API response."""
        return cls(
            id=txt.get('id'),
            thread_id=txt.get('threadId'),
            history_id=txt.get('historyId'),
            _internal_date=txt.get('internalDate'),
            size_estimate=txt.get('sizeEstimate'),
            label_ids=txt.get('labelIds', []),
            snippet=txt.get('snippet'),
            attachments={}
        )

    @staticmethod
    def _parse_headers(email: 'GmailEmail', headers: List[dict]) -> None:
        """Parse email headers and set corresponding fields."""
        header_mapping = {
            'subject': 'subject',
            'from': 'from_email',
            'to': 'to_email',
            # 'date': 'date',
            'cc': 'cc',
            'bcc': 'bcc',
            'message-id': 'message_id',
            'in-reply-to': 'in_reply_to',
            'references': 'references',
            'delivered-to': 'delivered_to'
        }
        
        for header in headers:
            name = header.get('name', '').lower()
            if name in header_mapping:
                setattr(email, header_mapping[name], header.get('value', ''))

    @classmethod
    def _extract_attachments_from_payload(cls, payload: dict) -> Dict[str, 'GmailAttachment']:
        """Extract attachment metadata from message payload and create GmailAttachment instances."""
        attachments = {}
        for part in payload.get("parts", []):
            if "attachmentId" in part.get("body", {}):
                attachment_id = part["body"]["attachmentId"]
                part_id = part["partId"]
                attachments[part_id] = GmailAttachment(
                    filename=part.get("filename", ""),
                    mime_type=part.get("mimeType", ""),
                    attachment_id=attachment_id,
                    part_id=part_id
                )
        return attachments

    @classmethod
    def _extract_and_set_body(cls, email: 'GmailEmail', payload: dict) -> None:
        """Extract and set email body from payload."""
        try:
            # For single part text messages (plain or html)
            if payload.get('mimeType') == 'text/plain':
                email.body_plain = cls._decode_body_data(payload.get('body', {}).get('data'))
                email.body = email.body_plain
                email.mime_type = 'text/plain'
                return
            elif payload.get('mimeType') == 'text/html':
                email.body_html = cls._decode_body_data(payload.get('body', {}).get('data'))
                email.body = email.body_html
                email.mime_type = 'text/html'
                return
            
            # For multipart messages
            if payload.get('mimeType', '').startswith('multipart/'):
                parts = payload.get('parts', [])
                
                # Extract both versions when available
                email.body_html = cls._find_text_html_body(parts)
                email.body_plain = cls._find_text_plain_body(parts)
                
                # For multipart/alternative, prefer HTML for the main body
                if payload.get('mimeType') == 'multipart/alternative':
                    email.body = (
                        email.body_html or      # Try HTML first
                        email.body_plain or     # Then plain text
                        cls._find_nested_body(parts) or  # Then nested
                        cls._find_fallback_body(parts)   # Finally fallback
                    )
                else:
                    # For other multipart types, prefer plain text
                    email.body = (
                        email.body_plain or
                        email.body_html or
                        cls._find_nested_body(parts) or
                        cls._find_fallback_body(parts)
                    )
                
                if email.body:
                    # Set mime_type based on which version we're using as the main body
                    if email.body == email.body_html:
                        email.mime_type = 'text/html'
                    elif email.body == email.body_plain:
                        email.mime_type = 'text/plain'
                    else:
                        email.mime_type = payload.get('mimeType')
                    
        except Exception as e:
            logging.error(f"Error extracting body: {str(e)}")
            logging.error(traceback.format_exc())

    @classmethod
    def _find_text_plain_body(cls, parts: List[dict]) -> Optional[str]:
        """Find and decode text/plain body from message parts."""
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                body = cls._decode_body_data(part.get('body', {}).get('data'))
                if body:
                    return body
        return None

    @classmethod
    def _find_text_html_body(cls, parts: List[dict]) -> Optional[str]:
        """Find and decode text/html body from message parts."""
        for part in parts:
            if part.get('mimeType') == 'text/html':
                body = cls._decode_body_data(part.get('body', {}).get('data'))
                if body:
                    return body
        return None

    @classmethod
    def _find_nested_body(cls, parts: List[dict]) -> Optional[str]:
        """Find body in nested multipart structures."""
        for part in parts:
            if part.get('mimeType', '').startswith('multipart/'):
                body = cls._extract_nested_body(part)
                if body:
                    return body
        return None

    @classmethod
    def _find_fallback_body(cls, parts: List[dict]) -> Optional[str]:
        """Try to get body from the first part as fallback."""
        if parts and 'body' in parts[0] and 'data' in parts[0]['body']:
            return cls._decode_body_data(parts[0]['body']['data'])
        return None

    @staticmethod
    def _decode_body_data(data: Optional[str]) -> Optional[str]:
        """Decode base64 encoded body data."""
        if data:
            try:
                return base64.urlsafe_b64decode(data).decode('utf-8')
            except Exception as e:
                logging.error(f"Error decoding body data: {str(e)}")
        return None

    @classmethod
    def _extract_nested_body(cls, payload: dict) -> Optional[str]:
        """Helper method to extract body from nested multipart structures."""
        try:
            # For single part text messages (plain or html)
            if payload.get('mimeType') in ['text/plain', 'text/html']:
                return cls._decode_body_data(payload.get('body', {}).get('data'))
            
            # For multipart messages
            if payload.get('mimeType', '').startswith('multipart/'):
                parts = payload.get('parts', [])
                return (
                    cls._find_text_plain_body(parts) or
                    cls._find_text_html_body(parts) or
                    cls._find_nested_body(parts)
                )

            return None
            
        except Exception as e:
            logging.error(f"Error extracting nested body: {str(e)}")
            return None

class GmailService():
    def __init__(self, user_id: str):
        credentials = gauth.get_stored_credentials(user_id=user_id)
        if not credentials:
            raise RuntimeError("No Oauth2 credentials stored")
        self.service = build('gmail', 'v1', credentials=credentials)

    def _query_emails_raw(self, query=None, max_results=100) -> List[dict]:
        """
        Query emails from Gmail and return raw API responses.
        
        Args:
            query (str, optional): Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
                                If None, returns all emails
            max_results (int): Maximum number of emails to retrieve (1-500, default: 100)
        
        Returns:
            List[dict]: List of raw Gmail API message responses
        """
        try:
            # Ensure max_results is within API limits
            max_results = min(max(1, max_results), 500)
            
            # Get the list of messages
            result = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query if query else ''
            ).execute()

            messages = result.get('messages', [])
            raw_messages = []

            # Fetch full message details for each message
            for msg in messages:
                txt = self.service.users().messages().get(
                    userId='me', 
                    id=msg['id']
                ).execute()
                
                raw_messages.append(txt)
                    
            return raw_messages
            
        except Exception as e:
            logging.error(f"Error reading raw emails: {str(e)}")
            logging.error(traceback.format_exc())
            return []

    def query_emails(self, query=None, max_results=100) -> List[GmailEmail]:
        """
        Query emails from Gmail based on a search query.
        
        Args:
            query (str, optional): Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
                                If None, returns all emails
            max_results (int): Maximum number of emails to retrieve (1-500, default: 100)
        
        Returns:
            List[GmailEmail]: List of parsed email messages, newest first
        """
        raw_messages = self._query_emails_raw(query=query, max_results=max_results)
        return [
            parsed_message 
            for msg in raw_messages
            if (parsed_message := GmailEmail.from_api_response(msg)) is not None
        ]
        
    def get_email_by_id(self, email_id: str) -> GmailEmail | None:
        """
        Fetch and parse a complete email message by its ID.
        
        Args:
            email_id (str): The Gmail message ID to retrieve
        
        Returns:
            GmailEmail: Complete parsed email message including body and attachments
            None: If retrieval or parsing fails
        """
        try:
            # Fetch the complete message by ID
            message = self.service.users().messages().get(
                userId='me',
                id=email_id
            ).execute()

            # Parse the message
            return GmailEmail.from_api_response(message)
            
        except Exception as e:
            logging.error(f"Error retrieving email {email_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None
        
    def create_draft(self, to: str, subject: str, body: str, cc: list[str] | None = None) -> GmailEmail | None:
        """
        Create a draft email message.
        
        Args:
            to (str): Email address of the recipient
            subject (str): Subject line of the email
            body (str): Body content of the email
            cc (list[str], optional): List of email addresses to CC
            
        Returns:
            GmailEmail: Draft message data if successful
            None: If creation fails
        """
        try:
            # Create message body
            message = {
                'to': to,
                'subject': subject,
                'text': body,
            }
            if cc:
                message['cc'] = ','.join(cc)
                
            # Create the message in MIME format
            mime_message = MIMEText(body)
            mime_message['to'] = to
            mime_message['subject'] = subject
            if cc:
                mime_message['cc'] = ','.join(cc)
                
            # Encode the message
            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
            
            # Create the draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={
                    'message': {
                        'raw': raw_message
                    }
                }
            ).execute()
            
            # Parse the draft message into a GmailEmail object
            if draft and 'message' in draft:
                return GmailEmail.from_api_response(draft['message'])
            return None
            
        except Exception as e:
            logging.error(f"Error creating draft: {str(e)}")
            logging.error(traceback.format_exc())
            return None
        
    def delete_draft(self, draft_id: str) -> bool:
        """
        Delete a draft email message.
        
        Args:
            draft_id (str): The ID of the draft to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.service.users().drafts().delete(
                userId='me',
                id=draft_id
            ).execute()
            return True
            
        except Exception as e:
            logging.error(f"Error deleting draft {draft_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return False
        
    def create_reply(self, original_message: GmailEmail, reply_body: str, send: bool = False, cc: list[str] | None = None) -> GmailEmail | None:
        """
        Create a reply to an email message and either send it or save as draft.
        
        Args:
            original_message (GmailEmail): The original message data
            reply_body (str): Body content of the reply
            send (bool): If True, sends the reply immediately. If False, saves as draft.
            cc (list[str], optional): List of email addresses to CC
            
        Returns:
            GmailEmail: Sent message or draft data if successful
            None: If operation fails
        """
        try:
            to_address = original_message.from_email
            if not to_address:
                raise ValueError("Could not determine original sender's address")
            
            subject = original_message.subject or ''
            if not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"

            original_date = original_message.date or ''
            original_from = original_message.from_email or ''
            original_body = original_message.body or ''
        
            full_reply_body = (
                f"{reply_body}\n\n"
                f"On {original_date}, {original_from} wrote:\n"
                f"> {original_body.replace('\n', '\n> ') if original_body else '[No message body]'}"
            )

            mime_message = MIMEText(full_reply_body)
            mime_message['to'] = to_address
            mime_message['subject'] = subject
            if cc:
                mime_message['cc'] = ','.join(cc)
                
            mime_message['In-Reply-To'] = original_message.id
            mime_message['References'] = original_message.id
            
            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
            
            message_body = {
                'raw': raw_message,
                'threadId': original_message.thread_id  # Ensure it's added to the same thread
            }

            if send:
                # Send the reply immediately
                result = self.service.users().messages().send(
                    userId='me',
                    body=message_body
                ).execute()
            else:
                # Save as draft
                result = self.service.users().drafts().create(
                    userId='me',
                    body={
                        'message': message_body
                    }
                ).execute()
            
            # Parse the result into a GmailEmail object
            if result:
                if not send:
                    result = result.get('message', {})
                return GmailEmail.from_api_response(result)
            return None
            
        except Exception as e:
            logging.error(f"Error {'sending' if send else 'drafting'} reply: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def get_attachment(self, message_id: str, attachment_id: str) -> dict | None:
        """
        Retrieves a Gmail attachment by its ID.
        
        Args:
            message_id (str): The ID of the Gmail message containing the attachment
            attachment_id (str): The ID of the attachment to retrieve
        
        Returns:
            dict: Attachment data including filename and base64-encoded content
            None: If retrieval fails
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id, 
                id=attachment_id
            ).execute()
            return {
                "size": attachment.get("size"),
                "data": attachment.get("data")
            }
            
        except Exception as e:
            logging.error(f"Error retrieving attachment {attachment_id} from message {message_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None