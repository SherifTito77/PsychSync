# Documentation Quality Pre-commit Hook

> **Part of:** Phase 1 Code Quality Initiative
> **Added:** January 17, 2026
> **Purpose:** Automatically validate documentation quality on every commit

---

## Overview

The documentation quality pre-commit hook automatically validates all markdown documentation files before they can be committed. This prevents broken code examples, security issues, and incomplete documentation from reaching the codebase.

---

## What It Checks

### 1. **Security Issues** (CRITICAL)
- ❌ Hardcoded credentials (emails, passwords, API tokens)
- ❌ Default secret keys
- ❌ Exposed sensitive data

### 2. **Code Syntax** (HIGH)
- ✅ Valid JSON in code examples
- ✅ Valid Python syntax
- ✅ Valid bash script syntax
- ✅ Proper cURL command formatting

### 3. **Documentation Completeness** (MEDIUM)
- ✅ Error response examples present
- ✅ Rate limiting information included
- ✅ Parameter documentation complete
- ✅ Authentication information provided

### 4. **File Quality** (LOW)
- ✅ File size reasonable (< 1MB)
- ✅ Proper markdown formatting

---

## Installation

The hook is already configured in `.pre-commit-config.yaml`. To enable it:

```bash
# Navigate to project root
cd /Users/sheriftito/Downloads/psychsync

# Install pre-commit (if not already installed)
pip install pre-commit

# Install git hooks
pre-commit install

# Verify installation
pre-commit run --all-files
```

---

## Usage

### Automatic Validation (Recommended)

The hook runs automatically on every commit that includes markdown files:

```bash
# Edit a documentation file
vim docs/API_GUIDE.md

# Try to commit - hook runs automatically
git add docs/API_GUIDE.md
git commit -m "docs: update API guide"

# If hook fails, fix the issues and try again
git add .
git commit -m "docs: update API guide (fixed)"
```

### Manual Validation

You can also run the hook manually without committing:

```bash
# Run on all documentation files
pre-commit run documentation-quality --all-files

# Run on specific files only
pre-commit run documentation-quality --files docs/API_GUIDE.md

# Run on staged files only
pre-commit run documentation-quality
```

---

## Troubleshooting

### Hook Fails with Security Issues

**Problem:**
```
❌ Found 2 hardcoded credential(s) in corrected doc:
    Line 674: Hardcoded secret key
```

**Solution:**
Replace hardcoded values with environment variables:

```bash
# BEFORE (❌ Wrong)
SECRET_KEY": "my-secret-key"

# AFTER (✅ Correct)
SECRET_KEY": "$SECRET_KEY"
```

---

### Hook Fails with JSON Syntax Errors

**Problem:**
```
❌ Found 1 invalid JSON example(s):
    Line 48: JSON parse error: Expecting value...
```

**Solution:**
Validate your JSON using a linter or online tool:

```bash
# Use jq to validate
cat <<'EOF' | jq .
{
  "invalid": json,
}
EOF

# Fix the JSON
cat <<'EOF' | jq .
{
  "valid": "json"
}
EOF
```

---

### Hook Fails with Python Syntax Errors

**Problem:**
```
❌ Python syntax error: invalid syntax
```

**Solution:**
Test your Python code before committing:

```bash
# Compile check
python -m py_compile <<'EOF'
def example():
    print("test")
EOF
```

---

### Hook is Too Slow

**Problem:** Hook takes too long to run on every commit.

**Solution 1:** Skip the hook for this commit (not recommended):
```bash
git commit --no-verify -m "docs: quick fix"
```

**Solution 2:** Run on specific files only:
```bash
# Only check the file you're editing
pre-commit run documentation-quality --files docs/MY_FILE.md
```

**Solution 3:** Adjust when hook runs:
```bash
# Run only on pushes (not every commit)
git commit --no-verify -m "docs: wip"
# Push will still run the hook
git push
```

---

## Configuration

### Enable/Disable the Hook

**Temporarily disable:**
```bash
# Skip hook for one commit
git commit --no-verify -m "docs: emergency fix"
```

**Permanently disable:**
```yaml
# Edit .pre-commit-config.yaml
# Comment out or remove the documentation-quality section
```

**Re-enable:**
```bash
# Uncomment the section in .pre-commit-config.yaml
pre-commit install --hook-type pre-commit
```

---

## Customization

### Adjust Severity Levels

Edit `tests/documentation/run_doc_tests.py` to change what's checked:

```python
# Make security warnings less strict
# Change forbidden patterns in FORBIDDEN_PATTERNS list

# Add new security checks
FORBIDDEN_PATTERNS = [
    (r'["\']your@email\.com["\']', "Hardcoded email address"),
    # Add your patterns here
]
```

### Add New Checks

Add new test functions to `run_doc_tests.py`:

```python
def test_custom_check():
    """Your custom validation logic"""
    print_info("Test: Running custom check...")

    # Your validation code here

    print_success("Custom check passed ✅")
```

---

## Test Results

When the hook runs, you'll see output like this:

```
╔══════════════════════════════════════════════════════════════════╗
║         Documentation Code Examples Validation Tests             ║
║                    Phase 1 Code Quality Initiative               ║
╚══════════════════════════════════════════════════════════════════╝

======================================================================
                            SECURITY TESTS
======================================================================

ℹ️  Test 1: Checking original documentation for hardcoded credentials...
✅ No hardcoded credentials found in corrected doc ✅

[... more tests ...]

======================================================================
                             TEST SUMMARY
======================================================================

Total Tests:  12
Passed:       11
Failed:       1
Success Rate: 91.7%

✨ EXCELLENT! Documentation quality is high!

Documentation Quality Check..............................................Passed
```

---

## Performance

- **Average Runtime:** 2-5 seconds
- **Files Checked:** All markdown files in `docs/`
- **Impact:** Minimal on development workflow

---

## Best Practices

### 1. **Run Tests Before Committing**
```bash
# Quick check before committing
pre-commit run documentation-quality --all-files
```

### 2. **Fix Issues Immediately**
Don't commit with `--no-verify` unless absolutely necessary.

### 3. **Use the Template**
For new documentation, use the template:
```bash
cp docs/templates/API_DOCUMENTATION_TEMPLATE.md docs/NEW_FEATURE.md
```

### 4. **Review Test Output**
Read the test output carefully - it often provides specific guidance.

---

## Related Documentation

- **Template:** `docs/templates/API_DOCUMENTATION_TEMPLATE.md`
- **Tests:** `tests/documentation/run_doc_tests.py`
- **Phase 1 Guide:** `CODE_QUALITY_START_HERE.md`
- **Error Codes:** `docs/developer/ERROR_CODE_QUICK_REFERENCE.md`

---

## Support

**Hook not working?**
1. Check pre-commit is installed: `pre-commit --version`
2. Reinstall hooks: `pre-commit install`
3. Check file permissions: `ls -la .git/hooks/`

**Need to bypass hook?**
```bash
git commit --no-verify -m "docs: emergency bypass"
```

**Want to improve the hook?**
1. Edit `tests/documentation/run_doc_tests.py`
2. Test your changes: `python tests/documentation/run_doc_tests.py`
3. Commit your improvements

---

## Summary

✅ **Automatically validates** all documentation on every commit
✅ **Prevents security issues** from reaching production
✅ **Ensures code examples work** before documentation is published
✅ **Maintains quality standards** across all documentation
✅ **Zero configuration** required - just install and commit

---

**Last Updated:** January 17, 2026
**Framework:** Phase 1 Code Quality Initiative
**Methodology:** Measure → Categorize → Prioritize → Systematize
