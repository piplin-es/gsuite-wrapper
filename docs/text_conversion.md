# Text Conversion Utilities

This document describes how to use the text conversion utilities (`html2text` and `pdf2text`) with the Gmail API.

## HTML to Text Conversion

The `html2text` function can be used to convert HTML email content to plain text. It handles both raw HTML strings and base64 encoded content from the Gmail API.

### Example Usage with Gmail API

```python
from mcp_gsuite.gmail import GmailService
from mcp_gsuite.text_conversion import html2text

# Initialize Gmail service
gmail_service = GmailService(user_id="your_user_id")

# Get email with body
email, _ = gmail_service.get_email_by_id_with_attachments(email_id="your_email_id")

# Convert HTML body to plain text
if email and "body" in email:
    # The body is already decoded from base64 by the Gmail service
    # and contains the text/plain content if available
    plain_text = html2text(email["body"])
    print(plain_text)
```

Note: The Gmail service automatically extracts the text/plain content from the email message. If the email is multipart, it will:
1. First try to find a direct text/plain part
2. If not found, recursively check nested multipart structures
3. As a last resort, use the first available part

## PDF to Text Conversion

The `pdf2text` function converts PDF attachments to plain text. It expects base64 encoded bytes, which matches the format of attachments from the Gmail API.

### Example Usage with Gmail API

```python
from mcp_gsuite.gmail import GmailService
from mcp_gsuite.text_conversion import pdf2text

# Initialize Gmail service
gmail_service = GmailService(user_id="your_user_id")

# Get email with attachments
email, attachments = gmail_service.get_email_by_id_with_attachments(email_id="your_email_id")

# Process PDF attachments
for part_id, attachment in attachments.items():
    if attachment["mimeType"] == "application/pdf":
        # Get attachment data
        attachment_data = gmail_service.get_attachment(
            message_id=email["id"],
            attachment_id=attachment["attachmentId"]
        )
        
        if attachment_data:
            # Convert PDF to text
            plain_text = pdf2text(attachment_data["data"])
            print(f"PDF content from {attachment['filename']}:")
            print(plain_text)
```

## Function Details

### html2text

```python
def html2text(html_content: str | bytes) -> str
```

Parameters:
- `html_content`: HTML content as string or base64 encoded bytes

Returns:
- Plain text content as string

Features:
- Automatically handles base64 encoded content
- Ignores links, images, and emphasis for cleaner output
- Preserves basic text structure and formatting

### pdf2text

```python
def pdf2text(pdf_content: bytes) -> str
```

Parameters:
- `pdf_content`: PDF content as base64 encoded bytes

Returns:
- Plain text content as string

Features:
- Processes multi-page PDFs
- Extracts text from all pages
- Handles base64 encoded PDF content from Gmail API

## Error Handling

Both functions handle common error cases:

- `html2text`:
  - Automatically detects and decodes base64 content
  - Handles UTF-8 encoding/decoding
  - Gracefully processes malformed HTML

- `pdf2text`:
  - Handles base64 decoding
  - Processes PDFs with multiple pages
  - Skips pages that don't contain extractable text

## Dependencies

Make sure you have the following packages installed:
- `html2text`
- `pdfplumber`

You can install them using pip:
```bash
pip install html2text pdfplumber
``` 