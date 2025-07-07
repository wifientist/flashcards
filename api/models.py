from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

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

class AuthRequest(BaseModel):
    password: str

class SessionInfo(BaseModel):
    session_id: Optional[str] = None
    roles: List[str] = ["guest"]
    authenticated: bool = False
    message: Optional[str] = None