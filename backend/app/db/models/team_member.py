
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

class TeamMember(Base):
    __tablename__ = "team_members"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False)
    team_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False)
    role = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)







# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class Framework(Base):
#     __tablename__ = "frameworks"

#     id = sa.Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         server_default=sa.text("gen_random_uuid()")
#     )
#     name = sa.Column(sa.Text, nullable=False, unique=True)
#     description = sa.Column(sa.Text, nullable=True)
#     created_at = sa.Column(
#         sa.TIMESTAMP(timezone=True),
#         server_default=sa.text("NOW()"),
#         nullable=False
#     )
#     updated_at = sa.Column(
#         sa.TIMESTAMP(timezone=True),
#         server_default=sa.text("NOW()"),
#         nullable=False
#     )





# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class TeamMember(Base):
#     __tablename__ = "team_members"

#     id = sa.Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         server_default=sa.text("gen_random_uuid()")
#     )
#     team_id = sa.Column(
#         UUID(as_uuid=True),
#         sa.ForeignKey("teams.id"),
#         nullable=False
#     )
#     user_id = sa.Column(
#         UUID(as_uuid=True),
#         sa.ForeignKey("users.id"),
#         nullable=False
#     )
#     role = sa.Column(sa.Text, nullable=False)
#     created_at = sa.Column(
#         sa.TIMESTAMP(timezone=True),
#         server_default=sa.text("NOW()"),
#         nullable=False
#     )











# # # backend/app/db/models/team_member.py
# # import sqlalchemy as sa
# # from sqlalchemy.dialects.postgresql import UUID
# # from ..base import Base


# # class TeamMember(Base):
# # __tablename__ = "team_members"


# # id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# # team_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
# # user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
# # role_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('roles.id'), nullable=False)
# # created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# # __table_args__ = (sa.UniqueConstraint('team_id', 'user_id', name='uq_team_user'),)