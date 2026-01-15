"""
Create a test user in the database.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db
from app.features.auth.repository import AuthRepository
from app.utils.password import hash_password
from app.core.logging import setup_logging, logger


async def create_test_user() -> None:
    """Create a test user."""
    setup_logging()
    
    logger.info("👤 Creating test user...")
    
    try:
        async for session in get_db():
            repo = AuthRepository(session)
            
            # Check if user exists
            existing = await repo.find_by_email("test@example.com")
            if existing:
                logger.warning("⚠️  Test user already exists!")
                logger.info(f"User ID: {existing.id}")
                logger.info(f"Email: {existing.email}")
                logger.info(f"Name: {existing.name}")
                return
            
            # Create user
            hashed_password = hash_password("Test1234")
            user = await repo.create_user(
                name="Test User",
                email="test@example.com",
                password=hashed_password,
            )
            
            # Mark as verified
            await repo.update_user(user.id, {"isEmailVerified": True})
            
            logger.info("✅ Test user created successfully!")
            logger.info(f"Email: test@example.com")
            logger.info(f"Password: Test1234")
            logger.info(f"User ID: {user.id}")
            
            break
        
    except Exception as e:
        logger.error(f"❌ Failed to create test user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_test_user())
