import stripe
import qrcode
from io import BytesIO
import utils
import os
from PIL import Image

class StripePaymentManager:
    def __init__(self, api_key=None):
        # Use provided API key or try to get from environment
        self.api_key = api_key or os.environ.get('STRIPE_API_KEY')
        if self.api_key:
            stripe.api_key = self.api_key
            self.initialized = True
        else:
            self.initialized = False
            utils.debug_log("Stripe API key not found. Payment features will be disabled.")
    
    def create_payment_link(self, amount, description, player_name):
        """Create a Stripe payment link"""
        if not self.initialized:
            utils.debug_log("Stripe not initialized. Cannot create payment link.")
            return None
            
        try:
            # Convert amount to pence/cents (Stripe requires integer amounts)
            amount_in_pence = int(amount * 100)
            
            # Create a payment link
            payment_link = stripe.PaymentLink.create(
                line_items=[{
                    'price_data': {
                        'currency': 'gbp',
                        'product_data': {
                            'name': f"Poker Debt: {player_name}",
                            'description': description,
                        },
                        'unit_amount': amount_in_pence,
                    },
                    'quantity': 1,
                }],
                payment_method_types=['card', 'apple_pay'],
                after_completion={'type': 'redirect', 'redirect': {'url': 'https://example.com/thank-you'}},
            )
            
            utils.debug_log(f"Created payment link for {player_name}: {payment_link.url}")
            return payment_link.url
            
        except Exception as e:
            utils.debug_log(f"Error creating Stripe payment link: {str(e)}")
            return None
    
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