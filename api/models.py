from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum
from datetime import datetime

class RoleUpdateRequest(BaseModel):
    roles: list[str]

class CardCreate(BaseModel):
    front: str
    back: str
    labels: Optional[List[str]] = []

class CardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    labels: Optional[List[str]] = None

class ProgressStatus(str, Enum):
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    MASTERED = "mastered"
    DIFFICULT = "difficult"

class ProgressUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[ProgressStatus] = None
    # True only for an actual review event (study flow); editing notes/status
    # alone must NOT inflate review_count/last_reviewed.
    reviewed: bool = False

class UserProgress(BaseModel):
    card_id: str
    notes: str = ""
    status: ProgressStatus = ProgressStatus.NEW
    last_reviewed: Optional[str] = None
    review_count: int = 0

class Card(BaseModel):
    card_id: str
    front: str
    back: str
    labels: List[str] = []
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    user_progress: Optional[UserProgress] = None

class Label(BaseModel):
    label: str
    card_count: int

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    # NOTE: roles are intentionally NOT accepted from the client. New users are
    # always created with the "user" role; admin promotion happens via the
    # admin-only PUT /auth/users/{user_id}/roles endpoint.

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    created_at: str
    last_login: Optional[str] = None

class SessionInfo(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = ["guest"]
    authenticated: bool = False
    message: Optional[str] = None

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

# User management models
class User(BaseModel):
    user_id: str
    email: str
    hashed_password: str
    roles: List[str]
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True