"""
Security headers middleware.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


async def security_headers_middleware(request: Request, call_next) -> Response:
    """
    Add security headers to all responses.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response: Response with security headers
    """
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Remove server header
    if "server" in response.headers:
        del response.headers["server"]

    return response
