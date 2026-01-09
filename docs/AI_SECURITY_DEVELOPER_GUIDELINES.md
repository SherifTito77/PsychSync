# AI Security Developer Guidelines

**Version**: 1.0
**Date**: 2025-12-27
**Project**: PsychSync Platform
**Audience**: Developers using AI assistants

---

## Executive Summary

AI assistants (Claude, ChatGPT, Copilot, etc.) are powerful productivity tools but can introduce critical security vulnerabilities if not properly supervised. This document provides guidelines for safely using AI assistants in the development workflow.

### Key Principles

1. **Never trust AI-generated code blindly**
2. **Always review for security issues**
3. **Run security tools before committing**
4. **Test thoroughly in development**

---

## Part 1: Understanding AI-Introduced Vulnerabilities

### What Are They?

AI assistants frequently generate code with security vulnerabilities because:

- They're trained on public code (including vulnerable examples)
- They prioritize functionality over security
- They don't know your specific security requirements
- They can't check against your security policies

### Common Vulnerability Patterns

| Vulnerability | AI Pattern | Severity |
|--------------|-----------|----------|
| Command Injection | `subprocess.run(shell=True)` | CRITICAL |
| SQL Injection | `text(f"SELECT ... {user_input}")` | CRITICAL |
| Unsafe Deserialization | `pickle.loads(data)` | CRITICAL |
| Hardcoded Credentials | `password = "secret123"` | MEDIUM |
| Weak Cryptography | `hashlib.md5(data)` | MEDIUM |

---

## Part 2: Safe AI-Assisted Development Workflow

### Step 1: Request Code from AI

**DO** ✅:
```python
# Ask AI for:
"Generate a function to process user upload using subprocess without shell=True"
"Create a secure database query with parameterized inputs"
"Implement JSON serialization for cache storage"
```

**DON'T** ❌:
```python
# Don't use vague prompts that let AI choose implementation:
"Generate a function to execute system commands"
"Create a database query function"
"Implement cache serialization"
```

### Step 2: Security Review Checklist

Before using AI-generated code, verify:

- [ ] No `shell=True` in subprocess calls
- [ ] No `pickle.loads()` or `pickle.load()`
- [ ] No raw SQL with user input (use parameterized queries)
- [ ] No hardcoded credentials
- [ ] No `eval()` or `exec()` with user input
- [ ] No weak crypto (MD5, SHA1)
- [ ] Input validation on all user inputs
- [ ] Output encoding for XSS prevention

### Step 3: Test Security Tools

Run automated security checks:

```bash
# Pre-commit hooks (automatically run on commit)
pre-commit run --all-files

# Manual Semgrep scan
semgrep --config=semgrep_rules/ai-introduced-security.yaml

# Quick security check
python scripts/security-quickstart.sh
```

### Step 4: Manual Code Review

Review these specific areas when AI generates code:

#### Subprocess Usage
```python
# ❌ DANGEROUS - AI often suggests this
subprocess.run(f"command {user_input}", shell=True)

# ✅ SAFE - What you should use
subprocess.run(["command", user_input], shell=False)
```

#### SQL Queries
```python
# ❌ DANGEROUS - AI often suggests this
query = text(f"SELECT * FROM users WHERE email = '{user_input}'")

# ✅ SAFE - What you should use
query = text("SELECT * FROM users WHERE email = :email")
result = await session.execute(query, {"email": user_input})
```

#### Serialization
```python
# ❌ DANGEROUS - AI often suggests this
import pickle
data = pickle.loads(user_data)

# ✅ SAFE - What you should use
import json
data = json.loads(user_data)
```

### Step 5: Test Thoroughly

```python
# Test with malicious input
test_cases = [
    {"email": "admin@domain.com"},  # Valid input
    {"email": "admin' OR '1'='1"},  # SQL injection attempt
    {"email": "; DROP TABLE users--"},  # Command injection attempt
    {"email": "$(malicious_command)"},  # Command injection attempt
]

for test_case in test_cases:
    response = await process_email(test_case)
    assert response.status_code == 200 or response.status_code == 422
    assert "error" not in response.text.lower()
```

---

## Part 3: Vulnerability Prevention

### Command Injection Prevention

#### The Problem

AI assistants frequently use `shell=True` because it's convenient:

```python
# ❌ VULNERABLE - AI generated
subprocess.run(f"ffmpeg -i {video_path} -vn output.wav", shell=True)
```

**Attack Vector**:
```python
video_path = "file.mp3; rm -rf /; echo "
# Result: Executes rm -rf /
```

#### The Solution

Always use argument lists without shell:

```python
# ✅ SECURE
subprocess.run(
    ["ffmpeg", "-i", video_path, "-vn", "output.wav"],
    shell=False  # Critical!
)
```

#### Input Validation

Validate file paths before use:

```python
def is_safe_filepath(filepath: str) -> bool:
    """Validate filepath contains only safe characters"""
    import re
    safe_pattern = r'^[a-zA-Z0-9_\-./:]+$'
    return bool(re.match(safe_pattern, filepath))

# Use it
if not is_safe_filepath(video_path):
    raise ValueError("Invalid filepath")
```

### SQL Injection Prevention

#### The Problem

AI assistants use f-strings for SQL queries:

```python
# ❌ VULNERABLE - AI generated
query = text(f"SELECT * FROM users WHERE email = '{user_input}'")
```

**Attack Vector**:
```python
user_input = "admin' OR '1'='1"
# Result: Bypasses authentication
```

#### The Solution

Use parameterized queries:

```python
# ✅ SECURE
query = text("SELECT * FROM users WHERE email = :email")
result = await session.execute(query, {"email": user_input})
```

#### Table Name Safety

For table names (can't be parameterized):

```python
from app.core.secure_sql import validate_table_name, quote_identifier

# ✅ SECURE
validate_table_name(table_name)
quoted_table = quote_identifier(table_name)
query = text(f"SELECT * FROM {quoted_table}")
```

### Unsafe Deserialization Prevention

#### The Problem

AI assistants use pickle for serialization:

```python
# ❌ VULNERABLE - AI generated
import pickle
data = pickle.loads(user_data)
```

**Attack Vector**:
```python
# Attacker crafts malicious pickle
malicious = b"cos\nsystem\n(S'rm -rf /')\ntR."
# Result: Executes arbitrary code
```

#### The Solution

Use JSON serialization:

```python
# ✅ SECURE
from app.core.secure_serialization import json_serialize, json_deserialize

serialized = json_serialize(data)
deserialized = json_deserialize(serialized)
```

### Hardcoded Credentials Prevention

#### The Problem

AI assistants hardcode credentials for convenience:

```python
# ❌ VULNERABLE - AI generated
password = "SuperSecret123!"
api_key = "sk_live_abc123"
```

#### The Solution

Use environment variables:

```python
# ✅ SECURE
import os
password = os.getenv("DB_PASSWORD")
api_key = os.getenv("API_KEY")

# With defaults
password = os.getenv("DB_PASSWORD", "")
```

---

## Part 4: Safe AI Prompting Patterns

### Bad Prompts ❌

```python
# Too vague - AI chooses implementation
"Write a function to execute system commands"

# No security constraints
"Generate code to process user input"

# Dangerous request
"Create a quick way to evaluate user expressions"
```

### Good Prompts ✅

```python
# Specific about security
"Generate a function to process video files using ffmpeg with subprocess.
IMPORTANT: Use shell=False and argument lists to prevent command injection.
Validate file paths before use."

# Explicit about constraints
"Create a database query function to search users by email.
IMPORTANT: Use parameterized queries to prevent SQL injection.
Use SQLAlchemy's text() with :parameter syntax."

# Security-first
"Implement cache serialization for Redis.
IMPORTANT: Use JSON serialization only, no pickle.
Use the secure_serialization module."
```

### Prompt Template

Use this template for AI code requests:

```
Task: [describe what you need]

Security Requirements:
- No shell=True in subprocess calls
- No pickle for serialization
- No raw SQL with user input
- No hardcoded credentials
- No eval/exec with user input
- Input validation on all user inputs
- Parameterized queries for database access

Context:
- Using FastAPI with SQLAlchemy
- PostgreSQL database
- Redis for caching
- Production environment

Please generate secure code following these requirements.
```

---

## Part 5: Detection and Remediation

### Automated Detection

We have automated tools in place:

#### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
- id: semgrep-ai-security
  name: 🔒 Semgrep AI Security Scan
  entry: semgrep --config=semgrep_rules/ai-introduced-security.yaml
```

**Install**:
```bash
pip install pre-commit
pre-commit install
```

#### CI/CD Gate

```yaml
# .github/workflows/ai-security-gate.yml
ai-security-scan:
  - Semgrep scan with AI rules
  - Blocks PR if critical issues found
```

#### Manual Scan

```bash
# Run anytime
semgrep --config=semgrep_rules/ai-introduced-security.yaml

# Quick scan for specific patterns
grep -r "shell=True" app/ --include="*.py"
grep -r "pickle.loads" app/ --include="*.py"
```

### What to Do When Issues Are Found

1. **Don't commit** the code
2. **Review the vulnerability** - understand why it's dangerous
3. **Fix the code** using the patterns in this guide
4. **Re-scan** to verify the fix
5. **Test** with malicious inputs

---

## Part 6: Real-World Examples

### Example 1: File Upload Processing

**AI Generated (VULNERABLE)** ❌:
```python
def process_video(video_path: str):
    # AI suggested this
    subprocess.run(f"ffmpeg -i {video_path} output.wav", shell=True)
```

**Fixed Version (SECURE)** ✅:
```python
def process_video(video_path: str):
    # Validate input
    if not is_safe_filepath(video_path):
        raise ValueError("Invalid filepath")

    # Use argument list
    subprocess.run(
        ["ffmpeg", "-i", video_path, "output.wav"],
        shell=False,  # Critical!
        check=True
    )
```

### Example 2: Database Query

**AI Generated (VULNERABLE)** ❌:
```python
async def get_user_by_email(email: str):
    # AI suggested this
    query = text(f"SELECT * FROM users WHERE email = '{email}'")
    result = await session.execute(query)
    return result.fetchone()
```

**Fixed Version (SECURE)** ✅:
```python
async def get_user_by_email(email: str):
    # Validate email format
    if not is_valid_email(email):
        raise ValueError("Invalid email format")

    # Use parameterized query
    query = text("SELECT * FROM users WHERE email = :email")
    result = await session.execute(query, {"email": email})
    return result.fetchone()
```

### Example 3: Cache Serialization

**AI Generated (VULNERABLE)** ❌:
```python
async def cache_data(data: dict):
    # AI suggested this
    serialized = pickle.dumps(data)
    await redis.set("key", serialized)
```

**Fixed Version (SECURE)** ✅:
```python
async def cache_data(data: dict):
    # Use JSON serialization
    from app.core.secure_serialization import serialize_for_cache

    serialized = serialize_for_cache(data)
    await redis.set("key", serialized)
```

---

## Part 7: Team Best Practices

### Code Review Process

When reviewing AI-generated code:

1. **Scan for dangerous patterns**
   - Look for `shell=True`
   - Look for `pickle.loads()`
   - Look for `text(f"...")` with variables

2. **Ask about security**
   - "How does this handle malicious input?"
   - "What if the user provides SQL injection?"
   - "Can an attacker execute arbitrary code?"

3. **Test with edge cases**
   - SQL injection strings
   - Command injection attempts
   - Malformed data
   - Extremely large inputs

### Pair Programming

When using AI assistants during pair programming:

1. **Driver** (Typing)
   - Reviews AI suggestions before accepting
   - Runs security checks
   - Tests with malicious inputs

2. **Navigator** (Observing)
   - Watches for security issues
   - Asks "what if" questions
   - Verifies security requirements

### Documentation

Document security decisions:

```python
def process_user_input(user_data: str) -> dict:
    """
    Process user input safely

    SECURITY:
    - Input validated against whitelist
    - SQL injection prevented via parameterized queries
    - Output encoded to prevent XSS
    - No command execution

    Args:
        user_data: User-provided input string

    Returns:
        Processed data dictionary

    Raises:
        ValueError: If input fails validation
    """
    # Implementation...
```

---

## Part 8: Learning Resources

### Internal Resources

- `docs/AI_SECURITY_FINAL_SUMMARY.md` - Vulnerability findings
- `docs/CACHE_LAYER_MIGRATION_GUIDE.md` - Serialization guide
- `semgrep_rules/ai-introduced-security.yaml` - Detection rules

### External Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE-78**: OS Command Injection
- **CWE-89**: SQL Injection
- **CWE-502**: Unsafe Deserialization
- **CWE-798**: Hardcoded Credentials

### Training

- Complete security awareness training
- Practice with secure coding exercises
- Review past security incidents
- Attend security workshops

---

## Part 9: Quick Reference

### Red Flags 🚩

Immediately reject code that contains:

```python
shell=True                              # Command injection
pickle.loads()                          # RCE vulnerability
text(f"...{variable}...")               # SQL injection
eval(user_input)                        # Code execution
exec(user_input)                        # Code execution
password = "..."                        # Hardcoded credentials
hashlib.md5()                           # Weak crypto
```

### Safe Alternatives ✅

```python
shell=False                             # Safe subprocess
json.loads()                            # Safe deserialization
text("... :param ...")                  # Parameterized query
ast.literal_eval()                      # Safe eval (trusted data only)
os.getenv("PASSWORD")                   # Environment variables
hashlib.sha256()                        # Strong crypto
```

### Before Committing

```bash
# 1. Run pre-commit hooks
pre-commit run --all-files

# 2. Run security scan
semgrep --config=semgrep_rules/ai-introduced-security.yaml

# 3. Run tests
pytest tests/

# 4. Manual review
git diff
```

---

## Part 10: Emergency Procedures

### If You Find a Vulnerability

1. **Stop** - Don't commit the code
2. **Isolate** - Don't deploy to production
3. **Report** - Notify security team
4. **Fix** - Use patterns from this guide
5. **Verify** - Test and scan again
6. **Document** - Learn from the incident

### Security Contact

- **Security Team**: security@psychsync.ai
- **Slack**: #security
- **Incident Response**: See docs/operations/INCIDENT_RESPONSE_RUNBOOK.md

---

## Summary

AI assistants are powerful tools but require careful supervision:

1. ✅ **Never trust blindly** - Always review AI-generated code
2. ✅ **Use security tools** - Pre-commit hooks, Semgrep, CI/CD gates
3. ✅ **Follow patterns** - Use safe alternatives from this guide
4. ✅ **Test thoroughly** - Include malicious inputs in tests
5. ✅ **Ask questions** - Verify security implications

**The automated tools will catch many issues, but human review is essential.**

---

**Remember**: The AI assistant doesn't understand security - YOU do!

**Questions?** Contact the Security Team
