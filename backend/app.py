import json
import time
import secrets
from flask import Flask, request, jsonify, send_from_directory
import config
from auth import hash_password, verify_password, generate_token, token_required
import database
import payment

app = Flask(__name__, static_folder=str(config.FRONTEND_DIR))


def get_json_data():
    return request.get_json(silent=True) or {}

# CORS support for all routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/<path:dummy>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def options_handler(dummy=None):
    return ('', 204)

# ----------------- STATIC FRONTEND ROUTES -----------------
@app.route('/')
def serve_index():
    return send_from_directory(config.FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path): 
    return send_from_directory(config.FRONTEND_DIR, path)

# ----------------- HEALTH & SYSTEM APIS -----------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "database": {
            "type": database.DB_TYPE,
            "connected": True,
            "host": config.DB_HOST if database.DB_TYPE == "mysql" else "local",
            "db_name": config.DB_NAME if database.DB_TYPE == "mysql" else "staynest.db"
        },
        "gateway": "Razorpay Test Mode"
    })

# ----------------- AUTHENTICATION APIS -----------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = get_json_data()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()
    role = data.get('role', 'student')

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email and password are required"}), 400

    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

    try:
        existing = database.fetch_one("SELECT id FROM users WHERE email = %s", (email,))
        if existing:
            return jsonify({"success": False, "error": "An account with this email already exists"}), 409

        pwd_hash, salt = hash_password(password)
        user_id = database.execute(
            "INSERT INTO users (name, email, password_hash, salt, phone, role) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, email, pwd_hash, salt, phone, role)
        )

        token = generate_token(user_id, email, name)
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email,
                "phone": phone,
                "role": role
            }
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = get_json_data()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    try:
        user = database.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if not user or not verify_password(password, user['password_hash'], user['salt']):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        token = generate_token(user['id'], user['email'], user['name'])
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "phone": user.get('phone', ''),
                "role": user.get('role', 'student')
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    try:
        user = database.fetch_one("SELECT id, name, email, phone, role, created_at FROM users WHERE id = %s", (current_user['sub'],))
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        return jsonify({"success": True, "user": user})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- HOSTELS APIS -----------------
@app.route('/api/hostels', methods=['GET'])
def list_hostels():
    q = request.args.get('q', '').strip().lower()
    stay_type = request.args.get('type', 'all')
    budget = request.args.get('budget', 'all')
    chip = request.args.get('chip', 'all')

    try:
        rows = database.fetch_all("SELECT * FROM hostels ORDER BY id ASC")
        results = []
        for h in rows:
            features = json.loads(h['features']) if isinstance(h['features'], str) else (h['features'] or [])
            if q:
                search_target = f"{h['name']} {h['area']} {h['type']} {h.get('city', '')}".lower()
                if q not in search_target:
                    continue
            if stay_type != 'all' and h['type'].lower() != stay_type.lower():
                continue
            if budget != 'all':
                try:
                    if h['price'] > int(budget):
                        continue
                except ValueError:
                    pass
            if chip == 'verified' and not h['verified']:
                continue
            if chip == 'wifi' and 'Wi-Fi' not in features:
                continue
            if chip == 'meals' and 'Meals' not in features:
                continue
            if chip == 'ac' and 'AC' not in features:
                continue

            results.append({
                "id": h['id'],
                "name": h['name'],
                "type": h['type'],
                "area": h['area'],
                "city": h.get('city', 'Pune'),
                "price": h['price'],
                "rating": float(h['rating']),
                "reviews": h['reviews'],
                "verified": bool(h['verified']),
                "features": features,
                "image": h['image'],
                "desc": h.get('desc_text', '')
            })

        return jsonify({"success": True, "count": len(results), "hostels": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hostels/<int:hostel_id>', methods=['GET'])
def get_hostel(hostel_id):
    try:
        h = database.fetch_one("SELECT * FROM hostels WHERE id = %s", (hostel_id,))
        if not h:
            return jsonify({"success": False, "error": "Hostel not found"}), 404

        features = json.loads(h['features']) if isinstance(h['features'], str) else (h['features'] or [])
        return jsonify({
            "success": True,
            "hostel": {
                "id": h['id'],
                "name": h['name'],
                "type": h['type'],
                "area": h['area'],
                "city": h.get('city', 'Pune'),
                "price": h['price'],
                "rating": float(h['rating']),
                "reviews": h['reviews'],
                "verified": bool(h['verified']),
                "features": features,
                "image": h['image'],
                "desc": h.get('desc_text', '')
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hostels', methods=['POST'])
def create_hostel():
    data = get_json_data()
    name = data.get('name', '').strip()
    stay_type = data.get('type', 'Co-living')
    area = data.get('area', '').strip()
    city = data.get('city', 'Pune').strip()
    try:
        price = int(data.get('price', 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Property price must be a valid number"}), 400
    features = data.get('features', ["Wi-Fi", "Security"])
    image = data.get('image', 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=900&q=80')
    desc = data.get('desc', 'Modern, newly listed property with essential amenities.')

    if not name or not area or price <= 0:
        return jsonify({"success": False, "error": "Property name, area, and monthly rent are required"}), 400

    try:
        new_id = database.execute("""
            INSERT INTO hostels (name, type, area, city, price, rating, reviews, verified, features, image, desc_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, stay_type, area, city, price, 4.5, 1, 1, json.dumps(features), image, desc))

        return jsonify({
            "success": True,
            "message": "Hostel listed successfully",
            "hostel_id": new_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- SAVED / WISHLIST APIS -----------------
@app.route('/api/saved', methods=['GET'])
@token_required
def get_saved(current_user):
    try:
        rows = database.fetch_all("SELECT hostel_id FROM saved_stays WHERE user_id = %s", (current_user['sub'],))
        saved_ids = [r['hostel_id'] for r in rows]
        return jsonify({"success": True, "saved": saved_ids})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/saved/<int:hostel_id>', methods=['POST'])
@token_required
def toggle_save(current_user, hostel_id):
    try:
        existing = database.fetch_one("SELECT id FROM saved_stays WHERE user_id = %s AND hostel_id = %s", (current_user['sub'], hostel_id))
        if existing:
            database.execute("DELETE FROM saved_stays WHERE id = %s", (existing['id'],))
            is_saved = False
            msg = "Removed from saved stays"
        else:
            database.execute("INSERT INTO saved_stays (user_id, hostel_id) VALUES (%s, %s)", (current_user['sub'], hostel_id))
            is_saved = True
            msg = "Saved to your list"

        return jsonify({"success": True, "saved": is_saved, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- BOOKING & PAYMENT APIS -----------------
@app.route('/api/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    data = get_json_data()
    hostel_id = data.get('hostel_id')
    check_in_date = data.get('check_in_date', '')
    try:
        duration_months = int(data.get('duration_months', 1))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "duration_months must be a valid integer"}), 400
    if duration_months <= 0:
        return jsonify({"success": False, "error": "duration_months must be greater than zero"}), 400
    guest_name = data.get('guest_name', current_user.get('name', ''))
    guest_email = data.get('guest_email', current_user.get('email', ''))
    guest_phone = data.get('guest_phone', '')

    if not hostel_id or not check_in_date or not guest_name:
        return jsonify({"success": False, "error": "Hostel, check-in date, and guest name are required"}), 400

    try:
        hostel = database.fetch_one("SELECT * FROM hostels WHERE id = %s", (hostel_id,))
        if not hostel:
            return jsonify({"success": False, "error": "Hostel not found"}), 404

        total_amount = hostel['price'] * duration_months
        booking_code = f"SN-{int(time.time())}-{secrets.token_hex(2).upper()}"

        booking_id = database.execute("""
            INSERT INTO bookings (booking_code, user_id, hostel_id, check_in_date, duration_months, total_amount, guest_name, guest_email, guest_phone, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """, (booking_code, current_user['sub'], hostel_id, check_in_date, duration_months, total_amount, guest_name, guest_email, guest_phone))

        # Generate Razorpay-compliant Order
        razorpay_order = payment.create_order(
            amount_in_inr=total_amount,
            receipt_id=booking_code,
            notes={"booking_id": booking_id, "hostel_name": hostel['name']}
        )

        return jsonify({
            "success": True,
            "message": "Booking created. Ready for payment.",
            "booking": {
                "id": booking_id,
                "booking_code": booking_code,
                "hostel_name": hostel['name'],
                "total_amount": total_amount,
                "check_in_date": check_in_date,
                "duration_months": duration_months,
                "status": "pending"
            },
            "razorpay_order": razorpay_order
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
@token_required
def list_user_bookings(current_user):
    try:
        rows = database.fetch_all("""
            SELECT b.*, h.name as hostel_name, h.area as hostel_area, h.image as hostel_image,
                   p.razorpay_payment_id, p.payment_method, p.created_at as paid_at
            FROM bookings b
            JOIN hostels h ON b.hostel_id = h.id
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE b.user_id = %s
            ORDER BY b.id DESC
        """, (current_user['sub'],))
        return jsonify({"success": True, "bookings": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
@token_required
def get_booking(current_user, booking_id):
    try:
        booking = database.fetch_one("""
            SELECT b.*, h.name as hostel_name, h.area as hostel_area, h.image as hostel_image,
                   p.razorpay_payment_id, p.payment_method, p.created_at as paid_at
            FROM bookings b
            JOIN hostels h ON b.hostel_id = h.id
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE b.id = %s AND b.user_id = %s
        """, (booking_id, current_user['sub']))

        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404

        return jsonify({"success": True, "booking": booking})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/payments/verify', methods=['POST'])
@token_required
def verify_payment(current_user):
    data = get_json_data()
    booking_id = data.get('booking_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')
    payment_method = data.get('payment_method', 'card')

    if not booking_id or not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return jsonify({"success": False, "error": "Missing required payment parameters"}), 400

    # Cryptographic HMAC-SHA256 signature verification
    is_valid = payment.verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    if not is_valid:
        return jsonify({"success": False, "error": "Invalid payment signature. Security verification failed."}), 400

    try:
        booking = database.fetch_one("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, current_user['sub']))
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404

        # Record payment in payments table
        database.execute("""
            INSERT INTO payments (booking_id, user_id, amount, currency, gateway, razorpay_order_id, razorpay_payment_id, razorpay_signature, status, payment_method)
            VALUES (%s, %s, %s, 'INR', 'razorpay', %s, %s, %s, 'success', %s)
        """, (booking_id, current_user['sub'], booking['total_amount'], razorpay_order_id, razorpay_payment_id, razorpay_signature, payment_method))

        # Update booking status to confirmed
        database.execute("UPDATE bookings SET status = 'confirmed' WHERE id = %s", (booking_id,))

        return jsonify({
            "success": True,
            "message": "Payment verified and booking confirmed successfully!",
            "booking_id": booking_id,
            "booking_code": booking['booking_code'],
            "transaction_id": razorpay_payment_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/payments/test-signature', methods=['POST'])
def test_signature():
    """Generates an authentic signature for frontend test checkout simulation."""
    data = get_json_data()
    order_id = data.get('order_id', '')
    payment_id = data.get('payment_id', f"pay_{secrets.token_hex(7)}")
    sig = payment.generate_mock_signature(order_id, payment_id)
    return jsonify({
        "success": True,
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": sig
    })

if __name__ == '__main__':
    print("Initializing StayNest Database...")
    success, msg = database.init_db()
    print(f"Database status: {msg} [Active Engine: {database.DB_TYPE.upper()}]")
    print("Starting StayNest Server on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
