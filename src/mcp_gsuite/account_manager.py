import logging
from typing import List, Optional, Tuple
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from .gauth import (
    AccountInfo,
    get_accounts_file,
    get_authorization_url,
    get_credentials,
    store_credentials,
    get_stored_credentials,
    _get_credential_filename,
)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""
    
    # Class variable to store the callback data
    callback_data = None
    
    def do_GET(self):
        """Handle GET request to the callback URL."""
        # Parse the URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Store the callback data
        OAuthCallbackHandler.callback_data = {
            'code': query_params.get('code', [None])[0],
            'state': query_params.get('state', [None])[0],
            'error': query_params.get('error', [None])[0]
        }
        
        # Send response to the browser
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
            <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
            </html>
        """)
    
    def log_message(self, format, *args):
        """Suppress logging of HTTP requests."""
        return


class GoogleAccountManager:
    """Manages Google OAuth accounts for the application.
    
    This class provides CRUD operations for managing Google OAuth accounts,
    including handling the OAuth flow for new accounts.
    """
    
    def __init__(self):
        self.accounts_file = get_accounts_file()
        self._ensure_accounts_file_exists()
    
    def _ensure_accounts_file_exists(self):
        """Ensure the accounts file exists with proper structure."""
        if not os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'w') as f:
                json.dump({"accounts": []}, f, indent=2)
    
    def _load_accounts(self) -> List[AccountInfo]:
        """Load all accounts from the accounts file."""
        with open(self.accounts_file) as f:
            data = json.load(f)
            return [AccountInfo.model_validate(acc) for acc in data.get("accounts", [])]
    
    def _save_accounts(self, accounts: List[AccountInfo]):
        """Save accounts to the accounts file."""
        with open(self.accounts_file, 'w') as f:
            json.dump({"accounts": [acc.model_dump() for acc in accounts]}, f, indent=2)
    
    def list_accounts(self) -> List[AccountInfo]:
        """List all configured Google accounts."""
        return self._load_accounts()
    
    def get_account(self, email: str) -> Optional[AccountInfo]:
        """Get account information for a specific email."""
        accounts = self._load_accounts()
        for account in accounts:
            if account.email == email:
                return account
        return None
    
    def add_account(self, email: str, account_type: str, extra_info: str = "") -> AccountInfo:
        """Add a new Google account.
        
        Args:
            email: The email address of the Google account
            account_type: Type of the account (e.g., "user", "service")
            extra_info: Additional information about the account
            
        Returns:
            AccountInfo: The created account information
            
        Raises:
            ValueError: If account with the email already exists
        """
        if self.get_account(email):
            raise ValueError(f"Account with email {email} already exists")
        
        account = AccountInfo(email=email, account_type=account_type, extra_info=extra_info)
        accounts = self._load_accounts()
        accounts.append(account)
        self._save_accounts(accounts)
        return account
    
    def remove_account(self, email: str) -> bool:
        """Remove a Google account and its associated credentials.
        
        Args:
            email: The email address of the account to remove
            
        Returns:
            bool: True if account was removed, False if not found
        """
        accounts = self._load_accounts()
        original_length = len(accounts)
        accounts = [acc for acc in accounts if acc.email != email]
        
        if len(accounts) == original_length:
            return False
        
        # Remove the account from the accounts file
        self._save_accounts(accounts)
        
        # Remove the OAuth credentials file
        try:
            cred_file_path = _get_credential_filename(user_id=email)
            if os.path.exists(cred_file_path):
                os.remove(cred_file_path)
                logging.info(f"Removed credentials file: {cred_file_path}")
        except Exception as e:
            logging.warning(f"Failed to remove credentials file: {e}")
        
        return True
    
    def _handle_oauth_callback(self, timeout: int = 300) -> Tuple[Optional[str], Optional[str]]:
        """Start a temporary HTTP server to handle the OAuth callback.
        
        Args:
            timeout: Maximum time to wait for the callback in seconds
            
        Returns:
            Tuple[Optional[str], Optional[str]]: Tuple of (authorization_code, state)
        """
        # Reset the callback data
        OAuthCallbackHandler.callback_data = None
        
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        server.timeout = timeout
        
        try:
            while True:
                server.handle_request()
                if OAuthCallbackHandler.callback_data:
                    if OAuthCallbackHandler.callback_data['error']:
                        raise ValueError(f"OAuth error: {OAuthCallbackHandler.callback_data['error']}")
                    return OAuthCallbackHandler.callback_data['code'], OAuthCallbackHandler.callback_data['state']
        finally:
            server.server_close()
    
    def wait_for_oauth_callback(self, email: str, timeout: int = 300) -> AccountInfo:
        """Wait for OAuth callback and complete account setup.
        
        This method will:
        1. Start a temporary HTTP server to handle the callback
        2. Wait for the callback
        3. Complete the account setup once callback is received
        
        Args:
            email: The email address of the account to authorize
            timeout: Maximum time to wait for the callback in seconds
            
        Returns:
            AccountInfo: The created account information
            
        Raises:
            ValueError: If account already exists or OAuth flow fails
        """
        if self.get_account(email):
            raise ValueError(f"Account with email {email} already exists")
            
        try:
            code, state = self._handle_oauth_callback(timeout)
            if not code or not state:
                raise ValueError("Failed to get authorization code from callback")
            
            # Complete the account setup
            return self.complete_account_setup(email, code, state)
        except Exception as e:
            logging.error(f"Failed to complete account setup: {e}")
            raise ValueError(f"Failed to complete account setup: {str(e)}")
    
    def get_authorization_url_for_new_account(self, email: str, state: str = None) -> str:
        """Get the authorization URL for setting up a new account.
        
        Args:
            email: The email address of the account to authorize
            state: Optional state parameter for the OAuth flow
            
        Returns:
            str: The authorization URL
        """
        if state is None:
            state = email  # Use email as state for simplicity
        return get_authorization_url(email, state)
    
    def complete_account_setup(self, email: str, authorization_code: str, state: str) -> AccountInfo:
        """Complete the OAuth setup for a new account.
        
        Args:
            email: The email address of the account
            authorization_code: The authorization code from the OAuth flow
            state: The state parameter used in the authorization URL
            
        Returns:
            AccountInfo: The created account information
            
        Raises:
            ValueError: If account already exists or OAuth flow fails
        """
        if self.get_account(email):
            raise ValueError(f"Account with email {email} already exists")
        
        try:
            credentials = get_credentials(authorization_code, state)
            # If we get here, the OAuth flow was successful
            account = self.add_account(email, "user")
            return account
        except Exception as e:
            logging.error(f"Failed to complete account setup: {e}")
            raise ValueError(f"Failed to complete account setup: {str(e)}")
    
    def is_account_authorized(self, email: str) -> bool:
        """Check if an account has valid OAuth credentials.
        
        Args:
            email: The email address of the account
            
        Returns:
            bool: True if account has valid credentials, False otherwise
        """
        if not self.get_account(email):
            return False
        return get_stored_credentials(user_id=email) is not None 