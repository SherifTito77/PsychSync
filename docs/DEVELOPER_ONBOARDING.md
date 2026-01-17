# Developer Onboarding Guide
## PsychSync Platform Architecture

**Welcome to the PsychSync Team!** 🎉

This guide will help you understand our transformed platform architecture and get you productive quickly.

---

## 📋 Table of Contents

1. [Platform Overview](#platform-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Development Environment Setup](#development-environment-setup)
4. [Key Development Patterns](#key-development-patterns)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Quality Standards](#code-quality-standards)
7. [Deployment Process](#deployment-process)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Resources & References](#resources--references)

---

## 🚀 Platform Overview

### What is PsychSync?
PsychSync is a **psychological assessment SaaS platform** that helps organizations understand and optimize their team dynamics through scientifically-backed assessments.

### Our Technical Transformation
We recently completed a comprehensive **technical debt elimination project** that transformed our platform from moderate-to-high technical debt (7.2/10) to enterprise-grade quality (2.1/10 technical debt score).

### Key Technical Achievements
- **71% reduction** in technical debt
- **Clean Architecture** implementation
- **Enterprise-grade security** with comprehensive hardening
- **100% automated deployment** pipeline
- **85%+ test coverage** with quality gates
- **Multi-layered monitoring** and alerting

---

## 🏗️ Architecture Deep Dive

### Clean Architecture Principles

Our platform follows **Clean Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   FastAPI       │  │   React SPA     │  │   GraphQL    │ │
│  │   API Endpoints │  │   Frontend      │  │   Gateway    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Use Cases     │  │   Services      │  │   DTOs       │ │
│  │   (Business     │  │   (Application  │  │   (Data      │ │
│  │    Logic)       │  │    Logic)       │  │    Transfer) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Entities      │  │   Value Objects │  │   Repository │ │
│  │   (Core Models) │  │   (Rich Types)  │  │   Interfaces │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│               INFRASTRUCTURE LAYER                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Repositories  │  │   External APIs │  │   Database   │ │
│  │   (Data Access) │  │   (Integrations)│  │   (PostgreSQL)│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Patterns

#### 1. Repository Pattern
```python
# Domain Layer - Interface
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass

# Infrastructure Layer - Implementation
class SQLAlchemyUserRepository(UserRepository):
    async def create(self, user: User) -> User:
        # SQLAlchemy implementation
        pass
```

#### 2. Dependency Injection
```python
# app/dependency_injection/container.py
container = DIContainer()

# Register services
container.register(IUserService, UserService, lifetime=Lifetime.scoped)
container.register(IUserRepository, SQLAlchemyUserRepository, lifetime=Lifetime.scoped)
```

#### 3. Service Layer Pattern
```python
# Application Layer
class UserService:
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def create_user(self, user_dto: CreateUserDTO) -> UserDTO:
        # Business logic here
        user = User.create(user_dto.email, user_dto.full_name)
        created_user = await self._user_repository.create(user)
        return UserDTO.from_entity(created_user)
```

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0
- **Cache**: Redis 7
- **Authentication**: JWT with refresh tokens
- **Validation**: Pydantic v2
- **Testing**: pytest with async support

#### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: React Context + Custom Hooks
- **UI Components**: Tailwind CSS + Headless UI
- **Testing**: Vitest + React Testing Library

#### DevOps & Infrastructure
- **Containerization**: Docker with multi-platform builds
- **CI/CD**: GitHub Actions (6 specialized workflows)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured JSON logging
- **Security**: Multiple security scanners and tools

---

## 💻 Development Environment Setup

### Prerequisites
- **Docker** and **Docker Compose**
- **Python 3.12+**
- **Node.js 18+**
- **Git**
- **VS Code** (recommended)

### Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/your-org/psychsync.git
cd psychsync

# 2. Start development environment
docker-compose up --build

# 3. Run database migrations
docker-compose exec db alembic upgrade head

# 4. Load test data (optional)
docker-compose exec app python scripts/generate_test_data.py

# 5. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development Setup

#### Backend Development
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.dev .env.local
# Edit .env.local with your settings

# 4. Run database migrations
alembic upgrade head

# 5. Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Development
```bash
# 1. Navigate to frontend directory
cd frontend/

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

#### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Check migration status
alembic current
alembic history
```

### IDE Configuration

#### VS Code Extensions (Recommended)
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "redhat.vscode-yaml",
    "ms-kubernetes-tools.vscode-kubernetes-tools"
  ]
}
```

#### VS Code Settings (`.vscode/settings.json`)
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 🔧 Key Development Patterns

### 1. Creating New API Endpoints

#### Step 1: Define DTOs (Application Layer)
```python
# app/schemas/user_dto.py
from pydantic import BaseModel, EmailStr

class CreateUserDTO(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "user"

class UserDTO(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> "UserDTO":
        return cls(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            role=user.role,
            created_at=user.created_at
        )
```

#### Step 2: Implement Use Case (Application Layer)
```python
# app/application/use_cases/user_management.py
class CreateUserUseCase:
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def execute(self, dto: CreateUserDTO) -> UserDTO:
        # Validate business rules
        existing_user = await self._user_repository.get_by_email(dto.email)
        if existing_user:
            raise ValueError("User already exists")

        # Create user entity
        user = User.create(dto.email, dto.full_name, dto.role)

        # Save to database
        created_user = await self._user_repository.create(user)

        return UserDTO.from_entity(created_user)
```

#### Step 3: Create API Endpoint (Presentation Layer)
```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependency_injection.container import get_container

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserDTO)
async def create_user(
    user_dto: CreateUserDTO,
    container: DIContainer = Depends(get_container)
):
    try:
        use_case = container.resolve(CreateUserUseCase)
        return await use_case.execute(user_dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. Database Repository Implementation

```python
# app/infrastructure/repositories/user_repository.py
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user: User) -> User:
        db_user = UserModel(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            role=user.role
        )

        self._session.add(db_user)
        await self._session.commit()
        await self._session.refresh(db_user)

        return self._to_domain_entity(db_user)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            return None

        return self._to_domain_entity(db_user)

    def _to_domain_entity(self, db_user: UserModel) -> User:
        return User(
            id=db_user.id,
            email=EmailAddress(db_user.email),
            full_name=db_user.full_name,
            role=db_user.role,
            created_at=db_user.created_at
        )
```

### 3. Error Handling Pattern

```python
# app/core/exceptions.py
class PsychSyncException(Exception):
    """Base exception for the application"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class UserNotFoundError(PsychSyncException):
    def __init__(self, user_id: str):
        super().__init__(f"User not found: {user_id}", "USER_NOT_FOUND")

class ValidationError(PsychSyncException):
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation error on {field}: {message}", "VALIDATION_ERROR")

# app/core/exception_handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def psychsync_exception_handler(request: Request, exc: PsychSyncException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code or "APPLICATION_ERROR",
            "message": exc.message
        }
    )
```

---

## 🧪 Testing Guidelines

### Testing Pyramid

```
        ▲
       / \
      / E2E \     ← Few tests, high confidence, slow
     /______\
    /        \
   /Integration\ ← Many tests, good confidence, medium speed
  /__________\
 /            \
/  Unit Tests   \ ← Most tests, fastest, specific
/______________\
```

### Unit Tests

```python
# tests/unit/application/test_create_user_use_case.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.application.use_cases.user_management import CreateUserUseCase
from app.domain.entities.user import User
from app.core.exceptions import UserAlreadyExistsError

@pytest.mark.asyncio
async def test_create_user_success():
    # Arrange
    mock_repo = Mock()
    mock_repo.get_by_email = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock()

    use_case = CreateUserUseCase(mock_repo)
    user_dto = CreateUserDTO(email="test@example.com", full_name="Test User")

    # Act
    result = await use_case.execute(user_dto)

    # Assert
    assert result.email == "test@example.com"
    assert result.full_name == "Test User"
    mock_repo.get_by_email.assert_called_once_with("test@example.com")
    mock_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_already_exists():
    # Arrange
    mock_repo = Mock()
    mock_repo.get_by_email = AsyncMock(return_value=User("existing-id", "test@example.com", "Existing"))

    use_case = CreateUserUseCase(mock_repo)
    user_dto = CreateUserDTO(email="test@example.com", full_name="Test User")

    # Act & Assert
    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(user_dto)
```

### Integration Tests

```python
# tests/integration/test_user_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/application/test_create_user_use_case.py -v
```

### Test Data Management

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import get_db
from app.db.models.base import Base

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/psychsync_test"
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    async with AsyncSession(test_engine) as session:
        yield session

@pytest.fixture
def mock_db(test_session):
    def override_get_db():
        return test_session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
```

---

## 📏 Code Quality Standards

### 1. Code Formatting

We use automated code formatting:

#### Python
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

#### JavaScript/TypeScript
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### 2. Code Review Checklist

#### Functionality
- [ ] Code works as expected
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Logging is included where needed

#### Architecture
- [ ] Follows clean architecture principles
- [ ] Dependencies are properly injected
- [ ] Single responsibility principle followed
- [ ] No code duplication

#### Security
- [ ] Input validation is implemented
- [ ] SQL injection protection is in place
- [ ] Authentication/authorization is correct
- [ ] No sensitive data in logs

#### Performance
- [ ] Database queries are optimized
- [ ] No N+1 query problems
- [ ] Appropriate caching is used
- [ ] Memory usage is reasonable

#### Testing
- [ ] Tests cover main functionality
- [ ] Tests are well-structured
- [ ] Test data is properly isolated
- [ ] Edge cases are tested

### 3. Git Workflow

#### Branch Naming
```bash
feature/user-authentication
bugfix/login-validation
hotfix/security-vulnerability
refactor/database-layer
```

#### Commit Messages
```bash
# Good commit message
feat(auth): implement JWT token refresh mechanism

- Add refresh token endpoint
- Implement automatic token rotation
- Add token blacklist on logout
- Update authentication middleware

Closes #123
```

#### Pull Request Template
```markdown
## Description
Brief description of changes made

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Security
- [ ] Code reviewed for security issues
- [ ] Input validation implemented
- [ ] Authentication/authorization verified

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests passing locally
```

---

## 🚀 Deployment Process

### Development Workflow

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Develop and Test**
```bash
# Make changes
npm run test  # Run tests
npm run lint  # Check code quality
```

3. **Create Pull Request**
- Target `develop` branch for features
- Target `main` branch for hotfixes
- Include description and testing details

4. **Automated Checks**
- Code quality checks
- Security scanning
- Automated tests
- Performance validation

5. **Merge and Deploy**
- Automatic deployment to staging on merge to `develop`
- Manual deployment to production from `main`

### Production Deployment

#### Automated Deployment
```bash
# Trigger production deployment via GitHub Actions
# Or use the deploy script
./scripts/deploy-production.sh
```

#### Manual Deployment Steps
1. **Health Check**
```bash
curl -f https://app.psychsync.com/health
```

2. **Database Migration**
```bash
# Run migrations if needed
alembic upgrade head
```

3. **Rollback if Needed**
```bash
# Rollback to previous version
./scripts/rollback-production.sh
```

### Monitoring During Deployment

1. **Check Application Health**
```bash
# Monitor Grafana dashboard
# https://grafana.psychsync.com/d/psychsync-overview
```

2. **Check Error Rates**
```bash
# Monitor error rate in production
# Alert if > 5% for more than 2 minutes
```

3. **Check Performance**
```bash
# Monitor response times
# Alert if P95 > 2 seconds for more than 5 minutes
```

---

## 🔧 Troubleshooting Guide

### Common Development Issues

#### 1. Database Connection Issues
```bash
# Check database connection
docker-compose exec db psql -U postgres -d psychsync

# Check connection string in .env.local
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/psychsync
```

#### 2. Migration Issues
```bash
# Check current migration status
alembic current

# Reset database (development only)
alembic downgrade base
alembic upgrade head
```

#### 3. Dependency Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Docker cache
docker system prune -a
docker-compose build --no-cache
```

#### 4. Performance Issues
```bash
# Profile memory usage
python scripts/profile_memory_usage.py

# Check database queries
python scripts/database_performance_test.py
```

### Production Troubleshooting

#### 1. Application Down
```bash
# Check application logs
docker-compose logs app

# Check system resources
docker stats

# Restart application
docker-compose restart app
```

#### 2. High Error Rate
```bash
# Check recent errors
docker-compose logs app --tail=100

# Check database connections
docker-compose exec db psql -U postgres -d psychsync -c "SELECT count(*) FROM pg_stat_activity;"

# Check system load
uptime
```

#### 3. Slow Performance
```bash
# Check database queries
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;"

# Check application metrics
curl http://localhost:8000/metrics
```

### Emergency Contacts

| Issue Type | Contact | Escalation |
|------------|---------|------------|
| Application Down | Platform Team | @platform-team |
| Security Incident | Security Team | @security-team |
| Database Issues | Platform Team | @platform-team |
| Performance Issues | Platform Team | @platform-team |

---

## 📚 Resources & References

### Documentation
- [Production Deployment Guide](../PRODUCTION_DEPLOYMENT_GUIDE.md)
- [API Documentation](../docs/API.md)
- [Architecture Overview](../docs/ARCHITECTURE.md)
- [Security Guidelines](../docs/SECURITY.md)

### Internal Tools
- **Grafana Dashboard**: https://grafana.psychsync.com
- **Kibana Logs**: https://kibana.psychsync.com
- **JIRA Project**: https://psychsync.atlassian.net
- **Slack Channel**: #development

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Clean Architecture Book](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [React Documentation](https://react.dev/)

### Training Materials
- [Clean Architecture Training](../training/clean-architecture.md)
- [Security Best Practices](../training/security.md)
- [Performance Optimization](../training/performance.md)
- [Testing Strategies](../training/testing.md)

---

## 🤝 Getting Help

### Your First Week Checklist

- [ ] Complete development environment setup
- [ ] Read this onboarding guide thoroughly
- [ ] Join team Slack channels
- [ ] Set up development tools (IDE, extensions)
- [ ] Review codebase structure
- [ ] Set up local development environment
- [ ] Run tests successfully
- [ ] Create your first feature branch
- [ ] Make your first small contribution

### Questions?
- **Technical Questions**: #development Slack channel
- **Architecture Questions**: @architecture-team
- **Security Questions**: @security-team
- **DevOps Questions**: @platform-team

### Mentorship Program
You'll be paired with a senior developer who will:
- Help you navigate the codebase
- Review your first few pull requests
- Answer your questions about our patterns
- Guide you through our deployment process

---

## 🎉 Welcome Again!

We're excited to have you on the team! Our platform transformation has created an amazing foundation for building scalable, secure, and maintainable software. You're joining at a great time to contribute to our mission of helping organizations build better teams through psychological insights.

**Happy Coding!** 🚀

---

*Last Updated: November 25, 2025*
*Next Review: December 25, 2025*
