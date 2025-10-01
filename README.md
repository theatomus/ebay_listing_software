# eBay Scheduled Listing Application - Modern Sell API Version

This is a **modern, compliant** eBay listing application that uses the current Sell API instead of the deprecated Trading API.

## ✅ What's New and Improved

- **Modern API**: Uses eBay's current Sell API (no deprecated Trading API)
- **OAuth2 Authentication**: Secure, token-based authentication
- **Proper Policy Management**: Validates business policies before listing
- **Inventory Management**: Uses the inventory/offer pattern for better listing management
- **Scheduled Listings**: Supports scheduling listings for future start dates
- **Error Handling**: Comprehensive error handling and validation

## 🚀 Quick Start

### 1. Collect Required Credentials

- **Client ID, Dev ID, Client Secret**: eBay Developer Console → Application Keys → Production
- **RuName**: Same page as your keys (used as redirect URI)
- **Business policy IDs**: Seller Hub → Account Settings → Business Policies (copy the ID from the detail URL)
- **Merchant location key**: Seller Hub → Shipping labels → Manage locations → create/edit warehouse → copy the Location Key
- **Public ngrok URL**: Start `ngrok http 80`, copy the HTTPS address for `Authentic URL` in Developer Console

### 2. Configure the app

1. Copy `