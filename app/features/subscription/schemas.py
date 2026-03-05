"""
Pydantic schemas for subscription management.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionResponse(BaseModel):
    """Response schema for subscription data"""
    id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    messages_per_week: int
    messages_used_this_week: int
    messages_remaining: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    week_reset_date: datetime
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True


class CreateCheckoutSessionRequest(BaseModel):
    """Request schema for creating checkout session"""
    plan: str = Field(..., description="Plan name: basic, standard, or premium")


class CreateCheckoutSessionResponse(BaseModel):
    """Response schema for checkout session"""
    success: bool
    message: str
    session_id: Optional[str] = None
    checkout_url: Optional[str] = None


class PlanResponse(BaseModel):
    """Response schema for plan details"""
    id: str
    name: str
    price: float
    messages_per_week: int
    price_id: Optional[str] = None


class CancelSubscriptionResponse(BaseModel):
    """Response schema for subscription cancellation"""
    success: bool
    message: str


class PortalSessionResponse(BaseModel):
    """Response schema for customer portal session"""
    success: bool
    message: str
    portal_url: Optional[str] = None
