# from fastapi import Request, HTTPException, status
# from jwt_utils import verify_token

# def get_current_session(request: Request):
#     """Get current session info without requiring authentication"""
#     token = request.cookies.get("access_token")
#     if not token:
#         return None
    
#     payload = verify_token(token)
#     return payload

# def require_authenticated(request: Request):
#     token = request.cookies.get("access_token")
#     if not token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

#     payload = verify_token(token)
#     if not payload or not payload.get("authenticated"):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
#     return payload

# def require_roles(required_roles: list):
#     def role_checker(request: Request):
#         token = request.cookies.get("access_token")
#         if not token:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

#         payload = verify_token(token)
#         if not payload or not payload.get("authenticated"):
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

#         user_roles = payload.get("roles", [])
#         if not any(role in user_roles for role in required_roles):
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

#         return payload
#     return role_checker

from fastapi import Request, HTTPException, status
from jwt_utils import verify_token
from session_manager import session_manager

def get_current_user(request: Request):
    """Get current user info without requiring authentication"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    # Update session activity
    session_id = request.cookies.get("session_id")
    if session_id:
        session_manager.update_session_activity(session_id)
    
    return payload

def require_authenticated(request: Request):
    """Require user to be authenticated"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing access token"
        )

    payload = verify_token(token)
    if not payload or not payload.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication required"
        )
    
    return payload

def require_roles(required_roles: list):
    """Require user to have one of the specified roles"""
    def role_checker(request: Request):
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Missing access token"
            )

        payload = verify_token(token)
        if not payload or not payload.get("authenticated"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Authentication required"
            )

        user_roles = payload.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Insufficient permissions"
            )

        return payload
    return role_checker

def require_admin(request: Request):
    """Require admin role"""
    return require_roles(["admin"])(request)
