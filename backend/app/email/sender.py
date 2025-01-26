import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.settings import settings


logger = logging.getLogger(__name__)

async def send_password_reset_email(email: str, reset_link: str):
    """Send password reset email"""
    sender_email = settings.SMTP_USERNAME
    sender_password = settings.SMTP_PASSWORD

    logger.info(f"Using email: {sender_email}")
    logger.info(f"Password length: {len(sender_password)}")

    message = MIMEMultipart()
    message["From"] = f"{settings.EMAIL_SENDER_NAME} <{sender_email}>"
    message["To"] = email
    message["Subject"] = "Password Reset Request"

    html = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>This link will expire in {settings.PASSWORD_RESET_TIMEOUT // 3600} hour.</p>
        </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))

    smtp_client = None
    try:
        logger.info(f"Initiating email send to {email} using SSL/TLS on port {settings.SMTP_PORT}")
        
        # Create SMTP client with SSL/TLS from the start
        smtp_client = aiosmtplib.SMTP(
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            use_tls=True,  # Enable TLS from the start
            timeout=30
        )

        logger.info("Establishing secure connection...")
        await smtp_client.connect()

        logger.info("Attempting login...")
        await smtp_client.login(sender_email, sender_password)
        
        logger.info("Sending message...")
        await smtp_client.send_message(message)
        
        logger.info(f"Password reset email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        raise
    finally:
        if smtp_client:
            try:
                await smtp_client.quit()
            except Exception as e:
                logger.error(f"Error during SMTP client cleanup: {str(e)}")