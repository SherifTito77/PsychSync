# PsychSync Database Layer

## Overview

The database layer manages all data persistence, relationships, and transactions. It uses SQLAlchemy ORM with PostgreSQL for structured data storage.

## Architecture

```
app/db/
├── models/              # SQLAlchemy ORM models
│   ├── __init__.py     # Model exports
│   ├── user.py         # User model
│   ├── assessment.py   # Assessment models
│   ├── team.py         # Team & organization models
│   └── ...
├── database.py         # Database connection setup
├── base.py             # Base model with common fields
└── crud/               # CRUD operations (optional)
    └── ...
```

## Database Configuration

**Connection**: PostgreSQL (configured in `app/core/config.py`)
**ORM**: SQLAlchemy 2.0 with async support
**Migrations**: Alembic

### Connection Setup

```python
from app.core.database import get_db

def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

## Core Models

### Base Model (`base.py`)

All models inherit from `Base` with common fields:
- `id`: Primary key (UUID or integer)
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update
- `is_deleted`: Soft delete flag

### Key Models

#### User (`models/user.py`)
```python
class User(Base):
    __tablename__ = "users"

    id: Column(Integer, primary_key=True)
    email: Column(String, unique=True, nullable=False)
    hashed_password: Column(String, nullable=False)
    full_name: Column(String)
    is_active: Column(Boolean, default=True)
    is_superuser: Column(Boolean, default=False)
    organization_id: Column(Integer, ForeignKey("organizations.id"))
```

#### Assessment (`models/assessment.py`)
```python
class Assessment(Base):
    __tablename__ = "assessments"

    id: Column(Integer, primary_key=True)
    title: Column(String, nullable=False)
    description: Column(Text)
    assessment_type: Column(String)  # MBTI, Big Five, etc.
    organization_id: Column(Integer, ForeignKey("organizations.id"))
    created_by: Column(Integer, ForeignKey("users.id"))
    questions: relationship("Question")
```

#### Organization (`models/team.py`)
```python
class Organization(Base):
    __tablename__ = "organizations"

    id: Column(Integer, primary_key=True)
    name: Column(String, nullable=False)
    plan_type: Column(String)  # free, tiered, enterprise
    created_at: Column(DateTime, default=datetime.utcnow)
    teams: relationship("Team")
    users: relationship("User")
```

## CRUD Operations

### Creating Records

```python
from app.db.models import User
from sqlalchemy.orm import Session

def create_user(email: str, password: str, db: Session):
    user = User(
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### Reading Records

```python
# Get by ID
user = db.query(User).filter(User.id == user_id).first()

# Get all with filtering
active_users = db.query(User).filter(
    User.is_active == True
).all()

# Join with relationships
user_with_org = db.query(User).join(Organization).filter(
    Organization.name == "Acme Corp"
).all()
```

### Updating Records

```python
user = db.query(User).filter(User.id == user_id).first()
user.full_name = "New Name"
db.commit()
```

### Deleting Records

**Soft Delete** (recommended):
```python
user.is_deleted = True
db.commit()
```

**Hard Delete** (use carefully):
```python
db.delete(user)
db.commit()
```

## Relationships

### One-to-Many
```python
class Organization(Base):
    teams = relationship("Team", back_populates="organization")

class Team(Base):
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization", back_populates="teams")
```

### Many-to-Many
```python
# Association table
team_members = Table(
    'team_members',
    Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class Team(Base):
    members = relationship("User", secondary=team_members)
```

## Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply Migration
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

## Query Optimization

### Indexing
```python
class User(Base):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True)  # Indexed
    created_at = Column(DateTime, index=True)  # Indexed for sorting
```

### Eager Loading
```python
from sqlalchemy.orm import selectinload, joinedload

# Load relationships efficiently
assessments = db.query(Assessment).options(
    selectinload(Assessment.questions),
    joinedload(Assessment.created_by)
).all()
```

### Pagination
```python
def get_assessments(skip: int = 0, limit: int = 100):
    return db.query(Assessment).offset(skip).limit(limit).all()
```

## Transactions

### Transaction Management
```python
from sqlalchemy.exc import IntegrityError

try:
    # Multiple operations
    user = User(email="test@example.com")
    db.add(user)

    team = Team(name="Test Team")
    db.add(team)

    db.commit()  # Commit all changes
except IntegrityError:
    db.rollback()  # Rollback on error
    raise
```

## Common Patterns

### Pagination with Filtering
```python
def get_items(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
):
    query = db.query(Item)

    if active_only:
        query = query.filter(Item.is_active == True)

    return query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()
```

### Soft Delete Query
```python
def get_active_users(db: Session):
    return db.query(User).filter(
        User.is_deleted == False,
        User.is_active == True
    ).all()
```

## Related Documentation

- [Services Layer](../services/README.md) - Business logic using models
- [API Layer](../api/README.md) - Endpoints that query models
- [Core Config](../core/README.md) - Database connection settings
