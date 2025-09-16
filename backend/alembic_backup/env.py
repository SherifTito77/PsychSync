
import sys
from pathlib import Path
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from alembic import context

# Add backend folder to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.base import Base
from app.db.models import *

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# -------------------
# Offline migrations
# -------------------
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

# -------------------
# Online migrations (async)
# -------------------
# async def run_async_migrations():
#     connectable = create_async_engine(
#         config.get_main_option("sqlalchemy.url"),
#         poolclass=pool.NullPool,
#     )
#     async with connectable.begin() as conn:
#         await conn.run_sync(lambda sync_conn: context.configure(connection=sync_conn, target_metadata=target_metadata))
#         # Run migrations
#         await conn.run_sync(context.run_migrations)
#     await connectable.dispose()

async def run_async_migrations():
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    async with connectable.begin() as conn:
        # Wrap run_migrations in a lambda accepting sync_conn
        await conn.run_sync(lambda sync_conn: context.configure(connection=sync_conn, target_metadata=target_metadata))
        await conn.run_sync(lambda sync_conn: context.run_migrations())
    await connectable.dispose()



def run_migrations_online():
    asyncio.run(run_async_migrations())

# -------------------
# Choose mode
# -------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()




# import sys
# import os
# from logging.config import fileConfig
# from sqlalchemy import create_engine, pool
# from alembic import context
# from pathlib import Path

# # Ensure the parent folder of 'app' is on sys.path
# sys.path.append(str(Path(__file__).resolve().parent.parent))

# from app.db.base import Base
# from app.db.models import *  # import all models so Alembic can see them

# # Alembic config
# config = context.config
# fileConfig(config.config_file_name)
# target_metadata = Base.metadata

# # Offline migrations
# def run_migrations_offline():
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
#     with context.begin_transaction():
#         context.run_migrations()

# # Online migrations (synchronous!)
# def run_migrations_online():
#     connectable = create_engine(
#         config.get_main_option("sqlalchemy.url"),
#         poolclass=pool.NullPool,
#     )
#     with connectable.connect() as connection:
#         context.configure(connection=connection, target_metadata=target_metadata)
#         with context.begin_transaction():
#             context.run_migrations()

# # Run
# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()




# import sys
# from pathlib import Path
# from logging.config import fileConfig

# from sqlalchemy import create_engine, pool
# from alembic import context

# # Add backend folder so 'app' is importable
# sys.path.append(str(Path(__file__).resolve().parent.parent))

# # Import your Base and all models
# from app.db.base import Base
# from app.db.models import *

# # Alembic config
# config = context.config
# fileConfig(config.config_file_name)
# target_metadata = Base.metadata


# def run_migrations_offline():
#     """Run migrations in 'offline' mode (SQL script only)."""
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#     )
#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online():
#     """Run migrations in 'online' mode (apply to DB)."""
#     # Use a synchronous engine for Alembic
#     connectable = create_engine(
#         config.get_main_option("sqlalchemy.url"),
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection,
#             target_metadata=target_metadata,
#         )
#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()


# import sys
# from pathlib import Path
# from logging.config import fileConfig
# from sqlalchemy import create_engine, pool
# from alembic import context

# # Add backend folder so 'app' is importable
# sys.path.append(str(Path(__file__).resolve().parent.parent))

# from app.db.base import Base
# from app.db.models import *

# target_metadata = Base.metadata
# config = context.config
# fileConfig(config.config_file_name)


# def run_migrations_offline():
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#     )
#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online():
#     # Use a synchronous engine for Alembic
#     connectable = create_engine(
#         config.get_main_option("sqlalchemy.url"),
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         context.configure(connection=connection, target_metadata=target_metadata)
#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()




# import asyncio
# from logging.config import fileConfig
# from pathlib import Path
# import sys

# from sqlalchemy import pool
# from sqlalchemy.ext.asyncio import create_async_engine
# from alembic import context

# # Ensure 'backend' folder is in sys.path so 'app' is importable
# sys.path.append(str(Path(__file__).resolve().parent.parent))

# # Import Base and all models
# from app.db.base import Base
# from app.db.models import *  # import all models for metadata
# target_metadata = Base.metadata

# # Alembic config
# config = context.config
# fileConfig(config.config_file_name)


# def run_migrations_offline():
#     """Run migrations in 'offline' mode."""
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online():
#     """Run migrations in 'online' mode using async engine."""
#     connectable = create_async_engine(
#         config.get_main_option("sqlalchemy.url"),
#         poolclass=pool.NullPool,
#     )

#     async def do_run_migrations():
#         async with connectable.connect() as conn:
#             # Configure context
#             await conn.run_sync(
#                 lambda sync_conn: context.configure(connection=sync_conn, target_metadata=target_metadata)
#             )
#             async with conn.begin():
#                 # Run migrations
#                 await conn.run_sync(context.run_migrations)

#     asyncio.run(do_run_migrations())


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()
