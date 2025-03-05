import paypalrestsdk
import qrcode
from io import BytesIO
import utils
import os
from PIL import Image
import requests

class PayPalPaymentManager:
    def __init__(self, client_id=None, client_secret=None, mode="sandbox", app=None):
        # Store app reference for config access
        self.app = app
        
        # Use provided credentials or try to get from environment
        self.client_id = client_id or os.environ.get('PAYPAL_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('PAYPAL_SECRET')
        self.mode = mode  # sandbox or live
        
        if self.client_id and self.client_secret:
            try:
                utils.debug_log(f"Initializing PayPal API in {self.mode} mode")
                # Use requests directly to test credentials first
                self.test_credentials()
                
                # Configure SDK if test was successful
                paypalrestsdk.configure({
                    "mode": self.mode,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                })
                self.initialized = True
                utils.debug_log("PayPal API initialized successfully.")
            except Exception as e:
                self.initialized = False
                utils.debug_log(f"Failed to initialize PayPal API: {str(e)}")
        else:
            self.initialized = False
            utils.debug_log("PayPal API credentials not found. Payment features will be disabled.")
    
    def test_credentials(self):
        """Test PayPal credentials by requesting an access token"""
        utils.debug_log("Testing PayPal credentials...")
        
        # PayPal token endpoint
        if self.mode == "sandbox":
            url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        else:
            url = "https://api-m.paypal.com/v1/oauth2/token"
        
        # Request headers and data
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        data = {
            "grant_type": "client_credentials"
        }
        
        # Make the request to get access token
        response = requests.post(
            url, 
            auth=(self.client_id, self.client_secret),
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            utils.debug_log(f"Successfully authenticated with PayPal. Token type: {token_data.get('token_type')}")
            return True
        else:
            error_msg = f"PayPal authentication failed. Status: {response.status_code}, Response: {response.text}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
    
    def create_simple_payment_link(self, amount, player_name):
        """Create a simple payment link without needing API authentication"""
        # Modified to handle the case when app isn't available
        
        # If we have direct access to app config
        if hasattr(self, 'app') and self.app is not None:
            paypal_username = self.app.config.get("paypal_username", "")
            bank_name = self.app.config.get("bank_account_name", "")
        else:
            # Use hardcoded values as fallback
            paypal_username = "Josh Hirschkorn"  # From your config
            bank_name = "Joshua Hirschkorn"  # From your config
        
        # Create PayPal.me link if we have a username
        if paypal_username:
            # Format the username by removing spaces
            formatted_username = paypal_username.replace(" ", "")
            amount_formatted = f"{amount:.2f}"
            payment_link = f"https://www.paypal.com/paypalme/{formatted_username}/{amount_formatted}"
            utils.debug_log(f"Created PayPal.me link: {payment_link}")
            return payment_link
        
        # Fall back to bank transfer instruction
        return f"Bank transfer to {bank_name} - Amount: £{amount:.2f}"

    def create_payment_link(self, amount, description, player_name):
        """Create a PayPal payment link, falling back to simple link if needed"""
        if not self.initialized:
            utils.debug_log("PayPal not initialized. Using simple PayPal.me link.")
            return self.create_simple_payment_link(amount, player_name)
        
        try:
            # Create a PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": "https://example.com/payment/success",
                    "cancel_url": "https://example.com/payment/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"Poker Debt: {player_name}",
                            "description": description,
                            "quantity": "1",
                            "price": f"{amount:.2f}",
                            "currency": "GBP"
                        }]
                    },
                    "amount": {
                        "total": f"{amount:.2f}",
                        "currency": "GBP"
                    },
                    "description": description
                }]
            })
            
            # Create the payment
            if payment.create():
                utils.debug_log(f"Payment created with ID: {payment.id}")
                
                # Get the approval URL (this is what we'll use for the QR code)
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        utils.debug_log(f"Created payment link for {player_name}: {approval_url}")
                        return approval_url
                
                utils.debug_log("No approval URL found in payment links")
                return None
            else:
                utils.debug_log(f"Error creating PayPal payment: {payment.error}")
                return None
            
        except Exception as e:
            utils.debug_log(f"Error creating PayPal payment link: {str(e)}")
            # Fall back to simple PayPal.me link
            utils.debug_log("Falling back to simple PayPal.me link")
            return self.create_simple_payment_link(amount, player_name)
    
    def generate_qr_code(self, url):
        """Generate QR code for a payment URL"""
        if not url:
            return None
            
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert PIL Image to bytes for CTkImage
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            
            return img_bytes
            
        except Exception as e:
            utils.debug_log(f"Error generating QR code: {str(e)}")
            return None

    def create_email_payment_link(self, amount, email, description=""):
        """Create a PayPal payment link to send money directly to an email address"""
        # Format amount properly
        amount_formatted = f"{amount:.2f}"
        
        # Create a PayPal send money link
        # This uses the PayPal send money flow with pre-filled information
        base_url = "https://www.paypal.com/myaccount/transfer/send"
        
        # Build query parameters
        params = {
            "amount": amount_formatted,
            "currencyCode": "GBP",
            "recipient": email,
            "note": description or "Poker winnings"
        }
        
        # Build the URL with query string
        query_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        payment_link = f"{base_url}?{query_string}"
        
        utils.debug_log(f"Created PayPal email payment link for {email}: {payment_link}")
        return payment_link 