from fastapi import APIRouter, Request, HTTPException, status, Depends, Response
from fastapi.responses import JSONResponse
from jwt_utils import create_access_token, create_refresh_token, verify_token
from roles import require_authenticated, get_current_user, require_admin
from models import (
    AuthRequest, SessionInfo, UserCreate, UserLogin, 
    UserInfo, RoleUpdateRequest
)
from user_manager import user_manager
from session_manager import session_manager
from datetime import datetime
import uuid

router = APIRouter(prefix='/auth')

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.post("/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = user_manager.create_user(user_data)
        return {
            "message": "User created successfully",
            "user_id": user.user_id,
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login")
async def login(response: Response, login_data: UserLogin):
    """Authenticate user and create session"""
    user = user_manager.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create session
    session_id = session_manager.create_session(
        user_id=user.user_id,
        email=user.email,
        roles=user.roles,
        authenticated=True
    )
    
    # Create tokens
    access_token = create_access_token(
        user_id=user.user_id,
        email=user.email,
        roles=user.roles,
        authenticated=True
    )
    refresh_token = create_refresh_token(
        user_id=user.user_id,
        email=user.email
    )
    
    # Set cookies
    response.set_cookie("access_token", access_token, httponly=True, max_age=900)
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=604800)
    response.set_cookie("session_id", session_id, httponly=True, max_age=604800)
    
    return {
        "message": "Login successful",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "roles": user.roles
        }
    }

@router.get("/whoami", response_model=SessionInfo)
def whoami(request: Request, payload=Depends(get_current_user)):
    """Get current user info"""
    if not payload:
        return SessionInfo(
            user_id=None,
            email=None,
            roles=["guest"],
            authenticated=False,
            message="No active session"
        )
    
    return SessionInfo(
        user_id=payload.get("user_id"),
        email=payload.get("email"),
        roles=payload.get("roles", ["guest"]),
        authenticated=payload.get("authenticated", False)
    )

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    payload = verify_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("user_id")
    user = user_manager.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    new_access_token = create_access_token(
        user_id=user.user_id,
        email=user.email,
        roles=user.roles,
        authenticated=True
    )
    
    response.set_cookie("access_token", new_access_token, httponly=True, max_age=900)
    return {"message": "Token refreshed successfully"}

@router.post("/logout")
def logout(request: Request, response: Response):
    """Logout user and invalidate session"""
    session_id = request.cookies.get("session_id")
    
    if session_id:
        session_manager.invalidate_session(session_id)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("session_id")
    
    return {"message": "Logged out successfully"}

@router.get("/users", dependencies=[Depends(require_admin)])
def list_users():
    """List all users (admin only)"""
    
    users = user_manager.list_users()
    if users:
        return {"users": users}
    else:
        return {"message": "No users found"}

@router.put("/users/{user_id}/roles", dependencies=[Depends(require_admin)])
def update_user_roles(user_id: str, role_update: RoleUpdateRequest):
    """Update user roles (admin only)"""
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_manager.update_user_roles(user_id, role_update.roles)
    
    # Invalidate user's sessions to force re-authentication with new roles
    session_manager.invalidate_user_sessions(user_id)
    
    return {"message": "User roles updated successfully"}

@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def deactivate_user(user_id: str):
    """Deactivate a user (admin only)"""
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_manager.deactivate_user(user_id)
    session_manager.invalidate_user_sessions(user_id)
    
    return {"message": "User deactivated successfully"}