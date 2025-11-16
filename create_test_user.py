import sys
sys.path.insert(0, '/Users/sheriftito/Downloads/psychsync')

from app.db.session import SessionLocal
from app.db.models.user import User
from app.core.security import get_password_hash
import uuid

db = SessionLocal()

# Delete existing test user if exists
existing = db.query(User).filter(User.email == "test@example.com").first()
if existing:
    print("Deleting existing test user...")
    db.delete(existing)
    db.commit()

# Create new test user
new_user = User(
    id=uuid.uuid4(),
    email="test@example.com",
    password_hash=get_password_hash("Test1234!"),
    full_name="Test User",
    is_active=True
)

db.add(new_user)
db.commit()

print("✅ Test user created successfully!")
print(f"   Email: test@example.com")
print(f"   Password: Test1234!")
print(f"   Full Name: {new_user.full_name}")
print(f"   ID: {new_user.id}")

db.close()
