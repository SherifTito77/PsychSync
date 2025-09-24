import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class OrgMember(Base):
    __tablename__ = "org_members"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    user_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False
    )
    org_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("organizations.id"),
        nullable=False
    )
    role = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False
    )







# # app/db/models/org_member.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class OrgMember(Base):
#     __tablename__ = "org_members"

#     id = sa.Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         server_default=sa.text("gen_random_uuid()")
#     )
#     user_id = sa.Column(
#         UUID(as_uuid=True),
#         sa.ForeignKey("users.id"),
#         nullable=False
#     )
#     org_id = sa.Column(
#         UUID(as_uuid=True),
#         sa.ForeignKey("organizations.id"),
#         nullable=False
#     )
#     role = sa.Column(sa.Text, nullable=False)
#     created_at = sa.Column(
#         sa.TIMESTAMP(timezone=True),
#         server_default=sa.text("NOW()"),
#         nullable=False
#     )








# # # app/db/models/org_member.py
# # import sqlalchemy as sa
# # from sqlalchemy.dialects.postgresql import UUID
# # from ..base import Base


# # class OrgMember(Base):
# # __tablename__ = "org_members"


# # id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# # org_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
# # user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
# # role_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('roles.id'), nullable=False)
# # created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# # __table_args__ = (sa.UniqueConstraint('org_id', 'user_id', name='uq_org_user'),)