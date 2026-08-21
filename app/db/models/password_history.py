# app/db/models/password_history.py
"""
Password history model for preventing password reuse.
NIST SP 800-63B compliant — tracks last N password hashes per user.
"""

import uuid

from sqlalchemy import Column, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.core.database import Base

# How many previous passwords to retain per user
PASSWORD_HISTORY_DEPTH = 12


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    password_hash = Column(Text, nullable=False)
    changed_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    change_reason = Column(
        String(50), nullable=True
    )  # "user_initiated", "admin_reset", "expired"
