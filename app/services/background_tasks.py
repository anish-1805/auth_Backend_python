"""
Background tasks for async operations.
"""

from typing import Callable

from fastapi import BackgroundTasks

from app.core.logging import logger
from app.services.email_service import EmailService


async def send_signup_otp_background(email: str, name: str, otp: str) -> None:
    """
    Background task to send signup OTP email.

    Args:
        email: User's email
        name: User's name
        otp: OTP code
    """
    try:
        success = await EmailService.send_signup_otp(email, name, otp)
        if success:
            logger.info(f"✅ Signup OTP email sent successfully to: {email}")
        else:
            logger.error(f"❌ Failed to send signup OTP email to: {email}")
    except Exception as e:
        logger.error(f"❌ Error sending signup OTP email to {email}: {e}")


async def send_password_reset_otp_background(email: str, name: str, otp: str) -> None:
    """
    Background task to send password reset OTP email.

    Args:
        email: User's email
        name: User's name
        otp: OTP code
    """
    try:
        success = await EmailService.send_password_reset_otp(email, name, otp)
        if success:
            logger.info(f"✅ Password reset OTP email sent successfully to: {email}")
        else:
            logger.error(f"❌ Failed to send password reset OTP email to: {email}")
    except Exception as e:
        logger.error(f"❌ Error sending password reset OTP email to {email}: {e}")


async def send_password_reset_success_background(email: str, name: str) -> None:
    """
    Background task to send password reset success notification.

    Args:
        email: User's email
        name: User's name
    """
    try:
        success = await EmailService.send_password_reset_success(email, name)
        if success:
            logger.info(f"✅ Password reset success email sent to: {email}")
        else:
            logger.error(f"❌ Failed to send password reset success email to: {email}")
    except Exception as e:
        logger.error(f"❌ Error sending password reset success email to {email}: {e}")


def add_background_task(
    background_tasks: BackgroundTasks, task: Callable, *args, **kwargs
) -> None:
    """
    Add a background task to the queue.

    Args:
        background_tasks: FastAPI BackgroundTasks instance
        task: Task function to execute
        *args: Positional arguments for the task
        **kwargs: Keyword arguments for the task
    """
    background_tasks.add_task(task, *args, **kwargs)
    logger.info(f"📋 Added background task: {task.__name__}")
