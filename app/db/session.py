# # app/db/session.py

import os
# from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from dotenv import load_dotenv


DATABASE_URL = "postgresql+asyncpg://psychsync_user:password@localhost/psychsync_db"



load_dotenv()  # This loads variables from .env

DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL, echo=True, future=True)


# Sync engine
# engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Async engine
async_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Sync session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine)

# Async session
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Async session factory
async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()






# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
# from app.core.config import settings
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# from app.db.session import engine
# from app.db.base import Base

# def init_db():
#     Base.metadata.create_all(bind=engine)

# # Sync engine (if you still use sync DB)
# engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# # Async engine (recommended with FastAPI + async SQLAlchemy)
# async_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# # Sync session
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Async session
# AsyncSessionLocal = sessionmaker(
#     bind=async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )

# # Dependency for routes
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# engine = create_engine(settings.DATABASE_URL, future=True, echo=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

# class Base(DeclarativeBase):
#     pass

# # Dependency for FastAPI
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



# # import os
# # from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# # from .base import Base
# # from app.core.config import settings
# # from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# # from sqlalchemy import create_engine
# # from sqlalchemy.orm import sessionmaker, declarative_base
# # from dotenv import load_dotenv

# # #DATABASE_URL = "DATABASE_URL:///./test.db"  # change later for Postgres

# # # Load environment variables
# # load_dotenv()

# # DATABASE_URL = os.getenv(
# # "DATABASE_URL",
# # "postgresql+asyncpg://psychsync_user:password@localhost/psychsync_db",
# # )

# # engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
# # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # def get_db():
# #     db = SessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()


# # # Single async engine
# # engine = create_async_engine(
# #     settings.DATABASE_URL,  # <- read from .env
# #     echo=True,              # logs SQL queries
# #     future=True,            # recommended for SQLAlchemy 2.0 style
# #     pool_pre_ping=True      # checks connections before using
# # )

# # # Async session factory
# # AsyncSessionLocal = sessionmaker(
# #     bind=engine,
# #      autocommit=False, 
# #     autoflush=False,
# #     class_=AsyncSession,
# #     expire_on_commit=False
# # )

# # # Sync engine (optional, for Alembic or scripts)
# # sync_engine = create_engine(DATABASE_URL, echo=True, future=True)
# # SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# # # Base class for models
# # Base = declarative_base()


# # # Dependency for FastAPI routes
# # async def get_db():
# #     async with AsyncSessionLocal() as session:
# #         yield session


# # # Init DB (for creating tables without Alembic)
# # def init_db():
# #     Base.metadata.create_all(bind=sync_engine)



# # print("Current DB URL:", settings.DATABASE_URL)






# # # Async engine for FastAPI
# # engine = create_async_engine(DATABASE_URL, future=True, pool_pre_ping=True)
# # engine = create_async_engine(settings.DATABASE_URL, echo=True)
# # AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# # Convenience: sync engine (for Alembic autogenerate if you prefer run_sync)
# # from sqlalchemy import create_engine
# # sync_engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))