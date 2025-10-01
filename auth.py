"""
eBay API Authentication Module
Handles OAuth2 authentication and token management for eBay API
"""

import requests
import json
import base64
from urllib.parse import urlencode, parse_qs
import webbrowser
from typing import Dict, Optional

class eBayAuth:
    """Handles eBay OAuth2 authentication"""
    
    def __init__(self, app_id: str, cert_id: str, dev_id: str, redirect_uri: str):
        self.app_id = app_id
        self.cert_id = cert_id
        self.dev_id = dev_id
        self.redirect_uri = redirect_uri
        
        # eBay OAuth2 endpoints
        self.auth_url = 'https://auth.ebay.com/oauth2/authorize'
        self.token_url = 'https://api.ebay.com/identity/v1/oauth2/token'
        
        # Required scopes for listing management
        self.scopes = [
            'https://api.ebay.com/oauth/api_scope/sell.inventory',
            'https://api.ebay.com/oauth/api_scope/sell.account',
            'https://api.ebay.com/oauth/api_scope/sell.fulfillment'
        ]
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate authorization URL for user consent"""
        params = {
            'client_id': self.app_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'state': state or 'ebay_auth'
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access token"""
        # Prepare credentials for basic auth
        credentials = f"{self.app_id}:{self.cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to exchange code for token: {e}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        credentials = f"{self.app_id}:{self.cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope': ' '.join(self.scopes)
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh token: {e}")
    
    def get_user_consent(self) -> str:
        """Interactive method to get user consent and authorization code"""
        auth_url = self.get_authorization_url()
        
        print("Please visit the following URL to authorize the application:")
        print(auth_url)
        print("\nAfter authorization, you'll be redirected to a URL with a 'code' parameter.")
        print("Please copy the entire redirect URL and paste it here.")
        
        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            print("Browser opened automatically.")
        except:
            print("Could not open browser automatically. Please copy the URL above.")
        
        redirect_url = input("\nPaste the redirect URL here: ").strip()
        
        # Parse the authorization code from the redirect URL
        try:
            parsed_url = parse_qs(redirect_url.split('?')[1])
            if 'code' in parsed_url:
                return parsed_url['code'][0]
            else:
                raise ValueError("No authorization code found in URL")
        except (IndexError, KeyError, ValueError) as e:
            raise Exception(f"Invalid redirect URL format: {e}")
    
    def authenticate(self) -> Dict:
        """Complete authentication flow and return token data"""
        try:
            auth_code = self.get_user_consent()
            token_data = self.exchange_code_for_token(auth_code)
            
            print("Authentication successful!")
            print(f"Access Token: {token_data.get('access_token', 'N/A')[:20]}...")
            print(f"Token expires in: {token_data.get('expires_in', 'N/A')} seconds")
            
            return token_data
        except Exception as e:
            raise Exception(f"Authentication failed: {e}")
    
    @staticmethod
    def save_token_data(token_data: Dict, filename: str = 'ebay_token.json'):
        """Save token data to file for future use"""
        with open(filename, 'w') as f:
            json.dump(token_data, f, indent=2)
        print(f"Token data saved to {filename}")
    
    @staticmethod
    def load_token_data(filename: str = 'ebay_token.json') -> Optional[Dict]:
        """Load token data from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {filename}")
            return None