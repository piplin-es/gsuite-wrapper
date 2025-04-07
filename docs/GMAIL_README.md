# Gmail API Usage Guide

## Basic Usage

```python
from mcp_gsuite.gmail import GmailService

# Initialize service with user email
gmail = GmailService(user_id='your.email@example.com')
```

## Core Features and Return Types

### 1. Querying Emails
```python
# Returns List[GmailEmail] or None if failed
emails = gmail.query_emails(
    query='is:unread',  # Optional: Gmail search query
    max_results=100     # Optional: 1-500, default=100
)

# Get up to 500 emails with attachments
emails = gmail.query_emails(query='has:attachment', max_results=500)

# Each email in the list is a GmailEmail object
for email in emails:
    print(f"Subject: {email.subject}")
```

### 2. Working with Individual Emails
```python
# Returns GmailEmail object or None if failed
email = gmail.get_email_by_id(email_id='your_email_id')

# Access email properties (all properties are Optional[str] unless noted)
print(email.id)           # str: Unique email ID
print(email.thread_id)    # str: Conversation thread ID
print(email.subject)      # Optional[str]: Email subject
print(email.from_email)   # Optional[str]: Sender's email
print(email.body)         # Optional[str]: Preferred version (HTML or plain text)
print(email.body_html)    # Optional[str]: HTML version if available
print(email.body_plain)   # Optional[str]: Plain text version if available
print(email.date)         # datetime: When Gmail received the message
print(email.label_ids)    # List[str]: Gmail labels
```

### 3. Working with Attachments
```python
# Returns Dict[str, Any] or None if failed
attachment_data = gmail.get_attachment(
    message_id='message_id_here',
    attachment_id='attachment_id_here'
)

# Attachment data structure
{
    "size": int,           # Size of the attachment in bytes
    "data": str           # Base64-encoded attachment content
}

# Email attachment metadata (from email.attachments)
for attachment in email.attachments.values():
    print(attachment.filename)    # str: Original filename
    print(attachment.mime_type)   # str: MIME type
    print(attachment.attachment_id)  # str: ID for downloading
    print(attachment.part_id)     # str: Part identifier in email
```

## Gmail Search Query Examples

- `is:unread`: Unread messages
- `from:example@gmail.com`: Messages from specific sender
- `subject:"Hello"`: Messages with specific subject
- `has:attachment`: Messages with attachments
- `in:inbox`: Messages in inbox
- `label:important`: Important messages
- `after:2024/01/01`: Messages after date
- `before:2024/01/01`: Messages before date

## Email Properties Detail

`GmailEmail` object contains the following properties:

### Required Properties (Always Present)
- `id: str` - Email ID
- `thread_id: str` - Conversation thread ID
- `history_id: str` - Email history identifier
- `_internal_date: str` - Raw timestamp in milliseconds
- `size_estimate: int` - Approximate size in bytes
- `label_ids: List[str]` - List of Gmail labels
- `snippet: str` - Short preview of the message

### Optional Properties (May be None)
- `subject: Optional[str]` - Email subject
- `from_email: Optional[str]` - Sender's email
- `to_email: Optional[str]` - Recipient's email
- `cc: Optional[str]` - CC recipients
- `bcc: Optional[str]` - BCC recipients
- `message_id: Optional[str]` - RFC 2822 message ID
- `in_reply_to: Optional[str]` - Reference to parent message
- `references: Optional[str]` - References to related messages
- `delivered_to: Optional[str]` - Final recipient
- `body_html: Optional[str]` - HTML version of the message
- `body_plain: Optional[str]` - Plain text version
- `body: Optional[str]` - Preferred version (HTML or plain)
- `mime_type: Optional[str]` - MIME type of the body

### Special Properties
- `date: datetime` - Parsed datetime object from _internal_date
- `attachments: Dict[str, GmailAttachment]` - Dictionary of attachment metadata

## Error Handling

All methods return `None` on failure and log errors. Always check return values:

```python
emails = gmail.query_emails(query='is:unread')
if emails is None:
    print("Failed to query emails")
```

