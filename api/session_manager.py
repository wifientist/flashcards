from redis_client import r0
from datetime import datetime
import uuid
from typing import Optional

class SessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def create_session(self, user_id: str, email: str, roles: list, authenticated: bool = False) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "email": email,
            "roles": ",".join(roles),
            "authenticated": str(authenticated),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        self.redis.hset(session_key, mapping=session_data)
        
        # Set session expiry (7 days for refresh token validity)
        self.redis.expire(session_key, 604800)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        session_key = f"session:{session_id}"
        session_data = self.redis.hgetall(session_key)
        
        if not session_data:
            return None
        
        return {
            "session_id": session_data["session_id"],
            "user_id": session_data["user_id"],
            "email": session_data["email"],
            "roles": session_data["roles"].split(",") if session_data["roles"] else [],
            "authenticated": session_data["authenticated"].lower() == "true",
            "created_at": session_data["created_at"],
            "last_activity": session_data.get("last_activity")
        }
    
    def update_session_activity(self, session_id: str):
        """Update session's last activity"""
        session_key = f"session:{session_id}"
        self.redis.hset(session_key, "last_activity", datetime.utcnow().isoformat())
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        session_key = f"session:{session_id}"
        self.redis.delete(session_key)
    
    def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        # This would require indexing sessions by user_id
        # For now, we'll implement a simple approach
        keys = self.redis.keys("session:*")
        for key in keys:
            session_data = self.redis.hgetall(key)
            if session_data.get("user_id") == user_id:
                self.redis.delete(key)

# Initialize session manager
session_manager = SessionManager(r0)
