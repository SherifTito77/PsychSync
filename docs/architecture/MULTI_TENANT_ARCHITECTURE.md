# Multi-Tenant Architecture Plan

**Version:** 1.0
**Date:** 2026-01-10
**Status:** Proposed Architecture

---

## Executive Summary

PsychSync requires a robust multi-tenant architecture to support enterprise customers while maintaining data isolation, security, and performance. This document outlines the transition from the current single-tenant database design to a scalable multi-tenant SaaS platform.

---

## Current State Analysis

### Existing Multi-Tenant Components

```
Organizations (1:N)
├── Teams (1:N per Organization)
│   ├── Team Members (Users)
│   └── Team Assessments
└── Organization-Level Data
```

**Current Models:**
- ✅ `Organization` model exists
- ✅ `Team` model exists
- ⚠️ `User` model lacks `organization_id` foreign key
- ⚠️ No row-level security (RLS) implementation
- ⚠️ No tenant-specific data partitioning

---

## Proposed Multi-Tenant Architecture

### 1. Tenant Isolation Strategy

#### **Option A: Database per Tenant (Recommended for Enterprise)**
```
psychsync_tenant_{id}
├── users
├── assessments
├── responses
└── analytics
```

**Pros:**
- Maximum security isolation
- Performance per tenant
- Easy backup/restore per tenant

**Cons:**
- Higher infrastructure cost
- Complex schema migrations
- Cross-tenant reporting challenges

**Use Case:** Large enterprises (>500 users) with strict compliance requirements

---

#### **Option B: Schema per Tenant (Recommended for Mid-Market)**
```
psychsync_db
├── tenant_123_schema
│   ├── users
│   ├── assessments
│   └── responses
├── tenant_456_schema
│   ├── users
│   ├── assessments
│   └── responses
└── shared_schema
    ├── organizations
    └── billing
```

**Pros:**
- Good balance of isolation & efficiency
- Shared metadata tables
- Easier cross-tenant analytics
- Lower cost than database-per-tenant

**Cons:**
- Moderate infrastructure complexity
- Schema-level migrations required

**Use Case:** Mid-size companies (50-500 users) with good growth potential

---

#### **Option C: Row-Level Security (Recommended for SMB)**
```
psychsync_db
├── organizations (id PK)
├── users (organization_id FK + RLS)
├── assessments (organization_id FK + RLS)
└── responses (organization_id FK + RLS)
```

**Pros:**
- Lowest infrastructure cost
- Simple deployment
- Easy cross-tenant analytics
- Fast to implement

**Cons:**
- Risk of data leakage if RLS fails
- Performance degradation at scale
- No per-tenant backup/restore
- Compliance challenges

**Use Case:** Small companies (<50 users) with cost sensitivity

---

### **RECOMMENDED HYBRID APPROACH:**

```
┌─────────────────────────────────────────────────┐
│           Application Layer (FastAPI)            │
│  - Tenant Context Middleware                    │
│  - Request Router (by tenant)                   │
│  - API Gateway (multi-tenant aware)              │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              Data Access Layer                  │
│  ┌───────────────┐  ┌───────────────┐          │
│  │ SMB Tenants   │  │ Enterprise    │          │
│  │ (Shared DB)   │  │ (Dedicated    │          │
│  │ + RLS         │  │  Databases)   │          │
│  └───────────────┘  └───────────────┘          │
└─────────────────────────────────────────────────┘
```

---

## 2. Data Model Enhancements

### User Model (Multi-Tenant Ready)

```python
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_user_org', 'organization_id'),
        Index('idx_user_email_org', 'email', 'organization_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(CitextString, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Tenant-specific role
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    team_memberships = relationship("TeamMember", back_populates="user")
```

### Organization Model (Enhanced)

```python
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    # Tenant Configuration
    tier = Column(Enum(TenantTier), default=TenantTier.SMB)
    max_users = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=10)

    # Feature Flags
    enable_advanced_analytics = Column(Boolean, default=False)
    enable_api_access = Column(Boolean, default=False)
    enable_sso = Column(Boolean, default=False)

    # Billing
    subscription_id = Column(String(255))  # Stripe/Stripe ID
    billing_email = Column(CitextString)

    # Database Routing (for hybrid approach)
    database_host = Column(String(255))  # NULL = shared DB
    database_name = Column(String(255))  # NULL = shared DB
```

### Team Model (Multi-Tenant)

```python
class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)

    # Team Settings
    max_members = Column(Integer, default=20)

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    assessments = relationship("Assessment", back_populates="team")
```

---

## 3. Implementation Phases

### Phase 1: Foundation (Weeks 1-4)

**Goal:** Add tenant identification to all data models

```python
# Migration 001: Add organization_id to users
ALTER TABLE users ADD COLUMN organization_id UUID;
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'USER';
ALTER TABLE users ADD CONSTRAINT fk_users_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id);
```

**Deliverables:**
- ✅ Update User model with `organization_id`
- ✅ Add tenant context middleware
- ✅ Implement `get_current_tenant()` dependency
- ✅ Add tenant ID to all audit logs

**Code Example:**
```python
# app/api/v1/deps.py
async def get_current_tenant(request: Request) -> Organization:
    """Extract tenant from request context"""
    tenant_id = request.state.get("tenant_id")
    if not tenant_id:
        # Fall back to user's organization
        user = await get_current_user(request)
        tenant_id = user.organization_id

    tenant = await db.get(Organization, tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    return tenant
```

---

### Phase 2: Row-Level Security (Weeks 5-8)

**Goal:** Implement PostgreSQL RLS policies

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their organization's data
CREATE POLICY tenant_isolation_policy ON assessments
    FOR ALL
    USING (organization_id = (
        SELECT organization_id FROM users WHERE id = current_user_id()
    ));

-- Policy: Team members can see their team's data
CREATE POLICY team_data_policy ON assessments
    FOR SELECT
    USING (
        team_id IN (
            SELECT team_id FROM team_members
            WHERE user_id = current_user_id()
        )
    );
```

**Deliverables:**
- ✅ RLS policies on all multi-tenant tables
- ✅ `set_tenant_context()` function for session management
- ✅ Automated testing for data leakage
- ✅ Performance benchmarks (<5% overhead)

---

### Phase 3: Tenant Context Middleware (Weeks 9-12)

**Goal:** Automatic tenant identification & routing

```python
# app/middleware/tenant.py
class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from:
        # 1. Subdomain (tenant1.psychsync.com)
        # 2. Header (X-Tenant-ID)
        # 3. JWT token claim
        # 4. User's organization (fallback)

        tenant_id = await self._extract_tenant_id(request)

        # Validate tenant exists and is active
        if not await self._validate_tenant(tenant_id):
            raise HTTPException(404, "Tenant not found")

        # Add tenant to request context
        request.state.tenant_id = tenant_id

        # Set PostgreSQL session variable for RLS
        async with db.session() as session:
            await session.execute(
                text("SELECT set_tenant_context(:tenant_id)"),
                {"tenant_id": tenant_id}
            )

        response = await call_next(request)
        return response
```

**Deliverables:**
- ✅ Subdomain-based routing
- ✅ JWT tenant claim injection
- ✅ Tenant validation caching (Redis)
- ✅ Tenant rate limiting

---

### Phase 4: Hybrid Database Routing (Weeks 13-16)

**Goal:** Route enterprise tenants to dedicated databases

```python
# app/core/tenant_database.py
class TenantDatabaseRouter:
    """Route queries to appropriate database"""

    def __init__(self):
        self.pools = {}  # tenant_id -> engine pool

    async def get_engine(self, tenant_id: UUID):
        """Get database engine for tenant"""
        tenant = await cache.get(f"tenant:{tenant_id}")

        if tenant.database_host:
            # Enterprise tenant with dedicated DB
            if tenant_id not in self.pools:
                self.pools[tenant_id] = create_async_engine(
                    f"postgresql+asyncpg://{tenant.database_host}/{tenant.database_name}",
                    pool_size=10,
                    max_overflow=20
                )
            return self.pools[tenant_id]
        else:
            # SMB tenant using shared DB
            return shared_engine
```

**Deliverables:**
- ✅ Database connection pooling per tenant
- ✅ Automatic failover to shared DB
- ✅ Tenant migration scripts
- ✅ Monitoring & alerting

---

## 4. API Design Changes

### Multi-Tenant Aware Endpoints

```python
@router.post("/api/v1/assessments")
async def create_assessment(
    assessment: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    # Tenant automatically enforced via RLS
    # No need to manually filter by organization_id

    assessment.organization_id = tenant.id
    assessment.created_by = current_user.id

    result = await db.execute(
        insert(Assessment).values(assessment.dict())
    )
    return result
```

### Cross-Tenant Admin (Superuser Only)

```python
@router.get("/api/v1/admin/tenants/{tenant_id}/analytics")
async def get_tenant_analytics(
    tenant_id: UUID,
    current_user: User = Depends(get_current_superuser),  # Admin only
    db: AsyncSession = Depends(get_async_db)
):
    # Explicitly switch tenant context
    await db.execute(text("SELECT set_tenant_context(:id)"), {"id": tenant_id})

    # Now all queries run in tenant's context
    result = await db.execute(select(Assessment))
    return result.scalars().all()
```

---

## 5. Security Considerations

### Tenant Isolation Checklist

- [ ] **Data Isolation:** RLS policies on all tables
- [ ] **Session Isolation:** Tenant context in every session
- [ ] **API Isolation:** Validate tenant on every request
- [ ] **File Isolation:** Tenant-specific storage paths
- [ ] **Cache Isolation:** Tenant-prefixed cache keys
- [ ] **Background Jobs:** Tenant-scoped task queues
- [ ] **Logging:** Tenant ID in all log entries
- [ ] **Monitoring:** Per-tenant metrics

### Cache Key Strategy

```python
# Before (non-tenant aware)
cache_key = f"user:{user_id}"

# After (tenant aware)
cache_key = f"tenant:{tenant_id}:user:{user_id}"
```

---

## 6. Migration Strategy

### Data Migration Steps

```sql
-- Step 1: Assign existing users to organizations
UPDATE users
SET organization_id = (
    SELECT team.organization_id
    FROM team_members
    JOIN teams ON team_members.team_id = teams.id
    WHERE team_members.user_id = users.id
    LIMIT 1
);

-- Step 2: Handle orphaned users (create default org)
INSERT INTO organizations (name, slug)
SELECT 'Default Organization', 'default-' || id::text
FROM users WHERE organization_id IS NULL;

UPDATE users
SET organization_id = (
    SELECT id FROM organizations WHERE slug LIKE 'default-%'
)
WHERE organization_id IS NULL;

-- Step 3: Add NOT NULL constraint
ALTER TABLE users
ALTER COLUMN organization_id SET NOT NULL;
```

---

## 7. Performance Optimization

### Database Indexing

```sql
-- Multi-column indexes for tenant queries
CREATE INDEX idx_assessments_tenant_created
    ON assessments(organization_id, created_at DESC);

CREATE INDEX idx_responses_tenant_user
    ON responses(organization_id, user_id);

-- Partial indexes for active tenants
CREATE INDEX idx_active_users
    ON users(organization_id)
    WHERE is_active = true;
```

### Connection Pooling

```python
# app/core/database.py
class TenantAwarePool:
    def __init__(self):
        self.shared_pool = create_engine(
            DATABASE_URL,
            pool_size=20,
            max_overflow=40
        )
        self.tenant_pools = {}  # For dedicated DBs

    async def get_pool(self, tenant_id):
        tenant = await self.get_tenant(tenant_id)
        if tenant.database_host:
            return self.get_tenant_pool(tenant)
        return self.shared_pool
```

---

## 8. Monitoring & Observability

### Tenant-Level Metrics

```python
# app/monitoring/tenant_metrics.py
class TenantMetrics:
    async def record_api_call(self, tenant_id, endpoint):
        await metrics.incr(
            f"tenant:{tenant_id}:api_calls",
            tags={"endpoint": endpoint}
        )

    async def get_tenant_usage(self, tenant_id):
        return {
            "api_calls": await metrics.get(f"tenant:{tenant_id}:api_calls"),
            "storage_gb": await self.get_storage_usage(tenant_id),
            "active_users": await self.get_active_users(tenant_id),
        }
```

---

## 9. Compliance & GDPR

### Data Portability

```python
@router.get("/api/v1/account/export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    tenant: Organization = Depends(get_current_tenant)
):
    """GDPR: Export all user data"""
    data = {
        "user": current_user.dict(),
        "assessments": await get_user_assessments(current_user.id),
        "responses": await get_user_responses(current_user.id),
        "team_data": await get_user_team_data(current_user.id),
    }

    # Generate signed URL (tenant-specific storage)
    url = await storage.upload_tenant_file(
        tenant.id,
        f"exports/{current_user.id}.json",
        json.dumps(data)
    )

    return {"download_url": url}
```

### Right to be Forgotten

```python
@router.delete("/api/v1/account/delete")
async def delete_account(
    current_user: User = Depends(get_current_user),
    tenant: Organization = Depends(get_current_tenant)
):
    """GDPR: Delete user and all associated data"""

    # Anonymize instead of delete (for analytics)
    await anonymize_user(current_user.id, tenant.id)

    # Revoke all tokens
    await revoke_all_tokens(current_user.id)

    # Log for audit
    await audit_log(
        action="user_deleted",
        tenant_id=tenant.id,
        user_id=current_user.id
    )
```

---

## 10. Rollout Plan

### Beta Testing (Weeks 1-4)
- 5 pilot customers
- Shared database with RLS
- Monitor performance

### General Availability (Weeks 5-12)
- All new customers on multi-tenant
- Legacy migration tools
- Gradual migration of existing customers

### Enterprise Tier (Weeks 13+)
- Dedicated databases
- Advanced analytics
- Custom SLAs

---

## Appendix: Code Examples

### Tenant-Scoped Repository

```python
# app/crud/base.py
class TenantScopedCRUD(Generic[Model]):
    async def get_multi(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Model]:
        """Get items scoped to tenant (RLS enforced automatically)"""
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
            # No WHERE clause needed - RLS handles filtering!
        )
        return result.scalars().all()
```

### Tenant Migration Script

```python
# scripts/migrate_to_multi_tenant.py
async def migrate_organization(org_id: UUID):
    """Migrate organization to dedicated database"""

    # 1. Create dedicated database
    await create_tenant_database(org_id)

    # 2. Copy data
    await copy_data_to_tenant_db(org_id)

    # 3. Update routing
    await update_org_database_config(org_id)

    # 4. Verify
    await verify_tenant_migration(org_id)

    # 5. Switch traffic
    await enable_tenant_routing(org_id)
```

---

## Success Metrics

- ✅ Zero data leakage between tenants
- ✅ <5% performance overhead from RLS
- ✅ <100ms API response time (p95)
- ✅ 99.9% uptime per tenant
- ✅ GDPR compliant
- ✅ SOC 2 Type II ready
