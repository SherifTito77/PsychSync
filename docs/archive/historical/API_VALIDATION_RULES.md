# API Validation Rules - Comprehensive Documentation

**Version:** 2.0
**Last Updated:** 2026-01-04
**Author:** Security Team

## Table of Contents

1. [Overview](#overview)
2. [Authentication Endpoints](#1-authentication-endpoints)
3. [Assessment Endpoints](#2-assessment-endpoints)
4. [User Management Endpoints](#3-user-management-endpoints)
5. [Team Management Endpoints](#4-team-management-endpoints)
6. [Organization Management](#5-organization-management)
7. [Analytics and Reporting](#6-analytics-and-reporting)
8. [Input Validation Middleware](#7-input-validation-middleware)
9. [Security Considerations](#8-security-considerations)
10. [Validation Gaps and Recommendations](#9-validation-gaps-and-recommendations)

---

## Overview

PsychSync API employs a multi-layered validation approach:
- **Schema-level validation** using Pydantic models
- **Middleware-level validation** for injection prevention
- **Endpoint-level validation** for business logic
- **Security-level validation** for attack prevention

### Validation Architecture

```
Request → Middleware → Pydantic Schema → Business Logic → Database
          ↓                ↓                    ↓
    Security Checks   Type/format Rules    Application Rules
```

---

## 1. Authentication Endpoints

### Base Path: `/api/v1/auth`

### 1.1 User Registration

**Endpoint:** `POST /auth/register-fixed`

**Request Schema:**
```python
class UserRegister(BaseModel):
    email: EmailStr                    # Required
    full_name: str                      # Required, min 2 characters
    password: str                       # Required, validated for strength
```

**Validation Rules:**

| Field | Type | Required | Validation Rules | Error Codes |
|-------|------|----------|------------------|-------------|
| `email` | EmailStr | Yes | • Valid email format<br>• Max 254 characters<br>• Local part max 64 chars<br>• Converted to lowercase<br>• Must be unique | `INVALID_EMAIL`<br>`EMAIL_TOO_LONG`<br>`EMAIL_EXISTS` |
| `full_name` | str | Yes | • Min 2 characters<br>• Max 255 characters<br>• Sanitized for XSS | `NAME_TOO_SHORT`<br>`NAME_TOO_LONG` |
| `password` | str | Yes | • Min 12 characters<br>• Must contain uppercase<br>• Must contain lowercase<br>• Must contain digit<br>• Must contain special char<br>• Entropy ≥ 60 bits<br>• Not in common password list<br>• No sequential patterns<br>• No repeated patterns | `PASSWORD_TOO_SHORT`<br>`PASSWORD_WEAK`<br>`PASSWORD_COMMON` |

**Password Strength Scoring:**
```python
Score Components:
- Length: 40 points max (2 points per character)
- Character Variety: 30 points max (7.5 each for upper, lower, digit, special)
- Entropy: 15 points max (min 60 bits required)
- Complexity Penalty: -15 for common, -10 for sequential/repeated

Strength Levels:
- Excellent: 90-100 points
- Strong: 75-89 points
- Good: 60-74 points
- Fair: 40-59 points
- Weak: 0-39 points
```

**Rate Limiting:**
- Max 3 registration attempts per IP per hour
- Response: `429 Too Many Requests`

**Security Checks:**
- Email format validation with regex
- SQL injection prevention
- XSS pattern detection
- Input sanitization
- Duplicate email check (case-insensitive)

**Example Valid Request:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecureP@ssw0rd123!XYZ"
}
```

**Example Error Response:**
```json
{
  "detail": {
    "message": "Password requirements not met",
    "errors": [
      "Password must be at least 12 characters long. Current length: 8",
      "Password must contain at least one special character"
    ]
  }
}
```

---

### 1.2 User Login

**Endpoint:** `POST /auth/token-fixed`

**Request Schema:** OAuth2PasswordRequestForm
```python
username: str    # Email address
password: str
```

**Validation Rules:**

| Field | Type | Required | Validation | Error Codes |
|-------|------|----------|------------|-------------|
| `username` | str | Yes | • Valid email format<br>• Converted to lowercase<br>• Max 254 characters | `INVALID_CREDENTIALS` |
| `password` | str | Yes | • Non-empty<br>• Max 128 characters | `INVALID_CREDENTIALS` |

**Rate Limiting:**
- Max 5 login attempts per IP per minute
- Brute force detection locks after 10 failed attempts in 5 minutes
- Response: `429 Too Many Requests`

**Security Checks:**
- Timing attack protection
- User existence check (consistent response time)
- Account active status verification
- Password hash verification (bcrypt, 12 rounds)
- Session management with CSRF tokens

**Response Format:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

**Cookies Set:**
- `access_token`: HttpOnly, Secure, SameSite=lax, 30 minutes
- `refresh_token`: HttpOnly, Secure, SameSite=lax, 7 days
- `csrf_token`: Non-HttpOnly (for AJAX), Secure, SameSite=lax

---

### 1.3 Password Reset

**Endpoint:** `POST /auth/password-reset`

**Request Schema:**
```python
class PasswordResetRequest(BaseModel):
    email: EmailStr    # Required
```

**Validation:**
- Valid email format
- Max 254 characters
- Case-insensitive lookup

**Endpoint:** `POST /auth/password-reset/confirm`

**Request Schema:**
```python
class PasswordResetConfirm(BaseModel):
    token: str              # Reset token from email
    new_password: str       # Must meet strength requirements
```

**Validation Rules:**
- `token`: Non-empty, valid UUID format
- `new_password`: Same as registration password requirements

**Token Security:**
- Tokens expire after 1 hour
- Single-use tokens (invalidated after use)
- Token blacklisting support

---

### 1.4 Password Change (Authenticated)

**Endpoint:** `POST /users/change-password`

**Request Schema:**
```python
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
```

**Validation Rules:**

| Field | Validation |
|-------|------------|
| `current_password` | • Max 128 characters<br>• Must match current password hash |
| `new_password` | • All password strength rules<br>• Must differ from current password |

**Rate Limiting:**
- Max 5 attempts per 15 minutes
- Response: `429 Too Many Requests`

**Security Features:**
- Current password verification
- Session invalidation on successful change
- Audit logging
- Password history check (optional, not yet implemented)

---

## 2. Assessment Endpoints

### Base Path: `/api/v1/assessments`

### 2.1 Create Assessment

**Endpoint:** `POST /assessments/`

**Request Schema:**
```python
class AssessmentCreate(BaseModel):
    title: str                          # Required, 3-200 characters
    description: Optional[str]          # Optional, max 5000 characters
    category: str                       # Required, must be in allowed list
    instructions: Optional[str]         # Optional, max 10000 characters
    estimated_duration: Optional[int]   # Optional, in minutes, max 1440
    is_public: bool = False
    allow_anonymous: bool = False
    randomize_questions: bool = False
    show_progress: bool = True
    team_id: Optional[int] = None
    sections: Optional[List[SectionCreate]] = []
```

**Validation Rules:**

| Field | Type | Required | Validation | Error Codes |
|-------|------|----------|------------|-------------|
| `title` | str | Yes | • Min 3 characters<br>• Max 200 characters<br>• Sanitized for XSS | `TITLE_TOO_SHORT`<br>`TITLE_TOO_LONG` |
| `category` | str | Yes | • Must be in: `personality`, `cognitive`, `clinical`, `behavioral`, `developmental`, `neuropsychological`, `other` | `INVALID_CATEGORY` |
| `estimated_duration` | int | No | • Min 1 minute<br>• Max 1440 minutes (24 hours) | `INVALID_DURATION` |
| `team_id` | int | No | • Must be valid team ID<br>• User must be member | `INVALID_TEAM` |

**Section Validation:**
```python
class SectionCreate(BaseModel):
    title: str                      # Required, max 255 characters
    description: Optional[str]      # Optional, max 5000 characters
    order: int = 0                 # Non-negative
    questions: List[QuestionCreate]
```

**Question Validation:**
```python
class QuestionCreate(BaseModel):
    question_type: str              # Required, validated type
    question_text: str              # Required, max 2000 characters
    help_text: Optional[str]        # Optional, max 1000 characters
    order: int = 0                  # Non-negative
    is_required: bool = True
    config: Optional[Dict[str, Any]]
```

**Allowed Question Types:**
- `multiple_choice`
- `rating_scale`
- `text`
- `yes_no`
- `likert`

---

### 2.2 Update Assessment

**Endpoint:** `PUT /assessments/{assessment_id}`

**Request Schema:**
```python
class AssessmentUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    instructions: Optional[str]
    estimated_duration: Optional[int]
    status: Optional[str]
    # ... other fields optional
```

**Authorization:**
- Must be assessment creator
- Or team admin

**Validation:**
- All fields optional
- Same validation rules as create for provided fields
- IDOR protection: verifies user ownership

---

### 2.3 Submit Assessment Response

**Endpoint:** `POST /assessments/{assessment_id}/responses`

**Request Schema:**
```python
class ResponseSubmit(BaseModel):
    assignment_id: Optional[int]
    responses: Dict[str, Any]        # JSON object with answers
    is_complete: bool = False
```

**Validation Rules:**

| Field | Validation |
|-------|------------|
| `assignment_id` | • Valid assignment ID if provided<br>• Assignment must be active |
| `responses` | • Max 10000 characters (JSON)<br>• Must be valid JSON object<br>• Answer keys must match question IDs<br>• Answer values must match question types |
| `is_complete` | • Boolean |

**Business Logic Constraints:**
- Assessment must be published
- Required questions must have answers
- Answer types must match question types
- Cannot submit after due date (if assigned)

---

### 2.4 List Assessments

**Endpoint:** `GET /assessments/`

**Query Parameters:**

| Parameter | Type | Validation | Default |
|-----------|------|------------|---------|
| `skip` | int | ≥ 0 | 0 |
| `limit` | int | 1-1000 | 100 |
| `search` | str | Max 100 chars, sanitized | None |
| `category` | str | Must be valid category | None |
| `status` | str | Must be valid status | None |
| `created_by` | int | Valid user ID | None |
| `created_after` | date | ISO 8601 date | None |
| `created_before` | date | ISO 8601 date | None |

**Pagination:**
```json
{
  "assessments": [...],
  "total": 150,
  "skip": 0,
  "limit": 100,
  "has_next": true,
  "has_prev": false
}
```

**Rate Limiting:**
- 30 requests per minute for authenticated users
- 10 requests per minute for anonymous users

---

## 3. User Management Endpoints

### Base Path: `/api/v1/users`

### 3.1 Get Current User Profile

**Endpoint:** `GET /users/me`

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "User profile retrieved successfully",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-04T00:00:00Z"
  }
}
```

**Caching:** 5 minutes for profile data

---

### 3.2 Update User Profile

**Endpoint:** `PUT /users/me` or `PATCH /users/me`

**Request Schema:**
```python
class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    full_name: Optional[str]
    is_active: Optional[bool]
    password: Optional[str]
```

**Validation Rules:**

| Field | Validation |
|-------|------------|
| `email` | • Valid email format<br>• Unique if changed<br>• Requires re-verification if changed |
| `full_name` | • Min 2 characters<br>• Max 255 characters |
| `password` | • All password strength rules if provided |

**Security:**
- Audit logging for all changes
- Email change requires verification
- Password change invalidates sessions

---

### 3.3 List Users (Admin Only)

**Endpoint:** `GET /users/`

**Authorization:** Admin role required

**Query Parameters:**

| Parameter | Type | Validation | Default |
|-----------|------|------------|---------|
| `skip` | int | ≥ 0 | 0 |
| `limit` | int | 1-100 | 100 |
| `search` | str | Max 100 chars, XSS sanitized | None |
| `is_active` | bool | true/false | None |
| `organization_id` | int | Valid org ID, ≥ 1 | None |
| `role` | str | regex: `^(admin\|user\|team_lead)$` | None |

**Security Features:**
- Role-based access control
- Input sanitization on search term
- SQL injection prevention via parameterized queries
- Audit logging for data access

**Rate Limiting:**
- 30 requests per minute

---

## 4. Team Management Endpoints

### Base Path: `/api/v1/teams`

### 4.1 Create Team

**Endpoint:** `POST /teams/`

**Request Schema:**
```python
class TeamCreate(BaseModel):
    name: str              # Required, 1-255 characters
    description: str       # Optional
```

**Validation Rules:**

| Field | Validation |
|-------|------------|
| `name` | • Min 1 character<br>• Max 255 characters<br>• Sanitized for XSS<br>• Must be unique within org |
| `description` | • Max 5000 characters<br>• Sanitized for XSS |

**Security:**
- Input sanitization via `sanitize_dict()`
- SQL injection prevention
- Organization membership verification

---

### 4.2 Add Team Member

**Endpoint:** `POST /teams/{team_id}/members`

**Request Schema:**
```python
class TeamMemberCreate(BaseModel):
    user_id: UUID          # Required, must be valid UUID
    role: TeamRole = TeamRole.MEMBER
```

**Allowed Roles:**
- `owner`
- `admin`
- `member`

**Validation:**
- `user_id` must be valid UUID format
- User must exist in database
- User cannot already be a member
- Adder must have admin/owner permissions

---

### 4.3 Update Team Member Role

**Endpoint:** `PATCH /teams/{team_id}/members/{member_id}`

**Request Schema:**
```python
class TeamMemberUpdate(BaseModel):
    role: TeamRole
```

**Authorization:**
- Must be team owner or admin
- Cannot change owner role unless you are the owner
- Cannot promote to owner without explicit transfer

---

### 4.4 List Teams

**Endpoint:** `GET /teams/`

**Query Parameters:**

| Parameter | Type | Validation | Default |
|-----------|------|------------|---------|
| `skip` | int | ≥ 0 | 0 |
| `limit` | int | 1-1000 | 100 |
| `my_teams` | bool | true/false | false |

**Security:**
- `my_teams=true` filters to user's teams only
- IDOR protection on team access
- Membership verification

---

## 5. Organization Management

### Base Path: `/api/v1/organizations`

### 5.1 Create Organization

**Endpoint:** `POST /organizations/`

**Request Schema:**
```python
class OrganizationCreate(BaseModel):
    name: str              # Required
    description: str       # Optional
```

**Validation:**

| Field | Validation |
|-------|------------|
| `name` | • Min 1 character<br>• Max 255 characters<br>• Sanitized |
| `description` | • Max 5000 characters<br>• Sanitized |

---

### 5.2 Update Organization

**Endpoint:** `PUT /organizations/{org_id}`

**Authorization:**
- Must be organization owner
- Or system admin

**Validation:** Same as create

---

## 6. Analytics and Reporting

### Base Path: `/api/v1/analytics`

### 6.1 Get Assessment Analytics

**Endpoint:** `GET /analytics/assessments/{assessment_id}`

**Query Parameters:**

| Parameter | Type | Validation | Default |
|-----------|------|------------|---------|
| `start_date` | date | ISO 8601 format | 30 days ago |
| `end_date` | date | ISO 8601 format, ≥ start_date | Today |
| `group_by` | str | `day\|week\|month` | `day` |

**Authorization:**
- Must be assessment owner
- Or team admin
- Or organization admin

**Data Validation:**
- Date ranges limited to 1 year max
- Response data anonymized for privacy
- PII removed from analytics

---

### 6.2 Export Data

**Endpoint:** `GET /analytics/export`

**Query Parameters:**

| Parameter | Type | Validation | Default |
|-----------|------|------------|---------|
| `format` | str | `csv\|json\|xlsx` | `json` |
| `assessment_id` | int | Valid ID | Required |
| `include_pii` | bool | Requires admin role | false |

**Security:**
- Rate limiting: 1 export per minute
- File size limit: 50MB
- PII redaction unless authorized
- Audit logging for all exports
- Virus scanning on generated files

---

## 7. Input Validation Middleware

### 7.1 SecurityValidationMiddleware

**Location:** `/app/middleware/input_validation_middleware.py`

**Protection Against:**
- SQL Injection
- XSS (Cross-Site Scripting)
- Command Injection
- Path Traversal
- LDAP Injection
- NoSQL Injection
- XXE (XML External Entity)
- Server-Side Template Injection

**SQL Injection Patterns:**
```python
PATTERNS = [
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
    r'["\'].*?\s+(or|and)\s+.*?["\'].*?=',
    r"exec(\s|\+)+(s|x)p\w+",
    r"union(\s|\+)+(all(\s|\+)+)?select",
    r"select(\s|\+).*?from",
    # ... 12 more patterns
]
```

**XSS Patterns:**
```python
PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"<[^>]*\s(on\w+)\s*=",
    r"<iframe[^>]*>",
    # ... 9 more patterns
]
```

**Path Traversal Patterns:**
```python
PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e",
    r"..%2f",
    r"..%5c",
    # ... 3 more patterns
]
```

**Request Size Limits:**
- Default: 10MB
- Configurable via `max_request_size`
- Response: `413 Request Entity Too Large`

**File Upload Validation:**
- Allowed content types:
  - `image/jpeg`, `image/png`, `image/gif`, `image/webp`
  - `application/pdf`
  - `text/plain`, `text/csv`
  - `application/json`
- Filename validation for path traversal
- File size validation

**Header Validation:**
- Skips safe headers (User-Agent, Accept, etc.)
- Validates custom headers for injection patterns
- Detects header-based attacks

---

### 7.2 InputValidator Class

**Location:** `/app/core/input_validation.py`

**Methods:**

#### `validate_uuid(value, field_name="ID")`
- Validates UUID format
- Returns string representation
- Error: `Invalid {field_name} format. Must be a valid UUID`

#### `validate_email(email)`
- Validates email format
- Max 254 characters
- Local part max 64 characters
- Converts to lowercase
- Error: `Invalid email format`

#### `validate_safe_string(value, field_name, min_length=1, max_length=1000)`
- Checks string length
- Blocks dangerous patterns
- Sanitizes by removing unsafe characters
- Error: `{field_name} contains unsafe content`

#### `validate_pagination_params(skip=0, limit=100, max_limit=1000)`
- Ensures non-negative skip
- Ensures valid limit (1-max_limit)
- Returns corrected tuple

#### `validate_sort_params(sort_by, allowed_fields)`
- Removes non-alphanumeric characters
- Checks against allowed fields list
- Error: `Invalid sort field. Allowed fields: ...`

#### `validate_json_data(data, max_size=10000)`
- Parses JSON if string
- Validates object type
- Checks size limit
- Error: `Invalid JSON format` or `JSON data too large`

#### `sanitize_search_term(term)`
- Removes non-safe characters
- Limits to 100 characters
- Returns sanitized string

#### `validate_file_upload(filename, allowed_extensions=None, max_size_mb=10)`
- Validates filename length (max 255)
- Blocks dangerous characters (`..`, `/`, `\`, `:`, etc.)
- Checks file extension
- Returns safe filename and max size

---

### 7.3 SecurityValidator Class

**Location:** `/app/core/security_validator.py`

**Security Levels:**
- `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

**ValidationResult DataClass:**
```python
@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_value: Any
    security_issues: List[str]
    risk_level: SecurityLevel
    original_value: Any = None
```

**Methods:**

#### `validate_uuid(value, field_name="id")`
- Comprehensive UUID validation
- Injection pattern detection
- Returns ValidationResult

#### `validate_email(email, field_name="email")`
- Email format validation
- Injection pattern detection
- Length validation
- Returns ValidationResult

#### `validate_text_input(value, field_name, max_length=10000, security_level=HIGH)`
- Text field validation
- XSS detection
- SQL injection detection
- HTML escaping
- Returns ValidationResult

---

## 8. Security Considerations

### 8.1 OWASP Top 10 Coverage

| Threat | Protection | Status |
|--------|------------|--------|
| A01: Broken Access Control | Role-based checks, IDOR protection | ✅ Implemented |
| A02: Cryptographic Failures | Bcrypt, JWT, HTTPS-only cookies | ✅ Implemented |
| A03: Injection | SQL parameterized, input sanitization, middleware | ✅ Implemented |
| A04: Insecure Design | Security-by-design principles | ⚠️ Partial |
| A05: Security Misconfiguration | Secure defaults, env-based config | ✅ Implemented |
| A06: Vulnerable Components | Dependency scanning, SBOM | ✅ Implemented |
| A07: Auth Failures | Rate limiting, password policies, MFA-ready | ✅ Implemented |
| A08: Data Integrity Failures | Digital signatures (SLSA) | ✅ Implemented |
| A09: Logging Failures | Audit logging, security events | ✅ Implemented |
| A10: SSRF | URL validation, allow-lists | ⚠️ Partial |

### 8.2 Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 5 attempts | 60 seconds |
| Registration | 3 attempts | 3600 seconds |
| Password change | 5 attempts | 900 seconds |
| General API | 30 requests | 60 seconds |
| Data export | 1 request | 60 seconds |
| Admin endpoints | 60 requests | 60 seconds |

### 8.3 Session Security

**Access Token:**
- Type: JWT
- Algorithm: RS256 (configurable)
- Expiry: 30 minutes
- Storage: HttpOnly cookie
- SameSite: lax
- Secure: true (HTTPS only)

**Refresh Token:**
- Expiry: 7 days
- Storage: HttpOnly cookie
- Rotation: Enabled
- Blacklisting: Supported

**CSRF Protection:**
- Token in non-HttpOnly cookie
- Validated on state-changing requests
- SameSite enforcement

### 8.4 Password Security

**Hashing:**
- Algorithm: bcrypt
- Rounds: 12
- Salt: Automatic (bcrypt built-in)

**Requirements:**
- Minimum 12 characters
- Uppercase + lowercase + digit + special
- Entropy ≥ 60 bits
- Not in common password list
- No sequential/repeated patterns

**History:**
- Password history tracking (not yet implemented)
- Reuse prevention (not yet implemented)

### 8.5 Data Protection

**PII Handling:**
- Encryption at rest (PostgreSQL)
- Encryption in transit (TLS 1.3)
- PII redaction in analytics
- GDPR compliance endpoints

**Data Retention:**
- Configurable retention policies
- Automated cleanup jobs
- Soft delete with hard delete option

---

## 9. Validation Gaps and Recommendations

### 9.1 Critical Gaps

#### Gap 1: Missing Content-Type Validation
**Location:** All endpoints
**Issue:** Some endpoints don't validate Content-Type header
**Risk:** malformed requests can bypass validation
**Recommendation:**
```python
@router.post("/endpoint")
async def endpoint(
    request: Request,
    ...
):
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(415, "Unsupported Media Type")
```

#### Gap 2: Missing Array Length Validation
**Location:** Assessment creation, response submission
**Issue:** Arrays (questions, sections, responses) have no max length
**Risk:** DoS via large payloads
**Recommendation:**
```python
class AssessmentCreate(BaseModel):
    sections: List[SectionCreate] = Field(
        ...,
        max_items=100  # Limit to 100 sections
    )
```

#### Gap 3: Missing Date Range Validation
**Location:** Analytics endpoints
**Issue:** No validation on date ranges
**Risk:** Performance degradation from large queries
**Recommendation:**
```python
def validate_date_range(start: datetime, end: datetime):
    max_range = timedelta(days=365)
    if (end - start) > max_range:
        raise HTTPException(400, "Date range too large (max 1 year)")
```

#### Gap 4: Missing File Content Validation
**Location:** Upload endpoints
**Issue:** Magic number validation not implemented
**Risk:** File type spoofing
**Recommendation:**
```python
MAGIC_NUMBERS = {
    'image/jpeg': b'\xff\xd8\xff',
    'image/png': b'\x89\x50\x4e\x47',
    'application/pdf': b'%PDF-',
}

def validate_file_content(content: bytes, declared_type: str):
    expected_magic = MAGIC_NUMBERS.get(declared_type)
    if expected_magic and not content.startswith(expected_magic):
        raise HTTPException(400, "File content doesn't match declared type")
```

---

### 9.2 High Priority Improvements

#### 1. Add Request ID Validation
```python
import uuid

def validate_request_id(request_id: str) -> str:
    """Validate X-Request-ID header if present"""
    if not request_id:
        return str(uuid.uuid4())

    try:
        return str(uuid.UUID(request_id))
    except ValueError:
        raise HTTPException(400, "Invalid Request ID format")
```

#### 2. Add Batch Request Validation
```python
class BatchRequest(BaseModel):
    operations: List[Dict] = Field(
        ...,
        min_items=1,
        max_items=100  # Limit batch size
    )

    @validator('operations')
    def validate_operations(cls, v):
        if len(v) > 100:
            raise ValueError("Too many operations (max 100)")
        return v
```

#### 3. Add Geo-Location Validation
```python
def validate_coordinates(lat: float, lon: float):
    """Validate geographic coordinates"""
    if not (-90 <= lat <= 90):
        raise HTTPException(400, "Invalid latitude")
    if not (-180 <= lon <= 180):
        raise HTTPException(400, "Invalid longitude")
```

#### 4. Add Phone Number Validation
```python
import phonenumbers

def validate_phone(phone: str, country: str = "US") -> str:
    """Validate phone number format"""
    try:
        parsed = phonenumbers.parse(phone, country)
        if not phonenumbers.is_valid_number(parsed):
            raise HTTPException(400, "Invalid phone number")
        return phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.E164
        )
    except phonenumbers.NumberParseException:
        raise HTTPException(400, "Invalid phone number format")
```

---

### 9.3 Medium Priority Improvements

#### 1. Schema Validation Enhancements
```python
# Add more granular email validation
class EnhancedEmailStr(EmailStr):
    """Enhanced email with additional checks"""

    @classmethod
    def validate(cls, value: str) -> str:
        value = super().validate(value)

        # Block disposable email domains
        disposable_domains = load_disposable_domains()
        domain = value.split('@')[1]
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses not allowed')

        # Block role-based emails
        role_prefixes = ['admin@', 'support@', 'info@']
        if any(value.startswith(prefix) for prefix in role_prefixes):
            raise ValueError('Role-based email addresses not allowed')

        return value
```

#### 2. Add Dependency Validation
```python
class AssessmentCreate(BaseModel):
    sections: List[SectionCreate]

    @validator('sections')
    def validate_section_dependencies(cls, v):
        """Ensure section IDs don't create circular dependencies"""
        section_ids = [s.id for s in v if hasattr(s, 'id')]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError('Duplicate section IDs detected')
        return v
```

#### 3. Add Business Rule Validation
```python
class AssessmentCreate(BaseModel):
    category: str
    questions: List[QuestionCreate]

    @validator('questions')
    def validate_question_count(cls, v, values):
        """Ensure minimum questions per category"""
        category = values.get('category')
        min_questions = {
            'personality': 20,
            'cognitive': 10,
            'clinical': 50,
        }

        if category in min_questions and len(v) < min_questions[category]:
            raise ValueError(
                f'{category} assessments require at least '
                f'{min_questions[category]} questions'
            )
        return v
```

---

### 9.4 Low Priority Enhancements

#### 1. Add Semantic Validation
```python
@validator('responses')
def validate_response_semantics(cls, v, values):
    """Validate response values make sense for question types"""
    question_type = values.get('question_type')

    for response in v:
        if question_type == 'likert':
            if not 1 <= response <= 5:
                raise ValueError('Likert responses must be 1-5')
        elif question_type == 'yes_no':
            if response not in [True, False]:
                raise ValueError('Yes/No responses must be boolean')

    return v
```

#### 2. Add Conditional Validation
```python
class QuestionCreate(BaseModel):
    question_type: str
    config: Optional[Dict[str, Any]]

    @validator('config')
    def validate_config_for_type(cls, v, values):
        """Ensure config matches question type"""
        question_type = values.get('question_type')

        if question_type == 'multiple_choice' and not v:
            raise ValueError('Multiple choice requires config with options')

        if question_type == 'multiple_choice' and 'options' not in v:
            raise ValueError('Multiple choice config must include options')

        if question_type == 'rating_scale':
            min_val = v.get('min', 1)
            max_val = v.get('max', 5)
            if min_val >= max_val:
                raise ValueError('Rating scale min must be less than max')

        return v
```

#### 3. Add Localization Validation
```python
def validate_localized_text(text: Dict[str, str], required_langs: List[str]):
    """Validate all required languages are present"""
    missing = set(required_langs) - set(text.keys())
    if missing:
        raise HTTPException(
            400,
            f'Missing translations for: {", ".join(missing)}'
        )

    for lang, translation in text.items():
        if not translation.strip():
            raise HTTPException(400, f'Empty translation for {lang}')
```

---

### 9.5 Testing Recommendations

#### Validation Test Cases
```python
# Test framework
import pytest
from fastapi.testclient import TestClient

def test_password_validation(client: TestClient):
    """Test all password validation rules"""

    # Too short
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "Short1!",
        "full_name": "Test User"
    })
    assert response.status_code == 422

    # Missing uppercase
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "alllowercase1!",
        "full_name": "Test User"
    })
    assert response.status_code == 422

    # Common password
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "Password123!",
        "full_name": "Test User"
    })
    assert response.status_code == 422

    # Valid password
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecureP@ssw0rd123!XYZ",
        "full_name": "Test User"
    })
    assert response.status_code in [200, 201]

def test_sql_injection_prevention(client: TestClient):
    """Test SQL injection patterns are blocked"""

    malicious_inputs = [
        "admin'--",
        "admin' OR '1'='1",
        "'; DROP TABLE users; --",
        "admin' UNION SELECT * FROM users--",
    ]

    for payload in malicious_inputs:
        response = client.post("/auth/login", data={
            "username": payload,
            "password": "password"
        })
        assert response.status_code == 401

def test_xss_prevention(client: TestClient):
    """Test XSS patterns are blocked"""

    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img onerror='alert(1)'>",
        "<svg onload=alert(1)>",
    ]

    for payload in xss_payloads:
        response = client.put("/users/me", json={
            "full_name": payload
        })
        # Should either reject or sanitize
        assert payload not in response.json()['full_name']
```

---

## 10. Quick Reference

### 10.1 Common Validation Patterns

#### Email Validation
```python
from pydantic import EmailStr

email: EmailStr  # Validates format, max 254 chars, local max 64 chars
```

#### UUID Validation
```python
from uuid import UUID

user_id: UUID  # Validates UUID format
```

#### String Length
```python
from pydantic import Field

name: str = Field(..., min_length=1, max_length=255)
```

#### Numeric Ranges
```python
age: int = Field(..., ge=0, le=150)
price: float = Field(..., gt=0, le=1000000)
```

#### Regex Validation
```python
from pydantic import validator

class User(BaseModel):
    username: str

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', v):
            raise ValueError('Invalid username')
        return v
```

#### Conditional Validation
```python
from pydantic import root_validator

class Assessment(BaseModel):
    category: str
    questions: List[Question]

    @root_validator
    def validate_assessment(cls, values):
        category = values.get('category')
        questions = values.get('questions', [])

        if category == 'clinical' and len(questions) < 50:
            raise ValueError('Clinical assessments require 50+ questions')

        return values
```

---

### 10.2 Error Response Format

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 12 characters long",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Custom Error:**
```json
{
  "success": false,
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "password",
    "issues": ["Too short", "Missing uppercase"]
  },
  "timestamp": "2026-01-04T00:00:00Z",
  "request_id": "uuid"
}
```

---

### 10.3 Status Codes

| Code | Usage | Example |
|------|-------|---------|
| 200 | Success | GET /users/me |
| 201 | Created | POST /assessments/ |
| 204 | No Content | DELETE /assessments/{id} |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Invalid credentials |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource doesn't exist |
| 413 | Payload Too Large | Request > 10MB |
| 415 | Unsupported Media | Wrong Content-Type |
| 422 | Validation Error | Pydantic validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Unexpected error |

---

## Appendix A: Validation Utilities

### Available Validators

1. **InputValidator** (`/app/core/input_validation.py`)
   - `validate_uuid()`
   - `validate_email()`
   - `validate_safe_string()`
   - `validate_pagination_params()`
   - `validate_sort_params()`
   - `validate_json_data()`
   - `sanitize_search_term()`
   - `validate_file_upload()`

2. **SecurityValidator** (`/app/core/security_validator.py`)
   - `validate_uuid()` (with injection checks)
   - `validate_email()` (with injection checks)
   - `validate_text_input()`
   - `validate_dict_input()`

3. **EnterprisePasswordValidator** (`/app/core/password_validator.py`)
   - `validate_password()`
   - `assess_strength()`
   - `_calculate_entropy()`
   - `_is_common_password()`
   - `_has_sequential_pattern()`
   - `_has_repeated_pattern()`

---

## Appendix B: Security Patterns

### SQL Injection Prevention
```python
# BAD - String concatenation
query = f"SELECT * FROM users WHERE email = '{email}'"

# GOOD - Parameterized query
result = await db.execute(
    select(User).where(User.email == email.lower())
)
```

### XSS Prevention
```python
# BAD - Direct return
return {"message": user_input}

# GOOD - Sanitization
from html import escape
return {"message": escape(user_input)}
```

### Path Traversal Prevention
```python
# BAD - Direct path
path = f"/uploads/{filename}"

# GOOD - Validation and sanitization
from pathlib import Path
safe_path = Path("/uploads").resolve()
requested_path = (safe_path / filename).resolve()
if not requested_path.is_relative_to(safe_path):
    raise HTTPException(400, "Invalid path")
```

---

**Document Version:** 2.0
**Last Reviewed:** 2026-01-04
**Next Review:** 2026-02-04

For questions or issues, contact the Security Team.
