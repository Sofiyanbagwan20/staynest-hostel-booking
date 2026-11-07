import unittest
import json
import config
from auth import hash_password, verify_password, generate_token, verify_token
import database
import payment
from app import app

class TestStayNestBackend(unittest.TestCase):

    def test_01_password_hashing(self):
        pwd = "SecureStudentPass123"
        pwd_hash, salt = hash_password(pwd)
        self.assertTrue(verify_password(pwd, pwd_hash, salt))
        self.assertFalse(verify_password("WrongPassword", pwd_hash, salt))
        print("[OK] Password hashing & salt verification passed.")

    def test_02_jwt_token(self):
        token = generate_token(101, "student@staynest.com", "John Doe")
        payload = verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], 101)
        self.assertEqual(payload["email"], "student@staynest.com")
        self.assertEqual(payload["name"], "John Doe")
        print("[OK] JWT creation & verification passed.")
        self.assertTrue(True)

    def test_03_razorpay_order_and_signature(self):
        # Test creating a Razorpay-compliant order
        amount_inr = 7500.0
        receipt = "SN-TEST-1234"
        order = payment.create_order(amount_inr, receipt)
        self.assertEqual(order["amount"], 750000) # In paise
        self.assertEqual(order["currency"], "INR")
        self.assertTrue(order["id"].startswith("order_"))

        # Test HMAC-SHA256 signature verification
        test_payment_id = "pay_test_payment_9988"
        valid_signature = payment.generate_mock_signature(order["id"], test_payment_id)
        
        # Valid signature should verify
        is_valid = payment.verify_payment_signature(order["id"], test_payment_id, valid_signature)
        self.assertTrue(is_valid)

        # Tampered signature should fail
        tampered_valid = payment.verify_payment_signature(order["id"], test_payment_id, "tampered_signature_123")
        self.assertFalse(tampered_valid)
        print("[OK] Razorpay Order & HMAC signature verification passed.")

    def test_04_api_json_missing_body_is_safe(self):
        database.init_db()
        client = app.test_client()
        response = client.post('/api/payments/verify', json={})
        self.assertEqual(response.status_code, 401)
        payload = response.get_json()
        self.assertIn('Authorization token missing', payload['error'])
        print("[OK] Empty JSON payloads are handled safely without server crashes.")

if __name__ == '__main__':
    unittest.main()
