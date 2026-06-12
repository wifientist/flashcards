"""Lightweight Redis-backed rate limiting.

Implemented as a FastAPI dependency factory using a fixed-window counter in
Redis (db0). Reuses existing infrastructure rather than adding a dependency.
Keys are scoped by client IP + an endpoint-specific scope string.
"""
from fastapi import Request, HTTPException, status
from redis_client import r0


def _client_ip(request: Request) -> str:
    """Best-effort client IP, honoring a single proxy hop via X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, limit: int, window_seconds: int):
    """Build a dependency that allows `limit` requests per `window_seconds`
    per client IP for the given `scope`.

    Fails open: if Redis is unavailable we allow the request rather than
    locking users out of auth entirely.
    """
    def dependency(request: Request):
        ip = _client_ip(request)
        key = f"ratelimit:{scope}:{ip}"
        try:
            current = r0.incr(key)
            if current == 1:
                r0.expire(key, window_seconds)
        except Exception:
            return  # fail open on Redis errors

        if current > limit:
            ttl = r0.ttl(key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
