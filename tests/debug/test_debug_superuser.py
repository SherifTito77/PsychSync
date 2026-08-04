from app.db.models.user import User

user = User(is_superuser=True)
print(f"Direct access: {user.is_superuser}")
print(f"Dict access: {user.__dict__.get('is_superuser')}")
