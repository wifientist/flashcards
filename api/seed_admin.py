"""Bootstrap the first admin user.

Reads ADMIN_EMAIL / ADMIN_PASSWORD from the environment (.env) and creates an
admin user if one doesn't already exist. Idempotent: if the email exists it is
promoted to admin rather than duplicated.

Usage:
    python seed_admin.py
"""
import os
import sys

from database import SessionLocal
from db_models import User
from jwt_utils import hash_password
from user_manager import user_manager


def main() -> int:
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be set (see api/.env.example).")
        return 1

    db = SessionLocal()
    try:
        existing = user_manager.get_user_by_email(db, email)
        if existing:
            if "admin" not in (existing.roles or []):
                existing.roles = sorted(set((existing.roles or []) + ["admin"]))
                db.commit()
                print(f"Promoted existing user {email!r} to admin.")
            else:
                print(f"Admin user {email!r} already exists. Nothing to do.")
            return 0

        admin = User(
            email=email,
            hashed_password=hash_password(password),
            roles=["user", "admin"],
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin user {email!r}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
