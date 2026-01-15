"""
Rate limiting middleware.
"""

import time
from typing import Dict

from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.logging import logger


class RateLimitData:
    """Rate limit data for a client."""

    def __init__(self) -> None:
        self.count: int = 0
        self.first_request: float = time.time()


# In-memory storage for rate limiting
rate_limit_storage: Dict[str, RateLimitData] = {}


def get_client_id(request: Request) -> str:
    """
    Get unique client identifier from request.

    Args:
        request: Incoming request

    Returns:
        str: Client identifier
    """
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit_middleware(request: Request) -> None:
    """
    Rate limiting middleware to prevent abuse.

    Args:
        request: Incoming request

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    client_id = get_client_id(request)
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_MINUTES * 60

    # Clean up old entries
    expired_clients = [
        cid
        for cid, data in rate_limit_storage.items()
        if now - data.first_request > window
    ]
    for cid in expired_clients:
        del rate_limit_storage[cid]

    # Check current client
    if client_id not in rate_limit_storage:
        rate_limit_storage[client_id] = RateLimitData()
        rate_limit_storage[client_id].count = 1
        rate_limit_storage[client_id].first_request = now
        return

    client_data = rate_limit_storage[client_id]

    # Reset if window expired
    if now - client_data.first_request > window:
        client_data.count = 1
        client_data.first_request = now
        return

    # Check if limit exceeded
    if client_data.count >= settings.RATE_LIMIT_REQUESTS:
        retry_after = int(window - (now - client_data.first_request))
        logger.warning(
            f"⚠️  Rate limit exceeded for client: {client_id}",
            client_id=client_id,
            retry_after=retry_after,
        )
        raise HTTPException(
            status_code=429,
            detail={
                "success": False,
                "message": "Too many requests. Please try again later.",
                "retryAfter": retry_after,
            },
        )

    client_data.count += 1
