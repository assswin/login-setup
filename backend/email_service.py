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


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "****"
    user_part, domain = email.split("@", 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + "*"
    else:
        masked_user = user_part[0] + "*" * (len(user_part) - 2) + user_part[-1]
    return f"{masked_user}@{domain}"


def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 4:
        return "****"
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"


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
    plain_text = (
        f"Your verification code to {purpose_text} is {otp}.\n\n"
        "This code expires in 5 minutes. If you did not request this code, you can ignore this email."
    )
    message.set_content(plain_text)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f6f8fa; margin: 0; padding: 24px; }}
        .card {{ max-width: 460px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e1e4e8; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .header {{ font-size: 20px; font-weight: 700; color: #1f2328; margin-bottom: 12px; }}
        .copy {{ font-size: 14px; color: #59636e; line-height: 1.5; margin-bottom: 24px; }}
        .otp-box {{ background: #f3f4f6; border-radius: 8px; border: 1px dashed #0969da; text-align: center; padding: 18px; margin-bottom: 24px; }}
        .otp-code {{ font-family: monospace; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #0969da; }}
        .footer {{ font-size: 12px; color: #8c959f; text-align: center; border-top: 1px solid #f0f2f5; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">Verification Code</div>
        <div class="copy">Use the 6-digit verification code below to {purpose_text}. This code expires in <strong>5 minutes</strong>.</div>
        <div class="otp-box">
          <div class="otp-code">{otp}</div>
        </div>
        <div class="copy">If you did not request this verification, no action is needed.</div>
        <div class="footer">Secure Login Authentication System</div>
      </div>
    </body>
    </html>
    """
    message.add_alternative(html_content, subtype="html")

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
