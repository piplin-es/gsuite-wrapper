
# GSuite Integration Library

This project is a fork of [mcp-gsuite](https://github.com/MarkusPfundstein/mcp-gsuite) that has been extensively rewritten to remove MCP bindings and provide a more streamlined, pure Python interface for Google Workspace (GSuite) services.

## Features

### Gmail Integration
- Search and query emails with flexible filters
- Retrieve complete email content with attachments
- Create and manage draft emails
- Reply to existing emails
- Handle email attachments efficiently
- Support for HTML and plain text email bodies

### Google Analytics Integration
- Access Google Analytics 4 data
- Generate various report types (URLs, Pages, Referrers)
- Custom metrics and dimensions support
- Flexible date range queries
- Export data to JSON format

### Multi-Account Management
- Support for multiple Google accounts
- OAuth2 authentication handling
- Account type categorization
- Custom metadata for accounts
- Secure credential storage

## Installation

```bash
pip install .
```

## Configuration

1. Create OAuth2 credentials in Google Cloud Console with required scopes:
   - Gmail: `https://mail.google.com/`
   - Analytics: `https://www.googleapis.com/auth/analytics.readonly`

2. Create `.gauth.json` in your working directory:
```json
{
    "web": {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "redirect_uris": ["http://localhost:4100/code"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}
```

3. Create `.accounts.json` to manage your accounts:
```json
{
    "accounts": [
        {
            "email": "your.email@example.com",
            "account_type": "personal",
            "extra_info": "Optional additional information about the account"
        }
    ]
}
```

## Usage Examples

### Gmail

```python
from mcp_gsuite.gmail import GmailService

# Initialize service
gmail = GmailService(user_id='your.email@example.com')

# Query unread emails
emails = gmail.query_emails(query='is:unread', max_results=10)
for email in emails:
    print(f"Subject: {email.subject}")
    print(f"From: {email.from_email}")
```

### Google Analytics

```python
from mcp_gsuite.analytics import check_analytics_data

# Get page views report
check_analytics_data(
    user_id="your.email@example.com",
    property_id="your_property_id",
    report_type="pages"
)
```

### Account Management

```python
from mcp_gsuite.account_manager import GoogleAccountManager

manager = GoogleAccountManager()

# Add new account
account = manager.setup_new_account(
    "your.email@example.com",
    extra_info="Primary account for analytics"
)

# List accounts
accounts = manager.list_accounts()
for account in accounts:
    print(f"Email: {account.email}, Type: {account.account_type}")
```

## Error Handling

The library includes comprehensive error handling and logging. All methods return `None` on failure and log appropriate error messages:

```python
email = gmail.get_email_by_id('some_id')
if email is None:
    print("Failed to retrieve email")
else:
    print(f"Retrieved email: {email.subject}")
```

## File Locations

- `.accounts.json`: Account information storage
- `.oauth2.{email}.json`: OAuth credentials for each account
- `.gauth.json`: OAuth client configuration

These locations can be customized using environment variables:
- `ACCOUNTS_FILE`: Path to accounts configuration
- `CREDENTIALS_DIR`: OAuth credentials directory
- `GAUTH_FILE`: OAuth client configuration path

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 