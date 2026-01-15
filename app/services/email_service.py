"""
Email service for sending emails via SMTP.
"""
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from jinja2 import Template
from app.core.config import settings
from app.core.logging import logger


class EmailService:
    """Service for sending emails."""
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("⚠️  SMTP credentials not configured, skipping email send")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            # Use start_tls for port 587 (most common), use_tls for port 465
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_TLS if settings.SMTP_PORT == 587 else False,
                use_tls=settings.SMTP_TLS if settings.SMTP_PORT == 465 else False,
            )
            
            logger.info(f"✅ Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    async def send_signup_otp(email: str, name: str, otp: str) -> bool:
        """
        Send signup OTP email.
        
        Args:
            email: User's email
            name: User's name
            otp: OTP code
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Verify Your Email - OTP Code"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .otp-box { background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }
                .otp-code { font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; }
                .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Email Verification</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ name }}!</h2>
                    <p>Thank you for signing up! Please verify your email address using the OTP code below:</p>
                    <div class="otp-box">
                        <div class="otp-code">{{ otp }}</div>
                    </div>
                    <p><strong>This code will expire in 5 minutes.</strong></p>
                    <p>If you didn't request this verification, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 Auth Backend. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        html_content = html_template.render(name=name, otp=otp)
        text_content = f"Hello {name}!\n\nYour verification code is: {otp}\n\nThis code will expire in 5 minutes."
        
        return await EmailService.send_email(email, subject, html_content, text_content)
    
    @staticmethod
    async def send_password_reset_otp(email: str, name: str, otp: str) -> bool:
        """
        Send password reset OTP email.
        
        Args:
            email: User's email
            name: User's name
            otp: OTP code
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Password Reset - OTP Code"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .otp-box { background: white; border: 2px dashed #f5576c; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }
                .otp-code { font-size: 32px; font-weight: bold; color: #f5576c; letter-spacing: 5px; }
                .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
                .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ name }}!</h2>
                    <p>We received a request to reset your password. Use the OTP code below to proceed:</p>
                    <div class="otp-box">
                        <div class="otp-code">{{ otp }}</div>
                    </div>
                    <p><strong>This code will expire in 5 minutes.</strong></p>
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong> If you didn't request a password reset, please ignore this email and ensure your account is secure.
                    </div>
                </div>
                <div class="footer">
                    <p>© 2024 Auth Backend. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        html_content = html_template.render(name=name, otp=otp)
        text_content = f"Hello {name}!\n\nYour password reset code is: {otp}\n\nThis code will expire in 5 minutes.\n\nIf you didn't request this, please ignore this email."
        
        return await EmailService.send_email(email, subject, html_content, text_content)
    
    @staticmethod
    async def send_password_reset_success(email: str, name: str) -> bool:
        """
        Send password reset success notification.
        
        Args:
            email: User's email
            name: User's name
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Password Reset Successful"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .success-icon { font-size: 64px; text-align: center; margin: 20px 0; }
                .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Password Reset Successful</h1>
                </div>
                <div class="content">
                    <div class="success-icon">🎉</div>
                    <h2>Hello {{ name }}!</h2>
                    <p>Your password has been successfully reset. You can now log in with your new password.</p>
                    <p>If you didn't make this change, please contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>© 2024 Auth Backend. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        html_content = html_template.render(name=name)
        text_content = f"Hello {name}!\n\nYour password has been successfully reset. You can now log in with your new password."
        
        return await EmailService.send_email(email, subject, html_content, text_content)
