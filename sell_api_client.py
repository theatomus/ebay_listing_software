"""
eBay Sell API Client Module
Handles communication with eBay Sell API (modern replacement for Trading API)
"""

import requests
import json
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime

class eBaySellAPIClient:
    """Client for eBay Sell API operations"""

    def __init__(self, access_token: str, marketplace_id: str = "EBAY_US"):
        self.access_token = access_token
        self.marketplace_id = marketplace_id

        # API endpoints
        self.base_url = 'https://api.ebay.com/sell'

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def _auth_headers(self) -> dict:
        """Get authentication headers for API calls"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _make_api_call(self, method: str, url: str, data: Optional[dict] = None, extra_headers: Optional[dict] = None) -> Tuple[bool, Dict, str]:
        """
        Make API call to eBay Sell API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: API endpoint URL
            data: Request payload data
            extra_headers: Additional headers to include

        Returns:
            Tuple of (success, response_dict, error_message)
        """

        headers = self._auth_headers()
        headers["X-EBAY-C-MARKETPLACE-ID"] = self.marketplace_id

        if extra_headers:
            headers.update(extra_headers)

        try:
            self.logger.info(f"Making {method} API call to {url}")

            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                if data is None:
                    response = requests.post(url, headers=headers, timeout=30)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                if data is None:
                    response = requests.put(url, headers=headers, timeout=30)
                else:
                    response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {}, f"Unsupported HTTP method: {method}"

            self.logger.info(f"API response status: {response.status_code}")

            if response.status_code in [200, 201, 204]:
                # Success responses
                if response.status_code == 204 or not response.text:
                    return True, {}, ""

                try:
                    response_dict = response.json()
                    return True, response_dict, ""
                except json.JSONDecodeError:
                    return True, {"message": "Success"}, ""

            else:
                # Error response
                try:
                    error_data = response.json()
                    error_msg = f"HTTP {response.status_code}: {error_data.get('message', response.text)}"
                except json.JSONDecodeError:
                    error_msg = f"HTTP {response.status_code}: {response.text}"

                self.logger.error(error_msg)
                return False, {}, error_msg

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg

    def create_inventory_item(self, sku: str, product_data: Dict, quantity: int = 1) -> Tuple[bool, Dict, str]:
        """
        Create or replace an inventory item

        Args:
            sku: Stock Keeping Unit identifier
            product_data: Product information including title, description, aspects, images
            quantity: Available quantity

        Returns:
            Tuple of (success, response_dict, error_message)
        """
        url = f"{self.base_url}/inventory/v1/inventory_item/{sku}"

        body = {
            "product": {
                "title": product_data.get("title", ""),
                "description": product_data.get("description", ""),
                "aspects": product_data.get("aspects", {}),
                "imageUrls": product_data.get("imageUrls", [])
            },
            "condition": product_data.get("condition", "NEW"),
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": quantity
                }
            }
        }

        headers = {"Content-Language": product_data.get("contentLanguage", "en-US")}

        return self._make_api_call("PUT", url, body, extra_headers=headers)

    def create_offer(self, sku: str, offer_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Create an offer for an inventory item

        Args:
            sku: Stock Keeping Unit identifier
            offer_data: Offer information including pricing, policies, scheduling

        Returns:
            Tuple of (success, response_dict, error_message)
        """
        url = f"{self.base_url}/inventory/v1/offer"

        required_fields = {
            "categoryId": offer_data.get("categoryId"),
            "merchantLocationKey": offer_data.get("merchantLocationKey"),
            "paymentPolicyId": offer_data.get("paymentPolicyId"),
            "fulfillmentPolicyId": offer_data.get("fulfillmentPolicyId"),
            "returnPolicyId": offer_data.get("returnPolicyId"),
        }

        missing = [field for field, value in required_fields.items() if not value]
        if missing:
            message = f"Missing required offer fields: {', '.join(missing)}"
            self.logger.error(message)
            return False, {}, message

        price_value = offer_data.get("price")
        if price_value is None:
            message = "Missing required offer field: price"
            self.logger.error(message)
            return False, {}, message

        body = {
            "sku": sku,
            "marketplaceId": self.marketplace_id,
            "format": offer_data.get("format", "FIXED_PRICE"),
            "availableQuantity": int(offer_data.get("availableQuantity", 1)),
            "categoryId": offer_data.get("categoryId"),
            "merchantLocationKey": offer_data.get("merchantLocationKey"),
            "listingDescription": offer_data.get("listingDescription", ""),
            "includeCatalogProductDetails": False,
            "itemAspects": offer_data.get("itemAspects", {}),
            "pricingSummary": {
                "price": {
                    "value": f"{price_value:.2f}" if isinstance(price_value, (int, float)) else str(price_value),
                    "currency": offer_data.get("currency", "USD")
                }
            },
            "listingPolicies": {
                "fulfillmentPolicyId": offer_data.get("fulfillmentPolicyId"),
                "paymentPolicyId": offer_data.get("paymentPolicyId"),
                "returnPolicyId": offer_data.get("returnPolicyId")
            }
        }

        if offer_data.get("quantityLimitPerBuyer"):
            body["quantityLimitPerBuyer"] = int(offer_data["quantityLimitPerBuyer"])

        if offer_data.get("bestOfferTerms"):
            body["bestOfferTerms"] = offer_data["bestOfferTerms"]

        if offer_data.get("storeCategoryNames"):
            body["storeCategoryNames"] = offer_data["storeCategoryNames"]

        if offer_data.get("listingStartDate"):
            body["listingStartDate"] = offer_data["listingStartDate"]

        if offer_data.get("listingDuration"):
            body["listingDuration"] = offer_data["listingDuration"]

        extra_headers = {"Content-Language": offer_data.get("contentLanguage", "en-US")}

        result = self._make_api_call("POST", url, body, extra_headers=extra_headers)
        success, response, error = result
        if success:
            echoed = response.get("listingStartDate") or response.get("listing", {}).get("listingStartDate")
            if echoed:
                self.logger.info(f"Offer acknowledged listingStartDate: {echoed}")
        return result

    def publish_offer(self, offer_id: str, start_date: Optional[str] = None) -> Tuple[bool, Dict, str]:
        """
        Publish an offer to make it live

        Args:
            offer_id: The offer ID to publish
            start_date: Optional ISO 8601 start date for scheduling

        Returns:
            Tuple of (success, response_dict, error_message)
        """
        url = f"{self.base_url}/inventory/v1/offer/{offer_id}/publish"

        return self._make_api_call("POST", url)

    def get_policies(self) -> Tuple[bool, Dict, str]:
        """
        Get business policies (payment, fulfillment, return)

        Returns:
            Tuple of (success, policies_dict, error_message)
        """
        url = f"{self.base_url}/account/v1/business_policy"

        success, response, error = self._make_api_call("GET", url)
        if success:
            return True, response, ""

        return False, {}, error

    def create_inventory_location(self, location_key: str, name: str, address: Dict) -> Tuple[bool, Dict, str]:
        """
        Create an inventory location (warehouse/fulfillment center)

        Args:
            location_key: Unique identifier for the location (your merchantLocationKey)
            name: Display name for the location
            address: Address dictionary with required fields

        Returns:
            Tuple of (success, response_dict, error_message)
        """
        url = f"{self.base_url}/inventory/v1/location/{location_key}"

        body = {
            "name": name,
            "merchantLocationStatus": "ENABLED",
            "locationTypes": ["WAREHOUSE"],
            "location": {
                "address": address
            }
        }

        return self._make_api_call("POST", url, body)

    def create_scheduled_listing(self, listing_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Create a scheduled listing using the Sell API pattern

        Args:
            listing_data: Complete listing information

        Returns:
            Tuple of (success, response_dict, error_message)
        """
        try:
            sku = listing_data.get("sku", f"LISTING_{int(datetime.now().timestamp())}")

            # Step 1: Create inventory item
            success, inventory_response, error = self.create_inventory_item(
                sku,
                listing_data.get("product", {}),
                listing_data.get("quantity", 1)
            )

            if not success:
                return False, {}, f"Failed to create inventory item: {error}"

            # Step 2: Create offer
            success, offer_response, error = self.create_offer(sku, listing_data.get("offer", {}))

            if not success:
                return False, {}, f"Failed to create offer: {error}"

            offer_id = offer_response.get("offerId")
            if not offer_id:
                return False, {}, "Offer created but offerId missing in response"

            publish_start = listing_data.get("publishStartDate")
            if start_date := listing_data.get("offer", {}).get("listingStartDate"):
                publish_start = start_date

            success, publish_response, error = self.publish_offer(offer_id, publish_start)

            if not success:
                return False, {}, f"Failed to publish offer: {error}"

            return True, {
                "sku": sku,
                "inventoryResponse": inventory_response,
                "offerResponse": offer_response,
                "publishResponse": publish_response
            }, ""

        except Exception as e:
            return False, {}, f"Error creating scheduled listing: {str(e)}"
