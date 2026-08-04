# Domain Layer: Entities & Value Objects Explained

## 🎯 What Is The Domain Layer?

The **domain layer** contains your **business logic** and **business rules**.

### Key Principle: Framework Independence

```python
✅ Domain Layer:
   - NO FastAPI
   - NO SQLAlchemy
   - NO Redis
   - NO HTTP
   - Pure Python business logic

❌ Infrastructure Layer:
   - FastAPI (HTTP)
   - SQLAlchemy (Database)
   - Redis (Cache)
```

**Why?** Business logic should NEVER depend on frameworks. Frameworks come and go, business logic stays.

---

## 📦 Part 1: Domain Entities

### What Is a Domain Entity?

A **domain entity** is a business object with:
1. **Identity** (it has an ID)
2. **Behavior** (methods that do things)
3. **Business rules** (validation logic)
4. **Lifecycle** (creation, changes, deletion)

### Example: User Entity

```python
# app/domain/entities/user_entity.py

from dataclasses import dataclass
from uuid import UUID
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password

@dataclass
class User:
    """User domain entity - pure business object"""

    # Identity
    id: UUID

    # Value objects (validated types)
    email: Email
    password: Password
    full_name: str | None = None

    # Business state
    role: UserRole
    is_active: bool
    is_verified: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # ═══════════════════════════════════════════════════════════
    # BEHAVIOR: Business logic methods
    # ═══════════════════════════════════════════════════════════

    def verify_email(self) -> None:
        """Mark email as verified"""
        self.is_verified = True
        self._touch()  # Update timestamp

    def can_login(self) -> bool:
        """Check if user is allowed to login"""
        return self.is_active and self.is_verified

    def change_password(self, new_password: Password) -> None:
        """Change password (with validation in Password VO)"""
        self.password = new_password
        self._touch()

    def _touch(self) -> None:
        """Private: Update timestamp"""
        self.updated_at = datetime.utcnow()
```

### Why Not Just Use Database Models?

```python
# ❌ Database Model (SQLAlchemy) - Technical, not conceptual
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True)
    email = Column(String)  # Just a string - no validation!
    password_hash = Column(String)  # Technical detail

    # No behavior! No business rules!
    # Just a dumb data holder
```

**Problems:**
- ❌ No validation (email can be "asdf")
- ❌ No behavior (can't do user.can_login())
- ❌ Tied to database (Column, Table - infrastructure details)
- ❌ Technical not conceptual (password_hash vs password)

```python
# ✅ Domain Entity - Conceptual, business-focused
@dataclass
class User:
    email: Email  # Validated!
    password: Password  # Secure!

    def can_login(self) -> bool:  # Behavior!
        return self.is_active and self.is_verified
```

**Benefits:**
- ✅ Validated data (email must be valid format)
- ✅ Rich behavior (methods that do things)
- ✅ Framework independent (no SQLAlchemy)
- ✅ Business language (password, not password_hash)

---

## 💎 Part 2: Value Objects

### What Is a Value Object?

A **value object** is:
1. **Immutable** (can't change after creation)
2. **Defined by its value** (two with same value are equal)
3. **Self-validating** (can't create invalid one)

### Example 1: Email Value Object

```python
# app/domain/value_objects/email.py

import re
from dataclasses import dataclass

@dataclass(frozen=True)  # frozen = immutable
class Email:
    """Email value object - validates on creation"""

    value: str

    def __post_init__(self):
        """Validate email format immediately"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        if not email_pattern.match(self.value):
            raise ValueError(f"Invalid email: {self.value}")

    @property
    def domain(self) -> str:
        """Extract domain from email"""
        return self.value.split("@")[1].lower()

    @property
    def normalized(self) -> str:
        """Get lowercase email"""
        return self.value.lower()

    def __eq__(self, other) -> bool:
        """Two emails with same value are equal"""
        return isinstance(other, Email) and self.normalized == other.normalized
```

### How It Works

```python
# ✅ Valid email creation
email = Email("user@example.com")
print(email.domain)  # "example.com"
print(email.normalized)  # "user@example.com"

# ❌ Invalid email - crashes immediately!
try:
    bad_email = Email("not-an-email")
except ValueError as e:
    print(e)  # "Invalid email: not-an-email"

# ✅ Equality based on value
email1 = Email("USER@EXAMPLE.COM")
email2 = Email("user@example.com")
email1 == email2  # True (same value, different case)
```

### Example 2: Password Value Object

```python
# app/domain/value_objects/password.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@dataclass(frozen=True)
class Password:
    """Password value object - handles hashing and validation"""

    hash_value: str  # Only store hashed password

    @classmethod
    def create(cls, plaintext: str) -> "Password":
        """Create password from plaintext (hashes automatically)"""
        cls._validate_strength(plaintext)  # Check strength
        hash_value = pwd_context.hash(plaintext)  # Hash it
        return cls(hash_value=hash_value)

    def verify(self, plaintext: str) -> bool:
        """Check if plaintext matches hash"""
        return pwd_context.verify(plaintext, self.hash_value)

    @staticmethod
    def _validate_strength(plaintext: str) -> None:
        """Enforce password strength rules"""
        if len(plaintext) < 12:
            raise ValueError("Password must be 12+ characters")
        if not any(c.isupper() for c in plaintext):
            raise ValueError("Must contain uppercase")
        if not any(c.isdigit() for c in plaintext):
            raise ValueError("Must contain digit")
        # ... more rules
```

### How It Works

```python
# ✅ Create password (validates + hashes)
password = Password.create("SecurePass123!")
# Automatically validated and hashed
# hash_value = "$2b$12$..." (bcrypt hash)

# ✅ Verify password
password.verify("SecurePass123!")  # True
password.verify("WrongPassword")  # False

# ❌ Weak password rejected
try:
    Password.create("weak")  # Too short!
except ValueError as e:
    print(e)  # "Password must be 12+ characters"

# ✅ Security: Never see plaintext
print(password.hash_value)  # "$2b$12$..."
# No way to get original plaintext back
```

---

## 🔄 Entity vs Value Object: The Difference

| Aspect | Entity | Value Object |
|--------|--------|--------------|
| **Identity** | Has ID (identity matters) | No ID (value matters) |
| **Equality** | ID-based | Value-based |
| **Mutability** | Mutable (changes over time) | Immutable (frozen) |
| **Lifecycle** | Created, updated, deleted | Created, used, discarded |
| **Examples** | User, Assessment, Team | Email, Password, Money |

### Examples:

```python
# ENTITY: Two users with same data are different
user1 = User(id=uuid1, email=Email("test@example.com"), ...)
user2 = User(id=uuid2, email=Email("test@example.com"), ...)

user1 == user2  # False (different IDs)

# VALUE OBJECT: Two emails with same value are equal
email1 = Email("test@example.com")
email2 = Email("test@example.com")

email1 == email2  # True (same value)
```

---

## 💡 Why Value Objects Matter

### Problem 1: Invalid Data Everywhere

```python
# ❌ Without value objects
def create_user(email: str, password: str):
    # Validation scattered everywhere
    if "@" not in email:
        raise ValueError("Invalid email")

    if len(password) < 12:
        raise ValueError("Password too short")

    # ... more validation

    user = User(email=email, password=password)
    # Did we forget to hash? 😱
```

### Solution 1: Validation in One Place

```python
# ✅ With value objects
def create_user(email: Email, password: Password):
    # Already validated!
    # Already hashed!

    user = User(
        email=email,  # Email is valid
        password=password  # Password is hashed
    )
    # Can't forget - enforced by type system
```

### Problem 2: Business Rules Scattered

```python
# ❌ Business rules everywhere
if user.is_active and user.is_verified and not user.locked:
    # Can login
    pass

# Repeated in 10 different files!
```

### Solution 2: Encapsulated in Entity

```python
# ✅ Business rule in one place
if user.can_login():  # Method handles all logic
    # Can login
    pass

# Defined once in User entity
# Reusable everywhere
```

---

## 🎨 Real-World Example: User Registration Flow

### WITHOUT Domain Layer (Current):

```python
# Endpoint
@router.post("/register")
async def register(data: UserCreate, db: AsyncSession):
    # ❌ Validation here
    if "@" not in data.email:
        raise HTTPException(400, "Invalid email")

    # ❌ Check duplicate here
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email exists")

    # ❌ Hashing here
    hashed = hash_password(data.password)

    # ❌ Creation here
    user = User(email=data.email, password_hash=hashed)
    db.add(user)
    await db.commit()

    return user
```

### WITH Domain Layer (New):

```python
# 1. Value objects validate
email = Email(data.email)  # Crashes if invalid
password = Password.create(data.password)  # Validates + hashes

# 2. Entity contains business rules
user = User.create(email=email, password=password)
# Business logic in create() method

# 3. Repository handles data access
user_model = await repository.create(user)

# 4. Endpoint is thin
return {"id": user.id}
```

**What Changed:**
- ✅ Validation in value objects (one place)
- ✅ Business logic in entity (one place)
- ✅ Data access in repository (one place)
- ✅ Endpoint only handles HTTP (one responsibility)

---

## 📊 Summary: Domain Layer Benefits

| Benefit | How It Helps |
|---------|--------------|
| **Validation** | Value objects enforce rules on creation |
| **Business Logic** | Entities encapsulate behavior |
| **Testability** | No frameworks needed for testing |
| **Reusability** | Entities work anywhere (CLI, API, tests) |
| **Type Safety** | Compiler catches type errors |
| **Clarity** | Business language, not technical terms |

---

## 🎓 Key Takeaways

1. **Domain Entities**: Business objects with behavior
   - Have identity (ID)
   - Contain business rules
   - Independent of frameworks

2. **Value Objects**: Validated, immutable types
   - No identity (value matters)
   - Self-validating
   - Can't be in invalid state

3. **Separation**: Domain ≠ Database
   - Domain = Business concepts
   - Database = Technical storage
   - They're different things!

4. **Benefits**: Centralized, clear, testable
   - Logic in one place
   - Business language
   - Easy to test

---

**Ready for Stop 4: AI Engine Separation?**
