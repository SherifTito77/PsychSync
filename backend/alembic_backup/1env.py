import sys
import os

# Add the parent folder of 'app' to sys.path
# Here, 'app' is inside backend/, so we add backend/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Optional: print to debug path
# print(sys.path)



import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Import your Base and models so Alembic can detect tables
from app.db.base import Base
from app.db.models import (
    organization,
    user,
    team,
    assessment,
    framework,
    question,
    question_option,
    response,
    role,
    org_member,
    team_member,
)

# Alembic config object
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode using async engine."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async def do_migrations():
        async with connectable.begin() as conn:
            await conn.run_sync(context.run_migrations)

    asyncio.run(do_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()











# from logging.config import fileConfig
# from sqlalchemy import pool
# from sqlalchemy.ext.asyncio import create_async_engine
# from alembic import context

# from app.db.base import Base
# from app.db.models import (
#     organization,
#     user,
#     team,
#     assessment,
#     framework,
#     question,
#     question_option,
#     response,
#     role,
#     org_member,
#     team_member,
# )

# config = context.config
# fileConfig(config.config_file_name)
# target_metadata = Base.metadata

# def run_migrations_online():
#     connectable = create_async_engine(
#         config.get_main_option("sqlalchemy.url"),
#         poolclass=pool.NullPool,
#     )

#     async def do_migrations():
#         async with connectable.begin() as conn:
#             await conn.run_sync(context.run_migrations)

#     import asyncio
#     asyncio.run(do_migrations())

# if context.is_offline_mode():
#     context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
#     context.run_migrations()
# else:
#     run_migrations_online()








# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from app.db.base import Base
# target_metadata = Base.metadata





# from sqlalchemy import engine_from_config
# from logging.config import fileConfig
# from sqlalchemy import pool
# from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
# from alembic import context
# import asyncio
# # import os

# # from app.db.base import Base  # import all models
# from app.db import models  # ensure models are registered
# from app.db import base
# from app.db.models import (    # <- import all models
#     organization,
#     user,
#     team,
#     assessment,
#     framework,
#     question,
#     question_option,
#     response,
#     role,
#     org_member,
#     team_member,
# )


# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://psychsync_user@localhost/psychsync_db")

# config = context.config
# fileConfig(config.config_file_name)

# target_metadata = Base.metadata

# def run_migrations_offline():
#     context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
#     with context.begin_transaction():
#         context.run_migrations()

# async def run_migrations_online():
#     connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
#     async with connectable.connect() as connection:
#         await connection.run_sync(
#             lambda conn: context.configure(connection=conn, target_metadata=target_metadata)
#         )
#         async with context.begin_transaction():
#             await connection.run_sync(context.run_migrations)

# def run_migrations_online_sync():
#     asyncio.run(run_migrations_online())

# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online_sync()
