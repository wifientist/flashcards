from fastapi import APIRouter, Request, HTTPException, status, Depends, Response
from fastapi.responses import JSONResponse
from redis_client import r0
from jwt_utils import create_access_token, create_refresh_token, verify_token
import os
from roles import require_authenticated
import uuid
from datetime import datetime


router = APIRouter(prefix='/auth')

ROLE_PASSWORDS = {
    "admin": os.getenv("ADMIN_PASSWORD", "adminpass"),
    "user": os.getenv("USER_PASSWORD", "userpass"),
}

@router.get("/whoami")
def whoami(request: Request, payload=Depends(require_authenticated)):
    return {
        "session_id": payload["session_id"],
        "roles": payload.get("roles", []),
        "authenticated": payload.get("authenticated", False)
    }

@router.post("/auth")
async def unlock(request: Request, data: dict):
    token = request.cookies.get("access_token")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    session_id = payload.get("session_id")
    redis_key = f"session:{session_id}"

    if not r0.exists(redis_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    input_password = data.get("password")

    matched_roles = []
    for role, password in ROLE_PASSWORDS.items():
        if input_password == password:
            matched_roles.append(role)

    if not matched_roles:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    # Update Redis session
    r0.hset(redis_key, mapping={
        "authenticated": "true",
        "roles": ",".join(matched_roles)
    })

    new_access_token = create_access_token(session_id, roles=matched_roles, authenticated=True)
    response = JSONResponse({"success": True})
    response.set_cookie("access_token", new_access_token, httponly=True, max_age=900)
    return response

@router.post("/start-session")
def start_session(response: Response):
    session_id = str(uuid.uuid4())
    redis_key = f"session:{session_id}"

    r0.hset(redis_key, mapping={
        "created_at": datetime.utcnow().isoformat(),
        "authenticated": "false",
        "roles": "guest"
    })

    access_token = create_access_token(session_id, roles=["guest"], authenticated=False)
    refresh_token = create_refresh_token(session_id)

    response.set_cookie("access_token", access_token, httponly=True, max_age=900)
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=604800)
    return {"message": "Session started", "session_id": session_id}

@router.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    payload = verify_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    session_id = payload.get("session_id")
    redis_key = f"session:{session_id}"

    if not r0.exists(redis_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    session_data = r0.hgetall(redis_key)
    roles = session_data.get("roles", "guest").split(",")
    authenticated = session_data.get("authenticated") == "true"

    new_access_token = create_access_token(session_id, roles=roles, authenticated=authenticated)
    response = JSONResponse({"success": True})
    response.set_cookie("access_token", new_access_token, httponly=True, max_age=900)
    return response
