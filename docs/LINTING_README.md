# PsychSync Linting and Code Quality

Comprehensive linting and code quality enforcement for the PsychSync project.

## Quick Start

### One-Time Setup

```bash
# Run the setup script
bash scripts/setup-linting.sh

# Or manually install tools
pip install ruff mypy bandit[toml] pre-commit
pre-commit install
cd frontend && npm install
```

### Daily Usage

```bash
# Before committing - hooks run automatically
git add .
git commit -m "feat: add feature"
# Pre-commit hooks run automatically

# If hooks fail, fix issues
ruff check --fix .               # Python linting
ruff format .                     # Python formatting
cd frontend && npm run lint:fix   # Frontend linting

# Try commit again
git add .
git commit -m "feat: add feature"
```

## Documentation

- **[Code Quality Standards](CODE_QUALITY_STANDARDS.md)** - Comprehensive coding standards
- **[Quick Start Guide](LINTING_QUICKSTART.md)** - Daily command reference
- **[Implementation Summary](LINTING_IMPLEMENTATION_SUMMARY.md)** - Technical details

## Configuration Files

| File | Purpose |
|------|---------|
| `ruff.toml` | Python linting and formatting rules |
| `pyproject.toml` | pytest, coverage, mypy config |
| `.bandit` | Security scanning configuration |
| `frontend/eslint.config.js` | TypeScript/React linting rules |
| `.editorconfig` | Editor settings (indentation, line endings) |
| `.pre-commit-config.yaml` | Pre-commit hook definitions |
| `.github/workflows/lint.yml` | CI linting workflow |

## What Gets Checked

### Python (Backend)
- ✅ Code style (PEP 8 + custom rules)
- ✅ Import organization
- ✅ Type annotations
- ✅ Security vulnerabilities
- ✅ Code complexity
- ✅ Bug patterns
- ✅ Modern Python syntax

### TypeScript/React (Frontend)
- ✅ Type safety (strict mode)
- ✅ React best practices
- ✅ Accessibility (a11y)
- ✅ Import organization
- ✅ Code formatting
- ✅ Security issues

### Security
- ✅ SQL injection
- ✅ Hardcoded secrets
- ✅ Insecure dependencies
- ✅ OWASP Top 10 patterns

## Benefits

### For Developers
- **Auto-fix**: Most issues fixed automatically
- **Clear errors**: Helpful error messages
- **Consistent style**: No debates about formatting
- **Better IDE**: Improved autocomplete and error detection

### For Teams
- **Code reviews**: Focus on logic, not style
- **Onboarding**: Clear standards for new developers
- **Quality**: Fewer bugs in production
- **Security**: Vulnerabilities caught early

### For Project
- **Maintainability**: Easier to understand and modify
- **Reliability**: Fewer runtime errors
- **Security**: Proactive vulnerability scanning
- **Consistency**: Uniform code across codebase

## CI/CD Integration

Linting runs automatically on:
- Pull requests (required before merge)
- Push to `main` or `develop` branches
- Manual trigger via GitHub Actions

**Required checks:**
- Python linting (blocking)
- Frontend linting (blocking)

**Warning checks:**
- Security scanning (non-blocking)
- Type checking (non-blocking)

## Common Issues

### Import Errors
```bash
# Solution: Install missing dependencies
pip install <package>
```

### Type Errors
```python
# Bad: No type hints
def get_user(id):
    ...

# Good: With type hints
def get_user(id: int) -> User:
    ...
```

### Line Too Long
```python
# Bad: Exceeds 100 characters
long_string = "This is a very long string that exceeds the line length limit"

# Good: Split across lines
long_string = (
    "This is a long string that "
    "is split across multiple lines"
)
```

### Unused Imports
```bash
# Auto-remove unused imports
ruff check --select F401 --fix .
```

## Editor Setup

### VS Code Extensions

Install these extensions:
- **EditorConfig** - Editor settings
- **Ruff** - Python linting
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.vscode-ruff"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Commands Reference

### Python

```bash
# Lint and auto-fix
ruff check --fix .

# Format code
ruff format .

# Type check
mypy app/

# Security scan
bandit -r app/
```

### Frontend

```bash
cd frontend

# Lint and auto-fix
npm run lint:fix

# Type check
npm run type-check

# Format code
npm run format
```

### Pre-commit

```bash
# Run all hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hook (not recommended)
SKIP=eslint git commit -m "message"
```

## Support

### Documentation
- [Code Quality Standards](CODE_QUALITY_STANDARDS.md)
- [Quick Start Guide](LINTING_QUICKSTART.md)

### Tools
- **Ruff**: https://docs.astral.sh/ruff/
- **ESLint**: https://eslint.org/
- **Prettier**: https://prettier.io/
- **mypy**: https://mypy.readthedocs.io/
- **Bandit**: https://bandit.readthedocs.io/

### Getting Help
1. Check documentation
2. Review error messages
3. Ask in team chat
4. Create GitHub issue

## Stats

- **Python files**: 200+
- **TypeScript files**: 150+
- **Linting rules**: 300+
- **Pre-commit hooks**: 15+
- **CI jobs**: 6

## Contributing

When adding new code:
1. Write code with linting in mind
2. Run linting before committing
3. Fix all linting errors
4. Update tests if needed
5. Document changes

## License

Part of the PsychSync project.

---

**Last Updated**: 2026-01-04
