import logging
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import requests

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)

FIREBASE_WEB_API_KEY = (os.getenv("FIREBASE_WEB_API_KEY") or "").strip()
FIREBASE_PROJECT_ID = (os.getenv("FIREBASE_PROJECT_ID") or "").strip()


class FirebaseVerificationError(Exception):
    pass


def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verifies a Firebase ID token using Google Identity Toolkit API.
    Returns user account information including verified phone_number.
    """
    if not id_token or not id_token.strip():
        raise FirebaseVerificationError("Firebase ID token is required")

    api_key = (os.getenv("FIREBASE_WEB_API_KEY") or FIREBASE_WEB_API_KEY).strip()
    if not api_key:
        # Fallback for dev mode if user hasn't configured FIREBASE_WEB_API_KEY yet:
        # Allow test tokens in format 'test-token:<phone>'
        if id_token.startswith("test-token:"):
            test_phone = id_token.split(":", 1)[1].strip()
            return {"phoneNumber": test_phone, "localId": "test-uid-12345"}
        raise FirebaseVerificationError(
            "FIREBASE_WEB_API_KEY is not configured in backend .env. "
            "Please add your Firebase Web API key."
        )

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
    payload = {"idToken": id_token.strip()}

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "Invalid Firebase token")
            logger.warning("Firebase token verification failed: %s", error_msg)
            raise FirebaseVerificationError(f"Firebase verification failed: {error_msg}")

        users = data.get("users", [])
        if not users:
            raise FirebaseVerificationError("No user found for provided Firebase ID token")

        user_info = users[0]
        phone_number = user_info.get("phoneNumber")
        if not phone_number:
            raise FirebaseVerificationError("Firebase token does not contain a verified phone number")

        return user_info

    except requests.RequestException as exc:
        logger.error("Failed to connect to Google Identity Toolkit: %s", exc)
        raise FirebaseVerificationError("Unable to verify token with Google servers. Please try again.")
