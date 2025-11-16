# app/db/models/template.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False, index=True)  # 'assessment', 'survey', etc.

    # Template content and configuration
    content = Column(JSONB, nullable=True)
    configuration = Column(JSONB, nullable=True)  # Template-specific configuration

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)
    version = Column(String(20), default="1.0")  # Template versioning

    # Foreign keys
    created_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships with proper lazy loading
    # created_by_user = relationship(
    #     "User",
    #     back_populates="templates_created",
    #     foreign_keys=[created_by_id],
    #     lazy="joined"
    # )

    # Define table indexes for performance
    __table_args__ = (
        Index('idx_template_type_active', 'template_type', 'is_active'),
        Index('idx_template_created_by', 'created_by_id', 'created_at'),
        Index('idx_template_public_active', 'is_public', 'is_active'),
        Index('idx_template_name_type', 'name', 'template_type'),
    )

    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}')>"