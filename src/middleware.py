"""
Security middleware and helpers.
Verifies JWT tokens by calling the Auth Service (inter-service communication).
"""

import os
import logging
import httpx
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
security = HTTPBearer(auto_error=False)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        return response


async def verify_token(
    credentials: HTTPAuthorizationCredentials = None,
) -> dict:
    """
    Validates JWT by calling the Auth Service /auth/verify endpoint.
    Returns decoded user payload on success.
    Inter-service communication demo point.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    token = credentials.credentials
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/auth/verify",
                json={"token": token},
                headers={"X-Internal-Service": "catalog-service"},
            )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
    except httpx.ConnectError:
        logger.warning("Auth service unreachable — falling back to unverified mode")
        # In dev/demo, allow requests through if Auth Service is down
        if os.getenv("AUTH_REQUIRED", "true").lower() == "false":
            return {"user_id": "dev-user", "role": "admin"}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = None,
) -> dict:
    """FastAPI dependency: returns current authenticated user."""
    from fastapi.security import HTTPBearer
    return await verify_token(credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = None,
) -> dict | None:
    """FastAPI dependency: returns user if authenticated, None otherwise (public routes)."""
    if credentials is None:
        return None
    try:
        return await verify_token(credentials)
    except HTTPException:
        return None
