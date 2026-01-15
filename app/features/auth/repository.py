"""
Authentication repository for database operations.
"""

import uuid
from typing import Dict, Optional, Union

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.user import User
from app.utils.decorators import execution_timer


class AuthRepository:
    """Repository for authentication-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            db: Database session
        """
        self.db = db

    @execution_timer
    async def create_user(
        self,
        name: str,
        email: str,
        password: Optional[str] = None,
        provider: str = "local",
        provider_id: Optional[str] = None,
        avatar: Optional[str] = None,
        is_social_login: bool = False,
    ) -> User:
        """
        Create a new user.

        Args:
            name: User's name
            email: User's email
            password: Hashed password (optional for OAuth)
            provider: Auth provider (local, google, etc.)
            provider_id: Provider's user ID
            avatar: Profile picture URL
            is_social_login: Whether user signed up via OAuth

        Returns:
            User: Created user object
        """
        user = User(
            id=str(uuid.uuid4()),
            name=name,
            email=email.lower().strip(),
            password=password,
            provider=provider,
            providerId=provider_id,
            avatar=avatar,
            isSocialLogin=is_social_login,
            isEmailVerified=is_social_login,  # OAuth users are pre-verified
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"✅ Created user: {user.email}")
        return user

    @execution_timer
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email.

        Args:
            email: User's email

        Returns:
            Optional[User]: User object or None
        """
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    @execution_timer
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find user by ID.

        Args:
            user_id: User's ID

        Returns:
            Optional[User]: User object or None
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @execution_timer
    async def find_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """
        Find user by OAuth provider and provider ID.

        Args:
            provider: OAuth provider name
            provider_id: Provider's user ID

        Returns:
            Optional[User]: User object or None
        """
        result = await self.db.execute(
            select(User).where(
                User.provider == provider,
                User.providerId == provider_id,
            )
        )
        return result.scalar_one_or_none()

    @execution_timer
    async def update_user(
        self, user_id: str, update_data: Dict[str, str | bool | dict | None]
    ) -> Optional[User]:
        """
        Update user by ID.

        Args:
            user_id: User's ID
            update_data: Dictionary of fields to update

        Returns:
            Optional[User]: Updated user object or None
        """
        user = await self.find_by_id(user_id)
        if not user:
            return None

        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"✅ Updated user: {user.email}")
        return user

    @execution_timer
    async def update_user_otp(
        self, user_id: str, otp_type: str, otp_data: Dict[str, Union[str, bool]]
    ) -> None:
        """
        Update OTP data for user.

        Args:
            user_id: User's ID
            otp_type: Type of OTP ('signupOTP' or 'passwordResetOTP')
            otp_data: OTP data dictionary containing otp, expiryTime, and isUsed
        """
        user = await self.find_by_id(user_id)
        if user:
            if otp_type == "signupOTP":
                user.signupOTP = otp_data
            elif otp_type == "passwordResetOTP":
                user.passwordResetOTP = otp_data
            await self.db.commit()
            logger.info(f"✅ Updated {otp_type} for user: {user.email}")

    @execution_timer
    async def store_signup_otp(
        self, email: str, otp_data: Dict[str, str | bool]
    ) -> None:
        """
        Store signup OTP for user.

        Args:
            email: User's email
            otp_data: OTP data dictionary
        """
        user = await self.find_by_email(email)
        if user:
            user.signupOTP = otp_data
            await self.db.commit()
            logger.info(f"✅ Stored signup OTP for: {email}")

    @execution_timer
    async def store_password_reset_otp(
        self, email: str, otp_data: Dict[str, str | bool]
    ) -> None:
        """
        Store password reset OTP for user.

        Args:
            email: User's email
            otp_data: OTP data dictionary
        """
        user = await self.find_by_email(email)
        if user:
            user.passwordResetOTP = otp_data
            await self.db.commit()
            logger.info(f"✅ Stored password reset OTP for: {email}")

    @execution_timer
    async def verify_signup_otp(self, email: str, otp: str) -> Optional[User]:
        """
        Verify signup OTP and mark user as verified.

        Args:
            email: User's email
            otp: OTP to verify

        Returns:
            Optional[User]: Verified user or None
        """
        user = await self.find_by_email(email)
        if not user or not user.signupOTP:
            return None

        # Mark OTP as used and verify email
        otp_data = user.signupOTP
        otp_data["isUsed"] = True
        user.signupOTP = otp_data
        user.isEmailVerified = True

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"✅ Verified signup OTP for: {email}")
        return user

    @execution_timer
    async def verify_password_reset_otp(self, email: str, otp: str) -> Optional[User]:
        """
        Verify password reset OTP.

        Args:
            email: User's email
            otp: OTP to verify

        Returns:
            Optional[User]: User or None
        """
        user = await self.find_by_email(email)
        if not user or not user.passwordResetOTP:
            return None

        # Mark OTP as used
        otp_data = user.passwordResetOTP
        otp_data["isUsed"] = True
        user.passwordResetOTP = otp_data

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"✅ Verified password reset OTP for: {email}")
        return user

    @execution_timer
    async def get_all_users(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """
        Get all users with pagination and search.

        Args:
            page: Page number
            limit: Items per page
            search: Search query
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            tuple: (list of users, total count)
        """
        # Build base query
        query = select(User)

        # Add search filter
        if search:
            search_filter = or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Add sorting
        sort_column = getattr(User, sort_by, User.createdAt)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Add pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        logger.info(f"✅ Retrieved {len(users)} users (page {page}, total {total})")
        return users, total

    @execution_timer
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User's ID

        Returns:
            bool: True if deleted, False otherwise
        """
        user = await self.find_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()

        logger.info(f"✅ Deleted user: {user.email}")
        return True

    @execution_timer
    async def delete_users_bulk(
        self, user_ids: list[str], current_user_id: str
    ) -> tuple[int, list[Dict[str, str]]]:
        """
        Delete multiple users in bulk.

        Args:
            user_ids: List of user IDs to delete
            current_user_id: ID of current user (cannot delete self)

        Returns:
            tuple: (deleted count, list of failed deletions)
        """
        deleted_count = 0
        failed_deletions: list[Dict[str, str]] = []

        for user_id in user_ids:
            # Prevent self-deletion
            if user_id == current_user_id:
                failed_deletions.append(
                    {
                        "userId": user_id,
                        "reason": "Cannot delete your own account",
                    }
                )
                continue

            try:
                success = await self.delete_user(user_id)
                if success:
                    deleted_count += 1
                else:
                    failed_deletions.append(
                        {
                            "userId": user_id,
                            "reason": "User not found",
                        }
                    )
            except Exception as e:
                failed_deletions.append(
                    {
                        "userId": user_id,
                        "reason": str(e),
                    }
                )

        logger.info(
            f"✅ Bulk delete: {deleted_count} deleted, {len(failed_deletions)} failed"
        )
        return deleted_count, failed_deletions
