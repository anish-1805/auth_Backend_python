"""
Stripe service for handling payment processing and subscription management.
"""

import stripe
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripeService:
    """Service for managing Stripe payment operations"""
    
    # Subscription plan configurations
    PLANS = {
        "basic": {
            "name": "Basic Plan",
            "price": 10.00,
            "messages_per_week": 10,
            "price_id": os.getenv("STRIPE_BASIC_PRICE_ID"),
        },
        "standard": {
            "name": "Standard Plan",
            "price": 20.00,
            "messages_per_week": 20,
            "price_id": os.getenv("STRIPE_STANDARD_PRICE_ID"),
        },
        "premium": {
            "name": "Premium Plan",
            "price": 30.00,
            "messages_per_week": 30,
            "price_id": os.getenv("STRIPE_PREMIUM_PRICE_ID"),
        },
    }
    
    @staticmethod
    async def create_customer(email: str, name: str, user_id: str) -> Optional[str]:
        """
        Create a Stripe customer
        
        Args:
            email: Customer email
            name: Customer name
            user_id: Internal user ID
            
        Returns:
            Stripe customer ID or None
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": user_id}
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            return None
    
    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        price_id: str,
        user_id: str,
        success_url: str,
        cancel_url: str
    ) -> Optional[Dict]:
        """
        Create a Stripe Checkout session for subscription
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            user_id: Internal user ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            Checkout session data or None
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id
                    }
                }
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}")
            return {
                "session_id": session.id,
                "url": session.url
            }
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return None
    
    @staticmethod
    async def cancel_subscription(subscription_id: str) -> bool:
        """
        Cancel a Stripe subscription
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Canceled subscription {subscription_id}")
            return True
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return False
    
    @staticmethod
    async def get_subscription(subscription_id: str) -> Optional[Dict]:
        """
        Get subscription details from Stripe
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription data or None
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except Exception as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            return None
    
    @staticmethod
    async def create_customer_portal_session(
        customer_id: str,
        return_url: str
    ) -> Optional[str]:
        """
        Create a customer portal session for managing subscription
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session
            
        Returns:
            Portal session URL or None
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except Exception as e:
            logger.error(f"Error creating portal session: {str(e)}")
            return None
    
    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> Optional[stripe.Event]:
        """
        Construct and verify a Stripe webhook event
        
        Args:
            payload: Request body
            sig_header: Stripe signature header
            
        Returns:
            Stripe event or None
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return None
    
    @staticmethod
    def get_plan_details(plan_name: str) -> Optional[Dict]:
        """
        Get plan configuration details
        
        Args:
            plan_name: Name of the plan (basic, standard, premium)
            
        Returns:
            Plan details or None
        """
        return StripeService.PLANS.get(plan_name.lower())
    
    @staticmethod
    def get_all_plans() -> List[Dict]:
        """
        Get all available subscription plans
        
        Returns:
            List of plan configurations
        """
        return [
            {
                "id": plan_id,
                "name": details["name"],
                "price": details["price"],
                "messages_per_week": details["messages_per_week"],
                "price_id": details["price_id"],
            }
            for plan_id, details in StripeService.PLANS.items()
        ]
