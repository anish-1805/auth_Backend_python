"""
Test database connection script.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db, get_db
from app.core.config import settings
from app.core.logging import setup_logging, logger


async def test_connection() -> None:
    """Test database connection."""
    setup_logging()
    
    logger.info("🔍 Testing database connection...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden'}")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database connection successful!")
        
        # Test query
        async for session in get_db():
            result = await session.execute("SELECT COUNT(*) FROM users")
            count = result.scalar()
            logger.info(f"✅ Found {count} users in database")
            break
        
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_connection())
