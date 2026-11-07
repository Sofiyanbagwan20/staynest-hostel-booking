import hmac
import hashlib
import time
import secrets
import config

def create_order(amount_in_inr: float, receipt_id: str, notes: dict = None) -> dict:
    """
    Creates a Razorpay-compliant order.
    Amount in Razorpay is represented in paise (1 INR = 100 paise).
    """
    amount_in_paise = int(round(amount_in_inr * 100))
    # Standard Razorpay order ID shape: order_<14 alphanumeric chars>
    random_suffix = secrets.token_hex(7)
    order_id = f"order_{random_suffix}"
    
    order_data = {
        "id": order_id,
        "entity": "order",
        "amount": amount_in_paise,
        "amount_paid": 0,
        "amount_due": amount_in_paise,
        "currency": "INR",
        "receipt": receipt_id,
        "status": "created",
        "attempts": 0,
        "notes": notes or {},
        "created_at": int(time.time()),
        "key_id": config.RAZORPAY_KEY_ID
    }
    return order_data

def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """
    Cryptographically verifies Razorpay payment signature using HMAC-SHA256.
    Formula: HMAC_SHA256(order_id + "|" + payment_id, secret)
    """
    if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
        return False
        
    msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
    expected_signature = hmac.new(
        config.RAZORPAY_KEY_SECRET.encode('utf-8'),
        msg,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, razorpay_signature)

def generate_mock_signature(razorpay_order_id: str, razorpay_payment_id: str) -> str:
    """Helper to generate a valid signature for test environments."""
    msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
    return hmac.new(
        config.RAZORPAY_KEY_SECRET.encode('utf-8'),
        msg,
        hashlib.sha256
    ).hexdigest()
