"""
Authentication interfaces and type definitions.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    """Request schema for user signup."""

    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="User's password"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name."""
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")


class OTPVerificationRequest(BaseModel):
    """Request schema for OTP verification."""

    email: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class EmailOnlyRequest(BaseModel):
    """Request schema for email-only operations."""

    email: EmailStr = Field(..., description="User's email address")


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset."""

    email: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")
    newPassword: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )

    @field_validator("newPassword")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password."""

    currentPassword: str = Field(..., min_length=1, description="Current password")
    newPassword: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )

    @field_validator("newPassword")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile."""

    name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="User's full name"
    )
    email: Optional[EmailStr] = Field(None, description="User's email address")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean name."""
        if v is not None:
            return v.strip()
        return v


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: str
    name: str
    email: str
    isEmailVerified: bool
    provider: str
    providerId: Optional[str] = None
    avatar: Optional[str] = None
    isSocialLogin: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Response schema for authentication operations."""

    success: bool
    message: str
    user: Optional[UserResponse] = None
    data: Optional[dict[str, str | bool | int | list[dict[str, str]]]] = None


class TokenPayload(BaseModel):
    """JWT token payload."""

    userId: str
    email: str
    exp: Optional[int | datetime] = None
    iat: Optional[int | datetime] = None
    iss: Optional[str] = None
    aud: Optional[str] = None


class OTPData(BaseModel):
    """OTP data structure."""

    otp: str
    expiryTime: str
    isUsed: bool


class DeleteUsersRequest(BaseModel):
    """Request schema for bulk user deletion."""

    userIds: list[str] = Field(
        ..., min_length=1, description="List of user IDs to delete"
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search query")
    sortBy: Optional[str] = Field(default="createdAt", description="Sort field")
    sortOrder: Optional[str] = Field(
        default="desc", description="Sort order (asc/desc)"
    )


class PaginatedUsersResponse(BaseModel):
    """Response schema for paginated users."""

    success: bool
    users: list[UserResponse]
    pagination: dict[str, int | bool]
