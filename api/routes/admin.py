from fastapi import APIRouter, HTTPException, status, Depends
from redis_client import r0
from roles import require_roles
import uuid
from models import RoleUpdateRequest

router = APIRouter(prefix='/admin')

@router.get("/sessions")
def list_sessions(payload=Depends(require_roles(["admin"]))):
    cursor = 0
    sessions = []

    while True:
        cursor, keys = r0.scan(cursor=cursor, match="session:*", count=100)
        for key in keys:
            session_id = key.split(":")[1]
            data = r0.hgetall(key)
            sessions.append({
                "session_id": session_id,
                "authenticated": data.get("authenticated"),
                "roles": data.get("roles", "").split(","),
                "created_at": data.get("created_at")
            })
        if cursor == 0:
            break

    return {"sessions": sessions}

@router.post("/sessions/{session_id}/roles")
def update_roles(session_id: str, role_request: RoleUpdateRequest, payload=Depends(require_roles(["admin"]))):
    redis_key = f"session:{session_id}"

    if not r0.exists(redis_key):
        raise HTTPException(status_code=404, detail="Session not found")

    roles = role_request.roles
    r0.hset(redis_key, "roles", ",".join(roles))
    return {"message": f"Roles updated for session {session_id}", "roles": roles}

#aka force logout
@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, payload=Depends(require_roles(["admin"]))):
    redis_key = f"session:{session_id}"

    if not r0.exists(redis_key):
        raise HTTPException(status_code=404, detail="Session not found")

    r0.delete(redis_key)
    return {
        "message": f"Session {session_id} deleted",
        "session_id": session_id,
        "status": "force_logged_out"
    }
