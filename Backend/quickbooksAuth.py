import os
import json
import secrets
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# QuickBooks Online OAuth settings
QUICKBOOKS_CLIENT_ID = os.getenv('QUICKBOOKS_CLIENT_ID')
QUICKBOOKS_CLIENT_SECRET = os.getenv('QUICKBOOKS_CLIENT_SECRET')
QUICKBOOKS_SANDBOX = os.getenv('QUICKBOOKS_SANDBOX', 'true').lower() == 'true'
REDIRECT_URI = 'http://localhost:8000/quickbooks/callback'
SCOPE = 'com.intuit.quickbooks.accounting'

# Token storage
TOKEN_FILE = 'quickbooks_token.json'

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the callback URL
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Handle non-callback requests
        if not self.path.startswith('/quickbooks/callback'):
            self.send_response(404)
            self.end_headers()
            self.wfile.write("Not found".encode())
            return
        
        # Extract authorization code and state
        auth_code = params.get('code', [None])[0]
        state = params.get('state', [None])[0] 
        realm_id = params.get('realmId', [None])[0]
        error = params.get('error', [None])[0]
        
        if error:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Authorization failed: {error}".encode())
            self.server.auth_result = {'error': error}
            return
            
        if not auth_code or not realm_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("Missing authorization code or realm ID".encode())
            self.server.auth_result = {'error': 'Missing parameters'}
            return
            
        # Exchange code for tokens
        try:
            tokens = exchange_code_for_tokens(auth_code, realm_id)
            self.send_response(200)
            self.end_headers()
            self.wfile.write("QuickBooks connected successfully! You can close this window.".encode())
            self.server.auth_result = tokens
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Token exchange failed: {str(e)}".encode())
            self.server.auth_result = {'error': str(e)}
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

def get_basic_auth_header():
    """Generate basic auth header for token requests"""
    credentials = f"{QUICKBOOKS_CLIENT_ID}:{QUICKBOOKS_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return encoded_credentials

def exchange_code_for_tokens(auth_code, realm_id):
    """Exchange authorization code for access and refresh tokens"""
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {get_basic_auth_header()}'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        token_data['realm_id'] = realm_id
        return token_data
    else:
        raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")

def refresh_access_token(refresh_token):
    """Refresh the access token using refresh token"""
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {get_basic_auth_header()}'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")

def load_stored_tokens():
    """Load stored tokens from file"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def save_tokens(tokens):
    """Save tokens to file"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

def main():
    """Main QuickBooks OAuth flow - similar to Gmail auth"""
    print("QuickBooks Online OAuth Authentication")
    print("=" * 40)
    
    if not QUICKBOOKS_CLIENT_ID or not QUICKBOOKS_CLIENT_SECRET:
        print("Error: QUICKBOOKS_CLIENT_ID and QUICKBOOKS_CLIENT_SECRET must be set in .env file")
        return None
    
    # Check for existing valid tokens
    existing_tokens = load_stored_tokens()
    if existing_tokens:
        print("Found existing tokens")
        
        # Check if tokens are still valid by trying to refresh
        try:
            if 'refresh_token' in existing_tokens:
                print("Refreshing tokens...")
                refreshed = refresh_access_token(existing_tokens['refresh_token'])
                refreshed['realm_id'] = existing_tokens['realm_id']
                save_tokens(refreshed)
                print("Tokens refreshed successfully")
                return refreshed
        except Exception as e:
            print(f" Token refresh failed: {e}")
            print("Starting new authorization flow...")
    
    # Generate state for security
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL
    auth_params = {
        'client_id': QUICKBOOKS_CLIENT_ID,
        'scope': SCOPE,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'access_type': 'offline',
        'state': state
    }
    
    auth_url = f"https://appcenter.intuit.com/connect/oauth2?{urlencode(auth_params)}"
    
    print(f"Opening authorization URL in browser...")
    print(f"URL: {auth_url}")
    
    # Start local server to handle callback (same as Gmail pattern)
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    server.auth_result = None
    
    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("Waiting for authorization...")
    print("(Complete the authorization in your browser)")
    
    # Wait for callback
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while server.auth_result is None and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    # Stop server
    server.shutdown()
    server.server_close()
    
    if server.auth_result is None:
        print("Authorization timed out")
        return None
    
    if 'error' in server.auth_result:
        print(f"Authorization failed: {server.auth_result['error']}")
        return None
    
    # Save tokens
    tokens = server.auth_result
    save_tokens(tokens)
    
    print("QuickBooks Online authentication successful!")
    print(f"Company ID: {tokens.get('realm_id')}")
    print(f"Tokens saved to: {TOKEN_FILE}")
    
    return tokens

if __name__ == "__main__":
    result = main()
    if result:
        print("\nNext steps:")
        print("1. Tokens are saved and ready to use")
        print("2. Import quickbooks_service.py to make API calls")
        print("3. Tokens will auto-refresh when needed") 