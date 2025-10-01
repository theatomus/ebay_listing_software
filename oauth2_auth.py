"""
eBay OAuth2 Authentication Module
Handles OAuth2 authentication flow for eBay Sell API
"""

import requests
import json
import time
import os
import webbrowser
from typing import Optional, Dict
import logging
import base64
from urllib.parse import urlencode, parse_qs

class eBayOAuth2Auth:
    """OAuth2 authentication for eBay Sell API"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes

        # OAuth2 endpoints
        self.authorization_url = "https://auth.ebay.com/oauth2/authorize"
        self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def get_authorization_url(self) -> str:
        """
        Generate the authorization URL for user consent

        Returns:
            Authorization URL string
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": "authenticated"
        }

        return f"{self.authorization_url}?{urlencode(params)}"

    def authenticate_interactive(self) -> Optional[Dict]:
        """
        Perform interactive OAuth2 authentication flow

        Returns:
            Token data dictionary or None if failed
        """
        try:
            self.logger.info("Starting interactive OAuth2 authentication...")

            # Generate authorization URL
            auth_url = self.get_authorization_url()
            print(f"\nPlease visit the following URL to authorize this application:")
            print(f"{auth_url}")

            # Try to open browser automatically
            try:
                webbrowser.open(auth_url)
                print("\nIf the browser didn't open automatically, please copy and paste the URL above.")
            except Exception:
                pass

            # Get authorization code from user
            print("\nAfter authorization, eBay will redirect you to a URL.")
            print("Please paste the full redirect URL here (or just the 'code' parameter value):")

            redirect_response = input("> ").strip()

            # Extract authorization code
            if "code=" in redirect_response:
                code = parse_qs(redirect_response.split("?", 1)[1])["code"][0]
            else:
                code = redirect_response

            if not code:
                self.logger.error("No authorization code received")
                return None

            # Exchange code for tokens
            return self._exchange_code_for_tokens(code)

        except Exception as e:
            self.logger.error(f"OAuth2 authentication failed: {e}")
            return None

    def _exchange_code_for_tokens(self, code: str) -> Optional[Dict]:
        """
        Exchange authorization code for access and refresh tokens

        Args:
            code: Authorization code from eBay

        Returns:
            Token data dictionary or None if failed
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._basic_auth_header()}"
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        try:
            self.logger.info("Exchanging authorization code for tokens...")

            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            self.logger.info("Successfully obtained tokens")

            # Add timestamp for token tracking
            token_data["obtained_at"] = int(time.time())

            return token_data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Token exchange failed: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Error response: {e.response.text}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh an expired access token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token or None if failed
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._basic_auth_header()}"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(self.scopes)
        }

        try:
            self.logger.info("Refreshing access token...")

            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            # Save the new refresh token if provided
            if "refresh_token" in token_data:
                self._save_tokens(token_data)

            self.logger.info("Successfully refreshed access token")
            return token_data.get("access_token")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Token refresh failed: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Error response: {e.response.text}")
            return None

    def _save_tokens(self, token_data: Dict):
        """Save tokens to a file for persistence"""
        try:
            with open("ebay_tokens.json", "w") as f:
                json.dump(token_data, f, indent=2)
            self.logger.info("Tokens saved to ebay_tokens.json")
        except Exception as e:
            self.logger.warning(f"Failed to save tokens: {e}")

    def load_tokens(self) -> Optional[Dict]:
        """Load tokens from file"""
        try:
            if os.path.exists("ebay_tokens.json"):
                with open("ebay_tokens.json", "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load tokens: {e}")

        return None

    def is_token_valid(self, token_data: Dict) -> bool:
        """
        Check if the access token is still valid

        Args:
            token_data: Token data dictionary

        Returns:
            True if token is valid, False otherwise
        """
        if not token_data or "access_token" not in token_data:
            return False

        # Check expiration time
        expires_in = token_data.get("expires_in")
        obtained_at = token_data.get("obtained_at")

        if not expires_in or not obtained_at:
            return False

        # Add 5 minute buffer for token expiration
        current_time = int(time.time())
        expiration_time = obtained_at + expires_in - 300  # 5 minute buffer

        return current_time < expiration_time

    def get_valid_access_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary

        Returns:
            Valid access token or None if authentication failed
        """
        # Try to load existing tokens
        token_data = self.load_tokens()

        if not token_data:
            self.logger.info("No existing tokens found, starting authentication...")
            token_data = self.authenticate_interactive()

            if not token_data:
                return None

            # Save the tokens
            self._save_tokens(token_data)

        # Check if access token is still valid
        if not self.is_token_valid(token_data):
            self.logger.info("Access token expired, attempting refresh...")

            refresh_token = token_data.get("refresh_token")
            if not refresh_token:
                self.logger.error("No refresh token available")
                return None

            new_access_token = self.refresh_access_token(refresh_token)
            if new_access_token:
                token_data["access_token"] = new_access_token
                token_data["obtained_at"] = int(time.time())
                self._save_tokens(token_data)
                return new_access_token
            else:
                self.logger.error("Failed to refresh token, need re-authentication")
                return None

        return token_data.get("access_token")

    def _basic_auth_header(self) -> str:
        creds = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return base64.b64encode(creds).decode("utf-8")
