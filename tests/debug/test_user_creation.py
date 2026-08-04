import uuid

from app.db.models.user import User

user = User(
    id=uuid.uuid4(), email="super_admin@example.com", role="admin", is_active=True
)
user.is_superuser = True
print(f"User is_superuser: {user.is_superuser}")
