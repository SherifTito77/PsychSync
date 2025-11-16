from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings

# Email configuration with correct field names for fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER or "dummy@example.com",  # Required, use dummy if None
    MAIL_PASSWORD=settings.SMTP_PASSWORD or "dummy",  # Required, use dummy if None
    MAIL_FROM=settings.EMAIL_FROM or "noreply@psychsync.com",
    MAIL_PORT=settings.SMTP_PORT or 587,
    MAIL_SERVER=settings.SMTP_HOST or "smtp.gmail.com",
    MAIL_FROM_NAME=settings.EMAIL_FROM_NAME or "PsychSync",
    MAIL_STARTTLS=settings.SMTP_TLS,  # Correct field name (not MAIL_USE_TLS)
    MAIL_SSL_TLS=settings.SMTP_SSL,  # Correct field name (not MAIL_USE_SSL)
    USE_CREDENTIALS=bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
    VALIDATE_CERTS=getattr(settings, 'MAIL_VALIDATE_CERTS', False)
)

# Create FastMail instance
fm = FastMail(conf)


class EmailService:
    """Email service for sending various types of emails"""
    
    @staticmethod
    async def send_email(
        email_to: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ):
        """Send a generic email"""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            print(f"⚠️ Email not configured. Would send email to {email_to}: {subject}")
            return
        
        message = MessageSchema(
            subject=subject,
            recipients=[email_to],
            body=html or body,
            subtype=MessageType.html if html else MessageType.plain
        )
        
        try:
            await fm.send_message(message)
            print(f"✅ Email sent to {email_to}: {subject}")
        except Exception as e:
            print(f"❌ Failed to send email to {email_to}: {e}")
    
    @staticmethod
    async def send_verification_email(email: str, token: str, name: str):
        """Send email verification link"""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            print(f"⚠️ Email not configured. Verification token for {email}: {token}")
            return
        
        frontend_url = settings.FRONTEND_EMAIL_VERIFY_URL or "http://localhost:3000/verify-email"
        verify_link = f"{frontend_url}?token={token}"
        
        subject = "Verify Your Email - PsychSync"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Welcome to PsychSync, {name}!</h2>
                    <p>Thank you for registering. Please verify your email address to get started.</p>
                    <p style="margin: 30px 0;">
                        <a href="{verify_link}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email
                        </a>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Or copy this link: <br>
                        <a href="{verify_link}">{verify_link}</a>
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 40px;">
                        If you didn't create this account, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        await EmailService.send_email(email, subject, verify_link, html)
    
    @staticmethod
    async def send_welcome_email(email: str, name: str):
        """Send welcome email after verification"""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            print(f"⚠️ Email not configured. Welcome email for {email}")
            return
        
        subject = "Welcome to PsychSync!"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Welcome aboard, {name}! 🎉</h2>
                    <p>Your email has been verified successfully.</p>
                    <p>You can now:</p>
                    <ul>
                        <li>Take psychological assessments</li>
                        <li>Create and manage teams</li>
                        <li>View analytics and insights</li>
                        <li>Build custom assessment templates</li>
                    </ul>
                    <p style="margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Get Started
                        </a>
                    </p>
                </div>
            </body>
        </html>
        """
        
        await EmailService.send_email(email, subject, "Welcome to PsychSync!", html)
    
    @staticmethod
    async def send_password_reset_email(email: str, token: str, name: str):
        """Send password reset link"""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            print(f"⚠️ Email not configured. Reset token for {email}: {token}")
            return
        
        frontend_url = settings.FRONTEND_PASSWORD_RESET_URL or "http://localhost:3000/reset-password"
        reset_link = f"{frontend_url}?token={token}"
        
        subject = "Reset Your Password - PsychSync"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Password Reset Request</h2>
                    <p>Hi {name},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Or copy this link: <br>
                        <a href="{reset_link}">{reset_link}</a>
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 40px;">
                        If you didn't request this, please ignore this email. 
                        Your password will remain unchanged.
                    </p>
                    <p style="color: #999; font-size: 12px;">
                        This link will expire in 15 minutes.
                    </p>
                </div>
            </body>
        </html>
        """
        
        await EmailService.send_email(email, subject, reset_link, html)
    
    @staticmethod
    async def send_team_invitation(email: str, team_name: str, inviter_name: str, invite_link: str):
        """Send team invitation email"""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            print(f"⚠️ Email not configured. Team invite for {email}: {invite_link}")
            return
        
        subject = f"You've been invited to join {team_name} on PsychSync"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Team Invitation</h2>
                    <p>{inviter_name} has invited you to join <strong>{team_name}</strong> on PsychSync.</p>
                    <p style="margin: 30px 0;">
                        <a href="{invite_link}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Accept Invitation
                        </a>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Or copy this link: <br>
                        <a href="{invite_link}">{invite_link}</a>
                    </p>
                </div>
            </body>
        </html>
        """
        
        await EmailService.send_email(email, subject, invite_link, html)