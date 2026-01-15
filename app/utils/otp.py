"""
OTP (One-Time Password) generation and verification utilities.
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict
from app.core.config import settings
from app.core.logging import logger


def generate_otp(length: int = 6) -> str:
    """
    Generate a random numeric OTP.
    
    Args:
        length: Length of the OTP (default: 6)
        
    Returns:
        str: Generated OTP
    """
    otp = "".join([str(secrets.randbelow(10)) for _ in range(length)])
    return otp


def generate_otp_with_expiry(expiry_minutes: int = 5) -> Dict[str, str | bool]:
    """
    Generate an OTP with expiry time.
    
    Args:
        expiry_minutes: OTP expiry time in minutes (default: 5)
        
    Returns:
        Dict containing otp, expiryTime, and isUsed flag
    """
    otp = generate_otp(settings.OTP_LENGTH)
    expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    return {
        "otp": otp,
        "expiryTime": expiry_time.isoformat(),
        "isUsed": False,
    }


def verify_otp(
    provided_otp: str,
    stored_otp: str,
    expiry_time: str,
    is_used: bool,
) -> Dict[str, bool | str]:
    """
    Verify an OTP against stored data.
    
    Args:
        provided_otp: OTP provided by user
        stored_otp: OTP stored in database
        expiry_time: ISO format expiry time string
        is_used: Whether OTP has been used
        
    Returns:
        Dict with isValid flag and optional error message
    """
    # Check if OTP has been used
    if is_used:
        logger.warning("OTP verification failed: OTP already used")
        return {
            "isValid": False,
            "error": "This OTP has already been used. Please request a new one.",
        }
    
    # Check if OTP has expired
    expiry_datetime = datetime.fromisoformat(expiry_time)
    if datetime.utcnow() > expiry_datetime:
        logger.warning("OTP verification failed: OTP expired")
        return {
            "isValid": False,
            "error": "This OTP has expired. Please request a new one.",
        }
    
    # Verify OTP matches
    if provided_otp != stored_otp:
        logger.warning("OTP verification failed: OTP mismatch")
        return {
            "isValid": False,
            "error": "Invalid OTP. Please check and try again.",
        }
    
    logger.info("✅ OTP verified successfully")
    return {"isValid": True}
