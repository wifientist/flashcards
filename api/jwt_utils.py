from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_DECODE_ALGO = os.getenv("JWT_DECODE_ALGO", "HS256")

def create_access_token(session_id: str, roles: list, authenticated: bool = False):
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "session_id": session_id,
        "authenticated": authenticated,
        "roles": roles,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_DECODE_ALGO)

def create_refresh_token(session_id: str):
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "session_id": session_id,
        "exp": expire
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