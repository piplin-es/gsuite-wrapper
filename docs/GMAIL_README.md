# Gmail API Usage Guide

## Setup

1. Install the package:
```bash
pip install mcp-gsuite
```

2. Set up credentials (one of two methods):

THE VALUES ARE THE VALID CREDENTIALS, YOU CAN USE THEM DIRECTLY:
   ```python
   import os
   os.environ['CREDENTIALS_DIR'] = '/Users/badasme/repos/aider/mcp-gsuite/'
   os.environ['ACCOUNTS_FILE'] = '/Users/badasme/repos/aider/mcp-gsuite/.accounts.json'
   os.environ['GAUTH_FILE'] = '/Users/badasme/repos/aider/mcp-gsuite/.gauth.json'
   ```

## REPL Usage Examples

```python
from mcp_gsuite.gmail import GmailService

# Initialize service with Gleb's email
gmail = GmailService(user_id='gleb@lynxtrading.com')

# Query emails
emails = gmail.query_emails(query='is:unread', max_results=10)

# Get specific email with attachments
email, attachments = gmail.get_email_by_id_with_attachments(email_id='email_id_here')

# Get attachment
attachment = gmail.get_attachment(
    message_id='message_id_here',
    attachment_id='attachment_id_here'
)
```

## Available Methods

- `query_emails(query=None, max_results=100)`: Search emails
- `get_email_by_id_with_attachments(email_id)`: Get full email with attachments
- `get_attachment(message_id, attachment_id)`: Get email attachment

## Gmail Search Query Examples

- `is:unread`: Unread messages
- `from:example@gmail.com`: Messages from specific sender
- `subject:"Hello"`: Messages with specific subject
- `has:attachment`: Messages with attachments
- `in:inbox`: Messages in inbox
- `label:important`: Important messages
- `after:2024/01/01`: Messages after date
- `before:2024/01/01`: Messages before date

## Error Handling

All methods return `None` on failure and log errors. Check the return value before proceeding:

```python
emails = gmail.query_emails()
if emails is None:
    print("Failed to query emails")
```

## Notes

- Credentials are stored in the specified credentials directory
- Maximum results per query is 500
- Email bodies are parsed as plain text
- Attachments are returned as base64-encoded data
