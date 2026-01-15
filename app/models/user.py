"""
User database model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    """
    User model for authentication and user management.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    isEmailVerified: Mapped[bool] = mapped_column(
        "isEmailVerified", Boolean, default=False, nullable=False
    )
    
    # OAuth fields
    provider: Mapped[str] = mapped_column(
        String(50), default="local", nullable=False
    )
    providerId: Mapped[Optional[str]] = mapped_column(
        "providerId", String(255), nullable=True
    )
    avatar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    isSocialLogin: Mapped[bool] = mapped_column(
        "isSocialLogin", Boolean, default=False, nullable=False
    )
    
    # Timestamps
    createdAt: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, default=datetime.utcnow, nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        "updatedAt",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    # OTP fields
    signupOTP: Mapped[Optional[dict]] = mapped_column(
        "signupOTP", JSON, nullable=True
    )
    passwordResetOTP: Mapped[Optional[dict]] = mapped_column(
        "passwordResetOTP", JSON, nullable=True
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
