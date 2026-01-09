# PsychSync Code Style Guide

## Table of Contents
- [Python Code Style](#python-code-style)
- [FastAPI Specific Conventions](#fastapi-specific-conventions)
- [Database/ORM Patterns](#databasemorm-patterns)
- [Error Handling Standards](#error-handling-standards)
- [Testing Conventions](#testing-conventions)
- [Documentation Standards](#documentation-standards)
- [Import Organization](#import-organization)
- [Type Hints Guidelines](#type-hints-guidelines)
- [Frontend Code Style](#frontend-code-style)
- [Security Guidelines](#security-guidelines)

---

## Python Code Style

### 1. Naming Conventions

#### Variables and Functions
- **Snake case** for all variables and functions
- **Descriptive names** - avoid single-letter variables except in loops
- **Private members** start with underscore (`_`)
- **Constants** use UPPER_SNAKE_CASE

```python
# ✅ Good
user_email = "user@example.com"
def validate_user_input(email: str) -> bool:
    if not email:
        return False
    return True

# ❌ Bad
email = "user@example.com"
def validate(e):
    if not e:
        return False
    return True
```

#### Classes
- **PascalCase** for class names
- **Exception classes** end with `Error` or `Exception`
- **Abstract classes** use `ABC` metaclass

```python
# ✅ Good
class UserService:
    pass

class DatabaseConnectionError(Exception):
    pass

from abc import ABC
class BaseProcessor(ABC):
    pass

# ❌ Bad
class user_service:
    pass

class DatabaseError:
    pass
```

### 2. Code Structure

#### File Organization
```
app/
├── __init__.py
├── main.py           # Application entry point
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── api.py     # Router aggregation
│       └── endpoints/
├── core/
│   ├── __init__.py
│   ├── config.py     # Configuration
│   └── database.py   # Database setup
├── db/
│   ├── __init__.py
│   ├── models/
│   └── crud/
├── services/
│   ├── __init__.py
│   └── auth_service.py
├── schemas/
│   ├── __init__.py
│   └── user.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

---

## FastAPI Specific Conventions

### 1. Route Patterns

#### Standard Route Structure
```python
@router.get("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> UserOut:
    '''
    Retrieve a specific user by ID.
    
    Args:
        user_id: UUID of the user to retrieve
        db: Database session
        current_user: Currently authenticated user
    
    Returns:
        UserOut: The requested user data
    
    Raises:
        HTTPException: When user is not found
    '''
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserOut.from_orm(user)
```

---

## Database/ORM Patterns

### 1. Model Definition

#### Standard Model Structure
```python
# app/db/models/user.py

from sqlalchemy import Column, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    # Primary columns
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, nullable=False, server_default="true")
    is_superuser = Column(Boolean, nullable=False, server_default="false")
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    assessments_created = relationship("Assessment", back_populates="created_by")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
```

---

## Error Handling Standards

### 1. Exception Classes

#### Custom Exception Hierarchy
```python
# app/core/exceptions.py

from fastapi import HTTPException
from typing import Any, Dict, Optional

class PsychSyncException(Exception):
    """Base exception for PsychSync application."""
    
    def __init__(
        self, 
        message: str, 
        detail: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.detail = detail or {}
        self.error_code = error_code

class AuthenticationError(PsychSyncException):
    """Authentication related errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            detail={"type": "authentication_error"},
            error_code="AUTH_ERROR"
        )

class AuthorizationError(PsychSyncException):
    """Authorization related errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            detail={"type": "authorization_error"},
            error_code="AUTHZ_ERROR"
        )

class ValidationError(PsychSyncException):
    """Data validation errors."""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            detail={"field": field, "type": "validation_error"},
            error_code="VALIDATION_ERROR"
        )

class DatabaseError(PsychSyncException):
    """Database operation errors."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            detail={"type": "database_error"},
            error_code="DB_ERROR"
        )
```

---

## Testing Conventions

### 1. Test Structure

#### Standard Test Structure
```python
# tests/integration/test_auth_flow.py

import pytest
import asyncio
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_async_db

@pytest.mark.integration
class TestAuthentication:
    """Test authentication flows."""
    
    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def test_db(self):
        """Create test database session."""
        async for session in get_async_db():
            yield session
    
    @pytest.mark.asyncio
    async def test_user_registration_success(
        self, 
        client: AsyncClient, 
        user_data: dict,
        test_db: AsyncSession
    ):
        """Test successful user registration."""
        # Arrange
        test_user = UserCreate(**user_data)
        
        # Act
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user.dict()
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "data" in data
        assert "access_token" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]
```

### 2. Test Fixtures

#### Common Fixtures
```python
# tests/conftest.py

import pytest
import asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import DATABASE_URL

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client(test_db):
    """Create test client with database."""
    app.dependency_overrides[get_async_db] = lambda: test_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user_data():
    """Sample user data."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!"
    }
```

---

## Documentation Standards

### 1. Docstring Format

#### Google Style Docstrings
```python
def function_name(param1: str, param2: int = 10) -> bool:
    '''
    Brief description of the function.
    
    This is a more detailed description of what the function does,
    including any important implementation details or considerations.
    
    Args:
        param1: Description of the first parameter.
            Can span multiple lines if needed.
        param2: Description of the second parameter.
            Default: 10
    
    Returns:
        bool: Description of the return value.
            - True: When condition is met
            - False: When condition is not met
    
    Raises:
        ValueError: When param1 is invalid.
        TypeError: When param2 is not an integer.
    
    Examples:
        >>> function_name("test", 5)
        True
        >>> function_name("")
        False
    '''
    # Implementation
    pass
```

---

## Import Organization

### 1. Import Order

#### Standard Import Organization
```python
# 1. Standard library imports
import os
import sys
import logging
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

# 2. Third-party imports
from fastapi import FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from jose import JWTError, jwt

# 3. Local application imports
from app.core.config import settings
from app.core.database import get_async_db
from app.db.models.user import User
from app.schemas.user import UserOut, UserCreate
from app.services.auth_service import AuthService

# 4. Relative imports (within same package)
from .database import get_db
from .models import BaseModel
```

---

## Type Hints Guidelines

### 1. Basic Type Hints

#### Standard Type Usage
```python
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from uuid import UUID

# Basic types
user_name: str = "John"
user_age: int = 30
is_active: bool = True
score: float = 95.5

# Optional types
middle_name: Optional[str] = None  # Can be string or None
phone_number: str | None = None     # Alternative syntax

# Collection types
user_emails: List[str] = ["user1@example.com", "user2@example.com"]
user_scores: Dict[str, float] = {"math": 95.0, "science": 88.5}

# Union types
value: Union[int, str] = 42  # Can be either int or str

# Any type (use sparingly)
data: Any = get_complex_data()

# Custom class types
user_id: UUID = uuid4()
created_at: datetime = datetime.now()
```

---

## Frontend Code Style

### 1. TypeScript Patterns

#### File Organization
```typescript
// src/services/authService.ts
import apiClient from './api';
import { User, LoginCredentials } from '../types';

// Interface definitions
interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Service class
export class AuthService {
  private readonly apiClient: typeof apiClient;
  
  constructor(apiClient: typeof apiClient) {
    this.apiClient = apiClient;
  }
  
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.apiClient.post<AuthResponse>(
      '/auth/login',
      credentials
    );
    return response.data;
  }
  
  async logout(): Promise<void> {
    await this.apiClient.post('/auth/logout');
  }
  
  async getCurrentUser(): Promise<User> {
    const response = await this.apiClient.get<User>('/auth/me');
    return response.data;
  }
}

// Export instance
export const authService = new AuthService(apiClient);
```

### 2. React Patterns

#### Component Structure
```typescript
// src/components/UserCard/UserCard.tsx
import React from 'react';
import { Card, CardHeader, CardContent } from '../UI/Card';
import { Avatar, AvatarFallback, AvatarImage } from '../UI/Avatar';
import { Badge } from '../UI/Badge';

interface UserCardProps {
  user: {
    id: string;
    email: string;
    full_name?: string;
    avatar_url?: string;
    is_active: boolean;
    role: 'admin' | 'user' | 'team_lead';
  };
  className?: string;
}

export const UserCard: React.FC<UserCardProps> = ({
  user,
  className = ''
}) => {
  const getRoleColor = (role: string): string => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'team_lead':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getInitials = (name?: string): string => {
    return name
      ? name.split(' ').map(n => n[0]).join('').toUpperCase()
      : user.email[0].toUpperCase();
  };

  return (
    <Card className={}>
      <CardHeader className="flex flex-row items-center space-y-0 pb-2">
        <Avatar className="h-8 w-8">
          <AvatarImage src={user.avatar_url} alt={user.full_name} />
          <AvatarFallback>{getInitials(user.full_name)}</AvatarFallback>
        </Avatar>
        <div className="ml-2 text-sm">
          <p className="font-medium">{user.full_name || user.email}</p>
          <p className="text-xs text-muted-foreground">{user.email}</p>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <Badge className={getRoleColor(user.role)}>
            {user.role}
          </Badge>
          <Badge variant={user.is_active ? 'default' : 'secondary'}>
            {user.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};
```

---

## Security Guidelines

### 1. Authentication Patterns

#### Secure Authentication Implementation
```python
# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import secrets
import logging

from app.core.security import verify_password, create_access_token
from app.core.database import get_async_db
from app.db.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Use cookie-based authentication for security
class CookieOAuth2Bearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        # Prioritize httpOnly cookies over Authorization header
        token = request.cookies.get("access_token")
        if token:
            return token
        
        # Fallback for backward compatibility
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization.split(" ")[1]
        
        return None

oauth2_scheme = CookieOAuth2Bearer(tokenUrl="/auth/login")

@router.post("/login")
async def login(
    request: Request,
    form_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    '''
    User login with secure cookie-based authentication.
    '''
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    # Validate credentials
    user = await db.execute(
        select(User).where(User.email == form_data.email)
    )
    user = user.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        # Log failed attempt
        logger.warning(
            f"Failed login attempt for {form_data.email} from {client_ip}",
            extra={"security_event": "FAILED_LOGIN"}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30)
    )
    
    refresh_token = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=7)
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create response with httpOnly cookies
    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": UserOut.from_orm(user).dict()
        }
    )
    
    # Set secure cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",
        max_age=1800  # 30 minutes
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    return response
```

---

## Summary

This code style guide provides comprehensive guidelines for the PsychSync FastAPI + React application. It covers:

1. **Python Code Style**: Naming conventions, structure, and formatting
2. **FastAPI Patterns**: Route definitions, dependency injection, and response models
3. **Database Patterns**: SQLAlchemy model definitions and CRUD operations
4. **Error Handling**: Custom exceptions and global handlers
5. **Testing Standards**: Test structure, fixtures, and markers
6. **Documentation**: Docstring formats and API documentation
7. **Import Organization**: Standard import order and best practices
8. **Type Hints**: Comprehensive type annotation guidelines
9. **Frontend Code**: TypeScript and React patterns
10. **Security Guidelines**: Authentication, validation, and rate limiting

Adherence to these guidelines will ensure consistent, maintainable, and secure code across the PsychSync application.
