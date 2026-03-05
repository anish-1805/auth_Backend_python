"""
Subscription database model for managing user subscriptions.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types"""
    FREE = "free"
    BASIC = "basic"      # $10 - 10 messages/week
    STANDARD = "standard"  # $20 - 20 messages/week
    PREMIUM = "premium"   # $30 - 30 messages/week


class SubscriptionStatus(str, enum.Enum):
    """Subscription status types"""
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class Subscription(Base):
    """
    Subscription model for managing user payment plans.
    """

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Subscription details
    plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, values_callable=lambda x: [e.value for e in x]), 
        default=SubscriptionPlan.FREE, 
        nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, values_callable=lambda x: [e.value for e in x]), 
        default=SubscriptionStatus.ACTIVE, 
        nullable=False
    )
    
    # Stripe details
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Message quota
    messages_per_week: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    messages_used_this_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    week_reset_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    
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

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan}, status={self.status})>"
