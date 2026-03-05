"""
Subscription management routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.schemas import UserResponse
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.services.stripe_service import StripeService
from app.features.subscription.schemas import (
    SubscriptionResponse,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    PlanResponse,
    CancelSubscriptionResponse,
    PortalSessionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans():
    """
    Get all available subscription plans
    """
    plans = StripeService.get_all_plans()
    return plans


@router.get("/my-subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription details
    """
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                plan=SubscriptionPlan.FREE.value,
                status=SubscriptionStatus.ACTIVE.value,
                messages_per_week=1,
                messages_used_this_week=0,
                week_reset_date=datetime.utcnow()
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
        
        messages_remaining = max(0, subscription.messages_per_week - subscription.messages_used_this_week)
        
        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=subscription.plan,
            status=subscription.status,
            messages_per_week=subscription.messages_per_week,
            messages_used_this_week=subscription.messages_used_this_week,
            messages_remaining=messages_remaining,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            week_reset_date=subscription.week_reset_date,
            createdAt=subscription.createdAt,
            updatedAt=subscription.updatedAt
        )
    except Exception as e:
        import traceback
        logger.error(f"Error fetching subscription: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscription: {str(e)}"
        )


@router.post("/create-checkout-session", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription purchase
    """
    try:
        plan_details = StripeService.get_plan_details(request.plan)
        if not plan_details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan selected"
            )
        
        if not plan_details["price_id"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Plan price ID not configured"
            )
        
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                plan=SubscriptionPlan.FREE.value,
                status=SubscriptionStatus.ACTIVE.value,
                messages_per_week=1,
                messages_used_this_week=0,
                week_reset_date=datetime.utcnow()
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
        
        if not subscription.stripe_customer_id:
            customer_id = await StripeService.create_customer(
                email=current_user.email,
                name=current_user.name,
                user_id=current_user.id
            )
            
            if not customer_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create Stripe customer"
                )
            
            subscription.stripe_customer_id = customer_id
            await db.commit()
        
        success_url = "myapp://subscription/success"
        cancel_url = "myapp://subscription/cancel"
        
        checkout_session = await StripeService.create_checkout_session(
            customer_id=subscription.stripe_customer_id,
            price_id=plan_details["price_id"],
            user_id=current_user.id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not checkout_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create checkout session"
            )
        
        return CreateCheckoutSessionResponse(
            success=True,
            message="Checkout session created successfully",
            session_id=checkout_session["session_id"],
            checkout_url=checkout_session["url"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel current subscription
    """
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription or not subscription.stripe_subscription_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        success = await StripeService.cancel_subscription(
            subscription.stripe_subscription_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
        
        return CancelSubscriptionResponse(
            success=True,
            message="Subscription will be canceled at the end of the billing period"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/create-portal-session", response_model=PortalSessionResponse)
async def create_portal_session(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe customer portal session
    """
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe customer found"
            )
        
        return_url = "myapp://subscription"
        
        portal_url = await StripeService.create_customer_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url
        )
        
        if not portal_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create portal session"
            )
        
        return PortalSessionResponse(
            success=True,
            message="Portal session created successfully",
            portal_url=portal_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        event = StripeService.construct_webhook_event(payload, sig_header)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        
        logger.info(f"Received Stripe webhook event: {event['type']}")
        
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"].get("user_id")
            
            if user_id:
                result = await db.execute(
                    select(Subscription).where(Subscription.user_id == user_id)
                )
                subscription = result.scalar_one_or_none()
                
                if subscription:
                    subscription.stripe_subscription_id = session.get("subscription")
                    await db.commit()
        
        elif event["type"] == "customer.subscription.created":
            stripe_subscription = event["data"]["object"]
            user_id = stripe_subscription["metadata"].get("user_id")
            
            if user_id:
                result = await db.execute(
                    select(Subscription).where(Subscription.user_id == user_id)
                )
                subscription = result.scalar_one_or_none()
                
                if subscription:
                    price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
                    
                    plan_name = None
                    for plan_id, plan_details in StripeService.PLANS.items():
                        if plan_details["price_id"] == price_id:
                            plan_name = plan_id
                            break
                    
                    if plan_name:
                        subscription.plan = SubscriptionPlan(plan_name)
                        subscription.status = SubscriptionStatus.ACTIVE
                        subscription.stripe_subscription_id = stripe_subscription["id"]
                        subscription.stripe_price_id = price_id
                        subscription.messages_per_week = StripeService.PLANS[plan_name]["messages_per_week"]
                        subscription.messages_used_this_week = 0
                        subscription.current_period_start = datetime.fromtimestamp(
                            stripe_subscription["current_period_start"]
                        )
                        subscription.current_period_end = datetime.fromtimestamp(
                            stripe_subscription["current_period_end"]
                        )
                        subscription.week_reset_date = datetime.utcnow()
                        await db.commit()
        
        elif event["type"] == "customer.subscription.updated":
            stripe_subscription = event["data"]["object"]
            
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_subscription["id"]
                )
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.status = SubscriptionStatus(stripe_subscription["status"])
                subscription.current_period_start = datetime.fromtimestamp(
                    stripe_subscription["current_period_start"]
                )
                subscription.current_period_end = datetime.fromtimestamp(
                    stripe_subscription["current_period_end"]
                )
                await db.commit()
        
        elif event["type"] == "customer.subscription.deleted":
            stripe_subscription = event["data"]["object"]
            
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_subscription["id"]
                )
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.plan = SubscriptionPlan.FREE
                subscription.status = SubscriptionStatus.CANCELED
                subscription.messages_per_week = 1
                subscription.messages_used_this_week = 0
                subscription.stripe_subscription_id = None
                subscription.stripe_price_id = None
                await db.commit()
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )
