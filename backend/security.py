
import os
from pathlib import Path
import jwt

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pwdlib import PasswordHash
from slowapi import Limiter
from slowapi.util import get_remote_address

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Password hashing using Argon2
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

REGISTER_LIMIT = "5/minute"
LOGIN_LIMIT = "5/minute"
OTP_LIMIT = "10/minute"


# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY") or "prod-secret-fallback-login-setup-9823482347234"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Generate JWT access token

def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire,
        "token_type": "access"
    })

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def create_password_reset_token(email: str) -> str:
    import secrets

    expire = datetime.now(timezone.utc) + timedelta(minutes=10)

    payload = {
        "sub": email,
        "token_type": "password_reset",
        "jti": secrets.token_hex(32),
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token

