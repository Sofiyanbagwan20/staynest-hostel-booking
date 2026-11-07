import os
import hmac
import hashlib
import base64
import json
import time
from functools import wraps
from flask import request, jsonify
import config

def hash_password(password: str) -> tuple[str, str]:
    """Generates a random salt and hashes the password using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    """Verifies a plain password against the stored hash and salt."""
    computed_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hmac.compare_digest(computed_hash, pwd_hash)

def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64_url_decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4)) if len(s) % 4 != 0 else ''
    return base64.urlsafe_b64decode(s + padding)

def generate_token(user_id: int, email: str, name: str, expires_in_days: int = 7) -> str:
    """Generates a secure signed JWT-style token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": int(time.time()) + (expires_in_days * 86400),
        "iat": int(time.time())
    }
    header_b64 = _b64_url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64_url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    
    signature = hmac.new(
        config.JWT_SECRET.encode('utf-8'),
        signing_input,
        hashlib.sha256
    ).digest()
    sig_b64 = _b64_url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_token(token: str) -> dict | None:
    """Validates token signature and expiration, returns payload or None."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        
        expected_sig = hmac.new(
            config.JWT_SECRET.encode('utf-8'),
            signing_input,
            hashlib.sha256
        ).digest()
        
        actual_sig = _b64_url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_data = json.loads(_b64_url_decode(payload_b64).decode('utf-8'))
        if payload_data.get("exp", 0) < time.time():
            return None # Expired
            
        return payload_data
    except Exception:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        
        if not token:
            return jsonify({"success": False, "error": "Authorization token missing"}), 401
            
        payload = verify_token(token)
        if not payload:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 401
            
        return f(payload, *args, **kwargs)
    return decorated
