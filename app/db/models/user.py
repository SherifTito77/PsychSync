
# app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owned_teams = relationship("Team", back_populates="owner", foreign_keys="Team.owner_id")
    team_memberships = relationship("TeamMember", back_populates="user")
    assessments = relationship("Assessment", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"


# from sqlalchemy import Column, Integer, String, Boolean
# # from app.db.session import Base
# from app.db.base import Base

# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True, nullable=False)
#     hashed_password = Column(String, nullable=False)
#     is_active = Column(Boolean, default=True)







# # import sqlalchemy as sa
# # from sqlalchemy.dialects.postgresql import UUID, CITEXT
# # from app.db.base import Base  # only Base here, no model imports
# # from sqlalchemy import Column, Integer, String, Boolean, DateTime

# # import datetime



# # class User(Base):
# #     __tablename__ = "users"

# #     id = sa.Column(
# #         UUID(as_uuid=True),
# #         primary_key=True,
# #         server_default=sa.text("gen_random_uuid()")
# #     )
# #     email = sa.Column(CITEXT, nullable=False, unique=True)
# #     password_hash = sa.Column(sa.Text, nullable=False)
# #     full_name = sa.Column(sa.Text, nullable=True)
# #     avatar_url = sa.Column(sa.Text, nullable=True)
# #     is_superuser = Column(Boolean, default=False)
# #     is_active = sa.Column(
# #         sa.Boolean,
# #         nullable=False,
# #         server_default=sa.text("true")
# #     )
# #     created_at = sa.Column(
# #         sa.TIMESTAMP(timezone=True),
# #         server_default=sa.text("NOW()"),
# #         nullable=False
# #     )
# #     updated_at = sa.Column(
# #         sa.TIMESTAMP(timezone=True),
# #         server_default=sa.text("NOW()"),
# #         server_onupdate=sa.text("NOW()"),
# #         nullable=False
# #     )
# #     deleted_at = sa.Column(
# #         sa.TIMESTAMP(timezone=True),
# #         nullable=True
# #     )
