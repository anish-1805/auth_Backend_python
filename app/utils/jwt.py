"""
JWT token generation and verification utilities.
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import logger


def parse_time_string(time_str: str) -> timedelta:
    """
    Parse time string like '7d', '24h', '30m' to timedelta.

    Args:
        time_str: Time string (e.g., '7d', '24h', '30m')

    Returns:
        timedelta: Parsed time delta
    """
    time_str = time_str.strip().lower()

    if time_str.endswith("d"):
        days = int(time_str[:-1])
        return timedelta(days=days)
    elif time_str.endswith("h"):
        hours = int(time_str[:-1])
        return timedelta(hours=hours)
    elif time_str.endswith("m"):
        minutes = int(time_str[:-1])
        return timedelta(minutes=minutes)
    elif time_str.endswith("s"):
        seconds = int(time_str[:-1])
        return timedelta(seconds=seconds)
    else:
        # Default to days if no unit specified
        return timedelta(days=int(time_str))


def create_access_token(
    data: dict[str, str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token
    """
    to_encode: dict[str, object] = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + parse_time_string(settings.JWT_EXPIRES_IN)

    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    to_encode["iss"] = "auth-backend"
    to_encode["aud"] = "auth-frontend"

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(
    data: dict[str, str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode: dict[str, object] = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + parse_time_string(settings.JWT_REFRESH_EXPIRES_IN)

    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    to_encode["iss"] = "auth-backend"
    to_encode["aud"] = "auth-frontend"
    to_encode["type"] = "refresh"

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def verify_token(token: str) -> dict[str, object]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        dict[str, object]: Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="auth-backend",
            audience="auth-frontend",
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise


def decode_token(token: str) -> Optional[dict[str, object]]:
    """
    Decode a JWT token without verification (for debugging).

    Args:
        token: JWT token to decode

    Returns:
        Optional[dict[str, object]]: Decoded token payload or None
    """
    try:
        payload = jwt.decode(
            token,
            key="",
            options={"verify_signature": False},
        )
        return payload
    except Exception as e:
        logger.error(f"JWT decoding failed: {e}")
        return None
