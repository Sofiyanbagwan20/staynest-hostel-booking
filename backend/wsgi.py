import database
from app import app

success, message = database.init_db()
if not success:
    raise RuntimeError(f"Database initialization failed: {message}")

print(f"StayNest database initialized: {message}")
