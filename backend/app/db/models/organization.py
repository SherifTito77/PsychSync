import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from ..base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    name = sa.Column(CITEXT, nullable=False, unique=True)
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False
    )
    updated_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False
    )






# backend/app/db/models/organization.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class Organization(Base):
# __tablename__ = "organizations"


# id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# name = sa.Column(sa.Text, nullable=False)
# slug = sa.Column(sa.Text, nullable=False, unique=True)
# created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# deleted_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)


# from sqlalchemy import Column, String, DateTime, func
# from sqlalchemy.dialects.postgresql import UUID
# from app.db.base import Base
# import uuid

# class Organization(Base):
#     __tablename__ = "organizations"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String, nullable=False)
#     slug = Column(String, nullable=False, unique=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
