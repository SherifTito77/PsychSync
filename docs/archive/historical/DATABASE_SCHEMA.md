# PsychSync Database Schema Documentation

**Document Owner:** Data Team
**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Database:** PostgreSQL 16
**ORM:** SQLAlchemy 2.0 (Async)

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Models](#core-models)
3. [Relationship Diagram](#relationship-diagram)
4. [Detailed Schema](#detailed-schema)
5. [Indexes and Performance](#indexes-and-performance)
6. [Security and Compliance](#security-and-compliance)
7. [Migration Strategy](#migration-strategy)

---

## Architecture Overview

### Database Design Principles

**Service-Oriented Monolithic Architecture:**
- Single PostgreSQL database with logical separation
- Connection pooling for performance
- Async operations for scalability
- Row-level security for multi-tenancy

**Key Patterns:**
- **Repository Pattern:** CRUD classes encapsulate database operations
- **Service Layer:** Business logic separated from data access
- **Dual Models:** Standard + Secure models for enterprise features
- **Soft Delete:** Logical deletion with audit trail
- **Audit Logging:** Comprehensive change tracking

### Database Statistics

**Scale (as of 2025-12-27):**
- Total Tables: 45+
- Total Indexes: 120+
- Database Size: ~100 GB (production)
- Growth Rate: ~5 GB/month

---

## Core Models

### Model Hierarchy

```
BaseModel
    ├── User
    ├── Organization
    │   └── Team
    │       └── TeamMember
    ├── Assessment
    │   ├── AssessmentSection
    │   │   └── AssessmentQuestion
    │   └── AssessmentResponse
    ├── Response
    ├── AuditLog
    └── Analytics
```

### Key Entities

**Users & Organizations:**
- Users: Core user accounts with authentication
- Organizations: Top-level business entities
- Teams: Organizational units within organizations
- TeamMembers: User membership in teams

**Assessments:**
- Assessments: Assessment definitions and templates
- AssessmentSections: Logical groupings of questions
- AssessmentQuestions: Individual questions
- AssessmentResponses: User assessment completions

**Responses & Scoring:**
- Responses: Individual question answers
- Analytics: Aggregated insights and metrics

**Security & Audit:**
- AuditLogs: Complete audit trail
- SecureUser: Enhanced security model (enterprise)

---

## Relationship Diagram

### Entity Relationship Overview

```
┌─────────────┐         ┌──────────────┐
│  Users      │────────▶│ Organizations│
│             │         │              │
└─────────────┘         └──────────────┘
       │                       │
       │                       │
       ▼                       ▼
┌─────────────┐         ┌──────────────┐
│  TeamMember │────────▶│    Teams     │
│             │         │              │
└─────────────┘         └──────────────┘
                               │
                               │
                               ▼
                        ┌──────────────┐
                        │ Assessments  │
                        │              │
                        └──────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ Sections │   │ Responses│   │Analytics │
         └──────────┘   └──────────┘   └──────────┘
              │
              ▼
       ┌──────────┐
       │Questions │
       └──────────┘
```

---

## Detailed Schema

### 1. Users & Authentication

#### Table: `users`

**Purpose:** Core user account information

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique user identifier |
| `email` | CITEXT | UNIQUE, NOT NULL, INDEXED | User email (case-insensitive) |
| `password_hash` | VARCHAR(255) | NOT NULL | Argon2 hashed password |
| `full_name` | VARCHAR(255) | NOT NULL | User's full name |
| `role` | ENUM | NOT NULL, DEFAULT 'USER' | User role (USER/TEAM_LEAD/ADMIN) |
| `organization_id` | UUID | FK → organizations.id, INDEXED | Organization membership |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Account status |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT false | Email verification status |
| `is_superuser` | BOOLEAN | NOT NULL, DEFAULT false | Superuser privileges |
| `timezone` | VARCHAR(50) | DEFAULT 'UTC' | User timezone |
| `locale` | VARCHAR(10) | DEFAULT 'en-US' | User locale |
| `preferences` | JSONB | DEFAULT '{}' | User preferences |
| `last_login` | TIMESTAMP WITH TIME ZONE | NULLABLE | Last successful login |
| `two_factor_enabled` | BOOLEAN | DEFAULT false | 2FA status |
| `two_factor_secret` | VARCHAR(255) | NULLABLE | TOTP secret |
| `two_factor_recovery_codes` | TEXT[] | NULLABLE | Backup recovery codes |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update time |

**Indexes:**
- `PRIMARY KEY` on `id`
- `UNIQUE INDEX` on `email`
- `INDEX` on `organization_id` (foreign key)
- `INDEX` on `is_active` (for filtering active users)
- `INDEX` on `created_at` (for time-based queries)

**Relationships:**
- One-to-Many with `team_members` (user can be in multiple teams)
- One-to-Many with `assessments` (user can create multiple assessments)
- One-to-Many with `assessment_responses` (user can complete multiple assessments)
- Many-to-One with `organizations` (user belongs to one organization)

**Security:**
- Password hashed using Argon2id with salt
- Email stored as CITEXT for case-insensitive unique constraint
- 2FA secrets stored encrypted (application-level encryption)

#### Table: `users_secure` (Enterprise)

**Purpose:** Extended user model with enhanced security and compliance features

**Additional Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique identifier |
| `user_id` | UUID | FK → users.id, UNIQUE | Link to base user |
| `data_classification` | ENUM | DEFAULT 'PUBLIC' | Data sensitivity level |
| `encrypted_fields` | JSONB | | Fields requiring encryption |
| `risk_score` | DECIMAL(5,2) | DEFAULT 0.00 | Account risk score (0-100) |
| `device_fingerprint` | VARCHAR(255) | NULLABLE | Known device fingerprint |
| `session_count` | INTEGER | DEFAULT 0 | Active session count |
| `last_password_change` | TIMESTAMP WITH TIME ZONE | | Last password update |
| `password_history` | JSONB | | Previous password hashes |
| `failed_login_attempts` | INTEGER | DEFAULT 0 | Failed login counter |
| `account_locked_until` | TIMESTAMP WITH TIME ZONE | NULLABLE | Lock expiration |
| `compliance_flags` | JSONB | | GDPR/CCPA compliance data |

**Enterprise Features:**
- Field-level encryption for PII/PHI data
- Device tracking for fraud detection
- Account lockout after failed attempts
- Password history and rotation enforcement
- GDPR right-to-be-forgotten support

### 2. Organizations & Teams

#### Table: `organizations`

**Purpose:** Top-level business entity for multi-tenancy

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique organization ID |
| `name` | VARCHAR(255) | NOT NULL | Organization name |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |

**Relationships:**
- One-to-Many with `users` (organization has many users)
- One-to-Many with `teams` (organization has many teams)
- One-to-Many with `assessments` (organization has assessments)

#### Table: `organizations_secure` (Enterprise)

**Additional Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `compliance_frameworks` | JSONB | HIPAA, GDPR, SOX, etc. |
| `data_region` | VARCHAR(10) | Geographic data storage |
| `encryption_key_id` | VARCHAR(255) | KMS key identifier |
| `audit_log_retention_days` | INTEGER | Audit retention policy |
| `sso_enabled` | BOOLEAN | Single sign-on status |
| `sso_config` | JSONB | SSO configuration |
| `ip_whitelist` | TEXT[] | Allowed IP ranges |
| `security_questions_enabled` | BOOLEAN | Security questions flag |

#### Table: `teams`

**Purpose:** Organizational units within organizations

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique team ID |
| `name` | TEXT | NOT NULL | Team name |
| `description` | TEXT | NULLABLE | Team description |
| `organization_id` | UUID | FK → organizations.id, NOT NULL, INDEXED | Parent organization |
| `created_by_id` | UUID | FK → users.id, NOT NULL | Creator user ID |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `INDEX` on `organization_id, created_at` (team listings)
- `INDEX` on `created_by_id, created_at` (user's created teams)
- `INDEX` on `name` (team search)

**Relationships:**
- Many-to-One with `organizations` (team belongs to organization)
- One-to-Many with `team_members` (team has many members)
- One-to-Many with `assessments` (team has assessments)

#### Table: `team_members`

**Purpose:** User membership in teams with roles

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique membership ID |
| `team_id` | UUID | FK → teams.id, NOT NULL | Team reference |
| `user_id` | UUID | FK → users.id, NOT NULL | User reference |
| `role` | ENUM | NOT NULL, DEFAULT 'MEMBER' | Member role (OWNER/ADMIN/MEMBER) |
| `joined_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Join timestamp |

**Constraints:**
- `UNIQUE(team_id, user_id)` - User can only be member once per team

**Relationships:**
- Many-to-One with `teams` (membership belongs to team)
- Many-to-One with `users` (membership belongs to user)

**Roles:**
- `OWNER`: Full control, can delete team
- `ADMIN`: Can manage members and assessments
- `MEMBER`: Can participate in assessments

### 3. Assessments

#### Table: `assessments`

**Purpose:** Assessment definitions and configurations

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique assessment ID |
| `title` | VARCHAR(255) | NOT NULL | Assessment title |
| `description` | TEXT | NULLABLE | Assessment description |
| `category` | ENUM | NOT NULL | PERSONALITY/SKILLS/BEHAVIORAL/COGNITIVE |
| `status` | ENUM | NOT NULL, DEFAULT 'DRAFT' | DRAFT/PUBLISHED/ARCHIVED |
| `framework_code` | VARCHAR(50) | NULLABLE | BIG_FIVE/MBTI/ENNEAGRAM/etc |
| `created_by_id` | UUID | FK → users.id, NOT NULL, INDEXED | Creator user |
| `team_id` | UUID | FK → teams.id, NULLABLE, INDEXED | Owning team |
| `organization_id` | UUID | FK → organizations.id, NULLABLE, INDEXED | Owning organization |
| `started_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Assessment start time |
| `completed_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Completion time |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `INDEX` on `created_by_id`
- `INDEX` on `team_id`
- `INDEX` on `organization_id`
- `INDEX` on `status`
- `INDEX` on `category`
- `INDEX` on `framework_code`
- `COMPOSITE INDEX` on `(organization_id, status, created_at)`

**Relationships:**
- Many-to-One with `users` (created by user)
- Many-to-One with `teams` (owned by team)
- Many-to-One with `organizations` (owned by organization)
- One-to-Many with `assessment_sections` (has sections)
- One-to-Many with `assessment_responses` (has responses)

**Status Flow:**
```
DRAFT → PUBLISHED → ARCHIVED
   ↑         ↓
   └─────────┘ (can edit while draft)
```

#### Table: `assessment_sections`

**Purpose:** Logical groupings of questions within assessments

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique section ID |
| `assessment_id` | UUID | FK → assessments.id, NOT NULL, INDEXED | Parent assessment |
| `title` | VARCHAR(255) | NOT NULL | Section title |
| `description` | TEXT | NULLABLE | Section description |
| `order` | INTEGER | NOT NULL, DEFAULT 0 | Display order |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Relationships:**
- Many-to-One with `assessments` (section belongs to assessment)
- One-to-Many with `assessment_questions` (section has questions)

#### Table: `assessment_questions`

**Purpose:** Individual assessment questions

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique question ID |
| `section_id` | UUID | FK → assessment_sections.id, NOT NULL, INDEXED | Parent section |
| `question_type` | VARCHAR(50) | NOT NULL | LIKERT/MULTIPLE_CHOICE/OPEN/etc |
| `question_text` | TEXT | NOT NULL | Question wording |
| `order` | INTEGER | NOT NULL, DEFAULT 0 | Display order |
| `is_required` | BOOLEAN | NOT NULL, DEFAULT true | Required flag |
| `config` | JSONB | DEFAULT '{}' | Question configuration |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Config JSONB Structure:**
```json
{
  "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
  "scale": [1, 2, 3, 4, 5],
  "reverse_scored": false,
  "dimension": "openness",
  "weight": 1.0
}
```

**Relationships:**
- Many-to-One with `assessment_sections` (question belongs to section)
- One-to-Many with `responses` (question has answers)

### 4. Responses & Analytics

#### Table: `assessment_responses`

**Purpose:** Assessment completion records

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique response ID |
| `assessment_id` | UUID | FK → assessments.id, NOT NULL, INDEXED | Assessment reference |
| `respondent_id` | UUID | FK → users.id, NOT NULL, INDEXED | User who responded |
| `status` | ENUM | NOT NULL, DEFAULT 'IN_PROGRESS' | IN_PROGRESS/COMPLETED/ABANDONED |
| `responses` | JSONB | NOT NULL | Question-answer mappings |
| `started_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Start time |
| `completed_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Completion time |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Responses JSONB Structure:**
```json
{
  "q1": 5,
  "q2": 4,
  "q3": 3,
  "response_time_ms": 300000,
  "device_info": {
    "user_agent": "...",
    "screen_width": 1920
  }
}
```

**Relationships:**
- Many-to-One with `assessments` (response belongs to assessment)
- Many-to-One with `users` (response by user)

#### Table: `responses`

**Purpose:** Individual question answers with scoring

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique response ID |
| `assessment_id` | UUID | FK → assessments.id, NOT NULL, INDEXED | Assessment reference |
| `user_id` | UUID | FK → users.id, NOT NULL, INDEXED | User who answered |
| `question_id` | UUID | FK → assessment_questions.id, NOT NULL, INDEXED | Question reference |
| `answer_text` | TEXT | NULLABLE | Text answer |
| `answer_value` | INTEGER | NULLABLE | Numeric answer (for scales) |
| `answer_data` | JSONB | NULLABLE | Complex answer data |
| `score` | DECIMAL(5,2) | NULLABLE | Calculated score |
| `normalized_score` | DECIMAL(5,2) | NULLABLE | Score normalized 0-1 |
| `response_time_ms` | INTEGER | NULLABLE | Time to answer (ms) |
| `confidence_rating` | INTEGER | NULLABLE | Confidence 1-5 |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Answer timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Update timestamp |

**Relationships:**
- Many-to-One with `assessments` (answer belongs to assessment)
- Many-to-One with `users` (answer by user)
- Many-to-One with `assessment_questions` (answer to question)

#### Table: `analytics`

**Purpose:** Aggregated insights and metrics

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique analytics ID |
| `entity_type` | VARCHAR(50) | NOT NULL, INDEXED | user/team/organization/assessment |
| `entity_id` | UUID | NOT NULL, INDEXED | Entity reference |
| `analytics_type` | VARCHAR(50) | NOT NULL | Type of analytics |
| `category` | VARCHAR(50) | NULLABLE | Analytics category |
| `raw_data` | JSONB | NOT NULL | Raw input data |
| `processed_data` | JSONB | NOT NULL | Processed results |
| `insights` | JSONB | NOT NULL | Generated insights |
| `overall_score` | DECIMAL(5,2) | NULLABLE | Overall score 0-100 |
| `confidence_level` | DECIMAL(3,2) | NULLABLE | Confidence 0-1 |
| `trend_data` | JSONB | NULLABLE | Historical trends |
| `period_start` | TIMESTAMP WITH TIME ZONE | NOT NULL | Analysis period start |
| `period_end` | TIMESTAMP WITH TIME ZONE | NOT NULL | Analysis period end |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending/processing/completed/error |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Relationships:**
- Polymorphic relationship to `users`, `teams`, `organizations`, `assessments` via `entity_type` + `entity_id`

### 5. Audit & Security

#### Table: `audit_logs`

**Purpose:** Complete audit trail of system events

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique log ID |
| `organization_id` | UUID | FK → organizations.id, NULLABLE, INDEXED | Organization context |
| `actor_user_id` | UUID | FK → users.id, NOT NULL, INDEXED | Acting user |
| `action` | VARCHAR(255) | NOT NULL, INDEXED | Action performed |
| `entity` | VARCHAR(255) | NOT NULL, INDEXED | Entity type affected |
| `entity_id` | UUID | NOT NULL, INDEXED | Entity ID affected |
| `meta` | JSONB | DEFAULT '{}' | Additional metadata |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW(), INDEXED | Event timestamp |

**Meta JSONB Structure:**
```json
{
  "ip_address": "192.168.1.1",
  "user_agent": "...",
  "changes": {
    "old": {"name": "Old Name"},
    "new": {"name": "New Name"}
  },
  "reason": "User request"
}
```

**Indexes:**
- `INDEX` on `organization_id`
- `INDEX` on `actor_user_id`
- `INDEX` on `action`
- `INDEX` on `entity`
- `INDEX` on `entity_id`
- `INDEX` on `created_at`
- `COMPOSITE INDEX` on `(organization_id, created_at)`

---

## Indexes and Performance

### Index Strategy

**Primary Indexes:**
- All tables have primary key indexes on `id` (UUID)

**Foreign Key Indexes:**
- All foreign keys are indexed for JOIN performance

**Query Optimization Indexes:**
- Composite indexes for common query patterns
- Partial indexes for filtered queries
- Covering indexes for frequently accessed columns

### Index Examples

**Users Table:**
```sql
-- Email lookup (authentication)
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Organization members listing
CREATE INDEX idx_users_organization ON users(organization_id)
  WHERE is_active = true;

-- Active user filtering
CREATE INDEX idx_users_active ON users(is_active)
  WHERE is_active = true;

-- Recent users
CREATE INDEX idx_users_created ON users(created_at DESC);
```

**Assessments Table:**
```sql
-- User's assessments
CREATE INDEX idx_assessments_creator ON assessments(created_by_id, created_at DESC);

-- Team assessments
CREATE INDEX idx_assessments_team ON assessments(team_id, status, created_at DESC);

-- Organization assessments
CREATE INDEX idx_assessments_org ON assessments(organization_id, status, created_at DESC);

-- Published assessments
CREATE INDEX idx_assessments_published ON assessments(status, category)
  WHERE status = 'PUBLISHED';
```

**Assessment Responses Table:**
```sql
-- User's responses
CREATE INDEX idx_responses_user ON assessment_responses(respondent_id, created_at DESC);

-- Assessment responses
CREATE INDEX idx_responses_assessment ON assessment_responses(assessment_id, status);

-- In-progress responses
CREATE INDEX idx_responses_in_progress ON assessment_responses(status, started_at)
  WHERE status = 'IN_PROGRESS';
```

### Performance Tips

**1. Use JSONB Querying:**
```sql
-- Query JSONB field
SELECT * FROM assessments
WHERE config->>'framework' = 'BIG_FIVE';

-- Index JSONB field
CREATE INDEX idx_assessments_config_framework
  ON assessments((config->>'framework'));
```

**2. Use Partial Indexes:**
```sql
-- Only index active users
CREATE INDEX idx_active_users
  ON users(email)
  WHERE is_active = true;
```

**3. Use Composite Indexes:**
```sql
-- Common query pattern
CREATE INDEX idx_assessments_org_status_date
  ON assessments(organization_id, status, created_at DESC);
```

---

## Security and Compliance

### Data Encryption

**At Rest:**
- Database: PostgreSQL encryption at rest (AWS RDS)
- Application-level encryption for sensitive fields
- KMS key management for encryption keys

**In Transit:**
- TLS 1.3 for all connections
- Certificate pinning
- Encrypted backups

**Field-Level Encryption:**
```python
# Encrypted fields in SecureUser model
encrypted_fields = [
    'ssn',
    'address',
    'phone_number',
    'emergency_contact'
]
```

### GDPR Compliance

**Right to be Forgotten:**
```sql
-- Soft delete with anonymization
UPDATE users_secure
SET
  email = 'deleted-' || id || '@deleted.local',
  full_name = 'Deleted User',
  data_classification = 'ANONYMIZED',
  encrypted_fields = '{}'::jsonb
WHERE id = $1;
```

**Data Export:**
```sql
-- Export user data
SELECT
  u.*,
  json_agg(DISTINCT t.*) as teams,
  json_agg(DISTINCT ar.*) as responses
FROM users u
LEFT JOIN team_members tm ON tm.user_id = u.id
LEFT JOIN teams t ON t.id = tm.team_id
LEFT JOIN assessment_responses ar ON ar.respondent_id = u.id
WHERE u.id = $1
GROUP BY u.id;
```

### HIPAA Compliance

**PHI Handling:**
- Encrypted storage for protected health information
- Access logging for all PHI access
- Minimum necessary access principle
- Business associate agreements

**Audit Trail:**
```sql
-- All PHI access logged
INSERT INTO audit_logs (
  actor_user_id,
  action,
  entity,
  entity_id,
  meta
) VALUES (
  $1, -- user_id
  'VIEW_PHI',
  'user_secure',
  $2, -- entity_id
  jsonb_build_object(
    'access_reason', $3,
    'ip_address', $4
  )
);
```

---

## Migration Strategy

### Migration Tool: Alembic

**Migration Workflow:**
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review generated migration
3. Test migration in staging
4. Apply to production: `alembic upgrade head`
5. Verify migration success

**Example Migration:**
```python
# alembic/versions/001_add_user_preferences.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users',
        sa.Column('preferences',
                  sa.JSON(),
                  nullable=False,
                  server_default='{}')
    )
    op.create_index('idx_users_preferences',
                    'users',
                    ['preferences'],
                    postgresql_using='gin')

def downgrade():
    op.drop_index('idx_users_preferences', table_name='users')
    op.drop_column('users', 'preferences')
```

### Database Backups

**Automated Backups:**
- Full backups every 6 hours
- 30-day retention
- S3 storage with encryption
- Automated backup verification

**Restore Procedure:**
```bash
# List available backups
aws s3 ls s3://psychsync-postgres-backups/backups/production/

# Restore from backup
./scripts/restore-postgres-production.sh \
  --timestamp 20251227-120000 \
  --force
```

---

## Appendices

### A. Database Connection Examples

**Python (SQLAlchemy):**
```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/psychsync"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

**Python (Psycopg3):**
```python
import psycopg

conn = psycopg.connect(
    "postgresql://user:pass@host:5432/psychsync"
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users LIMIT 10")
```

**Command Line:**
```bash
psql -h localhost -U postgres -d psychsync
```

### B. Useful Queries

**Get user with teams:**
```sql
SELECT
  u.id,
  u.email,
  u.full_name,
  json_agg(
    json_build_object(
      'team_id', t.id,
      'team_name', t.name,
      'role', tm.role
    )
  ) as teams
FROM users u
LEFT JOIN team_members tm ON tm.user_id = u.id
LEFT JOIN teams t ON t.id = tm.team_id
WHERE u.id = $1
GROUP BY u.id;
```

**Get assessment statistics:**
```sql
SELECT
  a.id,
  a.title,
  a.framework_code,
  COUNT(ar.id) as response_count,
  AVG(ar.completed_at - ar.started_at) as avg_completion_time
FROM assessments a
LEFT JOIN assessment_responses ar ON ar.assessment_id = a.id
  AND ar.status = 'COMPLETED'
WHERE a.organization_id = $1
GROUP BY a.id, a.title, a.framework_code;
```

**Find orphaned records:**
```sql
-- Responses without assessments
SELECT ar.id
FROM assessment_responses ar
LEFT JOIN assessments a ON a.id = ar.assessment_id
WHERE a.id IS NULL;
```

### C. Schema Diagrams

**ER Diagram Tool:**
Generate with:
```bash
# Install schemaer
pip install schemaer

# Generate diagram
schemaer -d postgresql://user:pass@host:5432/psychsync \
  -o docs/DATABASE_ERD.png
```

### D. Related Documentation

- **API Documentation:** `docs/api/OPENAPI_SPECIFICATION.yaml`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Deployment:** `docs/sops/PRODUCTION_DEPLOYMENT_SOP.md`
- **Backup SOP:** `docs/BACKUP_SLA_REQUIREMENTS.md`

---

**Document Status:** ✅ Approved

**Next Review Date:** 2026-06-27 (6 months)

**Maintained By:** Data Team

**Change Log:**
- Version 1.0.0 (2025-12-27): Initial comprehensive schema documentation
