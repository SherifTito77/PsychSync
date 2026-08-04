# PsychSync Architecture Documentation

**Version:** 2.0.0
**Last Updated:** 2025-01-19
**Architecture Style:** Clean Architecture with Domain-Driven Design

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Architectural Principles](#architectural-principles)
3. [System Layers](#system-layers)
4. [Technology Stack](#technology-stack)
5. [Key Patterns](#key-patterns)
6. [Data Flow](#data-flow)
7. [Deployment Architecture](#deployment-architecture)
8. [Scaling Strategy](#scaling-strategy)

---

## Architecture Overview

PsychSync follows **Clean Architecture** principles with clear separation of concerns and dependency inversion.

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           FastAPI Endpoints (app/api/)                │  │
│  │  - HTTP request/response handling                     │  │
│  │  - Input validation (Pydantic schemas)                │  │
│  │  - Authentication/authorization                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Domain Services (app/domain/services/)        │  │
│  │  - Business logic orchestration                       │  │
│  │  - Use case implementations                           │  │
│  │  - External service integration                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │  Entities   │  │ Value Objects│  │ Exceptions  │  │  │
│  │  │  (User,     │  │ (Email,      │  │ (Validation │  │  │
│  │  │   Assess)   │  │  Password)   │  │  Error)     │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────┘  │  │
│  │                                                           │  │
│  │  Pure business logic - No external dependencies         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │       Repositories (app/infrastructure/repositories/)  │  │
│  │  - Data access implementations                         │  │
│  │  - Database operations (SQLAlchemy)                    │  │
│  │  - External API clients                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     External Systems                         │
│  - PostgreSQL Database                                      │
│  - Redis Cache                                             │
│  - Email Service (SendGrid)                                │
│  - AI Engine (standalone package)                          │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Rule

**Critical Principle:** Dependencies point inward.

```
Presentation → Application → Domain ← Infrastructure
```

- **Domain Layer:** No dependencies on other layers
- **Application Layer:** Depends only on Domain
- **Infrastructure Layer:** Implements Domain interfaces
- **Presentation Layer:** Depends on Application and Domain

---

## Architectural Principles

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility:

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **Presentation** | HTTP handling | Request parsing, response formatting |
| **Application** | Business orchestration | User registration workflow |
| **Domain** | Business rules | Email validation, password hashing |
| **Infrastructure** | Data access | SQL queries, API calls |

### 2. Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions.

```python
# ❌ Bad: Service depends on concrete implementation
class UserService:
    def __init__(self):
        self.db = SQLAlchemyUserDB()  # Concrete dependency

# ✅ Good: Service depends on abstraction
class UserService:
    def __init__(self, repository: UserRepository):  # Abstract interface
        self._repository = repository
```

### 3. Domain Independence

Domain layer is completely isolated from external concerns:

```python
# app/domain/entities/user.py
# ✅ No imports from Flask, FastAPI, SQLAlchemy, etc.
from dataclasses import dataclass
from app.domain.value_objects.email import Email

@dataclass
class User:
    email: Email  # Value object
    password: Password  # Value object

    def verify_email(self) -> None:
        """Pure business logic - no HTTP or DB"""
        self.is_verified = True
```

### 4. Testability

Architecture enables testing at every level:

```python
# Unit test: No database required
def test_user_verify_email():
    user = User.create(email=Email("test@example.com"), ...)
    user.verify_email()
    assert user.is_verified is True

# Integration test: Real database
@pytest.mark.asyncio
async def test_repository_get_by_email(test_db):
    repo = UserRepository(db=test_db)
    user = await repo.get_by_email("test@example.com")
    assert user is not None
```

---

## System Layers

### Presentation Layer (`app/api/`)

**Responsibility:** Handle HTTP concerns only

```python
# app/api/v1/endpoints/users.py
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """HTTP handling only - no business logic"""
    try:
        user = await service.create_user(user_data)
        return UserResponse.from_entity(user)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Key Components:**
- FastAPI routers (`app/api/v1/endpoints/`)
- Pydantic schemas for validation (`app/schemas/`)
- Dependency injection (`app/api/v1/deps.py`)
- Authentication middleware (`app/core/security.py`)

### Application Layer (`app/domain/services/`)

**Responsibility:** Orchestrate business use cases

```python
# app/domain/services/user_service_v2.py
class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def create_user(self, user_data: UserCreate) -> User:
        """Business logic orchestration"""
        # 1. Check uniqueness (business rule)
        existing = await self._repository.get_by_email(user_data.email)
        if existing:
            raise ValidationError("Email already exists")

        # 2. Validate and create domain entity
        email = Email(user_data.email)
        password = Password.create(user_data.password)

        user = User.create(
            email=email,
            password=password,
            full_name=user_data.full_name
        )

        # 3. Persist via repository
        return await self._repository.create(user)
```

**Key Components:**
- Application services (`UserService`, `AssessmentProcessingService`)
- Use case implementations
- External service integration
- Transaction orchestration

### Domain Layer (`app/domain/`)

**Responsibility:** Core business logic

```python
# app/domain/entities/user_entity.py
@dataclass
class User:
    """Pure business object - no infrastructure"""
    email: Email
    password: Password
    is_verified: bool = False

    def verify_email(self) -> None:
        """Business rule: Email verification"""
        self.is_verified = True
        self._touch()

    def can_login(self) -> bool:
        """Business rule: Login eligibility"""
        return self.is_active and self.is_verified
```

**Key Components:**
- Domain entities (`User`, `Assessment`)
- Value objects (`Email`, `Password`)
- Domain exceptions (`ValidationError`)
- Business rules and invariants

### Infrastructure Layer (`app/infrastructure/`)

**Responsibility:** External system integration

```python
# app/infrastructure/repositories/user_repository.py
class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    """Data access implementation"""

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """SQLAlchemy-specific implementation"""
        result = await self._db.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        return result.scalar_one_or_none()
```

**Key Components:**
- Repository implementations (`UserRepository`, `AssessmentRepository`)
- Database models (`app/db/models/`)
- External API clients
- Caching implementations

---

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.104+ | Async web framework |
| **Database** | PostgreSQL 15+ | Relational data store |
| **ORM** | SQLAlchemy 2.0+ | Async database access |
| **Cache** | Redis 7+ | Session and data caching |
| **Auth** | JWT (passlib) | Token-based authentication |
| **Validation** | Pydantic v2 | Schema validation |
| **Testing** | pytest + pytest-asyncio | Test framework |
| **Migrations** | Alembic | Database versioning |

### AI Engine

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Package** | app.ai (standalone) | Assessment processing |
| **Processors** | MBTI, Big Five, Enneagram | Personality frameworks |
| **Interface** | BaseProcessor | Consistent API |

### Frontend (Separate Repository)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18 + TypeScript | UI framework |
| **Build** | Vite | Fast build tool |
| **State** | React Context | Global state |
| **HTTP** | Axios | API client |

---

## Key Patterns

### 1. Repository Pattern

**Purpose:** Abstract data access behind interface

```python
# Abstract interface (implicitly defined by usage)
class UserRepository(BaseRepository):
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email - implementation hidden"""
```

**Benefits:**
- ✓ Swappable data sources (PostgreSQL → MongoDB)
- ✓ Testable (mock repositories)
- ✓ Centralized query logic

### 2. Value Object Pattern

**Purpose:** Encapsulate validation and ensure immutability

```python
@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not self.EMAIL_PATTERN.match(self.value):
            raise ValueError(f"Invalid email: {self.value}")

    @property
    def normalized(self) -> str:
        return self.value.lower()
```

**Benefits:**
- ✓ Validation in constructor
- ✓ Immutable (thread-safe)
- ✓ Self-documenting
- ✓ Reusable across entities

### 3. Factory Method Pattern

**Purpose:** Encapsulate complex object creation

```python
@dataclass
class User:
    @classmethod
    def create(cls, email: Email, password: Password, ...) -> "User":
        """Factory method with validation"""
        if full_name and len(full_name) < 2:
            raise ValidationError("Name too short")

        return cls(
            email=email,
            password=password,
            full_name=full_name.strip() if full_name else None
        )
```

**Benefits:**
- ✓ Validation before creation
- ✓ Default values
- ✓ Clear creation intent

### 4. Dependency Injection

**Purpose:** Inject dependencies, don't create them

```python
# ✅ Good: Inject repository
@router.post("/users")
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)  # Injected
):
    return await service.create_user(user_data)

# ❌ Bad: Create dependency inside
@router.post("/users")
async def create_user(user_data: UserCreate):
    repo = UserRepository(db=get_db())  # Tight coupling
    service = UserService(repository=repo)
    return await service.create_user(user_data)
```

---

## Data Flow

### User Registration Flow

```
1. HTTP Request
   POST /api/v1/auth/register
   {
     "email": "user@example.com",
     "password": "SecureP@ss99!",
     "full_name": "John Doe"
   }
   ↓
2. Presentation Layer
   - Pydantic validates request schema
   - HTTP errors caught and formatted
   ↓
3. Application Layer (UserService)
   - Check if email exists (repository)
   - Create Email value object (validates format)
   - Create Password value object (hashes password)
   - Create User entity (validates business rules)
   - Persist via repository
   ↓
4. Domain Layer
   - Email.value validated
   - Password hashed with bcrypt
   - User entity created with is_verified=False
   ↓
5. Infrastructure Layer (UserRepository)
   - Execute SQL INSERT
   - Return UserModel
   ↓
6. Response
   HTTP 201 Created
   {
     "id": "123e4567-e89b-12d3-a456-426614174000",
     "email": "user@example.com",
     "is_verified": false,
     ...
   }
```

### Assessment Processing Flow

```
1. HTTP Request
   POST /api/v1/assessments/{id}/process
   {
     "responses": [1, 2, 3, 4, ...]
   }
   ↓
2. AssessmentProcessingService
   - Check cache (Redis)
   - Get processor (MBTI, Big Five, etc.)
   - Process responses
   - Cache result
   ↓
3. AI Engine (Standalone Package)
   - MBTIProcessor.process(responses)
   - Calculate dimensions
   - Determine type
   - Return ProcessingResult
   ↓
4. Response
   {
     "type": "INTJ",
     "dimensions": {"EI": {"I": 0.7, "E": 0.3}, ...},
     "confidence": 0.95
   }
```

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────┐
│                 Developer Machine                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  React SPA   │  │   FastAPI    │  │ PostgreSQL   │ │
│  │  (Port 5173) │  │  (Port 8000) │  │  (Port 5432) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                           │
│  ┌──────────────┐                                        │
│  │    Redis     │                                        │
│  │  (Port 6379) │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

### Production Environment

```
                        ┌─────────────┐
                        │   Nginx     │
                        │  (Reverse   │
                        │   Proxy)    │
                        └──────┬──────┘
                               │
            ┌──────────────────┴──────────────────┐
            ↓                                     ↓
     ┌─────────────┐                     ┌─────────────┐
     │   React     │                     │   FastAPI   │
     │   (S3/CDN)  │                     │  (Gunicorn) │
     └─────────────┘                     └──────┬──────┘
                                                │
                    ┌───────────────────────────┼───────────────────┐
                    ↓                           ↓                   ↓
             ┌─────────────┐           ┌─────────────┐    ┌─────────────┐
             │ PostgreSQL  │           │    Redis    │    │   AI Engine │
             │  (RDS/Aurora│           │   (Elasti-  │    │  (Standalone │
             │   Replica)  │           │    Cache)   │    │   Package)  │
             └─────────────┘           └─────────────┘    └─────────────┘
```

### Infrastructure Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Load Balancer** | AWS ALB / Nginx | Route traffic |
| **Web Server** | Nginx | Static files, proxy |
| **API Server** | Gunicorn + Uvicorn | FastAPI workers |
| **Database** | PostgreSQL (RDS) | Primary data store |
| **Cache** | Redis (ElastiCache) | Session, API cache |
| **Storage** | S3 | User uploads, reports |
| **CDN** | CloudFront | Static asset delivery |
| **Monitoring** | CloudWatch | Metrics, logs |

---

## Scaling Strategy

### Horizontal Scaling

**Stateless API Servers:**
```python
# FastAPI workers share no state
# Scale by adding more Gunicorn workers
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

**Database Read Replicas:**
```python
# Write to primary
PRIMARY_DB_URL = "postgresql://primary-db"

# Read from replicas
REPLICA_DB_URLS = [
    "postgresql://replica-1",
    "postgresql://replica-2"
]
```

### Caching Strategy

**Three-Level Cache:**
```
1. Application Cache (Python dict)
   - TTL: 5 minutes
   - User sessions, permissions

2. Redis Cache
   - TTL: 1 hour
   - Assessment results, expensive queries

3. CDN Cache
   - TTL: 24 hours
   - Static assets, API responses
```

### Database Optimization

**Connection Pooling:**
```python
# SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,      # Persistent connections
    max_overflow=40,   # Burst capacity
    pool_pre_ping=True # Health checks
)
```

**Query Optimization:**
```python
# Use selectinload for eager loading
stmt = (
    select(User)
    .options(selectinload(User.assessments))
    .where(User.id == user_id)
)
```

---

## Security Architecture

### Authentication Flow

```
1. User submits credentials
   POST /api/v1/auth/login
   { "email": "...", "password": "..." }

2. Service verifies password
   - User repository fetches user
   - Password value object verifies hash

3. JWT token issued
   - Access token: 30 minutes
   - Refresh token: 7 days

4. Subsequent requests
   Authorization: Bearer <access_token>

5. Token refresh
   POST /api/v1/auth/refresh
   { "refresh_token": "..." }
```

### Authorization

**Role-Based Access Control (RBAC):**
```python
# User roles
USER = "user"           # Basic access
TEAM_LEAD = "team_lead" # Team management
ADMIN = "admin"         # Full access

# Endpoint protection
@router.post("/admin/settings")
async def admin_settings(
    current_user: User = Depends(require_admin)
):
    # Only accessible by ADMIN role
    pass
```

**Permission Checks:**
```python
# Domain-level authorization
class Assessment:
    def can_be_taken_by_user(self, user: User) -> bool:
        """Business rule: Who can take this assessment"""
        return (
            self.status == AssessmentStatus.PUBLISHED and
            user.is_active and
            user.is_verified
        )
```

---

## Monitoring & Observability

### Logging Strategy

**Structured Logging:**
```python
# app/core/structured_logging.py
logger.info(
    "User registered",
    extra={
        "event_type": "user_registered",
        "user_id": str(user.id),
        "email": user.email,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

**Log Levels:**
- **DEBUG:** Detailed diagnostics
- **INFO:** Important events
- **WARNING:** Unexpected but recoverable
- **ERROR:** Errors affecting one request
- **CRITICAL:** System-wide issues

### Metrics

**Key Metrics to Track:**
1. **Request Metrics:** Latency, throughput, error rate
2. **Business Metrics:** Registrations, assessments taken
3. **Database Metrics:** Connection pool, query time
4. **Cache Metrics:** Hit rate, memory usage

### Health Checks

```python
@router.get("/health")
async def health_check():
    """System health endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "app.ai": await check_app.ai()
        }
    }
```

---

## Architecture Decision Records

Key architectural decisions are documented in ADRs:

1. **[ADR-001]** Use Repository Pattern
   - Location: `docs/architecture/adr/001-use-repository-pattern.md`
   - Decision: Abstract data access behind repositories

2. **[ADR-002]** Extract AI Engine
   - Location: `docs/architecture/adr/002-extract-ai-engine.md`
   - Decision: Make AI processing a standalone package

3. **[ADR-003]** Standardize UUIDs
   - Location: `docs/architecture/adr/003-standardize-uuids.md`
   - Decision: Use UUIDs for all entity IDs

---

## Related Documentation

- **Testing Guidelines:** `docs/TESTING_GUIDELINES.md`
- **Deployment Guide:** `docs/DEPLOYMENT.md`
- **Developer Onboarding:** `docs/DEVELOPER_ONBOARDING.md`
- **API Documentation:** `docs/API.md` or `/docs` (Swagger UI)
- **Migration Guide:** `architecture_refactor/plan/04_migration_guide.md`

---

**Generated:** 2025-01-19
**Maintained By:** Architecture Team
**Version:** 2.0.0 (Clean Architecture)
