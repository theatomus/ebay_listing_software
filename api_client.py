"""
eBay API Client Module
Handles communication with eBay Trading API
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime

class eBayAPIClient:
    """Client for eBay Trading API operations"""
    
    def __init__(self, app_id: str, cert_id: str, dev_id: str, user_token: str):
        self.app_id = app_id
        self.cert_id = cert_id
        self.dev_id = dev_id
        self.user_token = user_token
        
        # API endpoints
        self.production_endpoint = 'https://api.ebay.com/ws/api.dll'
        self.sandbox_endpoint = 'https://api.sandbox.ebay.com/ws/api.dll'
        
        # API headers
        self.headers = {
            'X-EBAY-API-SITEID': '0',  # US site
            'X-EBAY-API-COMPATIBILITY-LEVEL': '967',  # Latest compatibility level
            'Content-Type': 'text/xml',
            'X-EBAY-API-IAF-TOKEN': self.user_token
        }
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def _make_api_call(self, call_name: str, xml_payload: str, use_sandbox: bool = False) -> Tuple[bool, Dict, str]:
        """
        Make API call to eBay Trading API
        
        Args:
            call_name: Name of the API call (e.g., 'AddItem')
            xml_payload: XML request payload
            use_sandbox: Whether to use sandbox endpoint
            
        Returns:
            Tuple of (success, response_dict, error_message)
        """
        
        endpoint = self.sandbox_endpoint if use_sandbox else self.production_endpoint
        headers = self.headers.copy()
        headers['X-EBAY-API-CALL-NAME'] = call_name
        
        try:
            self.logger.info(f"Making {call_name} API call to {endpoint}")
            self.logger.debug(f"Request payload: {xml_payload}")
            
            response = requests.post(endpoint, headers=headers, data=xml_payload, timeout=30)
            
            self.logger.info(f"API response status: {response.status_code}")
            self.logger.debug(f"Response content: {response.text}")
            
            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.text)
                
                # Check for errors in response
                errors = root.findall('.//{urn:ebay:apis:eBLBaseComponents}Errors')
                if errors:
                    error_messages = []
                    for error in errors:
                        short_message = error.find('.//{urn:ebay:apis:eBLBaseComponents}ShortMessage')
                        long_message = error.find('.//{urn:ebay:apis:eBLBaseComponents}LongMessage')
                        error_code = error.find('.//{urn:ebay:apis:eBLBaseComponents}ErrorCode')
                        
                        error_msg = f"Error {error_code.text if error_code is not None else 'Unknown'}: {short_message.text if short_message is not None else 'Unknown error'}"
                        if long_message is not None:
                            error_msg += f" - {long_message.text}"
                        
                        error_messages.append(error_msg)
                    
                    return False, {}, '; '.join(error_messages)
                
                # Convert XML to dictionary for successful responses
                response_dict = self._xml_to_dict(root)
                return True, response_dict, ""
            
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return False, {}, error_msg
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        except ET.ParseError as e:
            error_msg = f"XML parsing failed: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    def _xml_to_dict(self, element) -> Dict:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content if no children
        if element.text and element.text.strip() and not element:
            return element.text.strip()
        
        # Process children
        for child in element:
            child_dict = self._xml_to_dict(child)
            
            # Handle multiple children with same tag
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        
        return result
    
    def add_item(self, listing_data: Dict, use_sandbox: bool = False) -> Tuple[bool, Dict, str]:
        """
        Create a new listing using AddItem API call
        
        Args:
            listing_data: Dictionary containing listing information
            use_sandbox: Whether to use sandbox environment
            
        Returns:
            Tuple of (success, response_dict, error_message)
        """
        
        # Convert listing data to XML
        from .listing_builder import ListingBuilder
        builder = ListingBuilder()
        xml_payload = builder.create_xml_payload(listing_data, self.user_token)
        
        return self._make_api_call('AddItem', xml_payload, use_sandbox)
    
    def get_item(self, item_id: str, use_sandbox: bool = False) -> Tuple[bool, Dict, str]:
        """
        Get item details using GetItem API call
        
        Args:
            item_id: eBay item ID
            use_sandbox: Whether to use sandbox environment
            
        Returns:
            Tuple of (success, response_dict, error_message)
        """
        
        xml_payload = f'''<?xml version="1.0" encoding="utf-8"?>
<GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{self.user_token}</eBayAuthToken>
  </RequesterCredentials>
  <ItemID>{item_id}</ItemID>
  <IncludeWatchCount>true</IncludeWatchCount>
</GetItemRequest>'''
        
        return self._make_api_call('GetItem', xml_payload, use_sandbox)
    
    def end_item(self, item_id: str, end_reason: str = "NotAvailable", use_sandbox: bool = False) -> Tuple[bool, Dict, str]:
        """
        End a listing using EndItem API call
        
        Args:
            item_id: eBay item ID
            end_reason: Reason for ending the listing
            use_sandbox: Whether to use sandbox environment
            
        Returns:
            Tuple of (success, response_dict, error_message)
        """
        
        xml_payload = f'''<?xml version="1.0" encoding="utf-8"?>
<EndItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{self.user_token}</eBayAuthToken>
  </RequesterCredentials>
  <ItemID>{item_id}</ItemID>
  <EndingReason>{end_reason}</EndingReason>
</EndItemRequest>'''
        
        return self._make_api_call('EndItem', xml_payload, use_sandbox)
    
    def get_my_ebay_selling(self, use_sandbox: bool = False) -> Tuple[bool, Dict, str]:
        """
        Get seller's listings using GetMyeBaySelling API call
        
        Args:
            use_sandbox: Whether to use sandbox environment
            
        Returns:
            Tuple of (success, response_dict, error_message)
        """
        
        xml_payload = f'''<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{self.user_token}</eBayAuthToken>
  </RequesterCredentials>
  <ActiveList>
    <Include>true</Include>
  </ActiveList>
  <ScheduledList>
    <Include>true</Include>
  </ScheduledList>
</GetMyeBaySellingRequest>'''
        
        return self._make_api_call('GetMyeBaySelling', xml_payload, use_sandbox)
    
    def upload_site_hosted_pictures(self, picture_data: bytes, picture_name: str = None, use_sandbox: bool = False) -> Tuple[bool, Dict, str]:
        """
        Upload pictures to eBay Picture Services
        
        Args:
            picture_data: Binary picture data
            picture_name: Name for the picture
            use_sandbox: Whether to use sandbox environment
            
        Returns:
            Tuple of (success, response_dict, error_message)
        """
        
        # This is a simplified implementation
        # In production, you'd need to handle multipart form data properly
        
        xml_payload = f'''<?xml version="1.0" encoding="utf-8"?>
<UploadSiteHostedPicturesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{self.user_token}</eBayAuthToken>
  </RequesterCredentials>
  <PictureName>{picture_name or 'listing_picture'}</PictureName>
  <PictureData>{picture_data}</PictureData>
</UploadSiteHostedPicturesRequest>'''
        
        return self._make_api_call('UploadSiteHostedPictures', xml_payload, use_sandbox)