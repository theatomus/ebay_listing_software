"""
Main Application Module - Sell API Version
Modern eBay scheduled listing application using Sell API (no deprecated Trading API)
"""

import logging
import sys
from datetime import datetime, timedelta
from textwrap import dedent

from config import eBayConfig
from oauth2_auth import eBayOAuth2Auth
from sell_api_client import eBaySellAPIClient

class eBayScheduledListingApp:
    """Main application class for eBay scheduled listing using Sell API"""

    def __init__(self):
        self.config = eBayConfig()
        self.setup_logging()

        # OAuth2 scopes required for Sell API
        self.oauth_scopes = [
            "https://api.ebay.com/oauth/api_scope",
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.account"
        ]

        # Initialize components
        self.oauth = None
        self.api_client = None

        self.logger = logging.getLogger(__name__)

    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ebay_listing.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def setup_authentication(self, redirect_uri: str = None) -> bool:
        """
        Set up eBay OAuth2 authentication

        Args:
            redirect_uri: OAuth redirect URI

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.info("Setting up eBay OAuth2 authentication...")

            # Choose redirect URI: prefer env/configured Production RuName
            effective_redirect_uri = redirect_uri or getattr(self.config, 'REDIRECT_URI', None)
            if not effective_redirect_uri or effective_redirect_uri == 'YOUR_PRODUCTION_RUNAME':
                self.logger.error("Redirect URI (Production RuName) is not set. Set EBAY_REDIRECT_URI or update config.")
                return False

            # Initialize OAuth2 handler
            self.oauth = eBayOAuth2Auth(
                self.config.APP_ID,
                self.config.CERT_ID,
                effective_redirect_uri,
                self.oauth_scopes
            )

            # Get valid access token
            access_token = self.oauth.get_valid_access_token()

            if not access_token:
                self.logger.error("Failed to obtain valid access token")
                return False

            # Create Sell API client
            self.api_client = eBaySellAPIClient(access_token, self.config.EBAY_MARKETPLACE_ID)

            self.logger.info("Authentication successful!")
            return True

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def validate_policies(self) -> bool:
        """
        Validate that all required policies are configured

        Returns:
            True if all policies are configured, False otherwise
        """
        is_valid, missing = self.config.validate_policies()

        if not is_valid:
            missing_list = ", ".join(missing)
            self.logger.error(f"Missing required policy configuration: {missing_list}")
            print("\nERROR: Missing required eBay policy configuration:")
            for policy in missing:
                print(f"  - {policy}")

            print("\nPlease set the following environment variables or update config.py:")
            for policy in missing:
                env_var = f"EBAY_{policy}"
                print(f"  export {env_var}=your_{policy.lower()}")

            print("\nYou can find these values in your eBay Seller Hub under:")
            print("  Account Settings > Business Policies > Payment, Shipping, and Return policies")

            return False

        self.logger.info("All required policies are configured")
        return True

    def setup_merchant_location(self) -> bool:
        """
        Create merchant location if it doesn't exist

        Returns:
            True if location is ready, False otherwise
        """
        try:
            if not self.api_client:
                self.logger.error("API client not initialized")
                return False

            # Use a simple location key
            location_key = "primary_warehouse"
            
            # Create the location with your address
            address = {
                "addressLine1": "19 Warren Park Dr",
                "addressLine2": "Apt B4",
                "city": "Pikesville",
                "stateOrProvince": "MD",
                "postalCode": "21208",
                "country": "US"
            }

            success, response, error = self.api_client.create_inventory_location(
                location_key, 
                "Primary Warehouse", 
                address
            )

            if success:
                self.logger.info(f"Merchant location created: {location_key}")
                # Update config with the location key
                self.config.MERCHANT_LOCATION_KEY = location_key
                return True
            else:
                # Location might already exist
                if "already exists" in error.lower() or "409" in error:
                    self.logger.info(f"Merchant location already exists: {location_key}")
                    self.config.MERCHANT_LOCATION_KEY = location_key
                    return True
                else:
                    self.logger.error(f"Failed to create merchant location: {error}")
                    return False

        except Exception as e:
            self.logger.error(f"Error setting up merchant location: {e}")
            return False

    def create_sample_laptop_listing(self, schedule_hours: int = 24) -> bool:
        """
        Create a sample laptop listing scheduled for future

        Args:
            schedule_hours: Hours from now to schedule the listing

        Returns:
            True if listing created successfully, False otherwise
        """
        try:
            if not self.api_client:
                self.logger.error("API client not initialized. Please run setup_authentication() first.")
                return False

            if not self.validate_policies():
                return False

            # Setup merchant location
            if not self.setup_merchant_location():
                return False

            self.logger.info(f"Creating sample laptop listing scheduled for {schedule_hours} hours from now...")

            # Create listing data
            min_buffer_minutes = 30
            schedule_time = None
            if schedule_hours and schedule_hours > 0:
                schedule_dt = datetime.utcnow() + timedelta(hours=schedule_hours)
                if schedule_dt < datetime.utcnow() + timedelta(minutes=min_buffer_minutes):
                    schedule_dt = datetime.utcnow() + timedelta(minutes=min_buffer_minutes)
                schedule_time = schedule_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            if schedule_time:
                self.logger.info(f"Scheduled time: {schedule_time}")
            else:
                self.logger.info("Immediate publish (no listingStartDate)")

            # Sample laptop product data
            product_data = {
                "title": "Apple MacBook Pro 13-inch M2 Chip 8GB RAM 256GB SSD - Space Gray",
                "description": dedent(
                    """
                    <h3>Apple MacBook Pro 13-inch with M2 Chip</h3>

                    <p><strong>Key Features:</strong></p>
                    <ul>
                        <li>Apple M2 chip with 8-core CPU and 10-core GPU</li>
                        <li>8GB unified memory</li>
                        <li>256GB SSD storage</li>
                        <li>13.3-inch Retina display with True Tone</li>
                        <li>Touch Bar and Touch ID</li>
                        <li>Two Thunderbolt 3 ports</li>
                        <li>Up to 20 hours battery life</li>
                    </ul>

                    <p><strong>Condition:</strong> Brand new, factory sealed</p>
                    <p><strong>Warranty:</strong> 1 year Apple warranty included</p>
                    <p><strong>Shipping:</strong> Fast and secure shipping</p>
                    <p><strong>Returns:</strong> 30-day return policy</p>

                    <p>Perfect for students, professionals, and anyone who needs a powerful, portable laptop.
                    The M2 chip delivers incredible performance while maintaining excellent battery life.</p>
                    """
                ).strip(),
                "aspects": {
                    "Brand": ["Apple"],
                    "Model": ["MacBook Pro"],
                    "Operating System": ["macOS"],
                    "Screen Size": ["13.3 in"],
                    "Storage Type": ["SSD (Solid State Drive)"],
                    "Processor": ["Apple M2"],
                    "RAM Size": ["8 GB"]
                },
                "imageUrls": ["https://upload.wikimedia.org/wikipedia/commons/9/9e/MacBook_Pro_16-inch.png"]
            }

            # Offer data
            offer_data = {
                "categoryId": self.config.LAPTOP_CATEGORY_ID,
                "merchantLocationKey": self.config.MERCHANT_LOCATION_KEY,
                "listingDescription": product_data["description"],
                "listingDuration": "GTC",
                "price": 1299.00,
                "currency": "USD",
                "availableQuantity": 1,
                "contentLanguage": "en-US",
                "itemAspects": {
                    "Brand": ["Apple"],
                    "Model": ["MacBook Pro"]
                },
                **self.config.get_policy_config()
            }
            if schedule_time:
                offer_data["listingStartDate"] = schedule_time

            # SKU
            sku = f"SAMPLE_LAPTOP_{int(datetime.now().timestamp())}"

            listing_data = {
                "sku": sku,
                "product": product_data,
                "offer": offer_data,
                "quantity": 1
            }
            if schedule_time:
                listing_data["publishStartDate"] = schedule_time

            self.logger.info(f"Listing title: {product_data['title']}")
            self.logger.info(f"Starting price: ${offer_data['price']}")

            # Make API call
            success, response, error = self.api_client.create_scheduled_listing(listing_data)

            if success:
                self.logger.info("Listing created successfully!")

                # Extract response data
                sku = response.get("sku", "Unknown")
                offer_response = response.get("offerResponse", {})

                self.logger.info(f"SKU: {sku}")
                self.logger.info(f"Offer ID: {offer_response.get('offerId', 'N/A')}")

                # Save listing details
                self._save_listing_details(sku, schedule_time, product_data['title'], offer_data['price'])

                return True
            else:
                self.logger.error(f"Failed to create listing: {error}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating listing: {e}")
            return False

    def _save_listing_details(self, sku: str, schedule_time: str, title: str, price: float):
        """Save listing details to file for reference"""
        try:
            with open('created_listing.txt', 'w') as f:
                f.write(f"Listing Details\n")
                f.write(f"===============\n")
                f.write(f"SKU: {sku}\n")
                f.write(f"Title: {title}\n")
                f.write(f"Price: ${price}\n")
                f.write(f"Scheduled for: {schedule_time}\n")
                f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"API Used: Sell API (Modern)\n")

            self.logger.info("Listing details saved to created_listing.txt")
        except Exception as e:
            self.logger.warning(f"Failed to save listing details: {e}")

    def get_my_listings(self) -> bool:
        """
        Get current listings from eBay (placeholder - Sell API has different methods)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.api_client:
                self.logger.error("API client not initialized. Please run setup_authentication() first.")
                return False

            self.logger.info("Retrieving current listings...")
            self.logger.info("Note: Sell API has different methods for retrieving listings")
            self.logger.info("This is a placeholder - implement based on your specific needs")

            return True

        except Exception as e:
            self.logger.error(f"Error retrieving listings: {e}")
            return False

    def run_interactive_mode(self):
        """Run the application in interactive mode"""
        print("=" * 60)
        print("eBay Scheduled Listing Application - Sell API Version")
        print("=" * 60)
        print("✓ Using modern Sell API (no deprecated Trading API)")
        print(f"✓ App ID: {self.config.APP_ID}")
        print(f"✓ Market: {self.config.EBAY_MARKETPLACE_ID}")
        print("✓ Ready to authenticate and create listings")

        # Setup authentication
        if not self.setup_authentication():
            print("\n❌ Authentication failed. Please check your credentials and try again.")
            print("Make sure your redirect URI matches your eBay app configuration.")
            return

        print("\n✅ Authentication successful!")

        while True:
            print("\nOptions:")
            print("1. Create sample laptop listing")
            print("2. View current listings (placeholder)")
            print("3. Exit")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == '1':
                hours = input("Schedule listing in how many hours? (default 24): ").strip()
                try:
                    hours = int(hours) if hours else 24
                    if hours < 0.25:  # Minimum 15 minutes
                        hours = 0.25
                except ValueError:
                    hours = 24

                success = self.create_sample_laptop_listing(hours)
                if success:
                    print("✅ Sample listing created successfully!")
                else:
                    print("❌ Failed to create sample listing.")

            elif choice == '2':
                self.get_my_listings()

            elif choice == '3':
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please try again.")

def main():
    """Main entry point"""
    app = eBayScheduledListingApp()

    print("=" * 60)
    print("eBay Scheduled Listing Application - Sell API Version")
    print("=" * 60)
    print("✓ Production API credentials configured")
    print(f"✓ App ID: {app.config.APP_ID}")
    print(f"✓ Dev ID: {app.config.DEV_ID[:8]}...")
    print("✓ Using modern Sell API (replaces deprecated Trading API)")
    print("✓ OAuth2 authentication configured")
    print("✓ Ready to authenticate and create listings")

    # Run interactive mode
    app.run_interactive_mode()

if __name__ == "__main__":
    main()
