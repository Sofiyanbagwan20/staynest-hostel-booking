import json
import os
import sqlite3
from pathlib import Path
import config
from auth import hash_password

DB_TYPE = "mysql"  # Default attempt
SQLITE_DB_PATH = Path(__file__).resolve().parent / "staynest.db"

INITIAL_HOSTELS = [
    {
        "id": 1,
        "name": "Greenwood Student Living",
        "type": "Girls",
        "area": "Shivajinagar, Pune",
        "city": "Pune",
        "price": 6500,
        "rating": 4.8,
        "reviews": 124,
        "verified": True,
        "features": ["Wi-Fi", "Meals", "AC"],
        "image": "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80",
        "desc_text": "A bright, comfortable stay with study-friendly spaces, friendly staff and easy access to colleges and public transport."
    },
    {
        "id": 2,
        "name": "The Urban Nest",
        "type": "Co-living",
        "area": "Kothrud, Pune",
        "city": "Pune",
        "price": 8000,
        "rating": 4.7,
        "reviews": 98,
        "verified": True,
        "features": ["Wi-Fi", "AC", "Laundry"],
        "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80",
        "desc_text": "Modern co-living with thoughtfully furnished rooms, shared common areas and a relaxed community atmosphere."
    },
    {
        "id": 3,
        "name": "Sunrise Girls Hostel",
        "type": "Girls",
        "area": "FC Road, Pune",
        "city": "Pune",
        "price": 5500,
        "rating": 4.6,
        "reviews": 86,
        "verified": True,
        "features": ["Wi-Fi", "Meals", "Security"],
        "image": "https://images.unsplash.com/photo-1564078516393-cf04bd966897?auto=format&fit=crop&w=900&q=80",
        "desc_text": "A welcoming girls hostel with secure entry, home-style meals and convenient access to shops and transit."
    },
    {
        "id": 4,
        "name": "Oakwood Residency",
        "type": "Boys",
        "area": "Aundh, Pune",
        "city": "Pune",
        "price": 9000,
        "rating": 4.9,
        "reviews": 152,
        "verified": True,
        "features": ["Wi-Fi", "AC", "Gym"],
        "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80",
        "desc_text": "Spacious rooms and useful amenities for students and working professionals looking for a premium stay."
    },
    {
        "id": 5,
        "name": "Maple House",
        "type": "Co-living",
        "area": "Viman Nagar, Pune",
        "city": "Pune",
        "price": 7200,
        "rating": 4.5,
        "reviews": 73,
        "verified": False,
        "features": ["Wi-Fi", "Laundry", "Meals"],
        "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80",
        "desc_text": "An affordable, relaxed home base with shared facilities, furnished rooms and easy connections across the city."
    },
    {
        "id": 6,
        "name": "Campus Corner Hostel",
        "type": "Boys",
        "area": "Pimpri, Pune",
        "city": "Pune",
        "price": 4800,
        "rating": 4.4,
        "reviews": 61,
        "verified": True,
        "features": ["Wi-Fi", "Meals", "Security"],
        "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=900&q=80",
        "desc_text": "Budget-friendly rooms close to campus, with everyday essentials and a friendly student community."
    }
]

def try_mysql_connect(with_db=True):
    import mysql.connector
    kwargs = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "autocommit": True
    }
    if with_db:
        kwargs["database"] = config.DB_NAME
    return mysql.connector.connect(**kwargs)

def get_sqlite_conn():
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def execute(query: str, params: tuple = None) -> int:
    """Executes an INSERT/UPDATE/DELETE and returns lastrowid."""
    params = params or ()
    global DB_TYPE
    if DB_TYPE == "mysql":
        conn = try_mysql_connect(with_db=True)
        cursor = conn.cursor()
        cursor.execute(query, params)
        last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return last_id
    else:
        # Adapt %s to ? for SQLite
        q_adapted = query.replace("%s", "?")
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(q_adapted, params)
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return last_id

def fetch_all(query: str, params: tuple = None) -> list[dict]:
    params = params or ()
    global DB_TYPE
    if DB_TYPE == "mysql":
        conn = try_mysql_connect(with_db=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    else:
        q_adapted = query.replace("%s", "?")
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(q_adapted, params)
        rows = cursor.fetchall()
        result = [dict(r) for r in rows]
        cursor.close()
        conn.close()
        return result

def fetch_one(query: str, params: tuple = None) -> dict | None:
    params = params or ()
    global DB_TYPE
    if DB_TYPE == "mysql":
        conn = try_mysql_connect(with_db=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None
    else:
        q_adapted = query.replace("%s", "?")
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(q_adapted, params)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None

def init_db():
    global DB_TYPE
    # First: attempt MySQL
    try:
        import mysql.connector
        server_conn = try_mysql_connect(with_db=False)
        c = server_conn.cursor()
        c.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        c.close()
        server_conn.close()

        db_conn = try_mysql_connect(with_db=True)
        c = db_conn.cursor()

        # Users table
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(191) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(64) NOT NULL,
            phone VARCHAR(30) DEFAULT '',
            role VARCHAR(20) DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)

        # Hostels table
        c.execute("""
        CREATE TABLE IF NOT EXISTS hostels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            type VARCHAR(50) NOT NULL,
            area VARCHAR(150) NOT NULL,
            city VARCHAR(80) DEFAULT 'Pune',
            price INT NOT NULL,
            rating DECIMAL(2,1) DEFAULT 4.5,
            reviews INT DEFAULT 1,
            verified BOOLEAN DEFAULT TRUE,
            features JSON,
            image TEXT,
            desc_text TEXT,
            owner_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)

        # Bookings table
        c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_code VARCHAR(50) NOT NULL UNIQUE,
            user_id INT NOT NULL,
            hostel_id INT NOT NULL,
            check_in_date VARCHAR(20) NOT NULL,
            duration_months INT DEFAULT 1,
            total_amount INT NOT NULL,
            guest_name VARCHAR(120) NOT NULL,
            guest_email VARCHAR(191) NOT NULL,
            guest_phone VARCHAR(30) NOT NULL,
            status VARCHAR(30) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)

        # Payments table
        c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL,
            user_id INT NOT NULL,
            amount INT NOT NULL,
            currency VARCHAR(10) DEFAULT 'INR',
            gateway VARCHAR(50) DEFAULT 'razorpay',
            razorpay_order_id VARCHAR(100) NOT NULL,
            razorpay_payment_id VARCHAR(100) NOT NULL,
            razorpay_signature VARCHAR(255) NOT NULL,
            status VARCHAR(30) DEFAULT 'success',
            payment_method VARCHAR(50) DEFAULT 'card',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)

        # Saved stays table
        c.execute("""
        CREATE TABLE IF NOT EXISTS saved_stays (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            hostel_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_hostel (user_id, hostel_id)
        ) ENGINE=InnoDB;
        """)

        # Seed initial user
        c.execute("SELECT COUNT(*) FROM users;")
        if c.fetchone()[0] == 0:
            pwd_hash, salt = hash_password("Password@123")
            c.execute(
                "INSERT INTO users (name, email, password_hash, salt, phone, role) VALUES (%s, %s, %s, %s, %s, %s)",
                ("Demo Student", "demo@staynest.com", pwd_hash, salt, "+91 98765 43210", "student")
            )
            print("[OK] Seeded demo student in MySQL: demo@staynest.com / Password@123")

        # Seed initial hostels
        c.execute("SELECT COUNT(*) FROM hostels;")
        if c.fetchone()[0] == 0:
            for h in INITIAL_HOSTELS:
                c.execute("""
                    INSERT INTO hostels (name, type, area, city, price, rating, reviews, verified, features, image, desc_text)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    h["name"], h["type"], h["area"], h["city"], h["price"],
                    h["rating"], h["reviews"], h["verified"],
                    json.dumps(h["features"]), h["image"], h["desc_text"]
                ))
            print("[OK] Seeded initial hostels in MySQL.")

        c.close()
        db_conn.close()
        DB_TYPE = "mysql"
        return True, "MySQL database connected and initialized"
    except Exception as mysql_err:
        print(f"[NOTE] MySQL unavailable ({mysql_err}). Initializing local SQLite fallback mode...")
        DB_TYPE = "sqlite"

        # Initialize SQLite fallback with identical schema
        conn = get_sqlite_conn()
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            phone TEXT DEFAULT '',
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS hostels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            area TEXT NOT NULL,
            city TEXT DEFAULT 'Pune',
            price INTEGER NOT NULL,
            rating REAL DEFAULT 4.5,
            reviews INTEGER DEFAULT 1,
            verified BOOLEAN DEFAULT 1,
            features TEXT,
            image TEXT,
            desc_text TEXT,
            owner_id INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            hostel_id INTEGER NOT NULL,
            check_in_date TEXT NOT NULL,
            duration_months INTEGER DEFAULT 1,
            total_amount INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            guest_email TEXT NOT NULL,
            guest_phone TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            currency TEXT DEFAULT 'INR',
            gateway TEXT DEFAULT 'razorpay',
            razorpay_order_id TEXT NOT NULL,
            razorpay_payment_id TEXT NOT NULL,
            razorpay_signature TEXT NOT NULL,
            status TEXT DEFAULT 'success',
            payment_method TEXT DEFAULT 'card',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS saved_stays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            hostel_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, hostel_id)
        );
        """)

        # Seed initial user in SQLite
        c.execute("SELECT COUNT(*) FROM users;")
        if c.fetchone()[0] == 0:
            pwd_hash, salt = hash_password("Password@123")
            c.execute(
                "INSERT INTO users (name, email, password_hash, salt, phone, role) VALUES (?, ?, ?, ?, ?, ?)",
                ("Demo Student", "demo@staynest.com", pwd_hash, salt, "+91 98765 43210", "student")
            )
            print("[OK] Seeded demo student in SQLite: demo@staynest.com / Password@123")

        # Seed hostels in SQLite
        c.execute("SELECT COUNT(*) FROM hostels;")
        if c.fetchone()[0] == 0:
            for h in INITIAL_HOSTELS:
                c.execute("""
                    INSERT INTO hostels (name, type, area, city, price, rating, reviews, verified, features, image, desc_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    h["name"], h["type"], h["area"], h["city"], h["price"],
                    h["rating"], h["reviews"], 1 if h["verified"] else 0,
                    json.dumps(h["features"]), h["image"], h["desc_text"]
                ))
            print("[OK] Seeded initial hostels in SQLite.")

        conn.commit()
        conn.close()
        return True, "SQLite database initialized (fallback mode)"
