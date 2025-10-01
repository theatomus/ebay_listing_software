"""
Load configuration for eBay API from config.json.
Populate config.json with your credentials and policy IDs.
"""

import json
import os
from datetime import datetime, timedelta

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULTS = {
    "APP_ID": "YOUR_APP_ID",
    "CERT_ID": "YOUR_CERT_ID",
    "DEV_ID": "YOUR_DEV_ID",
    "USER_TOKEN": "YOUR_USER_TOKEN",
    "REDIRECT_URI": "YOUR_RUNAME",
    "EBAY_MARKETPLACE_ID": "EBAY_US",
    "PAYMENT_POLICY_ID": "YOUR_PAYMENT_POLICY_ID",
    "FULFILLMENT_POLICY_ID": "YOUR_FULFILLMENT_POLICY_ID",
    "RETURN_POLICY_ID": "YOUR_RETURN_POLICY_ID",
    "MERCHANT_LOCATION_KEY": "primary_warehouse"
}


def _load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULTS, f, indent=2)
        return DEFAULTS.copy()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = DEFAULTS.copy()
    merged.update(data)
    return merged


class eBayConfig:
    _cfg = _load_config()

    APP_ID = _cfg["APP_ID"]
    CERT_ID = _cfg["CERT_ID"]
    DEV_ID = _cfg["DEV_ID"]
    USER_TOKEN = _cfg["USER_TOKEN"]
    REDIRECT_URI = _cfg["REDIRECT_URI"]

    EBAY_MARKETPLACE_ID = _cfg["EBAY_MARKETPLACE_ID"]
    PAYMENT_POLICY_ID = _cfg["PAYMENT_POLICY_ID"]
    FULFILLMENT_POLICY_ID = _cfg["FULFILLMENT_POLICY_ID"]
    RETURN_POLICY_ID = _cfg["RETURN_POLICY_ID"]
    MERCHANT_LOCATION_KEY = _cfg["MERCHANT_LOCATION_KEY"]

    PRODUCTION_ENDPOINT = "https://api.ebay.com/ws/api.dll"
    SANDBOX_ENDPOINT = "https://api.sandbox.ebay.com/ws/api.dll"
    API_SITE_ID = "0"
    API_COMPATIBILITY_LEVEL = "967"

    DEFAULT_CURRENCY = "USD"
    DEFAULT_COUNTRY = "US"
    DEFAULT_DISPATCH_TIME_MAX = "3"

    LAPTOP_CATEGORY_ID = "111422"

    CONDITION_NEW = "1000"
    CONDITION_USED_EXCELLENT = "3000"
    CONDITION_USED_VERY_GOOD = "4000"
    CONDITION_USED_GOOD = "5000"

    LISTING_DURATION_7_DAYS = "Days_7"
    LISTING_DURATION_10_DAYS = "Days_10"
    LISTING_DURATION_GTC = "GTC"

    LISTING_TYPE_FIXED_PRICE = "FixedPriceItem"
    LISTING_TYPE_AUCTION = "Chinese"

    PAYMENT_METHOD_PAYPAL = "PayPal"

    SHIPPING_SERVICE_USPS_PRIORITY = "USPSPriority"
    SHIPPING_SERVICE_USPS_MEDIA = "USPSMedia"
    SHIPPING_SERVICE_FEDEX_HOME = "FedExHomeDelivery"

    RETURNS_ACCEPTED = "ReturnsAccepted"
    RETURNS_NOT_ACCEPTED = "ReturnsNotAccepted"
    REFUND_MONEY_BACK = "MoneyBack"
    REFUND_EXCHANGE = "Exchange"
    RETURNS_WITHIN_14_DAYS = "Days_14"
    RETURNS_WITHIN_30_DAYS = "Days_30"
    SHIPPING_COST_PAID_BY_BUYER = "Buyer"
    SHIPPING_COST_PAID_BY_SELLER = "Seller"

    @staticmethod
    def get_schedule_time(hours_from_now=24):
        schedule_time = datetime.utcnow() + timedelta(hours=hours_from_now)
        return schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    @staticmethod
    def get_minimum_schedule_time():
        return eBayConfig.get_schedule_time(hours_from_now=0.25)

    def validate_policies(self):
        missing = []
        if self.PAYMENT_POLICY_ID.startswith("YOUR_"):
            missing.append("PAYMENT_POLICY_ID")
        if self.FULFILLMENT_POLICY_ID.startswith("YOUR_"):
            missing.append("FULFILLMENT_POLICY_ID")
        if self.RETURN_POLICY_ID.startswith("YOUR_"):
            missing.append("RETURN_POLICY_ID")
        if self.MERCHANT_LOCATION_KEY.startswith("YOUR_"):
            missing.append("MERCHANT_LOCATION_KEY")
        return len(missing) == 0, missing

    def get_policy_config(self):
        return {
            "paymentPolicyId": self.PAYMENT_POLICY_ID,
            "fulfillmentPolicyId": self.FULFILLMENT_POLICY_ID,
            "returnPolicyId": self.RETURN_POLICY_ID,
            "merchantLocationKey": self.MERCHANT_LOCATION_KEY,
        }