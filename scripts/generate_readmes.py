#!/usr/bin/env python3
"""
Mass README Generator for PsychSync
Generates comprehensive documentation for all directories missing READMEs
"""

import os
from pathlib import Path

# Directory documentation templates
README_TEMPLATES = {
    "app/api/dependencies": {
        "title": "API Dependencies",
        "description": "FastAPI dependency injection functions for authentication, database sessions, and common endpoint dependencies.",
        "purpose": "Provides reusable dependency functions for FastAPI endpoints using the `Depends()` pattern. Centralizes authentication, authorization, and resource access logic.",
        "key_files": [
            (
                "auth.py",
                "Authentication dependencies - get_current_user, get_current_active_user, require_role",
            ),
            ("__init__.py", "Package initialization and exports"),
        ],
        "usage": """```python
from fastapi import Depends
from app.api.dependencies.auth import get_current_user, get_current_active_user

@router.get("/users/me")
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user
```""",
        "sections": [
            "Authentication Flow",
            "Authorization & Role-Based Access",
            "Database Session Management",
            "Tenant Context Management",
            "Rate Limiting Dependencies",
        ],
    },
    "app/api/v1": {
        "title": "API v1 Router",
        "description": "Version 1 API router aggregation and configuration.",
        "purpose": "Central API router that aggregates all endpoint modules and applies common middleware, prefixes, and tags.",
        "key_files": [
            ("api.py", "Main API router aggregating all endpoint modules"),
            ("routes.py", "Route configuration and inclusion"),
            ("deps.py", "Shared dependencies for v1 endpoints"),
        ],
        "usage": """```python
from app.api.v1.api import api_router

app.include_router(api_router, prefix="/api/v1")
```""",
        "sections": [
            "Router Configuration",
            "Endpoint Modules",
            "Common Middleware",
            "API Versioning Strategy",
        ],
    },
    "app/api/v1/endpoints": {
        "title": "API Endpoint Modules",
        "description": "Individual FastAPI endpoint modules organized by feature domain.",
        "purpose": "Contains all API endpoint implementations organized by business domain. Each module handles CRUD operations for specific resources.",
        "key_files": [
            ("auth.py", "Authentication endpoints - login, register, password reset"),
            ("users.py", "User management - CRUD, profile, settings"),
            ("teams.py", "Team management - create, update, member operations"),
            ("assessments.py", "Assessment CRUD - create, update, delete, duplicate"),
            ("responses.py", "Assessment response submission and management"),
            ("templates.py", "Assessment template management"),
            ("predictions.py", "AI-powered predictive analytics endpoints"),
            ("optimizer.py", "Team optimization recommendations"),
            ("hris_connector.py", "HRIS system integration endpoints"),
            ("slack.py", "Slack integration webhooks and commands"),
            ("data_export.py", "Data export and GDPR compliance"),
            ("analytics.py", "Analytics and reporting endpoints"),
            ("admin.py", "Administrative operations"),
        ],
        "usage": """```python
from fastapi import APIRouter, Depends
from app.api.v1.endpoints.users import router as users_router

api_router.include_router(users_router, prefix="/users", tags=["users"])
```""",
        "sections": [
            "Authentication Endpoints",
            "User Management",
            "Team Management",
            "Assessment System",
            "Analytics & Reporting",
            "Integrations",
            "Administrative Functions",
        ],
    },
    "app/crud": {
        "title": "CRUD Operations Layer",
        "description": "Database CRUD (Create, Read, Update, Delete) operations using SQLAlchemy.",
        "purpose": "Provides a clean abstraction layer between API endpoints and the database. Encapsulates all database access logic using SQLAlchemy's async patterns.",
        "key_files": [
            ("crud_user.py", "User CRUD operations"),
            ("organization.py", "Organization CRUD operations"),
            ("tenant_aware.py", "Base class for tenant-scoped CRUD operations"),
            ("crud_code_quality.py", "Code quality metrics CRUD"),
            ("crud_sql_audit.py", "SQL query audit logging CRUD"),
            ("crud_query_performance.py", "Query performance tracking CRUD"),
            ("crud_build_analysis.py", "Build analysis data CRUD"),
            ("crud_caching_config.py", "Caching configuration CRUD"),
            ("crud_breaking_changes.py", "Breaking changes tracking CRUD"),
        ],
        "usage": """```python
from app.crud.crud_user import user_crud
from app.db.models import User

async def get_user(db: AsyncSession, user_id: int):
    return await user_crud.get(db, id=user_id)
```""",
        "sections": [
            "CRUD Base Classes",
            "User Operations",
            "Organization Operations",
            "Tenant-Aware Operations",
            "Analytics CRUD",
            "Product Operations CRUD",
        ],
    },
    "app/schemas": {
        "title": "Pydantic Schemas",
        "description": "Request/response validation schemas using Pydantic.",
        "purpose": "Defines data validation schemas for API requests and responses. Ensures type safety, validation, and automatic OpenAPI documentation generation.",
        "key_files": [
            ("user.py", "User schemas - UserCreate, UserUpdate, UserResponse"),
            ("auth.py", "Authentication schemas - login, register, token"),
            ("team.py", "Team and team member schemas"),
            ("assessment.py", "Assessment schemas"),
            ("response.py", "Assessment response schemas"),
            ("prediction.py", "Prediction result schemas"),
            ("team_optimization.py", "Team optimization schemas"),
            ("user_service.py", "User service metrics schemas"),
            ("onboarding.py", "Onboarding progress schemas"),
            ("team_personality.py", "Team personality analysis schemas"),
            ("code_quality.py", "Code quality metric schemas"),
            ("jira_integration.py", "Jira integration schemas"),
            ("sql_audit.py", "SQL audit schemas"),
            ("query_performance.py", "Query performance schemas"),
            ("build_analysis.py", "Build analysis schemas"),
            ("caching_config.py", "Caching configuration schemas"),
            ("breaking_changes.py", "Breaking changes schemas"),
        ],
        "usage": """```python
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserCreate, UserResponse

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
```""",
        "sections": [
            "Base Schema Classes",
            "Authentication Schemas",
            "User & Team Schemas",
            "Assessment Schemas",
            "Analytics Schemas",
            "Integration Schemas",
            "Product Operations Schemas",
        ],
    },
    "app/models": {
        "title": "Database Models (Legacy)",
        "description": "Legacy database models directory. New models should go in app/db/models/.",
        "purpose": "Contains older database model definitions. This directory is being phased out in favor of app/db/models/.",
        "key_files": [],
        "usage": """```python
# Prefer importing from app.db.models instead:
from app.db.models import User
```""",
        "sections": ["Migration Status", "Deprecated Models"],
    },
    "app/repositories": {
        "title": "Repository Pattern Implementation",
        "description": "Repository pattern for data access abstraction.",
        "purpose": "Provides repository classes that abstract database operations. Implements domain-driven design principles for data access.",
        "key_files": [],
        "usage": """```python
from app.repositories.user_repository import UserRepository

repo = UserRepository(db)
user = await repo.find_by_id(user_id)
```""",
        "sections": [
            "Repository Interfaces",
            "Implementation Classes",
            "Domain Repositories",
        ],
    },
    "app/assessments": {
        "title": "Assessment Domain Logic",
        "description": "Core assessment business logic and processing.",
        "purpose": "Contains assessment framework implementations, scoring algorithms, and assessment processing logic.",
        "key_files": [],
        "usage": """```python
from app.assessments.processor import AssessmentProcessor

processor = AssessmentProcessor()
results = await processor.process(responses)
```""",
        "sections": [
            "Assessment Frameworks",
            "Scoring Algorithms",
            "Response Processing",
            "Validation Logic",
        ],
    },
    "app/domain": {
        "title": "Domain Layer",
        "description": "Core domain entities and business rules following Domain-Driven Design.",
        "purpose": "Contains domain entities, value objects, domain services, and repository interfaces. Implements the heart of the business logic.",
        "key_files": [],
        "usage": """```python
from app.domain.entities import User, Team
from app.domain.value_objects import Email, TeamId

user = User(email=Email("user@example.com"))
```""",
        "sections": [
            "Domain Entities",
            "Value Objects",
            "Domain Services",
            "Domain Events",
            "Repository Interfaces",
        ],
    },
    "app/domain/entities": {
        "title": "Domain Entities",
        "description": "Core business entities with identity and behavior.",
        "purpose": "Defines the fundamental business objects with rich behavior and identity.",
        "key_files": [],
        "usage": """```python
from app.domain.entities import User

user = User(email="user@example.com", full_name="John Doe")
user.update_profile(new_name="John Smith")
```""",
        "sections": [
            "User Entity",
            "Team Entity",
            "Assessment Entity",
            "Entity Base Classes",
        ],
    },
    "app/domain/events": {
        "title": "Domain Events",
        "description": "Domain event definitions and handlers.",
        "purpose": "Implements domain events pattern for decoupling and eventual consistency.",
        "key_files": [],
        "usage": """```python
from app.domain.events import UserRegisteredEvent

event = UserRegisteredEvent(user_id=123, email="user@example.com")
await publish(event)
```""",
        "sections": ["Event Definitions", "Event Handlers", "Event Publishing"],
    },
    "app/domain/repositories": {
        "title": "Repository Interfaces",
        "description": "Abstract repository interfaces for domain layer.",
        "purpose": "Defines contracts for data access without implementation details.",
        "key_files": [],
        "usage": """```python
from app.domain.repositories import UserRepository

class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: int) -> User:
        pass
```""",
        "sections": [
            "Repository Interfaces",
            "Query Specifications",
            "Implementation Contracts",
        ],
    },
    "app/domain/services": {
        "title": "Domain Services",
        "description": "Stateless business logic that doesn't naturally fit in entities.",
        "purpose": "Contains business logic operations that span multiple entities or involve external services.",
        "key_files": [],
        "usage": """```python
from app.domain.services.team_composition import TeamCompositionService

service = TeamCompositionService()
optimal = service.calculate_optimal_composition(team, candidates)
```""",
        "sections": [
            "Team Composition Services",
            "Assessment Services",
            "Analytics Services",
            "Validation Services",
        ],
    },
    "app/domain/value_objects": {
        "title": "Value Objects",
        "description": "Immutable value objects with no identity.",
        "purpose": "Defines concepts identified by their attributes rather than identity.",
        "key_files": [],
        "usage": """```python
from app.domain.value_objects import Email, TeamId

email = Email("user@example.com")
team_id = TeamId("team-123")
```""",
        "sections": [
            "Email Value Object",
            "Team Identifiers",
            "Assessment Scores",
            "Validation Value Objects",
        ],
    },
    "app/application": {
        "title": "Application Layer",
        "description": "Application services and use cases orchestrating domain logic.",
        "purpose": "Contains application services that coordinate domain objects to fulfill use cases.",
        "key_files": [],
        "usage": """```python
from app.application.services.user_service import UserService

service = UserService()
await service.register_user(user_data)
```""",
        "sections": [
            "Application Services",
            "Use Cases",
            "Command Handlers",
            "Query Handlers",
        ],
    },
    "app/application/use_cases": {
        "title": "Use Case Implementations",
        "description": "Concrete use case implementations following Clean Architecture.",
        "purpose": "Encapsulates specific user interactions and business workflows.",
        "key_files": [],
        "usage": """```python
from app.application.use_cases.register_user import RegisterUserUseCase

use_case = RegisterUserUseCase(user_repo, email_service)
result = await use_case.execute(user_data)
```""",
        "sections": [
            "User Use Cases",
            "Team Use Cases",
            "Assessment Use Cases",
            "Analytics Use Cases",
        ],
    },
    "app/infrastructure": {
        "title": "Infrastructure Layer",
        "description": "External system integrations and technical implementations.",
        "purpose": "Contains implementations of domain interfaces, external service adapters, and technical infrastructure.",
        "key_files": [],
        "usage": """```python
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

repo = SqlAlchemyUserRepository(db)
```""",
        "sections": [
            "Repository Implementations",
            "External Service Adapters",
            "Persistence Implementations",
        ],
    },
    "app/infrastructure/models": {
        "title": "Infrastructure Models",
        "description": "Database models and technical infrastructure models.",
        "purpose": "Contains ORM models and other infrastructure-specific data structures.",
        "key_files": [],
        "usage": """```python
from app.infrastructure.models import UserRecord

record = UserRecord.from_domain_entity(user)
```""",
        "sections": ["ORM Models", "DTOs", "Mapping Utilities"],
    },
    "app/infrastructure/repositories": {
        "title": "Repository Implementations",
        "description": "Concrete repository implementations using SQLAlchemy.",
        "purpose": "Provides actual database access implementing domain repository interfaces.",
        "key_files": [],
        "usage": """```python
from app.infrastructure.repositories.user_repository import PostgresUserRepository

repo = PostgresUserRepository(session)
user = await repo.find_by_id(user_id)
```""",
        "sections": [
            "SQLAlchemy Repositories",
            "Cache-Aside Repositories",
            "Repository Decorators",
        ],
    },
    "app/integrations": {
        "title": "External Integrations",
        "description": "Third-party service integrations and adapters.",
        "purpose": "Contains adapters and clients for external services like HRIS, Slack, email providers.",
        "key_files": [],
        "usage": """```python
from app.integrations.slack import SlackClient

slack = SlackClient(token="xoxb-...")
await slack.send_message(channel="#general", text="Hello")
```""",
        "sections": [
            "Slack Integration",
            "HRIS Integration",
            "Email Providers",
            "Authentication Providers",
        ],
    },
    "app/integrations/hris": {
        "title": "HRIS System Integration",
        "description": "Human Resource Information System integrations.",
        "purpose": "Provides adapters for connecting to various HRIS platforms like BambooHR, Workday, etc.",
        "key_files": [],
        "usage": """```python
from app.integrations.hris.bamboohr import BambooHRClient

client = BambooHRClient(api_key="...")
employees = await client.get_employees()
```""",
        "sections": [
            "BambooHR Adapter",
            "Workday Adapter",
            "Unified HRIS Interface",
            "Sync Operations",
        ],
    },
    "app/integrations/slack": {
        "title": "Slack Integration",
        "description": "Slack API integration for notifications and bot functionality.",
        "purpose": "Handles Slack webhooks, slash commands, and interactive components.",
        "key_files": [],
        "usage": """```python
from app.integrations.slack.webhook import send_slack_notification

await send_slack_notification(
    channel="#team-updates",
    message="Assessment completed!"
)
```""",
        "sections": [
            "Slack Webhook Client",
            "Slash Command Handlers",
            "Interactive Components",
            "Event Handlers",
        ],
    },
    "app/middleware": {
        "title": "Custom Middleware",
        "description": "FastAPI middleware for cross-cutting concerns.",
        "purpose": "Contains custom middleware for logging, security, metrics, and request/response processing.",
        "key_files": [],
        "usage": """```python
from app.middleware.request_logging import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
```""",
        "sections": [
            "Request Logging",
            "Error Handling",
            "Security Headers",
            "Performance Metrics",
            "Rate Limiting",
        ],
    },
    "app/security": {
        "title": "Security Module",
        "description": "Security utilities and implementations.",
        "purpose": "Contains authentication, authorization, cryptography, and security-related utilities.",
        "key_files": [],
        "usage": """```python
from app.security.password import hash_password, verify_password

hashed = hash_password("plain-password")
valid = verify_password("plain-password", hashed)
```""",
        "sections": [
            "Password Hashing",
            "Token Generation",
            "Encryption Utilities",
            "Security Validators",
        ],
    },
    "app/security/logging": {
        "title": "Security Logging",
        "description": "Security-specific logging and audit trails.",
        "purpose": "Provides structured logging for security events, authentication attempts, and authorization failures.",
        "key_files": [],
        "usage": """```python
from app.security.logging import log_security_event

log_security_event(
    event_type="login_success",
    user_id=123,
    ip_address="192.168.1.1"
)
```""",
        "sections": [
            "Security Event Logging",
            "Audit Trail",
            "Alerting",
            "Compliance Reporting",
        ],
    },
    "app/core/config": {
        "title": "Configuration Management",
        "description": "Application configuration using Pydantic Settings.",
        "purpose": "Centralized configuration management with environment variable support.",
        "key_files": [],
        "usage": """```python
from app.core.config import settings

database_url = settings.DATABASE_URL
secret_key = settings.SECRET_KEY
```""",
        "sections": [
            "Settings Classes",
            "Environment Variables",
            "Configuration Validation",
            "Secrets Management",
        ],
    },
    "app/dependency_injection": {
        "title": "Dependency Injection Container",
        "description": "Dependency injection setup and management.",
        "purpose": "Configures and manages dependency injection for the application.",
        "key_files": [],
        "usage": """```python
from app.dependency_injection import container

user_service = container.user_service()
```""",
        "sections": [
            "Container Configuration",
            "Service Registration",
            "Lifecycle Management",
        ],
    },
    "app/data": {
        "title": "Data Directory",
        "description": "Static data files and seed data.",
        "purpose": "Contains seed data, reference data, and static datasets.",
        "key_files": [],
        "usage": """```python
# Seed data is loaded during database initialization
```""",
        "sections": ["Seed Data", "Reference Data", "Static Datasets"],
    },
    "app/events": {
        "title": "Event System",
        "description": "Event bus and event handling infrastructure.",
        "purpose": "Implements publish-subscribe pattern for domain events.",
        "key_files": [],
        "usage": """```python
from app.events import publish, subscribe

@subscribe(UserRegisteredEvent)
async def handle_user_registered(event):
    send_welcome_email(event.email)

await publish(UserRegisteredEvent(user_id=123))
```""",
        "sections": ["Event Bus", "Event Handlers", "Event Store", "Replay Mechanisms"],
    },
    "app/etl": {
        "title": "ETL Pipelines",
        "description": "Extract, Transform, Load pipelines for data processing.",
        "purpose": "Contains data processing pipelines for imports, exports, and data migrations.",
        "key_files": [],
        "usage": """```python
from app.etl.pipelines.import_users import UserImportPipeline

pipeline = UserImportPipeline(csv_file)
await pipeline.run()
```""",
        "sections": [
            "Import Pipelines",
            "Export Pipelines",
            "Data Transformations",
            "Validation Steps",
        ],
    },
    "app/factory": {
        "title": "Factory Pattern Implementations",
        "description": "Factory classes for object creation.",
        "purpose": "Implements Factory pattern for complex object creation.",
        "key_files": [],
        "usage": """```python
from app.factory.assessment_factory import AssessmentFactory

factory = AssessmentFactory()
assessment = factory.create_assessment(type="big_five")
```""",
        "sections": ["Assessment Factory", "Processor Factory", "Report Factory"],
    },
    "app/performance": {
        "title": "Performance Utilities",
        "description": "Performance monitoring and optimization utilities.",
        "purpose": "Contains caching, query optimization, and performance monitoring tools.",
        "key_files": [],
        "usage": """```python
from app.performance.cache import cached_result

@cached_result(ttl=3600)
async def expensive_operation(param):
    return await compute(param)
```""",
        "sections": [
            "Caching Utilities",
            "Query Optimization",
            "Performance Monitoring",
            "Profiling Tools",
        ],
    },
    "app/reports": {
        "title": "Report Generation",
        "description": "Report generation and formatting utilities.",
        "purpose": "Creates various reports from assessment data and analytics.",
        "key_files": [],
        "usage": """```python
from app.reports.team_report import TeamReportGenerator

generator = TeamReportGenerator()
report = await generator.generate(team_id=123)
```""",
        "sections": [
            "Team Reports",
            "Individual Reports",
            "Analytics Reports",
            "Export Formats",
        ],
    },
    "app/scripts": {
        "title": "Utility Scripts",
        "description": "Administrative and maintenance scripts.",
        "purpose": "Contains scripts for data migrations, maintenance tasks, and administrative operations.",
        "key_files": [],
        "usage": """```bash
python app/scripts/init_database.py
python app/scripts/cleanup_old_data.py
```""",
        "sections": [
            "Database Initialization",
            "Data Migration Scripts",
            "Maintenance Tasks",
            "Administrative Utilities",
        ],
    },
    "app/tasks": {
        "title": "Background Tasks",
        "description": "Asynchronous background task definitions.",
        "purpose": "Contains scheduled tasks and background job definitions.",
        "key_files": [],
        "usage": """```python
from app.tasks.email_tasks import send_daily_digest

await send_daily_digest.delay()
```""",
        "sections": [
            "Email Tasks",
            "Data Sync Tasks",
            "Cleanup Tasks",
            "Scheduled Jobs",
        ],
    },
    "app/testing": {
        "title": "Testing Utilities",
        "description": "Test helpers, fixtures, and utilities.",
        "purpose": "Provides common testing utilities and test data generators.",
        "key_files": [],
        "usage": """```python
from app.testing.fixtures import create_test_user
from app.testing.factories import UserFactory

user = UserFactory()
```""",
        "sections": [
            "Test Fixtures",
            "Test Factories",
            "Mock Helpers",
            "Test Data Generators",
        ],
    },
    "app/utils": {
        "title": "Utility Functions",
        "description": "General utility functions and helpers.",
        "purpose": "Contains reusable utility functions used across the application.",
        "key_files": [],
        "usage": """```python
from app.utils.date import utcnow
from app.utils.string import generate_random_string

now = utcnow()
token = generate_random_string(32)
```""",
        "sections": [
            "Date Utilities",
            "String Utilities",
            "Validation Helpers",
            "Conversion Utilities",
        ],
    },
    "app/services/optimizer": {
        "title": "Team Optimization Services",
        "description": "Team composition optimization algorithms.",
        "purpose": "Contains AI-powered optimization algorithms for team building.",
        "key_files": [],
        "usage": """```python
from app.services.optimizer.team_optimizer import TeamOptimizer

optimizer = TeamOptimizer()
recommendation = await optimizer.optimize_team(team_id=123)
```""",
        "sections": [
            "Team Composition Optimization",
            "Skill Gap Analysis",
            "Personality Matching",
            "Recommendation Engine",
        ],
    },
    "app/services/scoring": {
        "title": "Assessment Scoring Services",
        "description": "Assessment scoring and calculation services.",
        "purpose": "Implements scoring algorithms for various assessment frameworks.",
        "key_files": [],
        "usage": """```python
from app.services.scoring.big_five import BigFiveScorer

scorer = BigFiveScorer()
results = scorer.score(responses)
```""",
        "sections": [
            "Big Five Scoring",
            "MBTI Scoring",
            "Enneagram Scoring",
            "Custom Assessment Scoring",
        ],
    },
    "app/templates": {
        "title": "Template Directory",
        "description": "Email templates and document templates.",
        "purpose": "Contains templates for emails, reports, and documents.",
        "key_files": [],
        "usage": """```python
from app.templates.email import render_welcome_email

html = render_welcome_email(user_name="John")
```""",
        "sections": ["Email Templates", "Report Templates", "Document Templates"],
    },
    "app/templates/admin": {
        "title": "Admin Templates",
        "description": "Administrative interface templates.",
        "purpose": "Templates for admin panels and dashboards.",
        "key_files": [],
        "usage": """```python
from app.templates.admin import render_admin_dashboard

html = render_admin_dashboard(data=metrics)
```""",
        "sections": ["Dashboard Templates", "Admin Forms", "Admin Reports"],
    },
    "app/templates/docs": {
        "title": "Documentation Templates",
        "description": "Documentation generation templates.",
        "purpose": "Templates for generating user documentation and guides.",
        "key_files": [],
        "usage": """```python
from app.templates.docs import render_user_guide

html = render_user_guide(feature="assessments")
```""",
        "sections": ["User Guide Templates", "API Documentation", "Help Content"],
    },
    "app/templates/email": {
        "title": "Email Templates",
        "description": "HTML and text email templates.",
        "purpose": "Email templates for notifications, onboarding, and communications.",
        "key_files": [],
        "usage": """```python
from app.templates.email.welcome import render_welcome_email

html = render_welcome_email(user_name="John")
```""",
        "sections": [
            "Welcome Emails",
            "Notification Emails",
            "Onboarding Emails",
            "Transactional Emails",
        ],
    },
    "app/templates/email/old": {
        "title": "Legacy Email Templates",
        "description": "Deprecated email templates.",
        "purpose": "Old email templates kept for reference. Use app/templates/email/ instead.",
        "key_files": [],
        "usage": """```python
# These are deprecated. Use new templates instead.
```""",
        "sections": ["Deprecated Templates", "Migration Guide"],
    },
    "app/templates/emails": {
        "title": "Email Templates (Primary)",
        "description": "Primary email template directory.",
        "purpose": "Main email templates for all application communications.",
        "key_files": [],
        "usage": """```python
from app.templates.emails import render_email

html = render_email(template_name="welcome", context={"user": "John"})
```""",
        "sections": ["Notification Templates", "Welcome Templates", "Alert Templates"],
    },
    "app/templates/errors": {
        "title": "Error Page Templates",
        "description": "Error page templates for web interface.",
        "purpose": "Templates for displaying user-friendly error pages.",
        "key_files": [],
        "usage": """```python
from app.templates.errors import render_error_page

html = render_error_page(error_code=404)
```""",
        "sections": [
            "404 Not Found",
            "500 Server Error",
            "403 Forbidden",
            "Custom Error Pages",
        ],
    },
    "app/db/models": {
        "title": "Database Models",
        "description": "SQLAlchemy ORM model definitions.",
        "purpose": "Contains all database table definitions using SQLAlchemy ORM.",
        "key_files": [
            ("__init__.py", "Model exports and package initialization"),
            ("user.py", "User model definition"),
            ("organization.py", "Organization model"),
            ("team.py", "Team and TeamMember models"),
            ("framework.py", "Assessment framework model"),
            ("assessment.py", "Assessment models"),
            ("response.py", "Assessment response models"),
            ("analytics.py", "Analytics models"),
            ("employee_safety.py", "Employee safety models"),
            ("growth_trajectories.py", "Growth trajectory models"),
            ("intervention_effectiveness.py", "Intervention effectiveness models"),
            ("email_connection.py", "Email connection models"),
            ("communication_analysis.py", "Communication analysis models"),
            ("ab_testing.py", "A/B testing models"),
            ("feature_requests.py", "Feature request models"),
            ("churn_prediction.py", "Churn prediction models"),
            ("user_activation.py", "User activation models"),
            ("code_quality.py", "Code quality models"),
            ("jira_integration.py", "Jira integration models"),
        ],
        "usage": """```python
from app.db.models import User, Team, Organization
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(db: AsyncSession, email: str):
    user = User(email=email)
    db.add(user)
    await db.commit()
    return user
```""",
        "sections": [
            "Core Models",
            "Assessment Models",
            "Analytics Models",
            "Integration Models",
            "Product Operations Models",
            "Model Relationships",
            "Indexes and Constraints",
        ],
    },
    "app/db/seeds": {
        "title": "Database Seed Data",
        "description": "Seed data for database initialization.",
        "purpose": "Contains initial data for database seeding and testing.",
        "key_files": [],
        "usage": """```python
from app.db.seeds.seed_assessments import seed_assessments

await seed_assessments(db)
```""",
        "sections": [
            "Assessment Seeds",
            "Framework Seeds",
            "Demo Data",
            "Reference Data",
        ],
    },
    "app/db/sql": {
        "title": "SQL Scripts",
        "description": "Raw SQL scripts for database operations.",
        "purpose": "Contains SQL scripts for migrations, bulk operations, and complex queries.",
        "key_files": [],
        "usage": """```sql
-- Run custom SQL scripts directly
```""",
        "sections": [
            "Migration Scripts",
            "Batch Operations",
            "Performance Queries",
            "Maintenance Scripts",
        ],
    },
}


def generate_readme(directory: str, template: dict) -> str:
    """Generate README content from template."""
    title = template["title"]
    description = template["description"]
    purpose = template["purpose"]
    key_files = template["key_files"]
    usage = template["usage"]
    sections = template["sections"]

    readme = f"""# {title}

## Overview

{description}

## Purpose

{purpose}
"""

    if key_files:
        readme += "\n## Key Files\n\n"
        for filename, description in key_files:
            readme += f"- **`{filename}`**: {description}\n"

    readme += "\n## Usage\n\n"
    readme += usage
    readme += "\n\n"

    if sections:
        readme += "\n## Key Components\n\n"
        for section in sections:
            readme += f"- {section}\n"

    readme += """
## Related Documentation

- [Main README](../../../README.md)
- [API Documentation](../api/README.md)
- [Services Documentation](../services/README.md)
- [Database Documentation](../db/README.md)
- [Core Documentation](../core/README.md)

## Contributing

When adding new files to this directory, please:
1. Follow existing code patterns
2. Add comprehensive docstrings
3. Update this README with key changes
4. Ensure proper error handling
5. Add tests for new functionality

## Testing

Test files in this directory using:
```bash
pytest tests/path/to/this/directory/ -v
```
"""

    return readme


def main():
    """Generate all READMEs."""
    base_path = Path("/Users/sheriftito/Downloads/psychsync")

    created = 0
    skipped = 0

    for directory, template in README_TEMPLATES.items():
        dir_path = base_path / directory
        readme_path = dir_path / "README.md"

        # Check if directory exists
        if not dir_path.exists():
            print(f"⚠️  Directory does not exist: {directory}")
            skipped += 1
            continue

        # Check if README already exists
        if readme_path.exists():
            print(f"⏭️  README already exists: {directory}/README.md")
            skipped += 1
            continue

        # Create README
        try:
            content = generate_readme(directory, template)
            readme_path.write_text(content)
            print(f"✅ Created: {directory}/README.md")
            created += 1
        except Exception as e:
            print(f"❌ Failed to create {directory}/README.md: {e}")

    print(f"\n{'='*60}")
    print(f"README Generation Complete!")
    print(f"   Created: {created}")
    print(f"   Skipped: {skipped}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
