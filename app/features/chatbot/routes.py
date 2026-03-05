from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from app.features.auth.dependencies import get_current_user
from app.features.auth.schemas import UserResponse
from app.services.pollination_service import PollinationAIService
from app.core.database import get_db
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.chat_message import ChatMessage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    system_prompt: Optional[str] = Field(None, max_length=500)


class ChatResponse(BaseModel):
    success: bool
    message: str
    response: str
    messages_remaining: Optional[int] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the AI chatbot and get a response
    
    Requires authentication and active subscription.
    """
    try:
        logger.info(f"Chat request from user {current_user.id}: {request.message[:50]}...")
        
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                plan=SubscriptionPlan.FREE,
                status=SubscriptionStatus.ACTIVE,
                messages_per_week=1,
                messages_used_this_week=0,
                week_reset_date=datetime.utcnow()
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
        
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        if subscription.week_reset_date < week_ago:
            subscription.messages_used_this_week = 0
            subscription.week_reset_date = now
            await db.commit()
        
        if subscription.messages_used_this_week >= subscription.messages_per_week:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Message limit reached. Please upgrade your subscription."
            )
        
        ai_response = await PollinationAIService.generate_simple_response(
            request.message
        )
        
        subscription.messages_used_this_week += 1
        await db.commit()
        
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            message=request.message,
            response=ai_response
        )
        db.add(chat_message)
        await db.commit()
        
        messages_remaining = subscription.messages_per_week - subscription.messages_used_this_week
        
        return ChatResponse(
            success=True,
            message="Response generated successfully",
            response=ai_response,
            messages_remaining=messages_remaining
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )


@router.get("/chat/health")
async def chat_health():
    """Check if the chatbot service is available"""
    try:
        # Test with a simple message
        test_response = await PollinationAIService.generate_simple_response("Hello")
        
        return {
            "success": True,
            "message": "Chatbot service is operational",
            "test_response": test_response[:100]  # First 100 chars
        }
    except Exception as e:
        logger.error(f"Chatbot health check failed: {str(e)}")
        return {
            "success": False,
            "message": "Chatbot service is experiencing issues",
            "error": str(e)
        }
