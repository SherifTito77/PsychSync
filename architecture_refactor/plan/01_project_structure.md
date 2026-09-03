# PsychSync Refactored Project Structure

## Executive Summary

This document outlines the new project structure for PsychSync, transforming it from "vibe coding" to production-ready architecture following **Clean Architecture** and **Domain-Driven Design** principles.

---

## 📁 New Directory Structure

```
psychsync/
├── app.ai/                          # 🤖 Standalone AI/ML Package
│   ├── __init__.py
│   ├── processors/                     # Assessment processors
│   │   ├── __init__.py
│   │   ├── base.py                     # Base processor interface
│   │   ├── mbti.py                     # MBTI processor
│   │   ├── big_five.py                # Big Five processor
│   │   ├── enneagram.py               # Enneagram processor
│   │   ├── predictive_index.py        # Predictive Index
│   │   ├── social_styles.py           # Social Styles
│   │   ├── strengths.py               # Clifton Strengths
│   │   └── wellness.py                # Wellness assessments
│   ├── scoring/                        # Scoring algorithms
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── algorithms.py
│   │   └── validators.py
│   ├── models/                         # Shared AI models
│   │   ├── __init__.py
│   │   ├── shared_types.py            # Common data structures
│   │   └── processing_result.py       # Standardized output
│   ├── tests/                          # AI engine tests
│   │   ├── __init__.py
│   │   ├── test_processors.py
│   │   ├── test_scoring.py
│   │   └── fixtures.py
│   └── requirements.txt                # ML-specific dependencies
│
├── app/                                 # 🚀 FastAPI Application Layer
│   ├── __init__.py
│   ├── main.py                         # Slim application entry point
│   ├── dependencies.py                 # FastAPI dependencies
│   │
│   ├── api/                            # 📡 API Layer (Presentation)
│   │   ├── __init__.py
│   │   ├── deps.py                     # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                  # Router aggregation
│   │       └── endpoints/              # API endpoints (thin, only HTTP concerns)
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── assessments.py
│   │           ├── teams.py
│   │           └── ...
│   │
│   ├── domain/                         # 🧠 Domain Layer (Business Logic)
│   │   ├── __init__.py
│   │   ├── entities/                   # Domain entities (business objects)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── team.py
│   │   │   ├── assessment.py
│   │   │   ├── response.py
│   │   │   └── organization.py
│   │   ├── value_objects/              # Value objects (types with validation)
│   │   │   ├── __init__.py
│   │   │   ├── email.py
│   │   │   ├── password.py
│   │   │   └── percentage.py
│   │   ├── services/                   # Domain services (business logic)
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   ├── assessment_service.py
│   │   │   ├── team_service.py
│   │   │   └── auth_service.py
│   │   ├── events/                     # Domain events
│   │   │   ├── __init__.py
│   │   │   ├── user_created.py
│   │   │   └── assessment_completed.py
│   │   └── exceptions/                 # Domain-specific exceptions
│   │       ├── __init__.py
│   │       ├── validation.py
│   │       └── not_found.py
│   │
│   ├── infrastructure/                 # 🏗️ Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database/                   # Database setup
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # DB session management
│   │   │   └── base.py                 # SQLAlchemy Base
│   │   ├── repositories/               # Repository implementations (data access)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # BaseRepository
│   │   │   ├── user_repository.py
│   │   │   ├── team_repository.py
│   │   │   ├── assessment_repository.py
│   │   │   └── response_repository.py
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── team.py
│   │   │   ├── assessment.py
│   │   │   └── response.py
│   │   ├── cache/                      # Caching layer
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py
│   │   │   └── cache_service.py
│   │   └── external/                   # External service integrations
│   │       ├── __init__.py
│   │       ├── email.py
│   │       └── storage.py
│   │
│   ├── schemas/                        # 📋 Pydantic Schemas (API contracts)
│   │   ├── __init__.py
│   │   ├── base.py                     # Base schemas
│   │   ├── user.py                     # User request/response schemas
│   │   ├── team.py
│   │   ├── assessment.py
│   │   └── common.py                   # Shared schema components
│   │
│   ├── core/                           # ⚙️ Core Application Config
│   │   ├── __init__.py
│   │   ├── config.py                   # Application settings
│   │   ├── security.py                 # Security utilities
│   │   ├── logging.py                  # Logging configuration
│   │   └── exceptions.py               # Exception handlers
│   │
│   ├── middleware/                     # 🛡️ Middleware (minimized)
│   │   ├── __init__.py
│   │   ├── auth.py                     # Authentication middleware
│   │   ├── cors.py                     # CORS (single implementation)
│   │   └── error_handling.py           # Global error handling
│   │
│   └── utils/                          # 🔧 Utilities (pure functions)
│       ├── __init__.py
│       ├── validators.py
│       └── formatters.py
│
├── tests/                              # 🧪 Comprehensive Test Suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   ├── unit/                           # Unit tests
│   │   ├── domain/                     # Domain layer tests
│   │   │   ├── services/
│   │   │   └── entities/
│   │   ├── infrastructure/             # Repository tests
│   │   │   └── repositories/
│   │   └── schemas/                    # Schema validation tests
│   ├── integration/                    # Integration tests
│   │   ├── api/                        # API endpoint tests
│   │   │   ├── v1/
│   │   │   │   ├── test_auth.py
│   │   │   │   ├── test_users.py
│   │   │   │   └── test_assessments.py
│   │   └── database/                   # Database integration tests
│   ├── e2e/                            # End-to-end tests
│   │   ├── test_onboarding.py
│   │   ├── test_assessment_flow.py
│   │   └── test_team_management.py
│   ├── fixtures/                       # Test fixtures and factories
│   │   ├── __init__.py
│   │   ├── user_fixtures.py
│   │   └── assessment_fixtures.py
│   └── performance/                    # Performance tests
│       └── load_tests.py
│
├── alembic/                            # Database Migrations
│   ├── versions/                       # Migration files
│   └── env.py
│
├── docs/                               # 📚 Documentation
│   ├── architecture/                   # Architecture documentation
│   │   ├── adr/                        # Architecture Decision Records
│   │   │   ├── 001-use-repository-pattern.md
│   │   │   ├── 002-extract-ai-engine.md
│   │   │   └── 003-standardize-uuids.md
│   │   ├── overview.md                 # System overview
│   │   └── data-flow.md                # Data flow diagrams
│   ├── api/                            # API documentation
│   │   ├── authentication.md
│   │   ├── assessments.md
│   │   └── teams.md
│   └── development/                    # Developer documentation
│       ├── setup.md                    # Setup guide
│       ├── testing.md                  # Testing guide
│       └── deployment.md               # Deployment guide
│
├── scripts/                            # 🔨 Utility Scripts
│   ├── setup_db.py
│   ├── seed_data.py
│   └── migrate_data.py
│
├── .github/                            # GitHub Configuration
│   └── workflows/
│       ├── tests.yml                   # CI/CD test pipeline
│       └── lint.yml                    # Code quality checks
│
├── pyproject.toml                      # Project configuration
├── pytest.ini                          # Pytest configuration
├── .pre-commit-config.yaml             # Pre-commit hooks
└── README.md                           # Project README
```

---

## 🎯 Key Architectural Changes

### 1. **Domain Layer Isolation** (`app/domain/`)
- **Purpose**: Pure business logic, independent of frameworks
- **Contains**: Entities, value objects, domain services, business rules
- **Dependencies**: None (no FastAPI, no SQLAlchemy)

### 2. **Repository Pattern** (`app/infrastructure/repositories/`)
- **Purpose**: Separate data access from business logic
- **Benefits**: Testable, swappable data sources, clear separation of concerns
- **Implementation**: BaseRepository with generic CRUD operations

### 3. **AI Engine Separation** (`app.ai/`)
- **Purpose**: Isolate ML/assessment logic from FastAPI
- **Benefits**: Independent versioning, testable without HTTP layer
- **Interface**: Clean input/output contracts

### 4. **Thin API Layer** (`app/api/v1/endpoints/`)
- **Purpose**: Only HTTP concerns (validation, serialization, status codes)
- **Rule**: No business logic in endpoints
- **Delegates**: Calls domain services

### 5. **Comprehensive Testing** (`tests/`)
- **Structure**: Mirrors application structure
- **Coverage Target**: 85%+
- **Types**: Unit, integration, E2E, performance

---

## 📊 Layer Dependency Rules

```
┌─────────────────────────────────────────┐
│           API Layer (FastAPI)            │  ← External users
├─────────────────────────────────────────┤
│         Domain Services Layer            │  ← Business logic
├─────────────────────────────────────────┤
│    Repository Layer (Data Access)        │  ← Databases, cache
├─────────────────────────────────────────┤
│    Infrastructure (External Services)     │  ← Email, storage
└─────────────────────────────────────────┘

Rule: Dependencies only point inward
- API → Domain → Repository → Infrastructure
- Never: Repository → API ❌
```

---

## 🔄 Migration Strategy

### Phase 1: Setup (Week 1)
1. Create new directory structure
2. Set up testing infrastructure
3. Write ADRs documenting decisions

### Phase 2: Domain Layer (Week 2)
1. Create domain entities
2. Implement value objects
3. Write domain services with business rules

### Phase 3: Repository Layer (Week 3)
1. Implement BaseRepository
2. Create repository implementations
3. Add unit tests with mocks

### Phase 4: API Refactoring (Week 4)
1. Refactor endpoints to use domain services
2. Remove business logic from endpoints
3. Add integration tests

### Phase 5: AI Engine Extraction (Week 5)
1. Move AI code to standalone package
2. Create clean interfaces
3. Test in isolation

### Phase 6: Documentation (Week 6-7)
1. Write architecture documentation
2. Create API guides
3. Document deployment process

---

## 📈 Success Metrics

### Code Quality
- [x] Clear separation of concerns
- [x] Testable business logic (85%+ coverage)
- [x] Type-safe throughout
- [x] Consistent patterns

### Developer Experience
- [x] New feature addition < 2 hours
- [x] Onboarding time < 1 week
- [x] Clear documentation
- [x] Fast test suite (< 5 min)

### Production Readiness
- [x] Comprehensive error handling
- [x] Security best practices
- [x] Performance monitoring
- [x] Deployment automation

---

## 🎓 Next Steps

1. **Review this structure** with your team
2. **Approve the migration plan**
3. **Begin Phase 1.1** - Create base directories
4. **Generate ADRs** for key decisions
5. **Set up testing infrastructure**

---

*This structure follows industry best practices for FastAPI applications while maintaining the flexibility needed for PsychSync's AI-powered assessment platform.*
