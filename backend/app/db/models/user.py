import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from ..base import Base


class User(Base):
    __tablename__ = "users"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    email = sa.Column(CITEXT, nullable=False, unique=True)
    password_hash = sa.Column(sa.Text, nullable=False)
    full_name = sa.Column(sa.Text, nullable=True)
    avatar_url = sa.Column(sa.Text, nullable=True)
    is_active = sa.Column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true")
    )
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
    deleted_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)







# # backend/app/db/models/user.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID, CITEXT
# from ..base import Base  # make sure relative import works, or use 'from app.db.base import Base'


# class User(Base):
#     __tablename__ = "users"

#     id = sa.Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         server_default=sa.text("gen_random_uuid()")
#     )
#     email = sa.Column(CITEXT, nullable=False, unique=True)
#     password_hash = sa.Column(sa.Text, nullable=False)
#     full_name = sa.Column(sa.Text, nullable=True)
#     avatar_url = sa.Column(sa.Text, nullable=True)
#     is_active = sa.Column(
#         sa.Boolean,
#         nullable=False,
#         server_default=sa.text("true")
#     )
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
#     deleted_at = sa.Column(
#         sa.TIMESTAMP(timezone=True),
#         nullable=True
#     )









# # # backend/app/db/models/user.py
# # import sqlalchemy as sa
# # from sqlalchemy.dialects.postgresql import UUID, CITEXT
# # from ..base import Base


# # class User(Base):
# # __tablename__ = "users"


# # id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# # email = sa.Column(CITEXT, nullable=False, unique=True)
# # password_hash = sa.Column(sa.Text, nullable=False)
# # full_name = sa.Column(sa.Text, nullable=True)
# # avatar_url = sa.Column(sa.Text, nullable=True)
# # is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
# # created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# # updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# # deleted_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)