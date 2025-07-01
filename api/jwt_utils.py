import jwt
import uuid
from datetime import datetime, timedelta

SECRET_KEY = "super_secret_key"  # Change this!

def create_jwt(user_id):
    payload = {
        "user_id": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    #print(f'creating jwt {payload}')
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt(token):
    #print(f'verifying {token}')
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
