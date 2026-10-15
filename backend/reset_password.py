"""
One-time script: reset a user's password for testing.
Run with: python reset_password.py
Delete this file once you're done testing.
"""

from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

EMAIL = "kavya0308181@gmail.com"
NEW_PASSWORD = "Test1234!"

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == EMAIL).first()
    if not user:
        print(f"No user found with email: {EMAIL}")
    else:
        user.password_hash = hash_password(NEW_PASSWORD)
        db.commit()
        print(f"Success: password for {user.email} reset to '{NEW_PASSWORD}'")
finally:
    db.close()