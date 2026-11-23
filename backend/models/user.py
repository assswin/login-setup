
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, index=True, nullable=False)

    phone = Column(String(20), unique=True, nullable=True)

    password_hash = Column(String(255), nullable=False)

    email_verified = Column(Boolean, default=False)

    phone_verified = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)

    is_logged_in = Column(Boolean, default=False, nullable=False)

    is_admin = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
