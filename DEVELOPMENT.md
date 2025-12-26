# 🚀 **Development & Contributing Guide**

<div align="center">

![PsychSync Development](https://img.shields.io/badge/Development-Guide-blue?style=for-the-badge&logo=github)
![License](https://img.shields.io/badge/license-MIT-purple?style=for-the-badge)
![Version](https://img.shields.io/badge/version-2.0.0-green?style=for-the-badge)
![Contributors](https://img.shields.io/badge/contributors-welcome-orange?style=for-the-badge)

**Comprehensive guide for developers and contributors**

[🛠️ Setup](#️-development-setup) • [🔧 Architecture](#-architecture-overview) • [🧪 Testing](#-testing-strategy) • [📝 Contributing](#-contributing-guidelines)

</div>

---

## **🎯 Overview**

Welcome to the PsychSync AI development guide! This comprehensive resource will help you get started with development, understand the codebase architecture, and contribute effectively to our psychological assessment platform.

### **🌟 What We're Building**
PsychSync AI is an enterprise-grade SaaS platform that combines cutting-edge AI with evidence-based psychological frameworks to deliver comprehensive personality, team, and organizational insights.

### **💡 Why Contribute?**
- **Impact**: Help teams and organizations understand themselves better
- **Technology**: Work with modern tech stack (FastAPI, React, PostgreSQL, Redis)
- **Performance**: Contribute to 1000% optimized performance systems
- **Open Source**: Be part of a transparent, community-driven project

---

## **🛠️ Development Setup**

### **Prerequisites**

#### **Required Software**
- **Python 3.9+** (recommend 3.11)
- **Node.js 16+** (recommend 18+)
- **PostgreSQL 15+**
- **Redis 6+**
- **Git**
- **Docker & Docker Compose** (optional but recommended)

#### **Development Tools**
```bash
# Python development tools
pip install black isort flake8 pytest pytest-cov pre-commit

# Node.js development tools
npm install -g typescript @typescript-eslint/cli prettier

# Database tools
brew install postgresql redis  # macOS
# or
sudo apt-get install postgresql redis-server  # Ubuntu
```

### **Quick Start Setup**

#### **Option 1: Docker (Recommended)**
```bash
# Clone the repository
git clone https://github.com/psychsync/psychsync.git
cd psychsync

# Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

#### **Option 2: Manual Setup**
```bash
# Clone the repository
git clone https://github.com/psychsync/psychsync.git
cd psychsync

# Backend Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database Setup
createdb psychsync
alembic upgrade head

# Frontend Setup
cd frontend
npm install
cd ..

# Start Services
# Backend (Terminal 1)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (Terminal 2)
cd frontend && npm run dev
```

### **Environment Configuration**

Create `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/psychsync
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Performance
RATE_LIMIT_PER_MINUTE=1000
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_REQUESTS=100

# External Services
SENTRY_DSN=your-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true
```

Frontend environment (frontend/.env):

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_ADVANCED_REPORTS=true
```

---

## **🏗️ Architecture Overview**

### **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │   FastAPI       │    │   PostgreSQL    │
│   (Port 5173)   │◄──►│   (Port 8000)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Port 6379)   │
                       └─────────────────┘
```

### **Backend Architecture**

#### **Layer Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   API Routes    │  │  Middleware     │                  │
│  │   (endpoints)   │  │  (auth, rate)   │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Business Logic │  │   External APIs │                  │
│  │   (services)    │  │   (AI, email)   │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  SQLAlchemy     │  │     Redis       │                  │
│  │    (models)     │  │    (cache)      │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

#### **Key Design Patterns**
- **Repository Pattern**: CRUD classes encapsulate database operations
- **Service Layer Pattern**: Business logic separated from API routes
- **Factory Pattern**: Assessment processors for different frameworks
- **Observer Pattern**: Event-driven notifications and webhooks
- **Strategy Pattern**: Different authentication and validation strategies

### **Frontend Architecture**

#### **Component Structure**
```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI elements
│   ├── forms/          # Form components
│   └── layout/         # Layout components
├── pages/              # Page components
├── contexts/           # React contexts (state management)
├── services/           # API service layer
├── hooks/              # Custom React hooks
├── utils/              # Utility functions
└── types/              # TypeScript definitions
```

#### **State Management**
- **React Context**: Global state (auth, user, notifications)
- **React Query**: Server state management and caching
- **Local State**: Component-specific state with useState/useReducer

---

## **📁 Project Structure**

### **Backend Directory Structure**
```
app/
├── api/v1/             # API routes and endpoints
│   ├── endpoints/      # API endpoint modules
│   └── deps.py         # Dependency injection
├── core/               # Core application logic
│   ├── config.py       # Configuration management
│   ├── database.py     # Database setup
│   ├── security.py     # Authentication & security
│   └── tasks.py        # Background tasks
├── db/                 # Database layer
│   ├── models/         # SQLAlchemy models
│   └── crud/           # CRUD operations
├── schemas/            # Pydantic schemas
├── services/           # Business logic services
├── ai/                 # AI processing engine
│   └── processors/     # Assessment processors
└── main.py             # FastAPI application entry
```

### **Frontend Directory Structure**
```
frontend/src/
├── components/         # React components
│   ├── ui/            # Base UI components
│   ├── forms/         # Form components
│   └── layout/        # Layout components
├── pages/             # Page components
├── contexts/          # React contexts
├── services/          # API services
├── hooks/             # Custom hooks
├── utils/             # Utility functions
├── types/             # TypeScript types
├── styles/            # Global styles
└── App.tsx            # Main app component
```

---

## **🧪 Testing Strategy**

### **Testing Philosophy**
- **Pyramid Structure**: More unit tests, fewer integration tests
- **95%+ Coverage**: Aim for high test coverage
- **Behavior-Driven**: Tests should describe behavior, not implementation
- **Fast Feedback**: Tests should run quickly

### **Backend Testing**

#### **Unit Tests**
```bash
# Run unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_user_service.py -v
```

#### **Integration Tests**
```bash
# Run integration tests
pytest tests/integration -v

# Test API endpoints
pytest tests/integration/test_api_endpoints.py -v
```

#### **Example Test Structure**
```python
# tests/unit/test_user_service.py
import pytest
from app.services.user_service import UserService
from app.db.crud.user import UserCRUD

@pytest.mark.unit
class TestUserService:
    def test_create_user_success(self, db_session):
        user_crud = UserCRUD(db_session)
        user_service = UserService(user_crud)

        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "SecurePass123"
        }

        result = user_service.create_user(user_data)

        assert result.email == user_data["email"]
        assert result.full_name == user_data["full_name"]
        assert result.is_active is True
```

#### **Fixtures Setup**
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.db.base_class import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### **Frontend Testing**

#### **Component Tests**
```bash
# Run component tests
cd frontend && npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

#### **Example Component Test**
```typescript
// frontend/src/components/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../Button';

describe('Button Component', () => {
  test('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  test('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

#### **Service Tests**
```typescript
// frontend/src/services/__tests__/authService.test.ts
import { authService } from '../authService';

describe('Auth Service', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('stores token after login', async () => {
    const mockResponse = { access_token: 'test-token' };
    jest.spyOn(global, 'fetch').mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    } as Response);

    await authService.login('test@example.com', 'password');

    expect(localStorage.getItem('access_token')).toBe('test-token');
  });
});
```

---

## **🔄 Development Workflow**

### **Git Workflow**
We use a simplified GitHub Flow:

```
main (production) ←── develop (staging) ←── feature branches
```

#### **Branch Naming Conventions**
- `feature/user-authentication`
- `fix/validation-bug`
- `docs/api-documentation`
- `refactor/database-optimization`

#### **Commit Message Format**
```
type(scope): brief description

Detailed explanation (optional)

Closes #issue-number
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no functional changes)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add JWT refresh token functionality

Implement automatic token refresh to improve user experience
and reduce login frequency. Tokens now refresh when 80% expired.

Closes #123
```

### **Pre-commit Hooks**
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### **Pre-commit Configuration**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

### **Code Quality Standards**

#### **Python Code Style**
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

#### **TypeScript/JavaScript Code Style**
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check
```

---

## **📝 Contributing Guidelines**

### **How to Contribute**

#### **1. Find an Issue**
- Browse [GitHub Issues](https://github.com/psychsync/psychsync/issues)
- Look for `good first issue` or `help wanted` labels
- Comment on the issue to claim it

#### **2. Set Up Development**
```bash
# Fork the repository
git clone https://github.com/YOUR_USERNAME/psychsync.git
cd psychsync

# Add upstream remote
git remote add upstream https://github.com/psychsync/psychsync.git

# Create feature branch
git checkout -b feature/your-feature-name
```

#### **3. Make Changes**
- Follow the coding standards
- Add tests for new functionality
- Update documentation
- Ensure all tests pass

#### **4. Submit Pull Request**
```bash
# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### **Pull Request Guidelines**

#### **PR Template**
```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of the code completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Additional Notes
Any additional context or notes about the changes.
```

#### **Review Process**
1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: At least one maintainer must review the PR
3. **Testing**: PR must pass all tests
4. **Merge**: Maintainer merges after approval

### **Development Guidelines**

#### **Code Standards**

**Python:**
```python
# Use type hints
def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user with validation."""

    # Validate input
    if not user_data.email:
        raise ValueError("Email is required")

    # Create user
    user = user_service.create_user(user_data)
    return user

# Use async/await for I/O operations
async def get_user_assessments(user_id: str) -> List[Assessment]:
    """Get all assessments for a user."""
    return await assessment_service.get_user_assessments(user_id)
```

**TypeScript:**
```typescript
// Use interfaces for type definitions
interface User {
  id: string;
  email: string;
  fullName: string;
}

// Use functional components with hooks
const UserProfile: React.FC<{ userId: string }> = ({ userId }) => {
  const { data: user, isLoading } = useQuery(
    ['user', userId],
    () => userService.getUser(userId)
  );

  if (isLoading) return <div>Loading...</div>;
  return <div>{user?.fullName}</div>;
};
```

#### **Database Guidelines**
- Use Alembic for migrations
- All models must have `id`, `created_at`, `updated_at`
- Use foreign key relationships
- Add indexes for frequently queried fields

```python
# Example model
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### **API Guidelines**
- Use Pydantic for request/response models
- Include proper error handling
- Add rate limiting to public endpoints
- Document all endpoints with examples

```python
# Example endpoint
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user."""
    try:
        user = await user_service.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## **🐛 Debugging Guide**

### **Common Issues**

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
pg_ctl status

# Check connection
psql -U postgres -h localhost -d psychsync

# Reset database
dropdb psychsync && createdb psychsync
alembic upgrade head
```

#### **Redis Connection Issues**
```bash
# Check Redis status
redis-cli ping

# Clear Redis cache
redis-cli flushall

# Monitor Redis
redis-cli monitor
```

#### **Frontend Build Issues**
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install

# Clear build cache
npm run build -- --clean
```

### **Debugging Tools**

#### **Backend Debugging**
```bash
# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app --reload

# Use Python debugger
import pdb; pdb.set_trace()

# Log debugging
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")
```

#### **Frontend Debugging**
```bash
# Run with debugger
npm run dev -- --inspect

# Use browser devtools
# - React DevTools extension
# - Redux DevTools extension
# - Network tab for API calls
```

---

## **🚀 Performance Optimization**

### **Backend Performance**

#### **Database Optimization**
- Use connection pooling
- Add appropriate indexes
- Use query optimization
- Implement caching strategies

```python
# Example: Database optimization
from sqlalchemy import Index

# Add composite index
Index('idx_user_email_active', User.email, User.is_active)

# Use eager loading for relationships
from sqlalchemy.orm import joinedload

query = select(User).options(joinedload(User.organization))
```

#### **API Performance**
- Implement response caching
- Use pagination for large datasets
- Optimize serialization
- Use background tasks for heavy operations

### **Frontend Performance**

#### **React Optimization**
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Use code splitting
- Optimize bundle size

```typescript
// Example: React optimization
import React, { memo, useMemo } from 'react';

const ExpensiveComponent = memo(({ data }: { data: any[] }) => {
  const processedData = useMemo(() => {
    return data.map(item => expensiveTransform(item));
  }, [data]);

  return <div>{/* component content */}</div>;
});
```

---

## **📚 Documentation Standards**

### **Code Documentation**
- Use docstrings for all functions and classes
- Include type hints
- Add example usage
- Document edge cases

```python
def calculate_assessment_score(
    responses: List[Response],
    framework: AssessmentFramework,
    weights: Optional[Dict[str, float]] = None
) -> AssessmentScore:
    """
    Calculate assessment score based on user responses.

    Args:
        responses: List of user responses to questions
        framework: Assessment framework to use for scoring
        weights: Optional weights for different question categories

    Returns:
        AssessmentScore with calculated scores and insights

    Raises:
        ValueError: If responses are incomplete or invalid

    Example:
        >>> responses = [Response(question_id="q1", value=4)]
        >>> score = calculate_assessment_score(responses, Framework.BIG_FIVE)
        >>> print(score.openness)
        4.2
    """
```

### **API Documentation**
- Use OpenAPI/Swagger for API docs
- Include request/response examples
- Document all parameters
- Add error response examples

### **README Updates**
- Update installation instructions
- Add new feature documentation
- Include breaking changes
- Update configuration examples

---

## **🤝 Community Guidelines**

### **Code of Conduct**
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Maintain professional communication

### **Getting Help**
- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For general questions and ideas
- **Discord**: For real-time chat and community support
- **Documentation**: Check existing docs first

### **Recognition**
- Contributors are recognized in release notes
- Top contributors are highlighted in the README
- Special badges for significant contributions
- Annual contributor appreciation awards

---

## **📋 Development Checklist**

### **Before Submitting Code**
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Performance impact is considered
- [ ] Security implications are reviewed
- [ ] Breaking changes are documented

### **Before Merging**
- [ ] Code review is completed
- [ ] CI/CD pipeline passes
- [ ] Tests have sufficient coverage
- [ ] Breaking changes are approved
- [ ] Migration scripts are tested
- [ ] Rollback plan is documented

---

## **🔗 Additional Resources**

### **Development Tools**
- **PyCharm**: Python IDE with great Django/FastAPI support
- **VS Code**: Lightweight editor with excellent extensions
- **Postman**: API testing and documentation
- **DBeaver**: Database management tool
- **GitKraken**: Git GUI client

### **Learning Resources**
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://reactjs.org/docs)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com)
- [Redis Documentation](https://redis.io/documentation)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)

### **Best Practices**
- [Python Code Style Guide](https://pep8.org)
- [TypeScript Style Guide](https://typescript-eslint.io/rules)
- [API Design Guide](https://restfulapi.net)
- [Database Design Best Practices](https://www.vertabelo.com/blog/database-design-best-practices)

---

## **🎉 Ready to Contribute?**

We're excited to have you contribute to PsychSync AI! Every contribution, whether it's a bug fix, new feature, documentation improvement, or bug report, helps make this project better.

### **First Steps**
1. ⭐ Star the repository
2. 🔀 Fork and clone the repository
3. 📖 Read through this guide
4. 🐛 Find an issue to work on
5. 💬 Introduce yourself in our Discord

### **Need Help?**
- Create a discussion on GitHub
- Join our Discord server
- Email us at contributors@psychsync.ai

---

**🚀 Happy coding! Let's build something amazing together!**

*Generated with ❤️ for the developer community*

---

*Version: 2.0.0 | Last Updated: January 21, 2025*