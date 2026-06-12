"""User persistence backed by Postgres (SQLAlchemy).

Methods take a request-scoped Session (FastAPI `Depends(get_db)`). Returns ORM
`User` instances; callers read `.id`, `.email`, `.roles`, etc.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models import User
from models import UserCreate
from jwt_utils import hash_password, verify_password


class UserManager:
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create a new user. Always assigns the plain 'user' role."""
        if self.get_user_by_email(db, user_data.email):
            raise ValueError("User with this email already exists")

        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            roles=["user"],  # never trust client-supplied roles
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        return db.get(User, user_id)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.scalar(select(User).where(User.email == email))

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(db, email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        user.last_login = datetime.utcnow()
        db.commit()
        return user

    def list_users(self, db: Session) -> List[User]:
        return list(db.scalars(select(User)))

    def update_user_roles(self, db: Session, user_id: str, roles: List[str]) -> None:
        user = db.get(User, user_id)
        if user:
            user.roles = roles
            db.commit()

    def set_active(self, db: Session, user_id: str, active: bool) -> None:
        user = db.get(User, user_id)
        if user:
            user.is_active = active
            db.commit()

    def deactivate_user(self, db: Session, user_id: str) -> None:
        self.set_active(db, user_id, False)


user_manager = UserManager()
