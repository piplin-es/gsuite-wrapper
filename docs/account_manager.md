# Google Account Manager

This document provides examples of how to use the Google Account Manager in a Python REPL environment.

## Basic Usage

First, import and create an instance of the account manager:

```python
from mcp_gsuite.account_manager import GoogleAccountManager
manager = GoogleAccountManager()
```

This documentation focuses on REPL usage, which provides better control over the OAuth flow and account management process.

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

In a REPL environment, you can add a new Google account using a two-step process that gives you more control over the OAuth flow:

```python
from mcp_gsuite.account_manager import GoogleAccountManager
manager = GoogleAccountManager()

# Step 1: Get the authorization URL
email = "user@example.com"
auth_url = manager.get_authorization_url_for_new_account(email)
print(f"Please visit this URL in your browser: {auth_url}")

# Step 2: After you've opened the URL, wait for the OAuth callback
try:
    # Default timeout is 5 minutes (300 seconds)
    account = manager.wait_for_oauth_callback(email)
    print(f"Successfully added account: {account.email}")
except ValueError as e:
    print(f"Failed to add account: {e}")
```

This split approach is particularly useful in REPL environments because it:
- Allows you to get the URL first and ensure it's valid
- Gives you time to open the URL in your browser
- Lets you start the callback server only when you're ready
- Provides better control over the flow and error handling

The process works as follows:
1. Call `get_authorization_url_for_new_account()` to get the Google OAuth URL
2. Open the URL in your browser
3. When ready to proceed, call `wait_for_oauth_callback()` to start the temporary server
4. Complete the Google OAuth flow in your browser
5. The callback will be automatically handled and the account will be set up

### Error Handling and Troubleshooting

Here are common scenarios you might encounter and how to handle them:

1. **Account Already Exists**
   ```python
   try:
       account = manager.wait_for_oauth_callback("existing@example.com")
   except ValueError as e:
       if "already exists" in str(e):
           # Remove the existing account first
           manager.remove_account("existing@example.com")
           # Get a new authorization URL and try again
           auth_url = manager.get_authorization_url_for_new_account("existing@example.com")
           print(f"Please visit: {auth_url}")
           account = manager.wait_for_oauth_callback("existing@example.com")
   ```

2. **Authorization Timeout**
   ```python
   try:
       # You can adjust the timeout if needed (e.g., 10 minutes)
       account = manager.wait_for_oauth_callback("user@example.com", timeout=600)
   except ValueError as e:
       if "Failed to get authorization code" in str(e):
           print("Authorization timed out. Please try again with a fresh URL:")
           auth_url = manager.get_authorization_url_for_new_account("user@example.com")
           print(f"New URL: {auth_url}")
   ```

3. **Network or Server Issues**
   ```python
   try:
       account = manager.wait_for_oauth_callback("user@example.com")
   except Exception as e:
       print("Server or network error. Make sure:")
       print("- Port 8080 is available")
       print("- Your browser can access localhost:8080")
       print("- You have a working internet connection")
   ```

### Important Considerations

- **Authorization URLs**: Always use a fresh URL if the previous attempt failed
- **Timeouts**: Default timeout is 5 minutes, but you can adjust it using the `timeout` parameter
- **Port Usage**: The callback server requires port 8080 to be available
- **Credentials**: Make sure you have proper permissions for storing credentials

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

def manage_account(email: str):
    manager = GoogleAccountManager()
    
    # Check if account exists
    if manager.get_account(email):
        print(f"Account {email} already exists")
        return
    
    try:
        # Step 1: Get authorization URL
        print(f"Getting authorization URL for {email}...")
        auth_url = manager.get_authorization_url_for_new_account(email)
        print(f"\nPlease visit this URL in your browser:")
        print(f"{auth_url}\n")
        
        # Step 2: Wait for callback
        print("Waiting for OAuth callback (timeout: 5 minutes)...")
        account = manager.wait_for_oauth_callback(email)
        print(f"Successfully added account: {account.email}")
        
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
manage_account("support@example.com")
```

## File Locations

The account manager uses several files:
- `.accounts.json`: Stores basic account information (email, type, extra info)
- `.oauth2.{email}.json`: Stores OAuth credentials for each account (created during authorization)
- `.gauth.json`: Contains OAuth client configuration (required for authorization)

These files are managed automatically by the account manager. Their locations can be configured using environment variables:
- `ACCOUNTS_FILE`: Path to accounts configuration file
- `CREDENTIALS_DIR`: Directory for storing OAuth credentials
- `GAUTH_FILE`: Path to OAuth client configuration file

Note: Make sure these files and directories have appropriate read/write permissions for your application. 