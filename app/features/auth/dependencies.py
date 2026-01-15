"""
Authentication dependencies for dependency injection.
"""
from typing import Optional
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.core.database import get_db
from app.features.auth.repository import AuthRepository
from app.utils.jwt import verify_token
from app.features.auth.schemas import UserResponse, TokenPayload
from app.core.logging import logger


async def get_auth_repository(
    db: AsyncSession = Depends(get_db),
) -> AuthRepository:
    """
    Dependency to get authentication repository.
    
    Args:
        db: Database session
        
    Returns:
        AuthRepository: Authentication repository instance
    """
    return AuthRepository(db)


async def get_current_user(
    jwt: Optional[str] = Cookie(None),
    repository: AuthRepository = Depends(get_auth_repository),
) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT cookie.
    
    Args:
        jwt: JWT token from cookie
        repository: Authentication repository
        
    Returns:
        UserResponse: Current user data
        
    Raises:
        HTTPException: If authentication fails
    """
    if not jwt:
        logger.warning("⚠️  No JWT token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Access denied. No token provided.",
            },
        )
    
    try:
        # Verify token
        payload = verify_token(jwt)
        token_data = TokenPayload(**payload)
        
        # Get user from database
        user = await repository.find_by_id(token_data.userId)
        if not user:
            logger.warning(f"⚠️  User not found for token: {token_data.userId}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Access denied. User not found.",
                },
            )
        
        # Return user response (excluding password)
        return UserResponse.model_validate(user)
        
    except JWTError as e:
        logger.error(f"❌ JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid token",
            },
        )


async def get_current_user_optional(
    jwt: Optional[str] = Cookie(None),
    repository: AuthRepository = Depends(get_auth_repository),
) -> Optional[UserResponse]:
    """
    Dependency to get current user (optional authentication).
    
    Args:
        jwt: JWT token from cookie
        repository: Authentication repository
        
    Returns:
        Optional[UserResponse]: Current user data or None
    """
    if not jwt:
        return None
    
    try:
        payload = verify_token(jwt)
        token_data = TokenPayload(**payload)
        user = await repository.find_by_id(token_data.userId)
        
        if user:
            return UserResponse.model_validate(user)
        return None
        
    except Exception:
        return None
