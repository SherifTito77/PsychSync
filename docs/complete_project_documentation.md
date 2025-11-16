# PsychSync AI - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Backend Documentation](#backend-documentation)
4. [Frontend Documentation](#frontend-documentation)
5. [Database Schema](#database-schema)
6. [API Documentation](#api-documentation)
7. [Deployment Guide](#deployment-guide)
8. [Development Setup](#development-setup)
9. [Testing Strategy](#testing-strategy)
10. [Security Considerations](#security-considerations)

---

## Project Overview

**PsychSync AI** is a behavioral analytics platform designed for high-performance agile teams. It synthesizes multiple personality assessment frameworks to optimize team composition, predict performance, and provide actionable insights for team dynamics.

### Key Features
- Multi-framework personality synthesis (MBTI, Big Five, Enneagram, Predictive Index, StrengthsFinder)
- AI-powered team optimization
- Predictive analytics for team performance
- Real-time compatibility analysis
- Comprehensive team management dashboard

### Technology Stack
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18+ with TypeScript
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session management and caching
- **AI/ML**: TensorFlow, scikit-learn (optional dependencies)
- **Deployment**: Docker, Kubernetes, Nginx

---

## Architecture

### System Architecture Diagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React SPA     │───▶│   FastAPI API    │───▶│   PostgreSQL    │
│   (Frontend)    │    │    (Backend)     │    │   (Database)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │      Redis       │
                       │     (Cache)      │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   AI/ML Engine   │
                       │  (TensorFlow)    │
                       └──────────────────┘
```

### Application Structure
```
psychsync/
├── app/                    # Backend application
│   ├── main.py            # Application entry point
│   ├── core/              # Core configuration and setup
│   ├── api/               # API routes and endpoints
│   ├── ai/                # AI/ML components
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic services
├── frontend/              # React frontend
│   ├── public/           # Static assets
│   └── src/              # Source code
├── docker-compose.yml     # Development environment
├── kubernetes/            # K8s deployment configs
└── docs/                  # Additional documentation
```

---

## Backend Documentation

### Core Components

#### 1. Configuration Management (`app/core/config.py`)
Centralized configuration using Pydantic settings with environment variable support.

**Key Settings:**
- Database connections
- Redis configuration
- Security keys and tokens
- CORS origins
- AI/ML API keys

**Usage:**
```python
from app.core.config import settings

# Access any setting
database_url = settings.DATABASE_URL
debug_mode = settings.DEBUG
```

#### 2. Database Layer (`app/core/database.py`)
SQLAlchemy-based database layer with connection pooling and session management.

**Features:**
- Connection pooling for performance
- Automatic reconnection handling
- Session-per-request pattern
- Database migration support with Alembic

#### 3. Cache Layer (`app/core/cache.py`)
Redis-based caching with fallback mechanisms and error handling.

**Features:**
- Singleton pattern for Redis connections
- JSON serialization support
- TTL-based expiration
- Mock client for development without Redis

### AI/ML Components

#### 1. Behavioral AI Engine (`app/ai/engine/behavioral_ai.py`)
Core AI engine that synthesizes multiple personality frameworks into unified profiles.

**Key Methods:**
- `synthesize_personality_profile()` - Main synthesis method
- `_weighted_synthesis()` - Heuristic-based combination
- `_ai_synthesis()` - Neural network-based synthesis (when available)

**Synthesis Process:**
1. Validate input assessments
2. Convert to standardized feature vectors
3. Apply AI model or weighted heuristics
4. Generate unified personality profile
5. Calculate confidence scores

#### 2. Team Optimizer (`app/ai/engine/team_optimizer.py`)
Analyzes team composition and provides optimization recommendations.

**Key Features:**
- Compatibility matrix calculation
- Team balance analysis
- Performance prediction
- Conflict identification
- Optimization recommendations

#### 3. Assessment Processors (`app/ai/processors/`)
Individual processors for each personality framework.

**Processors Available:**
- `EnneagramProcessor` - 9-type personality system
- `MBTIProcessor` - Myers-Briggs Type Indicator
- `BigFiveProcessor` - Five-factor model
- `PredictiveIndexProcessor` - PI behavioral assessment
- `StrengthsProcessor` - StrengthsFinder themes
- `SocialStylesProcessor` - 4-quadrant communication styles

**Base Processor Features:**
- Input validation
- Error handling with fallbacks
- Standardized output format
- Confidence scoring

### API Layer

The API follows REST principles with proper HTTP status codes and comprehensive error handling.

**Endpoint Categories:**
- `/auth/` - Authentication and authorization
- `/users/` - User management
- `/teams/` - Team operations
- `/assessments/` - Personality assessments
- `/analytics/` - Performance analytics

---

## Frontend Documentation

### Application Structure

#### 1. Context Providers
State management using React Context API for global application state.

**Contexts:**
- `AuthContext` - User authentication and session management
- `NotificationContext` - Toast notifications and alerts
- `TeamContext` - Team data and operations

#### 2. Component Architecture
Organized in a hierarchical structure promoting reusability and maintainability.

```
src/components/
├── common/        # Reusable UI components
├── layout/        # Page layout components
├── forms/         # Form components
└── charts/        # Data visualization components
```

#### 3. Pages and Routing
Single-page application with client-side routing using React Router.

**Main Pages:**
- Dashboard - Overview and key metrics
- Teams - Team management interface
- Assessments - Personality assessment tools
- Analytics - Performance analytics dashboard
- Settings - User and system preferences

#### 4. Type Safety
Comprehensive TypeScript interfaces for type safety and better developer experience.

**Key Types:**
```typescript
interface User {
  id: number;
  name: string;
  email: string;
}

interface PersonalityProfile {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  // ... additional derived metrics
}
```

---

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
```

#### Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name CITEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### Teams Table
```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### Assessments Table
```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    framework_id UUID NOT NULL REFERENCES frameworks(id),
    results JSONB NOT NULL,
    confidence DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Relationships
- Users belong to Organizations through `org_members`
- Users can be in multiple Teams through `team_members`
- Assessments belong to Users and reference Frameworks
- Audit logs track all organizational changes

---

## API Documentation

### Authentication Endpoints

#### POST /api/v1/auth/login
Authenticate user and return JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com"
  }
}
```

### Team Management Endpoints

#### GET /api/v1/teams/
Get all teams for the authenticated user's organization.

**Response:**
```json
{
  "teams": [
    {
      "id": 1,
      "name": "Frontend Team",
      "description": "Web development team",
      "status": "active",
      "member_count": 5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### POST /api/v1/teams/{team_id}/optimize
Get optimization recommendations for a specific team.

**Response:**
```json
{
  "current_metrics": {
    "overall_score": 0.78,
    "average_compatibility": 0.82,
    "diversity_score": 0.65,
    "team_size": 5
  },
  "recommendations": [
    {
      "type": "role_assignment",
      "priority": "high",
      "title": "Optimal Team Lead Identified",
      "description": "Member shows strong leadership potential",
      "action": "Consider leadership role assignment"
    }
  ],
  "performance_prediction": {
    "predicted_velocity": 24.5,
    "satisfaction_score": 0.78,
    "conflict_probability": 0.15
  }
}
```

### Assessment Endpoints

#### POST /api/v1/assessments/
Submit new personality assessment results.

**Request:**
```json
{
  "framework": "mbti",
  "results": {
    "type": "INTJ",
    "confidence": 0.85,
    "preferences": {
      "energy": "Introversion",
      "information": "Intuition",
      "decisions": "Thinking",
      "lifestyle": "Judging"
    }
  }
}
```

---

## Deployment Guide

### Development Environment

#### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- PostgreSQL 15+
- Redis 7+

#### Quick Start
```bash
# Clone repository
git clone https://github.com/your-org/psychsync.git
cd psychsync

# Start development environment
docker-compose up -d

# Install dependencies
cd app && pip install -r requirements.txt
cd ../frontend && npm install

# Run database migrations
cd app && alembic upgrade head

# Start development servers
cd app && uvicorn main:app --reload
cd frontend && npm start
```

### Production Deployment

#### Docker Production Build
```bash
# Build production images
docker build -t psychsync/app:latest ./app
docker build -t psychsync/frontend:latest ./frontend

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

#### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/postgres.yaml
kubectl apply -f kubernetes/redis.yaml
kubectl apply -f kubernetes/app.yaml
kubectl apply -f kubernetes/frontend.yaml
kubectl apply -f kubernetes/ingress.yaml
```

### Environment Variables

#### Backend Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
POSTGRES_DB=psychsync_db
POSTGRES_USER=psychsync
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=another-secret-for-jwt
ENVIRONMENT=production

# AI/ML
OPENAI_API_KEY=sk-your-openai-key
HUGGINGFACE_API_KEY=hf_your-huggingface-key
```

#### Frontend Environment Variables
```bash
REACT_APP_API_URL=https://api.psychsync.ai
REACT_APP_ENVIRONMENT=production
```

---

## Development Setup

### Backend Development

#### Virtual Environment Setup
```bash
cd app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Database Setup
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Create sample data (optional)
python scripts/create_sample_data.py
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Frontend Development

#### Installation and Setup
```bash
cd frontend
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

#### Code Quality Tools
```bash
# Linting
npm run lint

# Type checking
npm run type-check

# Format code
npm run format
```

---

## Testing Strategy

### Backend Testing

#### Unit Tests
Located in `tests/unit/`, these test individual components in isolation.

**Test Categories:**
- AI processors (`test_processors.py`)
- Business logic (`test_services.py`)
- Utility functions (`test_utils.py`)

**Example Test:**
```python
# tests/unit/test_processors.py
import pytest
from ai.processors.mbti import MBTIProcessor

def test_mbti_processor_valid_input():
    processor = MBTIProcessor()
    raw_data = {
        'type': 'INTJ',
        'confidence': 0.85
    }
    
    result = processor.process(raw_data)
    
    assert result['type'] == 'INTJ'
    assert result['confidence'] == 0.85
    assert 'dimensions' in result
    assert result['dimensions']['openness'] > 0.5  # N types have higher openness
```

#### Integration Tests
Located in `tests/integration/`, these test component interactions.

**Test Categories:**
- API endpoints (`test_api.py`)
- Database operations (`test_database.py`)
- AI engine workflows (`test_ai_engine.py`)

#### Performance Tests
Load testing using pytest-benchmark and locust.

```python
# tests/performance/test_ai_performance.py
def test_synthesis_performance(benchmark):
    engine = BehavioralAIEngine()
    assessments = create_sample_assessments()
    
    result = benchmark(engine.synthesize_personality_profile, assessments)
    assert result['confidence'] > 0.3
```

### Frontend Testing

#### Component Tests
Using React Testing Library for component testing.

```javascript
// src/components/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button';

test('renders button with text', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByRole('button')).toHaveTextContent('Click me');
});

test('calls onClick when clicked', () => {
  const handleClick = jest.fn();
  render(<Button onClick={handleClick}>Click me</Button>);
  
  fireEvent.click(screen.getByRole('button'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});
```

#### End-to-End Tests
Using Cypress for full application testing.

```javascript
// cypress/e2e/auth.cy.ts
describe('Authentication', () => {
  it('should login successfully', () => {
    cy.visit('/login');
    cy.get('[data-testid=email]').type('test@example.com');
    cy.get('[data-testid=password]').type('password');
    cy.get('[data-testid=login-button]').click();
    
    cy.url().should('include', '/dashboard');
    cy.contains('Welcome back').should('be.visible');
  });
});
```

---

## Security Considerations

### Authentication & Authorization

#### JWT Token Security
- Tokens expire after 24 hours by default
- Refresh token rotation implemented
- Secure HTTP-only cookies in production
- CSRF protection enabled

#### Password Security
- bcrypt hashing with salt rounds
- Password complexity requirements
- Rate limiting on auth endpoints
- Account lockout after failed attempts

### Data Protection

#### Database Security
- All connections use TLS/SSL
- Row-level security policies
- Parameterized queries prevent SQL injection
- Regular security audits

#### API Security
- CORS properly configured
- Input validation using Pydantic
- Rate limiting on all endpoints
- Request size limits

#### Data Privacy
- GDPR compliance measures
- Data anonymization options
- User data export/deletion
- Audit logging for compliance

### Infrastructure Security

#### Container Security
- Non-root user in containers
- Minimal base images
- Regular security updates
- Container scanning in CI/CD

#### Network Security
- TLS 1.3 encryption
- Security headers (HSTS, CSP, etc.)
- WAF protection in production
- Network segmentation

---

## Monitoring and Observability

### Application Metrics

#### Backend Metrics
- Request/response times
- Error rates by endpoint
- Database query performance
- AI model inference times
- Memory and CPU usage

#### Frontend Metrics
- Page load times
- User interaction tracking
- JavaScript error rates
- Bundle size monitoring

### Logging Strategy

#### Structured Logging
```python
import logging
import structlog

logger = structlog.get_logger(__name__)

def process_assessment(user_id: int, framework: str):
    logger.info(
        "Processing assessment",
        user_id=user_id,
        framework=framework,
        timestamp=datetime.utcnow()
    )
```

#### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARNING`: Something unexpected but recoverable
- `ERROR`: Serious problems that need attention
- `CRITICAL`: System failures

### Health Checks

#### Application Health
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "ai_models": await check_ai_models_status()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

---

## Performance Optimization

### Backend Performance

#### Database Optimization
- Connection pooling (10-20 connections)
- Query optimization with indexes
- Read replicas for analytics queries
- Caching frequently accessed data

#### AI Model Performance
- Model quantization for faster inference
- Batch processing for multiple assessments
- Async processing for non-critical tasks
- GPU acceleration when available

#### Caching Strategy
```python
@lru_cache(maxsize=1000)
def calculate_compatibility(profile_a: str, profile_b: str) -> float:
    # Expensive compatibility calculation
    return compatibility_score
```

### Frontend Performance

#### Code Splitting
```javascript
// Lazy loading of routes
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Teams = lazy(() => import('./pages/Teams'));

// Component lazy loading
const AssessmentModal = lazy(() => import('./components/AssessmentModal'));
```

#### Asset Optimization
- Image compression and WebP format
- CSS/JS minification and compression
- CDN for static assets
- Service worker for offline capability

---

## Backup and Recovery

### Database Backup Strategy

#### Automated Backups
```bash
# Daily full backup
0 2 * * * pg_dump psychsync_db | gzip > /backups/psychsync_$(date +%Y%m%d).sql.gz

# Continuous WAL archiving
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
```

#### Backup Retention
- Daily backups kept for 30 days
- Weekly backups kept for 6 months
- Monthly backups kept for 2 years
- Point-in-time recovery capability

### Disaster Recovery

#### Recovery Time Objectives
- **RTO**: 4 hours maximum downtime
- **RPO**: 1 hour maximum data loss
- Automated failover to standby systems
- Cross-region backup replication

---

## Troubleshooting Guide

### Common Issues

#### Database Connection Issues
```
Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
```
**Solution:** Check PostgreSQL service status and connection parameters.

#### Redis Connection Issues
```
Error: No connection could be made because the target machine actively refused it
```
**Solution:** Verify Redis service is running and check firewall settings.

#### AI Model Loading Errors
```
Error: TensorFlow not available. Using simplified models.
```
**Solution:** This is expected behavior. Install TensorFlow for full AI capabilities.

### Debug Mode
Enable debug logging in development:
```python
# app/core/config.py
DEBUG = True
LOG_LEVEL = "DEBUG"
```

### Performance Debugging
Use profiling tools to identify bottlenecks:
```python
# Add to endpoints for profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... your code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

---

## Contributing Guidelines

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes with proper tests
4. Run quality checks: `make lint test`
5. Submit pull request with clear description

### Code Standards
- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript/TypeScript
- Maintain test coverage above 80%
- Document all public APIs
- Use semantic versioning

### Commit Messages
```
feat: add team optimization algorithm
fix: resolve compatibility calculation bug
docs: update API documentation
test: add unit tests for MBTI processor
```

This comprehensive documentation provides a complete reference for the PsychSync project, covering all aspects from development setup to production deployment and maintenance.