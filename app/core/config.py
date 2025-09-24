
# app/core/config.py
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv



# Load .env file if it exists
BASE_DIR = Path(__file__).resolve().parents[2]  # project root
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Security / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = str(ENV_PATH)
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()


# Singleton instance
settings = get_settings()








# from pathlib import Path
# from dotenv import load_dotenv
# from pydantic_settings import BaseSettings
# from functools import lru_cache

# # Load .env
# BASE_DIR = Path(__file__).resolve().parents[2]  # psychsync/
# ENV_PATH = BASE_DIR / ".env"

# if ENV_PATH.exists():
#     load_dotenv(dotenv_path=ENV_PATH)

# class Settings(BaseSettings):
#     DATABASE_URL: str
#     SECRET_KEY: str
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

#     class Config:
#         env_file = str(ENV_PATH)

# @lru_cache()
# def get_settings() -> Settings:
#     return Settings()

# # Singleton instance to import everywhere
# settings = get_settings()
