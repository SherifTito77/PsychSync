# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI)
```bash
# Development server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Database migrations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Testing
pytest tests/ -v --tb=short           # Run all tests
pytest tests/api/test_auth.py -v       # Run specific test file
pytest -m unit                         # Run only unit tests
pytest -m integration                  # Run only integration tests

# Individual command testing
python -m pytest tests/api/test_auth.py::test_register_success -v
```

### Frontend (React + TypeScript)
```bash
cd frontend/

# Development server (Vite)
npm run dev                            # Starts dev server on port 5173

# Build and type checking
npm run build                         # Production build
npm run type-check                    # TypeScript checking without build

# Testing
npm run test                          # Run all tests once
npm run test:watch                    # Run tests in watch mode
npm run test:ui                       # Open Vitest UI
npm test src/components/Button.test.tsx  # Run specific test file

# Code quality
npm run lint                          # ESLint checking
npm run lint:fix                      # Auto-fix linting issues
npm run format                        # Prettier formatting
```

### Docker Development
```bash
# Full development environment
docker-compose up --build            # Starts nginx, backend, db, redis

# Database operations
docker-compose exec db psql -U postgres -d psychsync  # Connect to database
```

## Architecture Overview

### System Structure
PsychSync is a psychological assessment SaaS platform with a **service-oriented monolithic architecture**:

```
React SPA (Port 5173) ↔ FastAPI (Port 8000) ↔ PostgreSQL (Port 5432)
                                     ↓
                              Redis (Port 6379)
                                     ↓
                              AI Processing Engine
```

### Key Architectural Patterns

#### Backend (FastAPI)
- **Service Layer Pattern**: API endpoints → Services → CRUD → Database
- **Repository Pattern**: CRUD classes encapsulate database operations
- **Processor Pattern**: AI engine with abstract base processors for different assessment frameworks

#### Frontend (React)
- **Context Pattern**: Global state management via React Context (Auth, Team, Notification)
- **Service Layer Pattern**: API calls abstracted into service functions
- **Component Composition**: Reusable UI components with variant-based styling

### Core Modules

#### Authentication Flow
1. JWT tokens with automatic refresh via axios interceptors
2. Email verification for account activation
3. Role-based access control (admin, user, team roles)

#### Assessment System
- **Templates**: Pre-built assessment frameworks (Big Five, MBTI, Enneagram, etc.)
- **Custom Assessments**: User-created assessments with questions and scoring
- **AI Processing**: Personality framework processors in `/ai/processors/`

#### Team Management
- Organizations → Teams → Members hierarchy
- Team-based assessment analytics and insights
- Role-based permissions within teams

## Important File Locations

### Backend Core Files
- `app/main.py` - FastAPI application entry point
- `app/core/config.py` - Settings management (uses pydantic-settings)
- `app/core/database.py` - Database connection setup
- `app/api/v1/routes.py` - API router aggregation
- `app/db/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - Business logic layer

### Frontend Core Files
- `frontend/src/App.tsx` - Main application with routing
- `frontend/src/contexts/` - React context providers
- `frontend/src/services/` - API service layer
- `frontend/src/types/` - TypeScript definitions
- `frontend/vite.config.ts` - Build configuration with path aliases

### AI Engine
- `ai/processors/processors_base.py` - Abstract base processor
- `ai/processors/big_five.py` - Big Five personality implementation
- `ai/processors/mbti_processor.py` - MBTI assessment processor

## Configuration

### Environment Files
- `.env.dev` - Development environment variables
- `.env.prod` - Production environment variables
- `frontend/.env.example` - Frontend environment template

### Key Settings
- Database: PostgreSQL with async SQLAlchemy 2.0
- Cache: Redis for sessions and API caching
- CORS: Configured for ports 3000, 5173, 5174 in development
- Authentication: JWT with 30-minute access tokens

## Database Schema

### Core Models
- **Users**: Basic user information with authentication
- **Organizations**: Top-level organization structure
- **Teams**: Team management within organizations
- **Assessments**: Assessment definitions and templates
- **Responses**: User assessment responses and scores
- **Audit Logs**: Comprehensive audit trail

### Relationships
- Organizations have many Teams
- Teams have many Members (Users)
- Assessments belong to Organizations or Teams
- Users have many Responses across Assessments

## Testing Strategy

### Backend Testing
- **Unit Tests**: Service layer and CRUD operations
- **Integration Tests**: API endpoints with database
- **Test Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
- **Fixtures**: Database setup in `tests/conftest.py`

### Frontend Testing
- **Component Tests**: React component testing with Testing Library
- **Service Tests**: API service function testing
- **User Interaction Tests**: User event simulation

## AI Assessment Frameworks

The system supports multiple psychological assessment frameworks:
- **Big Five** (OCEAN model) - Personality traits
- **MBTI** - Myers-Briggs Type Indicator
- **Enneagram** - Personality types
- **Predictive Index** - Behavioral assessment
- **Clifton Strengths** - Strengths-based assessment
- **Social Styles** - Behavioral patterns

Each framework extends the base processor class in `ai/processors/processors_base.py`.

## Development Notes

### Path Aliases (Frontend)
- `@/` → `src/`
- `@components/` → `src/components/`
- `@pages/` → `src/pages/`
- `@services/` → `src/services/`

### Database Migrations
Always review auto-generated migrations before applying:
```bash
alembic revision --autogenerate -m "description"
# Review generated file in alembic/versions/
alembic upgrade head
```

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### SSL Configuration
SSL certificates are generated via `ssl_init_script.sh` and stored in `certs/` directory.