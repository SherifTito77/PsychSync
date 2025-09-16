
from sqlalchemy import Column, String  #,UUID(as_uuid=True)
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base
import sqlalchemy as sa

class Framework(Base):
    __tablename__ = "frameworks"


    id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    name = sa.Column(sa.String, nullable=False, unique=True)
    description = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)

    # id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    # name = Column(String, nullable=False)
    # description = Column(String, nullable=True)










# # backend/app/db/models/framework.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class Framework(Base):
# __tablename__ = "frameworks"


# id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# code = sa.Column(sa.Text, nullable=False, unique=True)
# name = sa.Column(sa.Text, nullable=False)
# created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)