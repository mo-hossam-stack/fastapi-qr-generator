from datetime import datetime
from typing import Optional, Any
import uuid

from sqlalchemy import String, Boolean, CheckConstraint, TIMESTAMP, text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QRCode(Base):
    __tablename__ = "qr_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # QR Content
    type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("type IN ('url', 'text', 'vcard', 'wifi', 'email', 'sms', 'phone', 'geo', 'image')"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Dynamic QR (MVP: mostly default False)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=False)
    short_code: Mapped[Optional[str]] = mapped_column(String(10), unique=True, nullable=True, index=True)
    
    # Display Options (JSONB)
    options: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"), nullable=False)
    
    # Storage (JSONB) - {"png": "path", ...}
    storage_paths: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"), nullable=False)
    
    # Metadata
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{}'"), index=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="qr_codes")
