from datetime import datetime
from typing import Optional, Any
import uuid

from sqlalchemy import String, TIMESTAMP, text, ForeignKey, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    environment: Mapped[str] = mapped_column(
        String(10), 
        CheckConstraint("environment IN ('live', 'test')"),
        default="live"
    )
    
    permissions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'[\"qr:read\", \"qr:write\"]'")
    )
    
    ip_allowlist: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
