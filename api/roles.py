from fastapi import Request, HTTPException, status
from jwt_utils import verify_token

# def require_authenticated(request: Request):
#     token = request.cookies.get("access_token")
#     payload = verify_token(token)
#     if not payload or not payload.get("authenticated"):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
#     return payload

# def require_roles(required_roles: list):
#     def role_checker(request: Request):
#         token = request.cookies.get("access_token")
#         payload = verify_token(token)
#         if not payload or not payload.get("authenticated"):
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

#         user_roles = payload.get("roles", [])
#         if not any(role in user_roles for role in required_roles):
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

#         return payload
#     return role_checker


def require_authenticated(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    payload = verify_token(token)
    if not payload or not payload.get("authenticated"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return payload

def require_roles(required_roles: list):
    def role_checker(request: Request):
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

        payload = verify_token(token)
        if not payload or not payload.get("authenticated"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        user_roles = payload.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        return payload
    return role_checker
