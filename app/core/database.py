"""
Database configuration and session management.
"""
from typing import AsyncGenerator
from urllib.parse import quote_plus
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings
from app.core.logging import logger

# Convert postgresql:// to postgresql+asyncpg://
database_url = settings.DATABASE_URL

# Handle URL encoding for special characters in password
if "@" in database_url:
    # Parse and rebuild URL with encoded password
    try:
        # Extract parts: postgresql://user:password@host:port/database
        protocol = database_url.split("://")[0]
        rest = database_url.split("://")[1]
        
        # Split by last @ to separate credentials from host
        if "@" in rest:
            credentials_part = rest.rsplit("@", 1)[0]
            host_part = rest.rsplit("@", 1)[1]
            
            # Split credentials into user and password
            if ":" in credentials_part:
                user = credentials_part.split(":", 1)[0]
                password = credentials_part.split(":", 1)[1]
                
                # URL encode the password
                encoded_password = quote_plus(password)
                
                # Rebuild URL
                database_url = f"{protocol}://{user}:{encoded_password}@{host_part}"
    except Exception as e:
        logger.warning(f"Could not parse DATABASE_URL for encoding: {e}")

# Convert to asyncpg driver
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.DB_ECHO,
    poolclass=QueuePool if settings.ENVIRONMENT != "testing" else NullPool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection and test connectivity.
    """
    try:
        async with engine.begin() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connected successfully with connection pooling")
            logger.info("✅ Database connection test passed")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise
