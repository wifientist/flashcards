from jose import jwt, JWTError
from datetime import datetime, timedelta
import bcrypt
import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_DECODE_ALGO = os.getenv("JWT_DECODE_ALGO", "HS256")

def create_access_token(user_id: str, email: str, roles: list, authenticated: bool = False):
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "user_id": user_id,
        "email": email,
        "authenticated": authenticated,
        "roles": roles,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_DECODE_ALGO)

def create_refresh_token(user_id: str, email: str):
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_DECODE_ALGO)

def verify_token(token):
    """Verify JWT token and return payload"""
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_DECODE_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

