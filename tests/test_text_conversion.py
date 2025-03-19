import pytest
import os
import traceback
from mcp_gsuite.gmail import GmailService
from mcp_gsuite.text_conversion import html2text, pdf2text
from googleapiclient.errors import HttpError

# Set up credentials
os.environ['CREDENTIALS_DIR'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['ACCOUNTS_FILE'] = os.path.join(os.environ['CREDENTIALS_DIR'], '.accounts.json')
os.environ['GAUTH_FILE'] = os.path.join(os.environ['CREDENTIALS_DIR'], '.gauth.json')

@pytest.fixture
def gmail_service():
    """Create a GmailService instance for testing."""
    return GmailService("gleb@lynxtrading.com")

def test_html_conversion(gmail_service):
    """Test HTML to text conversion using a real email."""
    email_id = "195a418ec25193e4"
    
    try:
        # Get the email content
        email, _ = gmail_service.get_email_by_id_with_attachments(email_id)
        
        if email is None:
            print("\nFailed to retrieve email. Check if:")
            print("1. The email ID is correct")
            print("2. The credentials are properly set up")
            print("3. The email exists in the inbox")
            pytest.skip("Failed to retrieve email")
            
        print("\nOriginal Email Body:")
        print("-" * 80)
        print(email['body'][:1000] + "..." if len(email['body']) > 1000 else email['body'])
        print("-" * 80)
            
        # Convert HTML to text
        text = html2text(email['body'])
        
        # Basic assertions
        assert isinstance(text, str)
        assert len(text) > 0
        
        print("\nHTML Conversion Result:")
        print("-" * 80)
        print(text[:1000] + "..." if len(text) > 1000 else text)
        print("-" * 80)
        print(f"Total length: {len(text)} characters")
        
    except HttpError as e:
        print(f"\nGmail API Error: {str(e)}")
        print("Response content:", e.content)
        print("Traceback:")
        print(traceback.format_exc())
        pytest.skip(f"Skipping test due to Gmail API error: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        pytest.fail(f"Test failed with error: {str(e)}")

def test_pdf_conversion(gmail_service):
    """Test PDF to text conversion using a real email with PDF attachment."""
    email_id = "195a418ec25193e4"
    
    try:
        # Get the email content
        email, attachments = gmail_service.get_email_by_id_with_attachments(email_id)
        
        if email is None:
            print("\nFailed to retrieve email. Check if:")
            print("1. The email ID is correct")
            print("2. The credentials are properly set up")
            print("3. The email exists in the inbox")
            pytest.skip("Failed to retrieve email")
            
        print("\nEmail Subject:", email.get('subject', 'No subject'))
        print("Email From:", email.get('from', 'No sender'))
        print("-" * 80)
            
        # Find the PDF attachment
        pdf_attachment = None
        for part_id, attachment in attachments.items():
            if attachment.get('mimeType') == 'application/pdf':
                print(f"\nFound PDF attachment: {attachment.get('filename', 'unnamed.pdf')}")
                # Get the actual attachment data
                attachment_data = gmail_service.get_attachment(email_id, attachment['attachmentId'])
                if attachment_data:
                    pdf_attachment = attachment_data
                    break
        
        if pdf_attachment is None:
            print("\nNo PDF attachment found. Available attachments:")
            for part_id, attachment in attachments.items():
                print(f"- {attachment.get('filename', 'unnamed')} ({attachment.get('mimeType', 'unknown type')})")
            pytest.skip("No PDF attachment found in the test email")
        
        # Convert PDF to text
        text = pdf2text(pdf_attachment['data'])
        
        # Basic assertions
        assert isinstance(text, str)
        assert len(text) > 0
        
        print("\nPDF Conversion Result:")
        print("-" * 80)
        print(text[:1000] + "..." if len(text) > 1000 else text)
        print("-" * 80)
        print(f"Total length: {len(text)} characters")
        
    except HttpError as e:
        print(f"\nGmail API Error: {str(e)}")
        print("Response content:", e.content)
        print("Traceback:")
        print(traceback.format_exc())
        pytest.skip(f"Skipping test due to Gmail API error: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        pytest.fail(f"Test failed with error: {str(e)}")

def test_html2text_with_base64():
    """Test html2text function with base64 encoded content."""
    # Example HTML content
    html_content = """
    <html>
        <body>
            <h1>Test Heading</h1>
            <p>This is a test paragraph.</p>
        </body>
    </html>
    """
    
    # Convert to base64
    import base64
    base64_content = base64.b64encode(html_content.encode('utf-8'))
    
    # Test conversion
    text = html2text(base64_content)
    
    assert isinstance(text, str)
    assert "Test Heading" in text
    assert "test paragraph" in text

def test_pdf2text_with_invalid_data():
    """Test pdf2text function with invalid data."""
    with pytest.raises(Exception):
        pdf2text(b"invalid pdf data") 