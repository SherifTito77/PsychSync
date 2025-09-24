# app/scripts/foo.py
from app.core.config import settings

print("DB URL:", settings.DATABASE_URL)
print("Secret Key starts with:", settings.SECRET_KEY[:8])

