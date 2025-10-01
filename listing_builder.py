"""
eBay Listing Builder Module
Creates structured listing data for eBay API calls
"""

from typing import Dict, List, Optional
from datetime import datetime
from .config import eBayConfig

class ListingBuilder:
    """Builds eBay listing data structures"""
    
    def __init__(self):
        self.config = eBayConfig()
    
    def create_laptop_listing(self, 
                            title: str,
                            description: str,
                            price: float,
                            condition_id: str = None,
                            schedule_time: str = None,
                            seller_email: str = None,
                            postal_code: str = None,
                            location: str = None,
                            product_reference_id: str = None,
                            custom_picture_urls: List[str] = None) -> Dict:
        """
        Create a laptop listing with all required fields
        
        Args:
            title: Listing title
            description: Listing description
            price: Starting price
            condition_id: Condition ID (defaults to new)
            schedule_time: When to start the listing (defaults to 24 hours from now)
            seller_email: PayPal email for payments
            postal_code: Seller postal code
            location: Seller location
            product_reference_id: eBay Product ID for stock photos
            custom_picture_urls: Custom picture URLs
            
        Returns:
            Dictionary containing the listing data
        """
        
        # Set defaults
        condition_id = condition_id or self.config.CONDITION_NEW
        schedule_time = schedule_time or self.config.get_schedule_time()
        seller_email = seller_email or "seller@example.com"
        postal_code = postal_code or "95125"
        location = location or "San Jose, CA"
        
        # Build the listing structure
        listing = {
            "Item": {
                "Title": title,
                "Description": description,
                "PrimaryCategory": {
                    "CategoryID": self.config.LAPTOP_CATEGORY_ID
                },
                "StartPrice": str(price),
                "ConditionID": condition_id,
                "Country": self.config.DEFAULT_COUNTRY,
                "Currency": self.config.DEFAULT_CURRENCY,
                "DispatchTimeMax": self.config.DEFAULT_DISPATCH_TIME_MAX,
                "ListingDuration": self.config.LISTING_DURATION_7_DAYS,
                "ListingType": self.config.LISTING_TYPE_FIXED_PRICE,
                "Location": location,
                "PostalCode": postal_code,
                "Quantity": "1",
                "ScheduleTime": schedule_time,
                
                # Payment settings
                "PaymentMethods": self.config.PAYMENT_METHOD_PAYPAL,
                "PayPalEmailAddress": seller_email,
                
                # Shipping details
                "ShippingDetails": self._create_shipping_details(),
                
                # Return policy
                "ReturnPolicy": self._create_return_policy(),
                
                # Picture details
                "PictureDetails": self._create_picture_details(product_reference_id, custom_picture_urls),
                
                # Product listing details for stock photos
                "ProductListingDetails": self._create_product_listing_details(product_reference_id)
            }
        }
        
        return listing
    
    def _create_shipping_details(self) -> Dict:
        """Create shipping details structure"""
        return {
            "ShippingType": "Flat",
            "ShippingServiceOptions": [
                {
                    "ShippingServicePriority": "1",
                    "ShippingService": self.config.SHIPPING_SERVICE_USPS_PRIORITY,
                    "ShippingServiceCost": "15.00"
                },
                {
                    "ShippingServicePriority": "2", 
                    "ShippingService": self.config.SHIPPING_SERVICE_FEDEX_HOME,
                    "ShippingServiceCost": "20.00"
                }
            ]
        }
    
    def _create_return_policy(self) -> Dict:
        """Create return policy structure"""
        return {
            "ReturnsAcceptedOption": self.config.RETURNS_ACCEPTED,
            "RefundOption": self.config.REFUND_MONEY_BACK,
            "ReturnsWithinOption": self.config.RETURNS_WITHIN_30_DAYS,
            "ShippingCostPaidByOption": self.config.SHIPPING_COST_PAID_BY_BUYER
        }
    
    def _create_picture_details(self, product_reference_id: str = None, custom_urls: List[str] = None) -> Dict:
        """Create picture details structure"""
        picture_details = {}
        
        # Add custom picture URLs if provided
        if custom_urls:
            picture_details["PictureURL"] = custom_urls
        
        return picture_details
    
    def _create_product_listing_details(self, product_reference_id: str = None) -> Dict:
        """Create product listing details for stock photos"""
        if not product_reference_id:
            return {}
        
        return {
            "IncludeStockPhotoURL": "true",
            "UseStockPhotoURLAsGallery": "true",
            "ProductReferenceID": product_reference_id
        }
    
    def create_sample_laptop_listing(self) -> Dict:
        """Create a sample laptop listing with realistic data"""
        return self.create_laptop_listing(
            title="Apple MacBook Pro 13-inch M2 Chip 8GB RAM 256GB SSD - Space Gray",
            description="""
            <![CDATA[
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
            <p><strong>Shipping:</strong> Free shipping via USPS Priority Mail</p>
            <p><strong>Returns:</strong> 30-day return policy</p>
            
            <p>Perfect for students, professionals, and anyone who needs a powerful, portable laptop. 
            The M2 chip delivers incredible performance while maintaining excellent battery life.</p>
            """,
            price=1299.00,
            condition_id=self.config.CONDITION_NEW,
            seller_email="seller@example.com",
            postal_code="95125",
            location="San Jose, CA",
            # Using a sample eBay Product ID for MacBook Pro (this would be a real ePID in production)
            product_reference_id="123456789"  # Replace with actual ePID
        )
    
    def create_xml_payload(self, listing_data: Dict, user_token: str) -> str:
        """Convert listing data to XML payload for eBay API"""
        
        item = listing_data["Item"]
        
        xml = f'''<?xml version="1.0" encoding="utf-8"?>
<AddItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <Item>
    <Title><![CDATA[{item['Title']}]]></Title>
    <Description><![CDATA[{item['Description']}]]></Description>
    <PrimaryCategory>
      <CategoryID>{item['PrimaryCategory']['CategoryID']}</CategoryID>
    </PrimaryCategory>
    <StartPrice>{item['StartPrice']}</StartPrice>
    <ConditionID>{item['ConditionID']}</ConditionID>
    <Country>{item['Country']}</Country>
    <Currency>{item['Currency']}</Currency>
    <DispatchTimeMax>{item['DispatchTimeMax']}</DispatchTimeMax>
    <ListingDuration>{item['ListingDuration']}</ListingDuration>
    <ListingType>{item['ListingType']}</ListingType>
    <Location>{item['Location']}</Location>
    <PostalCode>{item['PostalCode']}</PostalCode>
    <Quantity>{item['Quantity']}</Quantity>
    <ScheduleTime>{item['ScheduleTime']}</ScheduleTime>
    <PaymentMethods>{item['PaymentMethods']}</PaymentMethods>
    <PayPalEmailAddress>{item['PayPalEmailAddress']}</PayPalEmailAddress>'''
        
        # Add shipping details
        if 'ShippingDetails' in item:
            xml += f'''
    <ShippingDetails>
      <ShippingType>{item['ShippingDetails']['ShippingType']}</ShippingType>'''
            
            for service in item['ShippingDetails']['ShippingServiceOptions']:
                xml += f'''
      <ShippingServiceOptions>
        <ShippingServicePriority>{service['ShippingServicePriority']}</ShippingServicePriority>
        <ShippingService>{service['ShippingService']}</ShippingService>
        <ShippingServiceCost>{service['ShippingServiceCost']}</ShippingServiceCost>
      </ShippingServiceOptions>'''
            
            xml += '''
    </ShippingDetails>'''
        
        # Add return policy
        if 'ReturnPolicy' in item:
            xml += f'''
    <ReturnPolicy>
      <ReturnsAcceptedOption>{item['ReturnPolicy']['ReturnsAcceptedOption']}</ReturnsAcceptedOption>
      <RefundOption>{item['ReturnPolicy']['RefundOption']}</RefundOption>
      <ReturnsWithinOption>{item['ReturnPolicy']['ReturnsWithinOption']}</ReturnsWithinOption>
      <ShippingCostPaidByOption>{item['ReturnPolicy']['ShippingCostPaidByOption']}</ShippingCostPaidByOption>
    </ReturnPolicy>'''
        
        # Add picture details
        if 'PictureDetails' in item and item['PictureDetails']:
            xml += '''
    <PictureDetails>'''
            if 'PictureURL' in item['PictureDetails']:
                for url in item['PictureDetails']['PictureURL']:
                    xml += f'''
      <PictureURL>{url}</PictureURL>'''
            xml += '''
    </PictureDetails>'''
        
        # Add product listing details for stock photos
        if 'ProductListingDetails' in item and item['ProductListingDetails']:
            xml += f'''
    <ProductListingDetails>
      <IncludeStockPhotoURL>{item['ProductListingDetails']['IncludeStockPhotoURL']}</IncludeStockPhotoURL>
      <UseStockPhotoURLAsGallery>{item['ProductListingDetails']['UseStockPhotoURLAsGallery']}</UseStockPhotoURLAsGallery>
      <ProductReferenceID>{item['ProductListingDetails']['ProductReferenceID']}</ProductReferenceID>
    </ProductListingDetails>'''
        
        xml += '''
  </Item>
</AddItemRequest>'''
        
        return xml