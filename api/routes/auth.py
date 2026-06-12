from fastapi import APIRouter, Request, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session
from jwt_utils import create_access_token, create_refresh_token, verify_token
from roles import get_current_user, require_admin
from models import SessionInfo, UserLogin, RoleUpdateRequest, AdminUserCreate
from database import get_db
from db_models import User
from user_manager import user_manager
from session_manager import session_manager
from rate_limit import rate_limit
from config import (
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    ACCESS_TOKEN_TTL_SECONDS,
    REFRESH_TOKEN_TTL_SECONDS,
)

router = APIRouter(prefix='/auth')


def _serialize_user(user: User) -> dict:
    """Public-safe user representation (never includes the password hash)."""
    return {
        "user_id": user.id,
        "email": user.email,
        "roles": list(user.roles or []),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "is_active": user.is_active,
    }


def _set_auth_cookie(response: Response, key: str, value: str, max_age: int):
    """Set an auth cookie with consistent, hardened flags."""
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )


def _clear_auth_cookie(response: Response, key: str):
    """Delete an auth cookie using the same attributes it was set with."""
    response.delete_cookie(
        key,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# NOTE: public self-registration is intentionally disabled. Users are created
# by admins via POST /auth/users (and the first admin via seed_admin.py).

@router.post(
    "/login",
    dependencies=[Depends(rate_limit("login", limit=10, window_seconds=300))],
)
async def login(response: Response, login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and create session"""
    user = user_manager.authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    roles = list(user.roles or [])

    # Create session
    session_id = session_manager.create_session(
        user_id=user.id,
        email=user.email,
        roles=roles,
        authenticated=True
    )

    # Create tokens
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        roles=roles,
        authenticated=True
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        email=user.email
    )

    # Set cookies
    _set_auth_cookie(response, "access_token", access_token, ACCESS_TOKEN_TTL_SECONDS)
    _set_auth_cookie(response, "refresh_token", refresh_token, REFRESH_TOKEN_TTL_SECONDS)
    _set_auth_cookie(response, "session_id", session_id, REFRESH_TOKEN_TTL_SECONDS)

    return {
        "message": "Login successful",
        "user": {
            "user_id": user.id,
            "email": user.email,
            "roles": roles
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
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    payload = verify_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("user_id")
    user = user_manager.get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    new_access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        roles=list(user.roles or []),
        authenticated=True
    )
    
    _set_auth_cookie(response, "access_token", new_access_token, ACCESS_TOKEN_TTL_SECONDS)
    return {"message": "Token refreshed successfully"}

@router.post("/logout")
def logout(request: Request, response: Response):
    """Logout user and invalidate session"""
    session_id = request.cookies.get("session_id")
    
    if session_id:
        session_manager.invalidate_session(session_id)
    
    _clear_auth_cookie(response, "access_token")
    _clear_auth_cookie(response, "refresh_token")
    _clear_auth_cookie(response, "session_id")

    return {"message": "Logged out successfully"}

@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    """List all users (admin only)"""
    users = user_manager.list_users(db)
    return {"users": [_serialize_user(u) for u in users]}

@router.post("/users", dependencies=[Depends(require_admin)])
def admin_create_user(data: AdminUserCreate, db: Session = Depends(get_db)):
    """Create a user with explicit roles (admin only)."""
    try:
        user = user_manager.create_user_with_roles(db, data.email, data.password, data.roles or ["user"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User created", "user_id": user.id, "email": user.email}

@router.put("/users/{user_id}/roles")
def update_user_roles(user_id: str, role_update: RoleUpdateRequest,
                      db: Session = Depends(get_db), payload=Depends(require_admin)):
    """Update user roles (admin only)"""
    user = user_manager.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Guard against an admin removing their own admin role and locking themselves out.
    if user_id == payload["user_id"] and "admin" not in role_update.roles:
        raise HTTPException(status_code=400, detail="You can't remove your own admin role")

    user_manager.update_user_roles(db, user_id, role_update.roles)

    # Invalidate user's sessions to force re-authentication with new roles
    session_manager.invalidate_user_sessions(user_id)

    return {"message": "User roles updated successfully"}

@router.delete("/users/{user_id}")
def deactivate_user(user_id: str, db: Session = Depends(get_db), payload=Depends(require_admin)):
    """Deactivate a user (admin only)"""
    user = user_manager.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_id == payload["user_id"]:
        raise HTTPException(status_code=400, detail="You can't deactivate yourself")

    user_manager.set_active(db, user_id, False)
    session_manager.invalidate_user_sessions(user_id)
    return {"message": "User deactivated successfully"}

@router.post("/users/{user_id}/activate", dependencies=[Depends(require_admin)])
def reactivate_user(user_id: str, db: Session = Depends(get_db)):
    """Reactivate a user (admin only)"""
    user = user_manager.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_manager.set_active(db, user_id, True)
    return {"message": "User reactivated successfully"}