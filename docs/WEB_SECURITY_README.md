# Web Application Security Implementation Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-26
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Secure Defaults](#secure-defaults)
3. [Security Utilities](#security-utilities)
4. [Implementation Examples](#implementation-examples)
5. [Trade-offs and Decisions](#trade-offs-and-decisions)
6. [Testing Security](#testing-security)
7. [CI/CD Integration](#cicd-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This document describes the comprehensive web application security implementation for PsychSync, following OWASP Top 10 security best practices.

### What We've Implemented

| Component | File | Purpose | Tests |
|-----------|------|---------|-------|
| **Parameterized Queries** | `app/core/secure_query.py` | Prevent SQL injection | ✅ |
| **Input Validation** | `app/core/input_validation.py` | Validate all user input | ✅ |
| **Output Encoding** | `app/core/output_encoding.py` | Prevent XSS attacks | ✅ |
| **Safe File Handling** | `app/core/safe_file_handling.py` | Prevent file-based attacks | ✅ |
| **OWASP Analysis** | `docs/OWASP_SECURITY_ANALYSIS.md` | Complete threat analysis | ✅ |
| **Security Tests** | `tests/unit/test_web_security.py` | 50+ security tests | ✅ |
| **Semgrep Rules** | `semgrep_rules/web_security.yml` | 30+ security rules | ✅ |

### Quick Stats

- **Lines of Security Code**: ~3,500+
- **Security Tests**: 50+ unit/integration tests
- **Semgrep Rules**: 35+ automated security checks
- **OWASP Coverage**: 10/10 Top 10 risks addressed
- **Documentation**: 5 comprehensive guides

---

## Secure Defaults

We follow the principle of **"Secure by Default"** - all configurations prioritize security over convenience.

### Password Security

```python
# Default: Argon2 with strong parameters
- Algorithm: Argon2id (Password Hashing Competition winner)
- Memory cost: 64 MB
- Time cost: 3 iterations
- Parallelism: 4 threads
- Minimum length: 12 characters
- Required: uppercase, lowercase, digit, special char
```

**Trade-off**: Higher computational cost for better security. Argon2 is slower than bcrypt but more resistant to GPU/ASIC attacks.

### Session Security

```python
# Default: Secure session cookies
- httpOnly: True (prevents XSS cookie theft)
- Secure: True (HTTPS only in production)
- SameSite: "lax" (CSRF protection)
- Max age: 30 minutes
- Expiration: Refresh tokens every 30 minutes
```

**Trade-off**: Shorter sessions require more frequent re-authentication, improving security at the cost of user convenience.

### TLS Configuration

```python
# Default: Strong TLS only
- Min version: TLS 1.2
- Ciphers: Only strong cipher suites
- HSTS: Enabled with 1-year max-age
- Certificate: Valid, signed by trusted CA
```

**Trade-off**: Excluding old TLS versions and weak ciphers breaks compatibility with very old browsers (IE < 11).

### File Upload Security

```python
# Default: Strict validation
- Max size: 100 MB (configurable)
- Allowed types: Whitelist only (text, CSV, JSON, PDF, images, Office docs)
- Blocked extensions: .exe, .bat, .sh, .js, etc.
- MIME verification: Magic bytes check
- Filename sanitization: Remove path traversal chars
```

**Trade-off**: Strict validation prevents some legitimate files. Users must convert files to allowed formats.

---

## Security Utilities

### 1. Parameterized Queries

**Location**: `app/core/secure_query.py`

**Purpose**: Prevent SQL injection by enforcing parameterized queries.

```python
from app.core.secure_query import SecureQueryExecutor
from app.db.models import User

async def get_user_safe(user_id: int):
    executor = SecureQueryExecutor(session)

    # ✅ SAFE: Parameterized by default
    user = await executor.fetch_one(
        select(User).where(User.id == user_id)
    )

    return user

# ❌ UNSAFE: Never do this!
# query = f"SELECT * FROM users WHERE id = {user_id}"
# result = session.execute(text(query))
```

**Usage in Controllers**:

```python
from fastapi import Depends
from app.core.database import get_db

@app.get("/api/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db)
):
    # Input validation
    user_id = InputValidator.validate_integer(
        user_id,
        min_val=1,
        max_val=1000000
    )

    # Safe query
    executor = SecureQueryExecutor(session)
    user = await executor.fetch_one(
        select(User).where(User.id == user_id)
    )

    return user
```

**Key Features**:
- All queries use parameterized :parameter syntax
- Automatic parameterization for ORM queries
- Input sanitization (null bytes, dangerous patterns)
- Whitelist validation for sort fields

**Trade-off**: Parameterized queries require more verbose code than raw SQL, but prevent SQL injection completely.

---

### 2. Input Validation

**Location**: `app/core/input_validation.py`

**Purpose**: Validate all user input against security rules.

```python
from app.core.input_validation import InputValidator

# Validate email
email = InputValidator.validate_email("user@example.com")

# Validate integer
age = InputValidator.validate_integer(age_str, min_val=18, max_val=120)

# Validate string
name = InputValidator.validate_string(
    name_input,
    min_length=1,
    max_length=100,
    pattern=r'^[a-zA-Z\s\-\.]+$'  # Only letters, spaces, hyphen, dot
)

# Validate URL
url = InputValidator.validate_url(user_url)
# Blocks: javascript:, data:, vbscript: protocols

# Validate file path
safe_path = InputValidator.validate_file_path(
    user_path,
    base_dir="/var/www/uploads"
)
# Blocks: ../../../etc/passwd attacks
```

**Request Validation**:

```python
from app.core.input_validation import RequestValidator

@app.post("/api/users")
async def create_user(data: dict):
    validator = RequestValidator()

    rules = {
        "email": {
            "type": "email",
            "required": True
        },
        "username": {
            "type": "alphanumeric",
            "min_length": 3,
            "max_length": 30,
            "required": True
        },
        "age": {
            "type": "integer",
            "min_val": 18,
            "max_val": 120,
            "required": False
        }
    }

    is_valid, errors, sanitized = validator.validate(data, rules)

    if not is_valid:
        raise HTTPException(status_code=422, detail=errors)

    # Use sanitized data
    return await create_user_record(sanitized)
```

**Key Features**:
- Type validation (string, int, float, bool, email, URL, etc.)
- Length limits (min/max)
- Pattern matching (regex)
- Dangerous pattern detection (XSS, injection attempts)
- Null byte removal

**Trade-off**: Strict validation may reject some valid edge cases (e.g., international email formats). Adjust based on requirements.

---

### 3. Output Encoding

**Location**: `app/core/output_encoding.py`

**Purpose**: Prevent XSS by encoding output for each context.

**Context-Aware Encoding**:

```python
from app.core.output_encoding import OutputEncoder

user_input = '<script>alert("XSS")</script>'

# HTML body context
safe_html = OutputEncoder.encode_for_html(user_input)
# Output: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;

# HTML attribute context
safe_attr = OutputEncoder.encode_for_html_attribute(user_input)
# Output: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;

# JavaScript context
safe_js = OutputEncoder.encode_for_javascript(user_input)
# Output: \x3Cscript\x3Ealert(\x22XSS\x22)\x3C/script\x3E

# URL context
safe_url = OutputEncoder.encode_for_url(user_input)
# Output: %3Cscript%3Ealert%28%22XSS%22%29%3C%2Fscript%3E

# JSON context
safe_json = OutputEncoder.encode_for_json({"data": user_input})
# Output: {"data":"<script>alert(\"XSS\")<\/script>"}
```

**Template Integration**:

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.core.output_encoding import OutputEncoder

@app.get("/profile/{username}")
async def profile(username: str, request: Request):
    # Validate username
    safe_username = InputValidator.validate_alphanumeric(username)

    # Get user data
    user = await get_user(safe_username)

    # Encode for HTML context
    safe_name = OutputEncoder.encode_for_html(user.name)
    safe_bio = OutputEncoder.encode_for_html(user.bio)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "name": safe_name,
        "bio": safe_bio
    })
```

**Key Features**:
- Context-specific encoding (HTML, HTML attr, JS, CSS, URL, JSON, XML)
- Unicode handling
- Script tag detection
- Protocol validation for URLs

**Trade-off**: Output encoding adds processing overhead. Cache pre-encoded data when possible.

---

### 4. Safe File Handling

**Location**: `app/core/safe_file_handling.py`

**Purpose**: Prevent file-based attacks (path traversal, zip slip, file bombs).

```python
from app.core.safe_file_handling import SafeFileHandler, FileValidationError
from fastapi import UploadFile

@app.post("/api/upload")
async def upload_file(file: UploadFile):
    # Read file with size limit
    content = await SecureFileUpload.read_upload(
        file,
        max_size=100 * 1024 * 1024  # 100 MB
    )

    # Validate file
    try:
        result = SafeFileHandler.validate_file_upload(
            content,
            file.filename,
            max_size=100 * 1024 * 1024
        )
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save with safe filename
    saved_path = SafeFileHandler.save_upload(
        content,
        file.filename,
        "/var/www/uploads"
    )

    return {"filename": saved_path}
```

**Archive Extraction**:

```python
from app.core.safe_file_handling import SafeFileHandler

@app.post("/api/upload-zip")
async def upload_zip(file: UploadFile):
    # Save uploaded ZIP
    content = await file.read()
    zip_path = SafeFileHandler.save_upload(content, file.filename, "/tmp")

    # Extract safely (prevents zip-slip)
    try:
        extracted = SafeFileHandler.extract_zip(
            zip_path,
            "/var/www/uploads",
            max_files=1000,
            max_total_size=1024 * 1024 * 1024  # 1 GB
        )
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"extracted_files": extracted}
```

**Key Features**:
- Path traversal prevention (blocks ../..)
- File size validation
- MIME type verification (magic bytes)
- Extension whitelisting
- Zip-slip protection
- Arbitrary file write prevention

**Trade-off**: Strict file validation may inconvenience users. Balance security with usability based on threat model.

---

## Implementation Examples

### Example 1: Secure User Registration

```python
from fastapi import APIRouter, HTTPException, Depends
from app.core.input_validation import InputValidator, RequestValidator
from app.core.secure_query import SecureQueryExecutor
from app.services.password_service import hash_password

router = APIRouter()

@router.post("/api/auth/register")
async def register(
    data: dict,
    session: AsyncSession = Depends(get_db)
):
    validator = RequestValidator()

    # Define validation rules
    rules = {
        "email": {
            "type": "email",
            "required": True
        },
        "username": {
            "type": "alphanumeric",
            "min_length": 3,
            "max_length": 30,
            "required": True
        },
        "password": {
            "type": "string",
            "min_length": 12,
            "max_length": 128,
            "required": True
        }
    }

    # Validate input
    is_valid, errors, sanitized = validator.validate(data, rules)

    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={"message": "Validation failed", "errors": errors}
        )

    # Validate password strength
    from app.services.password_policy import PasswordValidator
    pwd_validator = PasswordValidator()

    is_strong, pwd_errors = pwd_validator.validate(sanitized["password"])
    if not is_strong:
        raise HTTPException(
            status_code=422,
            detail={"message": "Weak password", "errors": pwd_errors}
        )

    # Check if email exists
    executor = SecureQueryExecutor(session)
    existing = await executor.fetch_or_none(
        select(User).where(User.email == sanitized["email"])
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Hash password (Argon2)
    hashed_pw = hash_password(sanitized["password"])

    # Create user (parameterized query)
    user = await executor.insert_one(
        User,
        {
            "email": sanitized["email"],
            "username": sanitized["username"],
            "hashed_password": hashed_pw,
            "is_active": True,
            "is_verified": False
        }
    )

    # Return safe response (no password)
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username
    }
```

### Example 2: Secure File Upload with Validation

```python
from fastapi import UploadFile, File
from app.core.safe_file_handling import (
    SafeFileHandler,
    SecureFileUpload,
    FileValidationError
)

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Define allowed types
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.csv', '.txt']
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'text/plain'
    }

    # Read file (size limit enforced)
    try:
        content = await SecureFileUpload.read_upload(
            file,
            max_size=10 * 1024 * 1024  # 10 MB
        )
    except FileValidationError as e:
        raise HTTPException(status_code=413, detail=str(e))

    # Validate file
    try:
        # Update allowed types
        SafeFileHandler.ALLOWED_MIME_TYPES = ALLOWED_MIME_TYPES

        result = SafeFileHandler.validate_file_upload(
            content,
            file.filename,
            content_type=file.content_type,
            max_size=10 * 1024 * 1024
        )
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate safe filename
    from datetime import datetime
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ext = result['extension']
    safe_filename = f"{current_user.id}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"

    # Save file
    upload_dir = f"/var/www/uploads/documents/{current_user.id}"
    saved_path = SafeFileHandler.save_upload(
        content,
        safe_filename,
        upload_dir
    )

    # Record in database
    await create_document_record(
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename,
        mime_type=result['mime_type'],
        size=result['size']
    )

    return {
        "filename": safe_filename,
        "size": result['size']
    }
```

### Example 3: XSS Prevention in API Response

```python
from fastapi import APIRouter
from app.core.output_encoding import OutputEncoder
from app.core.input_validation import InputValidator

router = APIRouter()

@router.get("/api/users/search")
async def search_users(q: str):
    # Validate and sanitize search query
    safe_query = InputValidator.sanitize_search_term(q)

    # Search database (parameterized)
    users = await search_users_by_name(safe_query)

    # Encode output for JSON context
    safe_results = []
    for user in users:
        safe_results.append({
            "id": user.id,
            "username": OutputEncoder.encode_for_html(user.username),
            "email": OutputEncoder.encode_for_html(user.email),
            "bio": OutputEncoder.encode_for_html(user.bio or "")
        })

    return {"results": safe_results}

@router.get("/api/reports/{report_id}")
async def get_report(report_id: int, request: Request):
    # Get report
    report = await get_report_by_id(report_id)

    # Validate ownership
    if report.user_id != request.state.user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Return report with user data encoded
    return {
        "id": report.id,
        "title": OutputEncoder.encode_for_html(report.title),
        "content": OutputEncoder.encode_for_html(report.content)
    }
```

---

## Trade-offs and Decisions

### Security vs Usability

We've made deliberate trade-offs prioritizing security:

| Decision | Security Benefit | Usability Impact | Rationale |
|----------|-----------------|------------------|-----------|
| **Argon2 for passwords** | Resistant to GPU/ASIC attacks | Slower hash (100-200ms) | Security > speed (auth is infrequent) |
| **30-min session timeout** | Limits exposure if stolen | Users re-auth more often | Security > convenience |
| **Strict file validation** | Prevents malware uploads | Users must convert files | Whitelist > blacklist |
| **HSTS max-age=1 year** | Forces HTTPS for year | Cannot downgrade TLS | Prevents downgrade attacks |
| **No HTML in inputs** | Prevents stored XSS | Rich text not allowed | Security > features |
| **Strong password policy** | Prevents brute force | Users must use complex passwords | Security > ease |

**Adjusting Trade-offs**:

```python
# If you need different trade-offs for your use case:

# Example: Allow longer sessions (less secure, more convenient)
SESSION_TIMEOUT_MINUTES = 120  # 2 hours instead of 30

# Example: Allow rich text with sanitization
from app.core.output_encoding import OutputEncoder
ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
html_content = OutputEncoder.sanitize_html(user_input, allowed_tags=ALLOWED_HTML_TAGS)

# Example: Relax password policy for internal tools
MIN_PASSWORD_LENGTH = 8  # Lower for low-risk apps
```

### Technology Choices

**Why SQLAlchemy ORM?**
- ✅ Automatic parameterization (prevents SQL injection)
- ✅ Database-agnostic
- ❌ Performance overhead (acceptable for our use case)

**Why Argon2 for passwords?**
- ✅ Winner of Password Hashing Competition 2015
- ✅ Resistant to GPU/ASIC attacks
- ✅ Memory-hard (protects against hardware attacks)
- ❌ Slower than bcrypt (acceptable for infrequent auth)

**Why JWT for sessions?**
- ✅ Stateless (scalable)
- ✅ Built-in expiration
- ✅ No server-side session storage
- ❌ No revocation (require blacklist for logout)

**Why Semgrep for scanning?**
- ✅ Fast, pattern-based detection
- ✅ Custom rules for our codebase
- ✅ CI/CD integration
- ❌ May have false positives (tune rules)

---

## Testing Security

### Unit Tests

Run security unit tests:

```bash
# Run all security tests
pytest tests/unit/test_web_security.py -v

# Run specific test class
pytest tests/unit/test_web_security.py::TestOutputEncoding -v

# Run with coverage
pytest tests/unit/test_web_security.py --cov=app.core --cov-report=html
```

### Integration Tests

```bash
# Run security integration tests
pytest tests/integration/test_security_integration.py -v
```

### Manual Security Testing

**1. SQL Injection Testing**

```python
# Test payloads to verify protection
sql_payloads = [
    "1 OR 1=1",
    "1'; DROP TABLE users--",
    "1' UNION SELECT * FROM users--",
    "1' OR '1'='1",
    "admin'--"
]

for payload in sql_payloads:
    # Should be validated/sanitized
    # Should NOT reach database unescaped
    response = client.get(f"/api/users/{payload}")
    assert response.status_code != 200
```

**2. XSS Testing**

```python
# Test XSS payloads
xss_payloads = [
    '<script>alert("XSS")</script>',
    '<img src=x onerror=alert("XSS")>',
    '<svg onload=alert("XSS")>',
    '"><script>alert(String.fromCharCode(88,83,83))</script>',
    'javascript:alert("XSS")',
    '" onfocus="alert(1)'
]

for payload in xss_payloads:
    # Should be encoded/escaped
    response = client.post("/api/profile", json={"bio": payload})

    # Check response doesn't contain raw XSS
    assert payload not in response.text
    assert '&lt;script&gt;' in response.text or 'alert' not in response.text
```

**3. Path Traversal Testing**

```python
# Test path traversal payloads
path_traversal_payloads = [
    '../../../etc/passwd',
    '..\\..\\..\\windows\\system32\\config\\sam',
    '/etc/passwd',
    '....//....//etc/passwd',
    '%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
]

for payload in path_traversal_payloads:
    # Should be blocked
    response = client.post("/api/files", json={"filename": payload})
    assert response.status_code in [400, 403, 404]
```

---

## CI/CD Integration

### Semgrep Scanning

**GitHub Actions Workflow**:

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  semgrep:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: semgrep_rules/web_security.yml

      # Upload results as PR comments
      - name: Semgrep PR Comment
        uses: mikesprague/semgrep-pr-comment-action@v1.0.0
        if: github.event_name == 'pull_request'
```

**Local Scanning**:

```bash
# Install Semgrep
pip install semgrep

# Run security scan
semgrep --config=semgrep_rules/web_security.yml .

# Scan specific directory
semgrep --config=semgrep_rules/web_security.yml app/

# Generate SARIF for GitHub
semgrep --config=semgrep_rules/web_security.yml --sarif -o results.sarif .
```

### OWASP ZAP (DAST)

**Run automated DAST scan**:

```bash
# Install OWASP ZAP
brew install zap  # macOS
# or download from https://www.zaproxy.org/

# Run baseline scan
zap-baseline.py -t http://localhost:8000

# Generate report
zap-cli quick-scan --self-contained http://localhost:8000 -o zap-report.html
```

### Dependency Scanning

```bash
# Python dependencies
pip-audit --desc

# Node.js dependencies
cd frontend
npm audit

# Container scanning
trivy image psychsync:latest
```

---

## Best Practices

### 1. Never Trust User Input

```python
# ❌ WRONG
@app.get("/api/items/{id}")
async def get_item(id: str):
    query = f"SELECT * FROM items WHERE id = {id}"
    return db.execute(query)

# ✅ CORRECT
@app.get("/api/items/{id}")
async def get_item(id: int):
    # Validate ID
    id = InputValidator.validate_integer(id, min_val=1)

    # Use parameterized query
    query = select(Item).where(Item.id == id)
    return await db.execute(query)
```

### 2. Always Encode Output

```python
# ❌ WRONG
return {"name": user.name}  # May contain <script>

# ✅ CORRECT
return {
    "name": OutputEncoder.encode_for_html(user.name)
}
```

### 3. Validate Files Before Processing

```python
# ❌ WRONG
with open(filename, 'wb') as f:
    f.write(file_content)

# ✅ CORRECT
# 1. Validate filename
safe_filename = SafeFileHandler.validate_filename(filename)

# 2. Validate file content
result = SafeFileHandler.validate_file_upload(
    file_content,
    safe_filename,
    max_size=100 * 1024 * 1024
)

# 3. Save in safe location
safe_path = SafeFileHandler.save_upload(
    file_content,
    safe_filename,
    base_dir="/var/www/uploads"
)
```

### 4. Use Prepared Statements

```python
# ❌ WRONG
cur.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ CORRECT
cur.execute("SELECT * FROM users WHERE email = :email", {"email": email})
```

### 5. Implement Proper Error Handling

```python
# ❌ WRONG - Exposes internal details
@app.exception_handler(Exception)
async def handle_exception(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": traceback.format_exc()}  # LEAKS!
    )

# ✅ CORRECT - Generic error messages
@app.exception_handler(Exception)
async def handle_exception(request, exc):
    logger.error(f"Error: {exc}", exc_info=True)

    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
```

---

## Troubleshooting

### Issue: "Validation failed for legitimate input"

**Cause**: Validation rules too strict.

**Solution**:

```python
# Relax validation (only after security review!)

# Example: Allow longer strings
result = InputValidator.validate_string(
    user_input,
    min_length=1,
    max_length=5000  # Increased from 1000
)

# Example: Allow more characters
result = InputValidator.validate_string(
    user_input,
    pattern=r'^[a-zA-Z0-9\s\-\._@#$%^&*()]+'  # Added special chars
)
```

### Issue: "File upload blocked incorrectly"

**Cause**: MIME type mismatch or extension not in whitelist.

**Solution**:

```python
# Add allowed MIME type
SafeFileHandler.ALLOWED_MIME_TYPES.add('application/vnd.ms-excel')

# Add allowed extension
ALLOWED_EXTENSIONS.append('.xls')
```

### Issue: "Semgrep false positives"

**Cause**: Pattern matches safe code.

**Solution**:

1. Update rule to be more specific
2. Add `nosemgrep` comment for false positive:

```python
# semgrep: python.sql-injection.string-concat
query = text(f"SELECT * FROM table WHERE id = {value}")  # False positive: value is validated
```

3. Or disable specific rules:

```yaml
# .semgrepignore
semgrep_rules/web_security.yml:sql-injection-string-concat
```

---

## Security Checklist

Use this checklist for new features:

- [ ] All user input is validated (type, length, format)
- [ ] All SQL queries use parameters (no string concatenation)
- [ ] All output is encoded for the correct context
- [ ] File uploads are validated (type, size, magic bytes)
- [ ] Filenames are sanitized (no path traversal)
- [ ] Error messages don't expose sensitive data
- [ ] Authentication checks are present
- [ ] Authorization checks are present
- [ ] CSRF protection is enabled
- [ ] Security headers are configured
- [ ] Secrets are in environment variables
- [ ] Dependencies are scanned for vulnerabilities
- [ ] Security tests are written and passing
- [ ] Semgrep scan passes

---

## Resources

- [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Semgrep Rules](https://semgrep.dev/)
- [CWE Top 25](https://cwe.mitre.org/top25/archive/2022/2022_top25_list.html)

---

**Status:** ✅ Production Ready
**Maintained By:** @security-team
**Last Updated:** 2025-12-26
