#!/usr/bin/env python3
"""
Utility script to reauthorize Google API access with updated scopes.
This script will revoke existing credentials and start a new authorization flow.
"""

import argparse
import json
import sys
import os
import httplib2
from src.mcp_gsuite import gauth
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser

# Global variable to store the authorization code
auth_code = None
auth_server = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code, auth_server
        
        url = urlparse(self.path)
        # Accept requests to the root path (with or without trailing slash)
        if url.path != "/" and url.path != "":
            print("Received request for invalid path")
            self.send_response(404)
            self.end_headers()
            return

        query = parse_qs(url.query)
        if "code" not in query:
            print("Received request without auth code")
            self.send_response(400)
            self.end_headers()
            return
        
        print("Received valid auth code")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("""
        <html>
        <head><title>Authorization Successful</title></head>
        <body>
        <h1>Authorization Successful!</h1>
        <p>You can close this window now and return to the terminal.</p>
        </body>
        </html>
        """.encode("utf-8"))
        self.wfile.flush()
        
        # Store the auth code
        auth_code = query["code"][0]
        
        # Shutdown the server
        threading.Thread(target=auth_server.shutdown).start()

def parse_args():
    parser = argparse.ArgumentParser(description='Reauthorize Google API access with updated scopes')
    parser.add_argument('--user-id', type=str, required=True, 
                        help='Email address of the Google account to reauthorize')
    parser.add_argument('--accounts-file', type=str, default='./.accounts.json',
                        help='Path to accounts configuration file')
    parser.add_argument('--gauth-file', type=str, default='./.gauth.json',
                        help='Path to client secrets file')
    parser.add_argument('--credentials-dir', type=str, default='.',
                        help='Directory to store OAuth2 credentials')
    return parser.parse_args()

def start_auth_server():
    global auth_server
    server_address = ('', 8080)
    auth_server = HTTPServer(server_address, OAuthCallbackHandler)
    auth_server.serve_forever()

def main():
    global auth_code
    
    # Parse command line arguments
    args = parse_args()
    
    # Set environment variables for configuration
    if args.accounts_file:
        os.environ['ACCOUNTS_FILE'] = args.accounts_file
    if args.gauth_file:
        os.environ['GAUTH_FILE'] = args.gauth_file
    if args.credentials_dir:
        os.environ['CREDENTIALS_DIR'] = args.credentials_dir
    
    # Check if the user exists in accounts
    accounts = gauth.get_account_info()
    account_emails = [account.email for account in accounts]
    
    if args.user_id not in account_emails:
        print(f"Error: User {args.user_id} not found in accounts file.")
        print(f"Available accounts: {', '.join(account_emails)}")
        sys.exit(1)
    
    # Check if credentials exist
    cred_file_path = gauth._get_credential_filename(user_id=args.user_id)
    if os.path.exists(cred_file_path):
        print(f"Found existing credentials for {args.user_id}.")
        
        # Ask for confirmation
        confirm = input(f"Are you sure you want to revoke and reauthorize access for {args.user_id}? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            sys.exit(0)
        
        # Delete the credentials file
        try:
            os.remove(cred_file_path)
            print(f"Deleted existing credentials file: {cred_file_path}")
        except Exception as e:
            print(f"Error deleting credentials file: {str(e)}")
            sys.exit(1)
    
    # Start the authorization flow
    try:
        # Start the auth server in a separate thread
        server_thread = threading.Thread(target=start_auth_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Get authorization URL
        auth_url = gauth.get_authorization_url(args.user_id, state={})
        print(f"Opening browser to authorize with the following URL:")
        print(auth_url)
        
        # Open the URL in the default browser
        webbrowser.open(auth_url)
        
        print("\nWaiting for authorization...")
        
        # Wait for the auth server to get the code
        server_thread.join()
        
        if not auth_code:
            print("Error: No authorization code received.")
            sys.exit(1)
        
        # Exchange code for credentials
        credentials = gauth.get_credentials(authorization_code=auth_code, state={})
        print("Authorization successful!")
        
        # Verify the scopes
        print("\nVerifying scopes...")
        if hasattr(credentials, 'scopes'):
            print("Authorized scopes:")
            for scope in credentials.scopes:
                print(f"  - {scope}")
            
            # Check for the Analytics scope
            analytics_scope = "https://www.googleapis.com/auth/analytics.readonly"
            if analytics_scope in credentials.scopes:
                print(f"\nSuccess! The {analytics_scope} scope is authorized.")
            else:
                print(f"\nWarning: The {analytics_scope} scope is not authorized.")
                print("You may need to check your OAuth2 configuration.")
        else:
            print("Could not verify scopes. Please check the credentials manually.")
        
    except Exception as e:
        print(f"Error during authorization: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 