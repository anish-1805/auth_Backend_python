import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PollinationAIService:
    """Service for interacting with Pollination AI API"""
    
    BASE_URL = "https://gen.pollinations.ai"
    
    @staticmethod
    async def generate_response(
        message: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate AI response using Pollination AI
        
        Args:
            message: User's message
            system_prompt: Optional system prompt to guide the AI
            
        Returns:
            AI generated response text
        """
        try:
            if not settings.POLLINATION_AI_API_KEY:
                logger.warning("Pollination AI API key not configured")
                return "I'm sorry, but the AI service is not properly configured. Please contact support."
            
            # Default system prompt if none provided
            if not system_prompt:
                system_prompt = (
                    "You are a helpful AI assistant. Provide clear, concise, and accurate responses. "
                    "Be friendly and professional in your interactions."
                )
            
            # Construct the prompt
            full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
            
            # Make request to Pollinations AI
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {settings.POLLINATION_AI_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                # Pollinations AI uses a simple text generation endpoint
                response = await client.post(
                    f"{PollinationAIService.BASE_URL}/generate",
                    json={
                        "prompt": full_prompt,
                        "model": "openai",  # or other available models
                        "max_tokens": 500,
                        "temperature": 0.7,
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "").strip()
                else:
                    logger.error(f"Pollination AI API error: {response.status_code} - {response.text}")
                    return "I apologize, but I'm having trouble generating a response right now. Please try again."
                    
        except httpx.TimeoutException:
            logger.error("Pollination AI request timed out")
            return "The request took too long. Please try again with a shorter message."
        except Exception as e:
            logger.error(f"Error calling Pollination AI: {str(e)}")
            return "I encountered an error while processing your request. Please try again."
    
    @staticmethod
    async def generate_simple_response(message: str) -> str:
        """
        Use Pollinations AI API - OpenAI-compatible chat completions endpoint
        Official docs: https://enter.pollinations.ai/api/docs
        Endpoint: https://gen.pollinations.ai/v1/chat/completions
        """
        try:
            if not settings.POLLINATION_AI_API_KEY:
                logger.error("Pollination AI API key not configured")
                return await PollinationAIService._fallback_response(message)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Correct endpoint from official docs
                url = f"{PollinationAIService.BASE_URL}/v1/chat/completions"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.POLLINATION_AI_API_KEY}"
                }
                
                # OpenAI-compatible format as per official docs
                payload = {
                    "model": "openai",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    "stream": False
                }
                
                logger.info(f"Calling Pollinations AI: {url}")
                logger.info(f"Message: {message[:50]}...")
                
                response = await client.post(url, json=payload, headers=headers)
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Response JSON keys: {list(result.keys())}")
                    
                    # OpenAI-compatible response format
                    if "choices" in result and len(result["choices"]) > 0:
                        ai_response = result["choices"][0].get("message", {}).get("content", "").strip()
                        logger.info(f"AI response: {ai_response[:100]}...")
                        
                        if ai_response:
                            return ai_response
                        else:
                            logger.warning("Empty content in response")
                            return await PollinationAIService._fallback_response(message)
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        return await PollinationAIService._fallback_response(message)
                        
                elif response.status_code == 401:
                    logger.error("Pollination AI authentication failed - check API key")
                    return "Authentication error. Please check the API key configuration."
                elif response.status_code == 402:
                    logger.error("Insufficient pollen balance")
                    return "Insufficient balance. Please add more pollen to your account."
                else:
                    logger.error(f"Pollination AI error {response.status_code}: {response.text[:500]}")
                    return await PollinationAIService._fallback_response(message)
                    
        except httpx.TimeoutException:
            logger.error("Pollination AI request timed out")
            return "The request took too long. Please try again."
        except Exception as e:
            logger.error(f"Error calling Pollination AI: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return await PollinationAIService._fallback_response(message)
    
    @staticmethod
    async def _fallback_response(message: str) -> str:
        """Provide a fallback response when API is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! How can I assist you today?"
        elif any(word in message_lower for word in ["help", "support"]):
            return "I'm here to help! Please describe what you need assistance with."
        elif "?" in message:
            return "That's an interesting question! Unfortunately, I'm having trouble connecting to my AI service right now. Please try again in a moment."
        else:
            return "I understand. Could you please provide more details so I can better assist you?"
