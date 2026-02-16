from datetime import datetime
from typing import Optional, Any
import uuid

from sqlalchemy import String, Boolean, CheckConstraint, TIMESTAMP, text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Subscription Plan: 'free', 'pro', 'business', 'enterprise'
    plan: Mapped[str] = mapped_column(
        String(20), 
        CheckConstraint("plan IN ('free', 'pro', 'business', 'enterprise')"),
        default="free",
        index=True
    )
    
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    qr_codes: Mapped[list["QRCode"]] = relationship("QRCode", back_populates="user", cascade="all, delete-orphan")
