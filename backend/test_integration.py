import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import database
import payment
from app import app

def run_tests():
    print("=" * 60)
    print("STAYNEST FULLSTACK BACKEND & PAYMENT INTEGRATION TESTS")
    print("=" * 60)
    
    # 1. Initialize DB
    success, msg = database.init_db()
    print(f"[TEST 1] Database Init: {msg} [OK]")
    assert success

    client = app.test_client()

    # 2. Health check
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    print(f"[TEST 2] Health Check: Status={data['status']}, Gateway={data['gateway']} [OK]")

    # 3. List Hostels
    res = client.get('/api/hostels')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["count"] >= 6
    print(f"[TEST 3] List Hostels API: Returned {data['count']} properties [OK]")

    # 4. User Registration
    test_email = f"john_test_{os.urandom(4).hex()}@staynest.com"
    reg_payload = {
        "name": "John Doe",
        "email": test_email,
        "password": "Password@123",
        "phone": "+91 91234 56789",
        "role": "student"
    }
    res = client.post('/api/auth/register', json=reg_payload)
    assert res.status_code == 201
    data = res.get_json()
    token = data["token"]
    print(f"[TEST 4] User Registration: Created {test_email} with JWT token [OK]")

    # 5. User Profile
    res = client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.get_json()["user"]
    assert user_data["email"] == test_email
    print(f"[TEST 5] Authenticated Profile /api/auth/me: Verified user ID {user_data['id']} [OK]")

    # 6. Save / Bookmark Hostel
    res = client.post('/api/saved/1', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    res_saved = client.get('/api/saved', headers={"Authorization": f"Bearer {token}"})
    assert 1 in res_saved.get_json()["saved"]
    print(f"[TEST 6] Saved Wishlist API: Hostel 1 bookmarked successfully [OK]")

    # 7. Create Booking & Generate Razorpay Order
    booking_payload = {
        "hostel_id": 1,
        "check_in_date": "2026-11-01",
        "duration_months": 2,
        "guest_name": "John Doe",
        "guest_email": test_email,
        "guest_phone": "+91 91234 56789"
    }
    res = client.post('/api/bookings', json=booking_payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    booking_res = res.get_json()
    booking = booking_res["booking"]
    rzp_order = booking_res["razorpay_order"]
    booking_id = booking["id"]
    print(f"[TEST 7] Booking Creation: Code={booking['booking_code']}, Amount={booking['total_amount']}, Razorpay Order={rzp_order['id']} [OK]")

    # 8. Cryptographic Signature Verification & Payment Confirmation
    test_payment_id = "pay_" + os.urandom(6).hex()
    signature = payment.generate_mock_signature(rzp_order["id"], test_payment_id)
    
    pay_verify_payload = {
        "booking_id": booking_id,
        "razorpay_order_id": rzp_order["id"],
        "razorpay_payment_id": test_payment_id,
        "razorpay_signature": signature,
        "payment_method": "card"
    }
    res = client.post('/api/payments/verify', json=pay_verify_payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    verify_data = res.get_json()
    assert verify_data["success"] is True
    print(f"[TEST 8] Razorpay HMAC Signature Verification: Booking confirmed with Txn ID {verify_data['transaction_id']} [OK]")

    # 9. List User Bookings
    res = client.get('/api/bookings', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_bookings = res.get_json()["bookings"]
    assert len(user_bookings) >= 1
    assert user_bookings[0]["status"] == "confirmed"
    print(f"[TEST 9] User Bookings List: Confirmed booking retrieved with receipt details [OK]")

    # 10. List New Hostel Property
    new_hostel_payload = {
        "name": "Sunset Villa Student Living",
        "type": "Co-living",
        "price": 8500,
        "area": "Koregaon Park",
        "city": "Pune",
        "features": ["Wi-Fi", "AC", "Gym"],
        "image": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5",
        "desc": "Spacious co-living with high speed fiber internet and study rooms."
    }
    res = client.post('/api/hostels', json=new_hostel_payload)
    assert res.status_code == 201
    print(f"[TEST 10] List New Property: Property published to database with ID {res.get_json()['hostel_id']} [OK]")

    print("=" * 60)
    print("ALL 10 END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
