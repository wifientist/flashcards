from jose import jwt, JWTError
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("JWT_SECRET", "notastrongpassword")
ALGORITHM = "HS256"

def create_access_token(session_id: str, roles: list, authenticated: bool = False):
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "session_id": session_id,
        "authenticated": authenticated,
        "roles": roles,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(session_id: str):
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "session_id": session_id,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
