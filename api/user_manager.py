from redis_client import r0
from datetime import datetime
import uuid
import json
from models import User, UserCreate
from jwt_utils import hash_password, verify_password
from typing import Optional, List

class UserManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.get_user_by_email(user_data.email):
            raise ValueError("User with this email already exists")
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)
        
        user = User(
            user_id=user_id,
            email=user_data.email,
            hashed_password=hashed_password,
            roles=user_data.roles,
            created_at=datetime.utcnow().isoformat(),
            is_active=True
        )
        
        # Store user in Redis
        user_key = f"user:{user_id}"
        email_key = f"email:{user_data.email}"
        
        # Store user data
        self.redis.hset(user_key, mapping={
            "user_id": user.user_id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "roles": ",".join(user.roles),
            "created_at": user.created_at,
            "is_active": str(user.is_active)
        })
        
        # Create email -> user_id mapping
        self.redis.set(email_key, user_id)
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        user_key = f"user:{user_id}"
        user_data = self.redis.hgetall(user_key)
        
        if not user_data:
            return None
        
        return User(
            user_id=user_data["user_id"],
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            roles=user_data["roles"].split(",") if user_data["roles"] else [],
            created_at=user_data["created_at"],
            last_login=user_data.get("last_login"),
            is_active=user_data.get("is_active", "true").lower() == "true"
        )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        email_key = f"email:{email}"
        user_id = self.redis.get(email_key)
        
        if not user_id:
            return None
        
        return self.get_user_by_id(user_id)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        
        if not user or not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        self.update_last_login(user.user_id)
        
        return user

    def list_users(self) -> List[User]:
        """Get all users"""
        user_keys = self.redis.keys("user:*")
        users = []
        
        for user_key in user_keys:
            user_data = self.redis.hgetall(user_key)
            if user_data:
                users.append(User(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    hashed_password=user_data["hashed_password"],
                    roles=user_data["roles"].split(",") if user_data["roles"] else [],
                    created_at=user_data["created_at"],
                    last_login=user_data.get("last_login"),
                    is_active=user_data.get("is_active", "true").lower() == "true"
                ))
        
        return users
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        user_key = f"user:{user_id}"
        self.redis.hset(user_key, "last_login", datetime.utcnow().isoformat())
    
    def update_user_roles(self, user_id: str, roles: List[str]):
        """Update user's roles"""
        user_key = f"user:{user_id}"
        self.redis.hset(user_key, "roles", ",".join(roles))
    
    def deactivate_user(self, user_id: str):
        """Deactivate a user"""
        user_key = f"user:{user_id}"
        self.redis.hset(user_key, "is_active", "false")

# Initialize user manager
user_manager = UserManager(r0)