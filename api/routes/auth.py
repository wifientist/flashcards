from fastapi import APIRouter, Request, HTTPException, status, Depends, Response
from fastapi.responses import JSONResponse
from redis_client import r0
from jwt_utils import create_access_token, create_refresh_token, verify_token
import os
from roles import require_authenticated, get_current_session
from models import AuthRequest, SessionInfo  # Import the new models
import uuid
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix='/auth')

ROLE_PASSWORDS = {
    "admin": os.getenv("ADMIN_PASSWORD"),
    "user": os.getenv("USER_PASSWORD"),
}

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.get("/whoami", response_model=SessionInfo)
def whoami(request: Request, payload=Depends(get_current_session)):
    """Get current session info - works for both authenticated and unauthenticated sessions"""

    if not payload:
        return SessionInfo(
            session_id=None,
            roles=["guest"],
            authenticated=False,
            message="No active session"
        )    
    return SessionInfo(
        session_id=payload["session_id"],
        roles=payload.get("roles", ["guest"]),
        authenticated=payload.get("authenticated", False)
    )

@router.post("/auth")
async def unlock(request: Request, auth_request: AuthRequest):
    """Authenticate with password to upgrade session"""
    token = request.cookies.get("access_token")
    
    # If no token exists, create a new session first
    if not token:
        session_id = str(uuid.uuid4())
        redis_key = f"session:{session_id}"
        
        # Create initial session in Redis
        r0.hset(redis_key, mapping={
            "created_at": datetime.utcnow().isoformat(),
            "authenticated": "false",
            "roles": "guest"
        })
    else:
        # Verify existing token
        try:
            payload = verify_token(token)
            if not payload:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
            session_id = payload.get("session_id")
            redis_key = f"session:{session_id}"
            
            if not r0.exists(redis_key):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")
        except Exception as e:
            # If token verification fails, create a new session
            session_id = str(uuid.uuid4())
            redis_key = f"session:{session_id}"
            
            r0.hset(redis_key, mapping={
                "created_at": datetime.utcnow().isoformat(),
                "authenticated": "false",
                "roles": "guest"
            })

    # Validate password
    input_password = auth_request.password
    matched_roles = []
    for role, password in ROLE_PASSWORDS.items():
        if input_password == password:
            matched_roles.append(role)

    if not matched_roles:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    # Update Redis session with authentication
    r0.hset(redis_key, mapping={
        "authenticated": "true",
        "roles": ",".join(matched_roles)
    })

    # Create new tokens
    new_access_token = create_access_token(session_id, roles=matched_roles, authenticated=True)
    new_refresh_token = create_refresh_token(session_id)
    
    response = JSONResponse({"success": True, "roles": matched_roles})
    response.set_cookie("access_token", new_access_token, httponly=True, max_age=900)
    response.set_cookie("refresh_token", new_refresh_token, httponly=True, max_age=604800)
    return response

@router.post("/start-session")
def start_session(response: Response):
    """Start a new unauthenticated session"""
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
    """Refresh access token using refresh token"""
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

@router.post("/logout")
def logout(request: Request, response: Response):
    """Logout - clear cookies and optionally invalidate session"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}