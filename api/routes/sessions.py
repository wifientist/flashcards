from fastapi import APIRouter, Request, Response, Depends, HTTPException, Cookie
from fastapi.responses import JSONResponse, RedirectResponse
from redis_client import r0
from jwt_utils import create_jwt, verify_jwt  # or paste inline
import uuid
from datetime import datetime

router = APIRouter()

SESSION_COOKIE_NAME = "session"

def get_current_user(session: str = Cookie(None)):
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = verify_jwt(session)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return data["user_id"]

@router.post("/start-session")
def start_session(response: Response):
    user_id = str(uuid.uuid4())
    # Create empty session in Redis (DB 0)
    r0.hset(f"session:{user_id}", mapping={"created_at": datetime.utcnow().isoformat()})
    token = create_jwt(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=60 * 60 * 24 * 30  # 30 days
    )
    return {"message": "Session started", "user_id": user_id}

@router.get("/recover/{user_id}")
def recover_session(user_id: str, response: Response):
    if not r0.exists(f"session:{user_id}"):
        raise HTTPException(status_code=404, detail="User not found")
    token = create_jwt(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=60 * 60 * 24 * 30
    )
    return {"message": "Session recovered"}

@router.get("/whoami")
def whoami(request: Request, user_id: str = Depends(get_current_user)):
    #print(f'whoami {request.cookies}')
    return {"user_id": user_id}

