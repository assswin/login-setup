
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import secrets
import hashlib

from datetime import datetime, timedelta, timezone
import jwt

from security import SECRET_KEY, ALGORITHM

from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from database import engine, Base, get_db

from security import (
    limiter,
    hash_password,
    verify_password,
    create_access_token,
    create_password_reset_token,
    REGISTER_LIMIT,
    LOGIN_LIMIT,
    OTP_LIMIT
)

from schemas import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse
)

from dependencies import get_current_user, bearer_scheme
from email_service import EmailDeliveryError, send_otp_email, mask_email, mask_phone

from models.user import User
from models.password_reset import PasswordResetOTP
from models.login_otp import LoginOTP
from models.reset_token import PasswordResetToken


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Secure Authentication API",
    description="Production Authentication System",
    version="1.0.0"
)

raw_origins = os.getenv("CORS_ORIGINS")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()] if raw_origins else [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

api_router = APIRouter()


# --------------------------------------------------
# DATABASE TABLE CREATION & MIGRATION
# --------------------------------------------------

Base.metadata.create_all(bind=engine)

try:
    from sqlalchemy import text
    inspector = inspect(engine)
    existing_cols = [c["name"] for c in inspector.get_columns("users")]
    if "is_logged_in" not in existing_cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_logged_in BOOLEAN DEFAULT 0"))
except Exception:
    pass


# --------------------------------------------------
# OTP REQUEST SCHEMA
# --------------------------------------------------

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

class LoginOTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

# Configurable Admin Passcode (Default: 735195)
ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE", "735195")

class AdminAuthRequest(BaseModel):
    passcode: str


# --------------------------------------------------
# OTP HELPER FUNCTIONS
# --------------------------------------------------

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(otp: str):
    return hashlib.sha256(otp.encode()).hexdigest()


def get_otp_expiry():
    return datetime.now(timezone.utc) + timedelta(minutes=5)


def save_otp_to_database(
    db: Session,
    user_id: int,
    otp_hash: str
):
    # Invalidate previous unused password-reset OTPs
    db.query(PasswordResetOTP).filter(
        PasswordResetOTP.user_id == user_id,
        PasswordResetOTP.is_used == False
    ).update(
        {"is_used": True},
        synchronize_session=False
    )

    # Set OTP expiry to 5 minutes
    expiry = get_otp_expiry()

    # Create new OTP record
    otp_record = PasswordResetOTP(
        user_id=user_id,
        otp_hash=otp_hash,
        expires_at=expiry,
        attempts=0,
        is_used=False
    )

    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    return otp_record


def save_login_otp_to_database(
    db: Session,
    user_id: int,
    otp_hash: str
):
    # Invalidate previous unused login OTPs
    db.query(LoginOTP).filter(
        LoginOTP.user_id == user_id,
        LoginOTP.is_used == False
    ).update(
        {"is_used": True},
        synchronize_session=False
    )

    # Set OTP expiry to 5 minutes
    expiry = get_otp_expiry()

    # Create new login OTP record
    otp_record = LoginOTP(
        user_id=user_id,
        otp_hash=otp_hash,
        expires_at=expiry
    )

    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    return otp_record



# --------------------------------------------------
# STATUS & HEALTH CHECKS
# --------------------------------------------------

@api_router.get("/status")
def status():
    return {
        "message": "Authentication Backend is running",
        "database": "SQLite",
        "status": "success"
    }


@api_router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@api_router.get("/db-check")
def database_check():

    inspector = inspect(engine)

    return {
        "database": "SQLite",
        "tables": inspector.get_table_names()
    }


@api_router.get("/db-test")
def database_test(
    db: Session = Depends(get_db)
):
    return {
        "message": "Database session connected successfully",
        "status": "success"
    }


# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

@api_router.post("/register", response_model=UserResponse)
@limiter.limit(REGISTER_LIMIT)
def register_user(
    request: Request,
    user: UserRegister,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    existing_phone = db.query(User).filter(
        User.phone == user.phone
    ).first()

    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------


@api_router.post("/login")
@limiter.limit(LOGIN_LIMIT)
def login_user(
    request: Request,
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not existing_user or not verify_password(
        user.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not existing_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated"
        )

    # Generate login OTP
    otp = generate_otp()

    # Hash OTP
    otp_hash = hash_otp(otp)

    # Save OTP in login_otps table
    otp_record = save_login_otp_to_database(
        db,
        existing_user.id,
        otp_hash
    )

    # Deliver OTP via Email (100% free Gmail SMTP)
    send_otp_email(existing_user.email, otp, "login")

    return {
        "message": f"Verification code sent to {mask_email(existing_user.email)}.",
        "email_masked": mask_email(existing_user.email),
        "phone": existing_user.phone,
        "phone_masked": mask_phone(existing_user.phone),
        "otp_required": True,
        "expires_in": 300
    }






@api_router.post("/verify-login-otp", response_model=TokenResponse)
@limiter.limit(OTP_LIMIT)
def verify_login_otp(
    request: Request,
    data: LoginOTPVerifyRequest,
    db: Session = Depends(get_db)
):
    # 1. Validate OTP format
    if not data.otp.isdigit() or len(data.otp) != 6:
        raise HTTPException(
            status_code=400,
            detail="OTP must contain exactly 6 digits"
        )

    # 2. Find registered user
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated"
        )

    # 3. Find latest unused login OTP
    otp_record = db.query(LoginOTP).filter(
        LoginOTP.user_id == user.id,
        LoginOTP.is_used == False
    ).order_by(
        LoginOTP.created_at.desc()
    ).first()

    if otp_record is None:
        raise HTTPException(
            status_code=400,
            detail="No active login OTP found"
        )

    # 4. Check OTP expiry
    expiry = otp_record.expires_at

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expiry:
        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Login OTP has expired"
        )

    # 5. Check maximum attempts
    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=429,
            detail="Too many incorrect attempts"
        )

    # 6. Verify OTP hash
    submitted_hash = hash_otp(data.otp)

    if not secrets.compare_digest(
        submitted_hash,
        otp_record.otp_hash
    ):
        otp_record.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid login OTP"
        )

    # 7. Mark OTP as used and user as logged in
    otp_record.is_used = True
    user.is_logged_in = True
    db.commit()

    # 8. Generate JWT after successful OTP verification
    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# --------------------------------------------------
# USER PROFILE & LOGOUT
# --------------------------------------------------

@api_router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@api_router.post("/logout")
def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.is_logged_in = False
    db.commit()
    return {"message": "Logged out successfully"}


# --------------------------------------------------
# TEMPORARY ADMIN USER MANAGEMENT (Passcode: 735195)
# Completely decoupled from standard authentication.
# Can be safely deleted in the future without impacting user login.
# --------------------------------------------------

@api_router.post("/admin/login")
def admin_login(data: AdminAuthRequest):
    if not secrets.compare_digest(data.passcode.strip(), ADMIN_PASSCODE):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin passcode"
        )
    token = create_access_token(data={"sub": "admin", "role": "admin"})
    return {
        "admin_token": token,
        "message": "Admin session authenticated successfully"
    }


def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin permissions required")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired admin session")
    return True


@api_router.get("/admin/users", response_model=list[UserResponse])
def admin_get_all_users(
    is_admin_verified: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    return db.query(User).order_by(User.id.asc()).all()


@api_router.post("/admin/users/{user_id}/toggle-block")
def admin_toggle_block_user(
    user_id: int,
    is_admin_verified: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.is_active = not target_user.is_active
    if not target_user.is_active:
        target_user.is_logged_in = False
    db.commit()
    db.refresh(target_user)

    action = "unblocked" if target_user.is_active else "blocked"
    return {
        "message": f"User {target_user.email} successfully {action}.",
        "user_id": target_user.id,
        "is_active": target_user.is_active,
        "is_logged_in": target_user.is_logged_in
    }


@api_router.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    is_admin_verified: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_email = target_user.email

    # Clean up all related foreign key records first
    db.query(LoginOTP).filter(LoginOTP.user_id == user_id).delete(synchronize_session=False)
    db.query(PasswordResetOTP).filter(PasswordResetOTP.user_id == user_id).delete(synchronize_session=False)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete(synchronize_session=False)

    # Permanently delete the user account
    db.delete(target_user)
    db.commit()

    return {
        "message": f"User account {user_email} has been permanently deleted.",
        "user_id": user_id
    }


# --------------------------------------------------
# GENERATE PASSWORD RESET OTP
# --------------------------------------------------

@api_router.post("/generate-otp")
@limiter.limit(OTP_LIMIT)
def generate_otp_api(
    request: Request,
    otp_data: OTPRequest,
    db: Session = Depends(get_db)
):

    # 1. Find registered user using email

    user = db.query(User).filter(
        User.email == otp_data.email
    ).first()

    if user is None:
        return {
            "message": "If the email is registered, an OTP has been sent.",
            "expires_in": 300
        }

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated"
        )

    # 2. Check OTP generation limit
    # Maximum 3 requests within 5 minutes

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=5)

    recent_requests = db.query(PasswordResetOTP).filter(
        PasswordResetOTP.user_id == user.id,
        PasswordResetOTP.created_at >= cutoff
    ).count()

    if recent_requests >= 3:
        raise HTTPException(
            status_code=429,
            detail="Too many OTP requests. Please try again later."
        )

    # 3. Generate six-digit OTP

    otp = generate_otp()

    # 4. Hash OTP

    otp_hash = hash_otp(otp)

    # 5. Save OTP hash using user ID

    otp_record = save_otp_to_database(
        db,
        user.id,
        otp_hash
    )

    # Deliver OTP via Email (100% free Gmail SMTP)
    send_otp_email(user.email, otp, "password_reset")

    return {
        "message": f"OTP sent to {mask_email(user.email)}.",
        "email_masked": mask_email(user.email),
        "phone": user.phone,
        "phone_masked": mask_phone(user.phone),
        "expires_in": 300
    }


@api_router.post("/verify-otp")
@limiter.limit(OTP_LIMIT)
def verify_otp_api(
    request: Request,
    data: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    # 1. Validate OTP format
    if not data.otp.isdigit() or len(data.otp) != 6:
        raise HTTPException(
            status_code=400,
            detail="OTP must contain exactly 6 digits"
        )

    # 2. Find registered user
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated"
        )

    # 3. Find latest unused OTP
    otp_record = db.query(PasswordResetOTP).filter(
        PasswordResetOTP.user_id == user.id,
        PasswordResetOTP.is_used == False
    ).order_by(
        PasswordResetOTP.created_at.desc()
    ).first()

    if otp_record is None:
        raise HTTPException(
            status_code=400,
            detail="No active OTP found"
        )

    # 4. Check OTP expiry
    expiry = otp_record.expires_at

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expiry:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="OTP has expired"
        )

    # 5. Check maximum attempts
    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=429,
            detail="Too many incorrect attempts. Generate a new OTP."
        )

    # 6. Compare submitted OTP hash
    submitted_hash = hash_otp(data.otp)

    if not secrets.compare_digest(
        submitted_hash,
        otp_record.otp_hash
    ):
        otp_record.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    # 7. Generate password-reset token
    reset_token = create_password_reset_token(user.email)

    # 8. Decode our generated token to get its JTI and expiry
    payload = jwt.decode(
        reset_token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    token_jti = payload["jti"]

    token_expiry = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc
    )

    # 9. Mark OTP as used
    otp_record.is_used = True

    # 10. Save reset-token tracking record
    reset_token_record = PasswordResetToken(
        jti=token_jti,
        user_id=user.id,
        expires_at=token_expiry,
        is_used=False
    )

    db.add(reset_token_record)
    db.commit()

    return {
        "message": "OTP verified successfully",
        "status": "success",
        "reset_token": reset_token,
        "expires_in": 600
    }



@api_router.post("/reset-password")
@limiter.limit(OTP_LIMIT)
def reset_password_api(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # 1. Validate new password
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    # 2. Decode reset token
    try:
        payload = jwt.decode(
            data.reset_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        token_type = payload.get("token_type")
        token_jti = payload.get("jti")

        if not email or token_type != "password_reset" or not token_jti:
            raise HTTPException(
                status_code=401,
                detail="Invalid password reset token"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired reset token"
        )

    # 3. Find user
    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated"
        )

    # 4. Find reset token in database
    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.jti == token_jti,
        PasswordResetToken.user_id == user.id
    ).first()

    if reset_record is None:
        raise HTTPException(
            status_code=401,
            detail="Reset token not found"
        )

    # 5. Check whether token was already used
    if reset_record.is_used:
        raise HTTPException(
            status_code=401,
            detail="Reset token has already been used"
        )

    # 6. Check database token expiry
    expiry = reset_record.expires_at

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(
            status_code=401,
            detail="Reset token has expired"
        )

    # 7. Update password
    user.password_hash = hash_password(data.new_password)

    # 8. Mark reset token as used
    reset_record.is_used = True

    db.commit()

    return {
        "message": "Password reset successfully",
        "status": "success"
    }


# --------------------------------------------------
# ROUTER REGISTRATION & FRONTEND STATIC SERVING
# --------------------------------------------------

# Register API routes under /api and root
app.include_router(api_router, prefix="/api")
app.include_router(api_router)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = (BASE_DIR.parent / "frontend" / "dist").resolve()

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = FRONTEND_DIST / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def fallback_home():
        return {
            "message": "Authentication Backend is running (build frontend for UI)",
            "status": "success"
        }


