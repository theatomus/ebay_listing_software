#!/usr/bin/env python3
"""
eBay Scheduled Listing Setup and Run Script
Helps configure policies and run the modern Sell API application
"""

import json
import os
import shutil
import subprocess
import time
from typing import Optional

import requests

try:
    from config import eBayConfig
except ImportError:
    eBayConfig = None

NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"
DEFAULT_NGROK_PORT = 80
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

PLACEHOLDERS = {
    "APP_ID": "YOUR_APP_ID",
    "CERT_ID": "YOUR_CERT_ID",
    "DEV_ID": "YOUR_DEV_ID",
    "USER_TOKEN": "YOUR_USER_TOKEN",
    "REDIRECT_URI": "YOUR_RUNAME",
    "PAYMENT_POLICY_ID": "YOUR_PAYMENT_POLICY_ID",
    "FULFILLMENT_POLICY_ID": "YOUR_FULFILLMENT_POLICY_ID",
    "RETURN_POLICY_ID": "YOUR_RETURN_POLICY_ID",
    "MERCHANT_LOCATION_KEY": "YOUR_MERCHANT_LOCATION_KEY",
}

DEFAULT_PUBLIC_URL = None


def _is_config_ready() -> bool:
    if eBayConfig is None:
        return False

    for attr, placeholder in PLACEHOLDERS.items():
        value = getattr(eBayConfig, attr, "")
        if not value or placeholder in value:
            return False
    return True


def _prompt_user_to_fill_config():
    print("❌ config.json is missing required values.")
    print("   Edit config.json and fill in:")
    for attr in PLACEHOLDERS:
        print(f"   - {attr}")
    print("   -> ", os.path.abspath(CONFIG_PATH))
    print("   After updating, run this script again.")


def _fetch_ngrok_tunnel(port: int) -> Optional[str]:
    try:
        response = requests.get(NGROK_API_URL, timeout=2)
        response.raise_for_status()
        data = response.json()
        for tunnel in data.get("tunnels", []):
            addr = str(tunnel.get("config", {}).get("addr", ""))
            if addr.endswith(f":{port}") or addr.endswith(f"localhost:{port}"):
                return tunnel.get("public_url")
    except requests.RequestException:
        return None
    return None


def ensure_ngrok_running(port: int = DEFAULT_NGROK_PORT) -> Optional[str]:
    if not shutil.which("ngrok"):
        print("❌ ngrok command not found.")
        print("   Install from https://ngrok.com/download and ensure it is on your PATH.")
        print("   After installing, re-run this setup script.")
        return None

    existing_tunnel = _fetch_ngrok_tunnel(port)
    if existing_tunnel:
        print(f"✅ ngrok tunnel already running: {existing_tunnel}")
        return existing_tunnel

    print(f"ℹ️ Starting ngrok tunnel on http://localhost:{port}/")
    creation_flag = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    try:
        subprocess.Popen([
            "ngrok",
            "http",
            str(port)
        ], creationflags=creation_flag)
    except OSError as exc:
        print(f"❌ Failed to launch ngrok automatically: {exc}")
        print("   Run this manually in a separate terminal: ngrok http 80")
        return None

    for _ in range(10):
        time.sleep(1)
        tunnel = _fetch_ngrok_tunnel(port)
        if tunnel:
            print(f"✅ ngrok tunnel established: {tunnel}")
            print("   Leave the ngrok window running while you use this tool.")
            return tunnel

    print("❌ Could not verify ngrok tunnel. Please start it manually with 'ngrok http 80'.")
    return None


def print_ngrok_setup_help(public_url: Optional[str]):
    print("\nDeveloper Settings Checklist")
    print("=" * 30)
    if public_url:
        callback = f"{public_url}/oauth-callback"
        print(f"Auth accepted URL : {callback}")
        print("Auth declined URL : https://auth.ebay.com/oauth2/ThirdPartyAuthSucessFailure?isAuthSuccessful=false")
        print("Privacy policy URL: https://yourdomain.com/privacy (required in production)")
        print("Hint: Update the eBay Developer Console any time the ngrok URL changes.")
    else:
        print("Start ngrok and update your eBay Developer Console with your HTTPS callback:")
        print("  1. Run: ngrok http 80")
        print("  2. Copy the HTTPS forwarding URL -> Your auth accepted URL (add /oauth-callback)")
        print("  3. Keep the ngrok session active while using the tool")
        print("  4. Update config.json REDIRECT_URI with your RuName if needed")
    print("=" * 30)


def check_policy_configuration():
    if eBayConfig is None:
        _prompt_user_to_fill_config()
        return False

    print("=" * 60)
    print("eBay Policy Configuration Check")
    print("=" * 60)

    required = {
        "PAYMENT_POLICY_ID": eBayConfig.PAYMENT_POLICY_ID,
        "FULFILLMENT_POLICY_ID": eBayConfig.FULFILLMENT_POLICY_ID,
        "RETURN_POLICY_ID": eBayConfig.RETURN_POLICY_ID,
        "MERCHANT_LOCATION_KEY": eBayConfig.MERCHANT_LOCATION_KEY,
    }

    missing = [name for name, value in required.items() if not value or 'YOUR_' in value]

    if not missing:
        print("✅ All required policies are configured!")
        return True

    print("❌ Missing required policy configuration:")
    for policy in missing:
        print(f"  - {policy}")

    print("\nTo configure your policies:")
    print("1. Go to eBay Seller Hub: https://www.ebay.com/sh/landing")
    print("2. Account Settings > Business Policies")
    print("3. Find the IDs for payment, fulfillment/shipping, return policies")
    print("4. For merchant location key, use Shipping labels > Manage locations")

    print("\nUpdate config.json with those values and run this script again.")
    return False


def main():
    print("eBay Scheduled Listing - Modern Sell API Setup")
    print("=" * 60)

    if not _is_config_ready():
        _prompt_user_to_fill_config()
        return

    public_url = ensure_ngrok_running() or DEFAULT_PUBLIC_URL
    print_ngrok_setup_help(public_url)

    if not check_policy_configuration():
        print("\nPlease configure your policies first, then run this script again.")
        return

    print("\n" + "=" * 60)
    print("Running eBay Scheduled Listing Application")
    print("=" * 60)

    try:
        from main_sell_api import main as run_app
        run_app()
    except ImportError as e:
        print(f"❌ Error importing main application: {e}")
        print("Make sure all required files are in the same directory.")
        return
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return


if __name__ == "__main__":
    main()
