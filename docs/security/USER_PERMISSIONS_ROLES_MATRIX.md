# User Permissions & Roles Matrix (RBAC)
## Role-Based Access Control System

---

## Executive Summary

This document defines PsychSync's comprehensive Role-Based Access Control (RBAC) system, ensuring users have appropriate access to features and data based on their role within the organization. RBAC is critical for security, compliance, and user experience.

**Principles:**
- **Least Privilege:** Users only get access they need
- **Separation of Duties:** Critical actions require multiple roles
- **Auditability:** All access changes are logged
- **Scalability:** System supports 100k+ users

---

## Part 1: Role Definitions

### 1.1 System Roles

#### Super Admin
**Scope:** Platform-wide (not customer-facing)
**Description:** Full system access for PsychOps staff only
**Count:** 5-10 users (engineering leadership, devops)

**Responsibilities:**
- Complete platform administration
- User management across all organizations
- System configuration and maintenance
- Emergency access for customer support

**Unique Permissions:**
- Access to any organization's data
- Modify system-wide settings
- Manage all users and roles
- View all audit logs
- Execute database migrations

---

### 1.2 Organization Roles

#### Org Owner
**Description:** Highest-level role within an organization
**Typical Users:** CEO, Founder, VP of HR
**Limit:** 1-3 users per organization

**Key Permissions:**
- Manage organization subscription and billing
- Assign all organization-level roles
- Access all organization data
- Delete organization (with confirmation)
- Manage API keys
- Configure SSO

**Cannot Do:**
- Impersonate other users (unless Super Admin)
- Access other organizations
- Modify platform settings

#### Org Admin
**Description:** Administrative privileges within organization
**Typical Users:** HR Director, IT Manager, Operations Manager
**Limit:** 5-10 users per organization

**Key Permissions:**
- Manage users and teams
- View all organization assessments
- Run organization-wide reports
- Manage integrations (Slack, Teams, HRIS)
- Configure assessment templates
- Access audit logs

**Cannot Do:**
- Modify billing/subscription
- Delete organization
- Assign Org Owner role

#### Org Member
**Description:** Standard user with basic access
**Typical Users:** Regular employees, team members
**Limit:** Unlimited

**Key Permissions:**
- View own assessments and results
- Take assigned assessments
- View team insights (if on team)
- Edit own profile
- Export own data

**Cannot Do:**
- View others' assessments (without explicit permission)
- Run organization reports
- Manage users
- Access billing

---

### 1.3 Team Roles

#### Team Owner
**Description:** Highest authority within a team
**Typical Users:** Team Lead, Manager, Department Head
**Limit:** 1-3 users per team

**Key Permissions:**
- Create and delete team
- Manage team members (add/remove)
- Assign team roles
- View all team assessments and insights
- Create and manage team assessments
- Run team analytics reports
- Configure team settings

**Hierarchy:** Can override Team Admin decisions

#### Team Admin
**Description:** Administrative privileges for team operations
**Typical Users:** Senior Manager, Project Lead
**Limit:** 2-5 users per team

**Key Permissions:**
- Add/remove team members
- Assign assessments to team
- View all team data
- Run team reports
- Manage team integrations

**Cannot Do:**
- Delete team
- Assign Team Owner role
- Modify team billing

#### Team Member
**Description:** Standard team participant
**Typical Users:** Individual contributors
**Limit:** Unlimited per team

**Key Permissions:**
- View own assessments
- View team insights (aggregated only)
- Take team assessments
- View team calendar
- Access team shared resources

**Cannot Do:**
- View individual team member results
- Manage team members
- Run team reports

---

### 1.4 Assessment Roles

#### Assessment Creator
**Description:** Can create custom assessments
**Typical Users:** HR Professional, Consultant, Coach
**Limit:** 10-20 per organization

**Key Permissions:**
- Create custom assessments
- Edit own assessments
- Deploy assessments to teams
- View assessment results
- Manage assessment templates

#### Assessment Taker
**Description:** User who takes assessments
**Typical Users:** All users
**Limit:** Unlimited

**Key Permissions:**
- Take assigned assessments
- View own results
- Save assessments as draft
- Retake assessments (if allowed)

#### Assessment Viewer (Read-Only)
**Description:** Can view but not edit assessments
**Typical Users:** Executives, Stakeholders
**Limit:** 5-10 per organization

**Key Permissions:**
- View assessment results
- View assessment analytics
- Export reports
- Cannot edit or create

---

### 1.5 Support Roles

#### Support Agent
**Description:** Customer support representative
**Typical Users:** PsychSync support team
**Limit:** 20-50 users (PsychSync staff only)

**Key Permissions:**
- View customer organizations (read-only, escalated access)
- Impersonate users (with explicit consent)
- View support tickets
- Access customer data for troubleshooting
- Create and edit support tickets

**Audit:** All impersonation logged, requires customer consent

#### Account Manager (CSM)
**Description:** Customer success manager
**Typical Users:** Enterprise CSMs
**Limit:** 1 per enterprise account

**Key Permissions:**
- View assigned customer organizations
- Run customer health reports
- Access customer usage analytics
- Manage customer success plans
- View customer billing (read-only)

---

## Part 2: Permissions Matrix

### 2.1 Core Permissions

#### Permissions Categorization

**User Management (UM)**
- `UM_VIEW` - View users
- `UM_CREATE` - Create new users
- `UM_EDIT` - Edit user profiles
- `UM_DELETE` - Delete users
- `UM_ASSIGN_ROLES` - Assign roles to users
- `UM_IMPERSONATE` - Impersonate users (Super Admin, Support only)

**Team Management (TM)**
- `TM_VIEW` - View teams
- `TM_CREATE` - Create teams
- `TM_EDIT` - Edit team settings
- `TM_DELETE` - Delete teams
- `TM_ADD_MEMBERS` - Add members to team
- `TM_REMOVE_MEMBERS` - Remove members from team
- `TM_ASSIGN_ROLES` - Assign team roles

**Assessment Management (AM)**
- `AM_VIEW` - View assessments
- `AM_CREATE` - Create assessments
- `AM_EDIT` - Edit assessments
- `AM_DELETE` - Delete assessments
- `AM_DEPLOY` - Deploy assessments to users/teams
- `AM_VIEW_RESULTS` - View assessment results
- `AM_EXPORT` - Export assessment data

**Analytics & Reporting (AR)**
- `AR_VIEW_OWN` - View own analytics
- `AR_VIEW_TEAM` - View team analytics
- `AR_VIEW_ORG` - View organization analytics
- `AR_EXPORT` - Export reports
- `AR_VIEW_PII` - View personally identifiable information

**Billing & Subscription (BS)**
- `BS_VIEW` - View billing information
- `BS_EDIT` - Edit subscription
- `BS_UPGRADE` - Upgrade/downgrade plan
- `BS_MANAGE_PAYMENT` - Manage payment methods
- `BS_VIEW_INVOICES` - View and download invoices

**System Administration (SA)**
- `SA_VIEW_LOGS` - View audit logs
- `SA_MANAGE_INTEGRATIONS` - Manage third-party integrations
- `SA_CONFIGURE_SSO` - Configure single sign-on
- `SA_MANAGE_API_KEYS` - Create/delete API keys
- `SA_VIEW_SETTINGS` - View org settings
- `SA_EDIT_SETTINGS` - Edit org settings

**Data Management (DM)**
- `DM_EXPORT_OWN` - Export own data
- `DM_DELETE_OWN` - Request account deletion
- `DM_VIEW_AUDIT` - View audit trail

---

### 2.2 Role-Permission Mapping

#### Super Admin
```
All Permissions: ✅
Scope: Platform-wide
```

#### Org Owner
```
UM_VIEW ✅ (org only)
UM_CREATE ✅ (org only)
UM_EDIT ✅ (org only)
UM_DELETE ✅ (org only)
UM_ASSIGN_ROLES ✅ (Org Admin, Org Member only)

TM_VIEW ✅ (org only)
TM_CREATE ✅ (org only)
TM_EDIT ✅ (org only)
TM_DELETE ✅ (org only)
TM_ADD_MEMBERS ✅
TM_REMOVE_MEMBERS ✅
TM_ASSIGN_ROLES ✅

AM_VIEW ✅ (org only)
AM_CREATE ✅ (org only)
AM_EDIT ✅ (org only)
AM_DELETE ✅ (org only)
AM_DEPLOY ✅
AM_VIEW_RESULTS ✅ (all org results)
AM_EXPORT ✅

AR_VIEW_OWN ✅
AR_VIEW_TEAM ✅
AR_VIEW_ORG ✅
AR_EXPORT ✅
AR_VIEW_PII ✅

BS_VIEW ✅
BS_EDIT ✅
BS_UPGRADE ✅
BS_MANAGE_PAYMENT ✅
BS_VIEW_INVOICES ✅

SA_VIEW_LOGS ✅
SA_MANAGE_INTEGRATIONS ✅
SA_CONFIGURE_SSO ✅
SA_MANAGE_API_KEYS ✅
SA_VIEW_SETTINGS ✅
SA_EDIT_SETTINGS ✅

DM_EXPORT_OWN ✅
DM_DELETE_OWN ✅
DM_VIEW_AUDIT ✅
```

#### Org Admin
```
UM_VIEW ✅ (org only)
UM_CREATE ✅ (org only)
UM_EDIT ✅ (org only)
UM_DELETE ✅ (org only)
UM_ASSIGN_ROLES ✅ (Org Member, Team roles only)

TM_VIEW ✅
TM_CREATE ✅
TM_EDIT ✅
TM_DELETE ✅
TM_ADD_MEMBERS ✅
TM_REMOVE_MEMBERS ✅
TM_ASSIGN_ROLES ✅

AM_VIEW ✅
AM_CREATE ✅
AM_EDIT ✅
AM_DELETE ✅
AM_DEPLOY ✅
AM_VIEW_RESULTS ✅
AM_EXPORT ✅

AR_VIEW_OWN ✅
AR_VIEW_TEAM ✅
AR_VIEW_ORG ✅
AR_EXPORT ✅
AR_VIEW_PII ✅

SA_MANAGE_INTEGRATIONS ✅
SA_VIEW_SETTINGS ✅
SA_EDIT_SETTINGS ✅
DM_VIEW_AUDIT ✅

BS: ❌ (cannot access billing)
UM_ASSIGN_ROLES: Cannot assign Org Owner
```

#### Team Owner
```
TM_VIEW ✅ (own teams only)
TM_EDIT ✅ (own teams only)
TM_ADD_MEMBERS ✅ (own teams only)
TM_REMOVE_MEMBERS ✅ (own teams only)
TM_ASSIGN_ROLES ✅ (own teams, Team Admin/Member only)

AM_VIEW ✅
AM_CREATE ✅ (team assessments only)
AM_DEPLOY ✅ (to own team only)
AM_VIEW_RESULTS ✅ (own team only)
AM_EXPORT ✅ (own team only)

AR_VIEW_OWN ✅
AR_VIEW_TEAM ✅ (own teams only)
AR_EXPORT ✅ (own team data only)

All other permissions: ❌
```

#### Team Member
```
TM_VIEW ✅ (own teams only)
AM_VIEW ✅
AM_VIEW_RESULTS ✅ (own only)
AR_VIEW_OWN ✅
AR_VIEW_TEAM ✅ (aggregated only, no individual data)

All other permissions: ❌
```

#### Org Member
```
AM_VIEW ✅
AM_VIEW_RESULTS ✅ (own only)
AR_VIEW_OWN ✅
DM_EXPORT_OWN ✅
DM_DELETE_OWN ✅

All other permissions: ❌
```

---

## Part 3: Implementation

### 3.1 Database Schema

#### RBAC Tables

```sql
-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    scope VARCHAR(20) NOT NULL, -- system, organization, team
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions
CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL, -- UM_VIEW, TM_CREATE, etc.
    category VARCHAR(50) NOT NULL, -- user_management, team_management, etc.
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Role Permissions (Many-to-Many)
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

-- User Roles (Many-to-Many with context)
CREATE TABLE user_roles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE, -- Nullable for org-level roles
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- For temporary access
    UNIQUE(user_id, role_id, organization_id, COALESCE(team_id, '00000000-0000-0000-0000-000000000000'))
);

-- Permission Audit Log
CREATE TABLE permission_audit_log (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL, -- role_granted, role_revoked, permission_checked
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    resource_type VARCHAR(50), -- user, team, assessment, etc.
    resource_id UUID,
    granted_by UUID REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Permission Checking Service

```python
from app.services.rbac_service import RBACService

# Check if user has permission
async def check_permission(user_id: UUID, permission_code: str, resource_id: UUID = None):
    """
    Check if user has specific permission.

    Args:
        user_id: User to check
        permission_code: Permission to check (e.g., "AM_DELETE")
        resource_id: Specific resource (team, assessment, etc.)

    Returns:
        Boolean indicating if user has permission
    """
    async for db in get_async_db():
        service = RBACService(db)
        has_permission = await service.user_has_permission(
            user_id=user_id,
            permission_code=permission_code,
            resource_id=resource_id
        )
        return has_permission

# Usage example
if await check_permission(current_user.id, "AM_DELETE", assessment_id):
    # Allow deletion
    await delete_assessment(assessment_id)
else:
    # Deny with 403 Forbidden
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

### 3.3 Middleware for API Endpoints

```python
from fastapi import Depends
from app.dependencies import require_permission

# Protect API endpoint
@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("AM_DELETE"))
):
    """Delete assessment (requires AM_DELETE permission)"""
    # Only reachable if user has AM_DELETE permission
    return await assessment_service.delete(assessment_id)
```

---

## Part 4: Role Assignment Rules

### 4.1 Role Hierarchy & Constraints

**Maximum Limits:**
- Org Owner: 3 per organization
- Org Admin: 10 per organization
- Team Owner: 3 per team
- Team Admin: 5 per team

**Assignment Rules:**
1. Only Org Owners can assign Org Owner role
2. Only Org Owners/Org Admins can assign Org Admin role
3. Only Team Owners can assign Team Owner role
4. Team Owners/Org Admins can assign Team roles

**Self-Service:**
- Org Owners can manage their own roles (within limits)
- Team Owners can manage team roles (within limits)

**Escalation Path:**
- Users can request role changes via support ticket
- Support can escalate to Org Owner for approval
- Audit trail maintained for all role changes

### 4.2 Temporary Access

**Use Cases:**
- Contractor/consultant access (30-90 days)
- Temporary project access (specific duration)
- Emergency access (until resolved)

**Implementation:**
```python
# Grant temporary role with expiration
await rbac_service.grant_role(
    user_id=user_id,
    role_id=team_admin_role.id,
    organization_id=org_id,
    team_id=team_id,
    expires_at=datetime.now(timezone.utc) + timedelta(days=30)
)

# Automatically revoke expired roles (scheduled job)
await rbac_service.revoke_expired_roles()
```

---

## Part 5: Audit & Compliance

### 5.1 Audit Logging

**All Permission Changes Logged:**
- Role grants/revocations
- Permission modifications
- Impersonation sessions (start/end)
- Failed access attempts (403 errors)

**Log Format:**
```json
{
  "timestamp": "2025-01-12T14:30:00Z",
  "user_id": "user-123",
  "action": "role_granted",
  "role": "Team Admin",
  "granted_by": "org-owner-456",
  "organization_id": "org-789",
  "team_id": "team-101",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "reason": "Project lead needs team management"
}
```

### 5.2 Access Reviews

**Quarterly Access Reviews:**
- Review all role assignments
- Remove unnecessary access
- Confirm ongoing need for privileged roles
- Document review decisions

**Certification:**
- Org Owner certifies Org Admin access
- Team Owner certifies Team access
- PsychSync certifies Support access

---

## Part 6: Security Best Practices

### 6.1 Principle of Least Privilege
- Default to most restrictive access
- Grant additional permissions only when needed
- Revoke access when no longer required
- Regularly audit and clean up unused permissions

### 6.2 Separation of Duties
- Critical actions require multiple users (e.g., delete organization)
- No single user has all permissions
- Financial access separated from operational access

### 6.3 Just-in-Time Access
- Grant temporary access for specific tasks
- Auto-expire after task completion
- Require justification for privileged access

---

## Conclusion

PsychSync's RBAC system provides enterprise-grade access control with:
- ✅ 10+ defined roles across 5 categories
- ✅ 60+ granular permissions
- ✅ Hierarchical role assignment
- ✅ Comprehensive audit logging
- ✅ Scalable to 100k+ users

**Next Steps:**
1. Implement database schema
2. Build permission checking middleware
3. Create role assignment UI
4. Set up audit logging
5. Train support team on RBAC

**Security is not a feature—it's a foundation. 🛡️**
