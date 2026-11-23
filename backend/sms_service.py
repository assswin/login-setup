import logging
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


class SMSError(Exception):
    pass


def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 4:
        return "****"
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"


def send_sms_otp(phone: str, otp: str, purpose: str) -> None:
    purpose_text = "log in" if purpose == "login" else "reset your password"

    twilio_account_sid = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
    twilio_auth_token = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
    twilio_phone = (os.getenv("TWILIO_PHONE_NUMBER") or "").strip()

    if twilio_account_sid and twilio_auth_token and twilio_phone:
        try:
            from twilio.rest import Client
            client = Client(twilio_account_sid, twilio_auth_token)
            client.messages.create(
                body=f"Your verification code to {purpose_text} is {otp}. Valid for 5 minutes.",
                from_=twilio_phone,
                to=phone
            )
            return
        except Exception as exc:
            logger.warning("Twilio SMS delivery failed (%s). Falling back to console OTP.", exc)

    # Local development output for localhost testing
    print(
        f"\n========================================\n"
        f"[LOCAL DEV SMS OTP]\n"
        f"Purpose:         {purpose_text.upper()}\n"
        f"Recipient Phone: {phone} (Masked: {mask_phone(phone)})\n"
        f"OTP Code:        {otp}\n"
        f"Expires in:      5 minutes\n"
        f"========================================\n"
    )
