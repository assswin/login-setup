import logging
import os
from pathlib import Path
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


def send_otp_email(recipient: str, otp: str, purpose: str) -> None:
    gmail_address = (os.getenv("GMAIL_ADDRESS") or "").strip()
    gmail_app_password = "".join(
        (os.getenv("GMAIL_APP_PASSWORD") or "").split()
    )

    if purpose == "login":
        subject = "Your login verification code"
        purpose_text = "log in"
    elif purpose == "password_reset":
        subject = "Your password reset code"
        purpose_text = "reset your password"
    else:
        raise ValueError(f"Unsupported OTP email purpose: {purpose}")

    # Fallback to local console OTP display if 16-character Google App Password is not provided
    if not gmail_address or len(gmail_app_password) != 16:
        logger.warning(
            "GMAIL_APP_PASSWORD is not a valid 16-character Google App Password. "
            "Falling back to local console OTP for local development."
        )
        print(
            f"\n========================================\n"
            f"[LOCAL DEV OTP] Purpose: {purpose_text.upper()}\n"
            f"Recipient: {recipient}\n"
            f"OTP Code:  {otp}\n"
            f"Expires in: 5 minutes\n"
            f"========================================\n"
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = gmail_address
    message["To"] = recipient
    message.set_content(
        f"Your code to {purpose_text} is {otp}.\n\n"
        "This code expires in 5 minutes. If you did not request this code, "
        "you can ignore this email."
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(gmail_address, gmail_app_password)
            refused_recipients = server.send_message(message)
            if refused_recipients:
                raise EmailDeliveryError("Gmail rejected the OTP email recipient.")
    except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
        logger.exception("Gmail OTP email delivery failed. Logging OTP locally.")
        print(
            f"\n========================================\n"
            f"[LOCAL DEV OTP FALLBACK] Purpose: {purpose_text.upper()}\n"
            f"Recipient: {recipient}\n"
            f"OTP Code:  {otp}\n"
            f"Note: Gmail delivery failed ({exc}). Use code above.\n"
            f"========================================\n"
        )
