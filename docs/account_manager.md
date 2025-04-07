# Google Account Manager

This document provides examples of how to use the Google Account Manager in a Python REPL environment.

## Basic Usage

First, import and create an instance of the account manager:

```python
from mcp_gsuite.account_manager import GoogleAccountManager
manager = GoogleAccountManager()
```

## Listing Accounts

To see all configured Google accounts:

```python
accounts = manager.list_accounts()
for account in accounts:
    print(f"Email: {account.email}, Type: {account.account_type}")
    if account.extra_info:
        print(f"Extra info: {account.extra_info}")
```

## Adding a New Account

To add a new Google account, use the `setup_new_account` method. This will:
1. Open your browser for Google OAuth authorization
2. Handle the callback automatically
3. Save the account credentials

You can provide additional context about the account using the `extra_info` parameter. This is useful for storing information about:
- Email usage patterns (e.g., "Primary support email", "Marketing communications")
- Main email languages (e.g., "Primary language: English")
- Gmail labels or categories (e.g., "Uses labels: Support, Marketing")
- Any other contextual information that helps identify the account's purpose

```python
try:
    # Basic account setup
    account = manager.setup_new_account("user@example.com")
    
    # Or with extra information
    account = manager.setup_new_account(
        "support@example.com",
        extra_info="Primary support email, English language, Uses labels: Support, Urgent"
    )
    print(f"Successfully added account: {account.email}")
except ValueError as e:
    print(f"Failed to add account: {e}")
```

## Removing an Account

To remove an account and its associated credentials:

```python
if manager.remove_account("user@example.com"):
    print("Account removed successfully")
else:
    print("Account not found")
```

## Checking Account Status

To check if an account exists and has valid credentials:

```python
email = "user@example.com"
if manager.is_account_authorized(email):
    print(f"Account {email} is authorized")
else:
    print(f"Account {email} is not authorized or doesn't exist")
```

## Getting Account Details

To get information about a specific account:

```python
account = manager.get_account("user@example.com")
if account:
    print(f"Email: {account.email}")
    print(f"Type: {account.account_type}")
    print(f"Extra info: {account.extra_info}")
else:
    print("Account not found")
```

## Complete Example

Here's a complete example showing how to manage an account with proper error handling and status verification:

```python
from mcp_gsuite.account_manager import GoogleAccountManager

def manage_account(email: str, extra_info: str = ""):
    manager = GoogleAccountManager()
    
    # Check if account exists
    if manager.get_account(email):
        print(f"Account {email} already exists")
        return
    
    try:
        # Add new account
        print(f"Setting up account for {email}...")
        account = manager.setup_new_account(email, extra_info=extra_info)
        print(f"Successfully added account: {account.email}")
        if extra_info:
            print(f"Extra info: {account.extra_info}")
        
        # Verify authorization
        if manager.is_account_authorized(email):
            print("Account is properly authorized")
        else:
            print("Warning: Account was added but not properly authorized")
            
    except ValueError as e:
        print(f"Error during account setup: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Usage example
manage_account(
    "support@example.com",
    extra_info="Primary support email, English language, Uses labels: Support, Urgent"
)
```

## Common Error Handling

When working with the account manager, you might encounter these common errors and their solutions:

1. **ValueError: "Account with email {email} already exists"**
   ```python
   try:
       account = manager.setup_new_account("existing@example.com")
   except ValueError as e:
       print(f"Error: {e}")
       # Remove the existing account first
       manager.remove_account("existing@example.com")
       # Try again
       account = manager.setup_new_account("existing@example.com")
   ```

2. **ValueError: "Failed to get authorization code from callback"**
   ```python
   try:
       account = manager.setup_new_account("user@example.com")
   except ValueError as e:
       if "Failed to get authorization code" in str(e):
           print("Authorization timed out or failed. Please try again.")
           print("Make sure you completed the authorization in your browser.")
   ```

3. **ValueError: "Failed to complete account setup"**
   ```python
   try:
       account = manager.setup_new_account("user@example.com")
   except ValueError as e:
       if "Failed to complete account setup" in str(e):
           print("OAuth flow failed. Check your credentials and permissions.")
           print("Make sure you have the correct OAuth scopes configured.")
   ```

## Troubleshooting

1. **Authorization Fails**
   - Make sure you're using the correct Google account
   - Check if you have the necessary permissions
   - Verify that the OAuth client is properly configured

2. **Account Already Exists**
   - Use `remove_account()` to remove the existing account first
   - Then try adding the account again

3. **Callback Issues**
   - Ensure port 8080 is available
   - Check if your browser can access localhost:8080
   - The callback server will timeout after 5 minutes (300 seconds)

4. **Credentials Issues**
   - Check if the credentials directory is writable
   - Verify that the `.gauth.json` file is properly configured
   - Make sure you have the required OAuth scopes

## File Locations

The account manager uses several files:
- `.accounts.json`: Stores account information
- `.oauth2.{email}.json`: Stores OAuth credentials for each account
- `.gauth.json`: Contains OAuth client configuration

These files can be configured using environment variables:
- `ACCOUNTS_FILE`: Path to accounts configuration file
- `CREDENTIALS_DIR`: Directory for OAuth credentials
- `GAUTH_FILE`: Path to OAuth client configuration 