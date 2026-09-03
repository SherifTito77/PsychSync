# Code Quality Standards

Comprehensive linting and code quality standards for the PsychSync project.

## Table of Contents

- [Overview](#overview)
- [Python Standards](#python-standards)
- [TypeScript/React Standards](#typescriptreact-standards)
- [File Naming Conventions](#file-naming-conventions)
- [Documentation Standards](#documentation-standards)
- [Testing Standards](#testing-standards)
- [Git Workflow](#git-workflow)
- [CI/CD Integration](#cicd-integration)
- [Team Adoption Guide](#team-adoption-guide)

## Overview

This document defines the code quality standards for PsychSync, ensuring consistency across the codebase. These standards are enforced through:

- **Linting tools**: Ruff (Python), ESLint (TypeScript)
- **Formatters**: Ruff format (Python), Prettier (TypeScript)
- **Type checkers**: mypy (Python), TypeScript (TypeScript)
- **Pre-commit hooks**: Automated checks before commits
- **CI/CD**: GitHub Actions workflows

### Goals

1. **Consistency**: Uniform code style across the team
2. **Quality**: Catch bugs and anti-patterns early
3. **Security**: Prevent security vulnerabilities
4. **Maintainability**: Easy to understand and modify
5. **Collaboration**: Smooth code review process

## Python Standards

### Code Style

PsychSync follows [PEP 8](https://pep8.org/) with modifications enforced by Ruff.

#### Line Length

```python
# Maximum line length: 100 characters
# This balances readability with modern screen sizes

# Good
def calculate_user_score(user_id: str, assessment_type: str) -> dict[str, int]:
    ...

# Bad - too long
def calculate_user_score_from_assessment_results_by_user_id_and_type(user_id: str, assessment_type: str) -> dict[str, int]:
    ...
```

#### Imports

```python
# Import order (enforced by Ruff)
# 1. Standard library
# 2. Third-party imports
# 3. Local imports (app.*, ai.*)
# 4. Relative imports

# Good
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.models.user import User
```

#### Type Annotations

```python
# All functions must have type annotations
# Good
async def get_user(user_id: int, db: AsyncSession) -> Optional[User]:
    ...

# Bad - no type hints
async def get_user(user_id, db):
    ...
```

#### Naming Conventions

```python
# Variables and functions: snake_case
user_id = 123
def calculate_score(): ...

# Classes: PascalCase
class UserService: ...

# Constants: UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 5
API_VERSION = "v1"

# Private members: leading underscore
class UserService:
    def _internal_method(self): ...
```

#### Docstrings

```python
# Use Google-style docstrings
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token as string

    Raises:
        ValueError: If data is empty
    """
    ...
```

#### Async/Await

```python
# Use async/await consistently for FastAPI
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### Security Standards

#### SQL Injection Prevention

```python
# Good - parameterized queries
result = await db.execute(
    select(User).where(User.email == email)
)

# Bad - string formatting (SQL injection risk)
query = f"SELECT * FROM users WHERE email = '{email}'"
result = await db.execute(text(query))
```

#### Password Handling

```python
# Always hash passwords before storage
from app.core.security import hash_password

hashed_password = hash_password(plain_password)

# Never log or store plain text passwords
logger.info(f"User password: {password}")  # FORBIDDEN
```

#### Input Validation

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)
```

### Complexity Limits

```python
# Maximum cyclomatic complexity: 15
# Maximum function arguments: 7
# Maximum function statements: 50

# If a function exceeds these limits, refactor:
# - Extract helper functions
# - Use strategy pattern
# - Break down into smaller functions

# Good - simple, focused
async def validate_user_email(email: str, db: AsyncSession) -> bool:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none() is not None

# Bad - too complex (example)
async def process_user_data_with_validation_and_scoring_and_notifications(
    user_id: int, email: str, password: str, full_name: str,
    role: str, team_id: int, db: AsyncSession
):
    # 100+ lines of complex logic
    ...
```

## TypeScript/React Standards

### Code Style

PsychSync uses TypeScript strict mode with ESLint enforcement.

#### Type Definitions

```typescript
// Good - explicit types
interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

const getUser = async (id: string): Promise<User> => {
  const response = await apiClient.get<User>(`/users/${id}`);
  return response.data;
};

// Bad - using 'any'
const getUser = async (id: string): Promise<any> => {
  return await apiClient.get(`/users/${id}`);
};
```

#### React Components

```typescript
// Good - functional component with types
interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = 'primary'
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  );
};

// Bad - missing types
export const Button = ({ children, onClick, disabled }) => {
  return <button onClick={onClick}>{children}</button>;
};
```

#### Hooks

```typescript
// Good - proper hook usage
const UserProfile = () => {
  const { user, loading, error } = useAuth();
  const [data, setData] = useState<UserData | null>(null);

  useEffect(() => {
    if (user) {
      fetchUserData(user.id).then(setData);
    }
  }, [user]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return <div>{data?.full_name}</div>;
};

// Bad - missing dependencies
useEffect(() => {
  fetchUserData(user.id);
}, []); // Missing 'user' dependency
```

#### Imports

```typescript
// Import order (enforced by ESLint)
// 1. React imports
// 2. Third-party imports
// 3. Internal imports (@/...)
// 4. Relative imports

// Good
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@mui/material';
import { User } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import './UserProfile.css';

// Bad - disorganized imports
import { User } from '@/types';
import React from 'react';
import { Button } from '@mui/material';
import './UserProfile.css';
```

### Accessibility Standards

```typescript
// Good - accessible components
<button
  type="button"
  onClick={handleClick}
  aria-label="Close dialog"
  aria-pressed={isPressed}
>
  <Icon name="close" />
</button>

// Good - form accessibility
<label htmlFor="email-input">Email Address</label>
<input
  id="email-input"
  type="email"
  aria-required="true"
  aria-describedby="email-help"
/>
<p id="email-help">Enter your work email address</p>

// Bad - missing accessibility
<input type="email" placeholder="Email" />
<button onClick={handleClick}>
  <Icon name="close" />
</button>
```

### Error Handling

```typescript
// Good - proper error handling
const fetchUser = async (id: string): Promise<User> => {
  try {
    const response = await apiClient.get<User>(`/users/${id}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to fetch user: ${error.message}`);
    }
    throw error;
  }
};

// Bad - silent failures
const fetchUser = async (id: string): Promise<User> => {
  try {
    return await apiClient.get(`/users/${id}`);
  } catch (error) {
    console.log(error); // Should use proper logging
    return null; // Suppresses error
  }
};
```

## File Naming Conventions

### Python Files

```
# Modules: lowercase with underscores
user_service.py
auth_helper.py

# Tests: test_ prefix
test_user_service.py
test_auth_endpoints.py

# Private modules: leading underscore
_internal_utils.py
```

### TypeScript/React Files

```
# Components: PascalCase
UserProfile.tsx
Button.tsx
LoadingSpinner.tsx

# Utilities/services: camelCase
authService.ts
apiClient.ts

# Types: PascalCase
UserTypes.ts
ApiResponse.ts

# Tests: .test.ts or .spec.ts suffix
UserProfile.test.tsx
authService.spec.ts
```

### Configuration Files

```
# Config files: kebab-case
eslint.config.js
vite.config.ts
tailwind.config.js

# Environment files: .env prefix
.env.dev
.env.prod
.env.example
```

## Documentation Standards

### Code Comments

```python
# Good - explanatory comments
# Calculate the compound annual growth rate (CAGR)
# Formula: (Ending Value / Beginning Value) ^ (1 / Years) - 1
def calculate_cagr(beginning_value: float, ending_value: float, years: int) -> float:
    ...

# Bad - obvious comments
# Set x to 5
x = 5
```

### README Standards

Every major module should have a README.md explaining:

- Purpose and functionality
- Usage examples
- Dependencies
- Configuration options

### API Documentation

```python
# FastAPI endpoints benefit from docstrings
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new user account.

    Args:
        user_data: User creation data with email, password, full_name
        db: Database session (injected)

    Returns:
        Created user object with ID and timestamp

    Raises:
        HTTPException 400: If email already registered
        HTTPException 422: If validation fails
    """
    ...
```

## Testing Standards

### Python Tests

```python
# Tests should follow AAA pattern (Arrange, Act, Assert)
@pytest.mark.asyncio
async def test_create_user_success(db: AsyncSession):
    # Arrange
    user_data = UserCreate(
        email="test@example.com",
        password="SecurePass123!",
        full_name="Test User"
    )

    # Act
    result = await create_user(user_data, db)

    # Assert
    assert result.email == "test@example.com"
    assert result.full_name == "Test User"
    assert result.id is not None
```

### TypeScript Tests

```typescript
// Tests should be descriptive and test single behavior
describe('AuthService', () => {
  it('should successfully login with valid credentials', async () => {
    const credentials = {
      email: 'test@example.com',
      password: 'SecurePass123!'
    };

    const result = await login(credentials);

    expect(result.user).toBeDefined();
    expect(result.user.email).toBe(credentials.email);
  });

  it('should throw error with invalid credentials', async () => {
    const credentials = {
      email: 'test@example.com',
      password: 'WrongPassword'
    };

    await expect(login(credentials)).rejects.toThrow('Invalid credentials');
  });
});
```

## Git Workflow

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes
- `security`: Security vulnerability fix

Examples:

```
feat(auth): add OAuth2 login support

Add support for Google and GitHub OAuth2 providers.
Implements user profile creation and token management.

Closes #123
```

```
fix(api): resolve race condition in user creation

Fixed issue where concurrent user creation requests
could result in duplicate email addresses.

Fixes #456
```

### Branch Naming

```
feature/feature-name
bugfix/bug-name
hotfix/urgent-fix
release/version-number
```

## CI/CD Integration

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files

# Skip specific hook (not recommended)
SKIP=eslint git commit -m "message"
```

### GitHub Actions

Linting runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual trigger via workflow dispatch

Jobs:
1. **Python Linting**: Ruff, mypy, bandit
2. **Frontend Linting**: ESLint, TypeScript, Prettier
3. **Security Scanning**: Bandit, Semgrep, Safety
4. **Config Validation**: YAML, TOML, JSON
5. **Documentation**: Markdown linting, spell check
6. **Pre-commit Check**: Ensures hooks work in CI

## Team Adoption Guide

### Getting Started

1. **Install dependencies**

```bash
# Python
pip install ruff mypy bandit[toml] pre-commit

# Frontend
cd frontend
npm install
```

2. **Install pre-commit hooks**

```bash
pre-commit install
```

3. **Configure your editor**

- Install `.editorconfig` support plugin
- Configure Prettier for frontend
- Enable Ruff for Python (VS Code: extension `charliermarsh.ruff`)

### Daily Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-user-analytics

# 2. Make changes
# ... code ...

# 3. Run linting before commit
ruff check . --fix
cd frontend && npm run lint:fix

# 4. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat(analytics): add user engagement tracking"

# 5. Push and create PR
git push origin feature/add-user-analytics
```

### Troubleshooting

#### Ruff Errors

```bash
# Auto-fix most issues
ruff check --fix .

# See all errors
ruff check .

# Check specific file
ruff check app/services/auth_service.py
```

#### ESLint Errors

```bash
# Auto-fix most issues
cd frontend
npm run lint:fix

# Check specific file
npm run lint -- src/services/authService.ts
```

#### Type Errors

```python
# Python mypy
mypy app/ --ignore-missing-imports

# TypeScript
cd frontend
npm run type-check
```

### Onboarding Checklist

- [ ] Install Python linting tools (ruff, mypy, bandit)
- [ ] Install pre-commit hooks
- [ ] Configure editor with .editorconfig
- [ ] Install frontend linting tools (ESLint, Prettier)
- [ ] Read through code style standards
- [ ] Run linting on existing codebase
- [ ] Fix any linting errors in your first PR

### Exception Handling

If you need to disable a specific rule:

```python
# Python - use noqa comment with specific rule
def complex_function():  # noqa: PLR0912  # too-many-branches
    ...

# TypeScript - use eslint-disable comment
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = fetchData();
```

**Note**: Get team approval before adding rule exceptions.

## Continuous Improvement

This standards document evolves with the project. To suggest changes:

1. Propose change in team meeting
2. Update this document with rationale
3. Update linting configurations
4. Announce change to team
5. Provide transition period

---

For questions or suggestions about these standards, please open an issue or contact the development team.

Last updated: 2026-01-04
