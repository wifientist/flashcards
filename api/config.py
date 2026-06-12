"""Centralized application configuration.

Loads settings from the environment (.env) and validates the critical ones at
import time so the app fails fast on misconfiguration instead of silently
running insecurely.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Values we refuse to start with — these are the placeholders shipped in the
# repo and must be replaced before the app will boot outside of explicit dev.
_INSECURE_SECRETS = {"notastrongpassword", "changeme", "secret", ""}


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable {name!r} is not set. "
            f"Copy api/.env.example to api/.env and fill it in."
        )
    return value


# --- Environment -----------------------------------------------------------
# "development" relaxes a few constraints (e.g. allows the cookie to be sent
# over http://localhost). Anything else is treated as production.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT not in ("development", "dev", "local", "test")

# --- Auth / JWT ------------------------------------------------------------
JWT_SECRET_KEY = _require("JWT_SECRET_KEY")
JWT_DECODE_ALGO = os.getenv("JWT_DECODE_ALGO", "HS256")

if JWT_SECRET_KEY.strip().lower() in _INSECURE_SECRETS:
    raise RuntimeError(
        "JWT_SECRET_KEY is set to a known-insecure placeholder value. "
        "Generate a strong secret, e.g.:  python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

# --- CORS ------------------------------------------------------------------
# Comma-separated list of allowed browser origins. Must be explicit because we
# use credentialed (cookie) requests, which forbid the "*" wildcard.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5177,http://127.0.0.1:5177",
    ).split(",")
    if origin.strip()
]

# --- Cookies ---------------------------------------------------------------
# In production cookies must be Secure (HTTPS-only). In local dev we relax this
# so login works over http://localhost.
COOKIE_SECURE = IS_PRODUCTION
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

ACCESS_TOKEN_TTL_SECONDS = 15 * 60          # 15 minutes
REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
