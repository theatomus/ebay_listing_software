"""
Main Application Module
Main entry point for eBay scheduled listing application
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

from .config import eBayConfig
from .auth import eBayAuth
from .listing_builder import ListingBuilder
from .api_client import eBayAPIClient

class eBayScheduledListingApp:
    """Main application class for eBay scheduled listing"""
    
    def __init__(self):
        self.config = eBayConfig()
        self.setup_logging()
        
        # Initialize components
        self.auth = None
        self.api_client = None
        self.listing_builder = ListingBuilder()
        
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
        Set up eBay authentication
        
        Args:
            redirect_uri: OAuth redirect URI
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.info("Setting up eBay authentication...")
            
            # Check if we have stored token data
            token_data = eBayAuth.load_token_data()
            
            if token_data and 'access_token' in token_data:
                self.logger.info("Found existing token data")
                
                # Check if token is still valid (basic check)
                if 'expires_in' in token_data:
                    # You might want to implement proper token expiration checking here
                    self.api_client = eBayAPIClient(
                        self.config.APP_ID,
                        self.config.CERT_ID,
                        self.config.DEV_ID,
                        token_data['access_token']
                    )
                    return True
            
            # Need to authenticate
            self.logger.info("No valid token found, starting authentication process...")
            
            # Choose redirect URI: prefer env/configured Production RuName
            effective_redirect_uri = redirect_uri or getattr(self.config, 'REDIRECT_URI', None)
            if not effective_redirect_uri or effective_redirect_uri == 'YOUR_PRODUCTION_RUNAME':
                self.logger.error("Redirect URI (Production RuName) is not set. Set EBAY_REDIRECT_URI or update config.")
                return False

            self.auth = eBayAuth(
                self.config.APP_ID,
                self.config.CERT_ID,
                self.config.DEV_ID,
                effective_redirect_uri
            )
            
            token_data = self.auth.authenticate()
            
            # Save token data
            eBayAuth.save_token_data(token_data)
            
            # Create API client
            self.api_client = eBayAPIClient(
                self.config.APP_ID,
                self.config.CERT_ID,
                self.config.DEV_ID,
                token_data['access_token']
            )
            
            self.logger.info("Authentication successful!")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
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
            
            self.logger.info(f"Creating sample laptop listing scheduled for {schedule_hours} hours from now...")
            
            # Create listing data
            schedule_time = (datetime.utcnow() + timedelta(hours=schedule_hours)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            listing_data = self.listing_builder.create_sample_laptop_listing()
            listing_data["Item"]["ScheduleTime"] = schedule_time
            
            self.logger.info(f"Scheduled time: {schedule_time}")
            self.logger.info(f"Listing title: {listing_data['Item']['Title']}")
            self.logger.info(f"Starting price: ${listing_data['Item']['StartPrice']}")
            
            # Make API call
            success, response, error = self.api_client.add_item(listing_data, use_sandbox=False)
            
            if success:
                self.logger.info("Listing created successfully!")
                
                # Extract item ID from response
                if 'ItemID' in response:
                    item_id = response['ItemID']
                    self.logger.info(f"Item ID: {item_id}")
                    
                    # Save item ID for future reference
                    with open('created_listing.txt', 'w') as f:
                        f.write(f"Item ID: {item_id}\n")
                        f.write(f"Created: {datetime.now()}\n")
                        f.write(f"Scheduled for: {schedule_time}\n")
                        f.write(f"Title: {listing_data['Item']['Title']}\n")
                    
                    self.logger.info("Listing details saved to created_listing.txt")
                
                return True
            else:
                self.logger.error(f"Failed to create listing: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating listing: {e}")
            return False
    
    def create_custom_laptop_listing(self, 
                                   title: str,
                                   description: str,
                                   price: float,
                                   schedule_hours: int = 24,
                                   condition_id: str = None,
                                   seller_email: str = None,
                                   postal_code: str = None,
                                   location: str = None,
                                   product_reference_id: str = None) -> bool:
        """
        Create a custom laptop listing
        
        Args:
            title: Listing title
            description: Listing description
            price: Starting price
            schedule_hours: Hours from now to schedule the listing
            condition_id: Condition ID
            seller_email: PayPal email
            postal_code: Seller postal code
            location: Seller location
            product_reference_id: eBay Product ID for stock photos
            
        Returns:
            True if listing created successfully, False otherwise
        """
        try:
            if not self.api_client:
                self.logger.error("API client not initialized. Please run setup_authentication() first.")
                return False
            
            self.logger.info(f"Creating custom laptop listing: {title}")
            
            # Create listing data
            schedule_time = (datetime.utcnow() + timedelta(hours=schedule_hours)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            listing_data = self.listing_builder.create_laptop_listing(
                title=title,
                description=description,
                price=price,
                condition_id=condition_id,
                schedule_time=schedule_time,
                seller_email=seller_email,
                postal_code=postal_code,
                location=location,
                product_reference_id=product_reference_id
            )
            
            self.logger.info(f"Scheduled time: {schedule_time}")
            self.logger.info(f"Starting price: ${price}")
            
            # Make API call
            success, response, error = self.api_client.add_item(listing_data, use_sandbox=False)
            
            if success:
                self.logger.info("Custom listing created successfully!")
                
                # Extract item ID from response
                if 'ItemID' in response:
                    item_id = response['ItemID']
                    self.logger.info(f"Item ID: {item_id}")
                    
                    # Save item ID for future reference
                    with open('created_listing.txt', 'w') as f:
                        f.write(f"Item ID: {item_id}\n")
                        f.write(f"Created: {datetime.now()}\n")
                        f.write(f"Scheduled for: {schedule_time}\n")
                        f.write(f"Title: {title}\n")
                        f.write(f"Price: ${price}\n")
                    
                    self.logger.info("Listing details saved to created_listing.txt")
                
                return True
            else:
                self.logger.error(f"Failed to create listing: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating listing: {e}")
            return False
    
    def get_my_listings(self) -> bool:
        """
        Get current listings from eBay
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.api_client:
                self.logger.error("API client not initialized. Please run setup_authentication() first.")
                return False
            
            self.logger.info("Retrieving current listings...")
            
            success, response, error = self.api_client.get_my_ebay_selling(use_sandbox=False)
            
            if success:
                self.logger.info("Listings retrieved successfully!")
                self.logger.info(f"Response: {response}")
                return True
            else:
                self.logger.error(f"Failed to retrieve listings: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error retrieving listings: {e}")
            return False
    
    def run_interactive_mode(self):
        """Run the application in interactive mode"""
        print("=" * 60)
        print("eBay Scheduled Listing Application")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("Authentication failed. Please check your credentials and try again.")
            return
        
        while True:
            print("\nOptions:")
            print("1. Create sample laptop listing")
            print("2. Create custom laptop listing")
            print("3. View current listings")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
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
                    print("Sample listing created successfully!")
                else:
                    print("Failed to create sample listing.")
            
            elif choice == '2':
                title = input("Enter listing title: ").strip()
                description = input("Enter listing description: ").strip()
                price_str = input("Enter starting price: ").strip()
                
                try:
                    price = float(price_str)
                except ValueError:
                    print("Invalid price. Using default $500.")
                    price = 500.0
                
                hours = input("Schedule listing in how many hours? (default 24): ").strip()
                try:
                    hours = int(hours) if hours else 24
                    if hours < 0.25:
                        hours = 0.25
                except ValueError:
                    hours = 24
                
                success = self.create_custom_laptop_listing(title, description, price, hours)
                if success:
                    print("Custom listing created successfully!")
                else:
                    print("Failed to create custom listing.")
            
            elif choice == '3':
                self.get_my_listings()
            
            elif choice == '4':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")

def main():
    """Main entry point"""
    app = eBayScheduledListingApp()
    
    print("=" * 60)
    print("eBay Scheduled Listing Application - Production Mode")
    print("=" * 60)
    print("✓ Production API credentials configured")
    print(f"✓ App ID: {app.config.APP_ID}")
    print(f"✓ Dev ID: {app.config.DEV_ID[:8]}...")
    print("✓ Ready to authenticate and create listings")
    
    # Run interactive mode
    app.run_interactive_mode()

if __name__ == "__main__":
    main()