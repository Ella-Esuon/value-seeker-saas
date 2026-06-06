import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import settings

_logger = logging.getLogger("value_seeker")


class EmailService:
    """
    Email abstraction layer.
    Set SMTP_HOST + SMTP_USER env vars to enable real delivery; otherwise logs only.
    """

    def __init__(self):
        self._enabled = bool(settings.SMTP_HOST and settings.SMTP_USER)

    def send_password_reset(self, to_email: str, reset_token: str, username: str) -> None:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Password Reset Request – Value Seeker"
        body = (
            f"Hello {username},\n\n"
            f"You requested a password reset. Use the link below:\n\n"
            f"{reset_url}\n\n"
            f"This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"Value Seeker Team"
        )

        if self._enabled:
            self._send_smtp(to_email, subject, body)
        else:
            _logger.info(
                '{"event":"email_mock","to":"%s","subject":"%s","reset_url":"%s"}',
                to_email, subject, reset_url,
            )

    def _send_smtp(self, to: str, subject: str, body: str) -> None:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)


email_service = EmailService()
