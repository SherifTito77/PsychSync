# Linting Quick Start Guide

Quick reference for linting and code quality tools in PsychSync.

## Installation

```bash
# Python linting tools
pip install ruff mypy bandit[toml] pre-commit

# Install pre-commit hooks
pre-commit install

# Frontend linting tools (installed via npm)
cd frontend
npm install
```

## Daily Commands

### Python

```bash
# Lint and auto-fix Python code
ruff check --fix .

# Format Python code
ruff format .

# Type check
mypy app/ --ignore-missing-imports

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

# Update hooks to latest versions
pre-commit autoupdate

# Skip specific hook (not recommended)
SKIP=eslint git commit -m "message"
```

## Configuration Files

| File | Purpose |
|------|---------|
| `ruff.toml` | Python linting and formatting rules |
| `pyproject.toml` | pytest, coverage, mypy config |
| `.bandit` | Security scanning configuration |
| `frontend/eslint.config.js` | TypeScript/React linting rules |
| `frontend/package.json` | Frontend linting scripts |
| `.editorconfig` | Editor settings (indentation, line endings) |
| `.pre-commit-config.yaml` | Pre-commit hook definitions |
| `.gitignore` | Files to exclude from git (linting caches) |

## Common Issues and Solutions

### Import Errors (Python)

**Error**: `Import "pydantic" could not be resolved`

**Solution**:
```bash
pip install pydantic
# or
ruff check --ignore=I001  # temporary skip
```

### Type Errors (TypeScript)

**Error**: `Cannot find module '@/types'`

**Solution**: Check `tsconfig.json` path mappings:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Line Too Long

**Error**: `E501 line too long (102 > 100 characters)`

**Solution**:
```bash
# Auto-fix if possible
ruff check --fix .

# Or refactor long lines
# Bad
long_string = "This is a very long string that exceeds the line length limit"

# Good
long_string = (
    "This is a long string that "
    "is split across multiple lines"
)
```

### Unused Imports

**Error**: `F401 'module' imported but unused`

**Solution**:
```bash
# Auto-remove unused imports
ruff check --select F401 --fix .
```

### Missing Type Hints

**Error**: Missing type annotation for function parameter

**Solution**:
```python
# Bad
def calculate_score(user_id, db):
    ...

# Good
def calculate_score(user_id: int, db: AsyncSession) -> dict:
    ...
```

## VS Code Setup

### Recommended Extensions

```json
{
  "recommendations": [
    "charliermarsh.ruff",           // Ruff Python linter
    "ms-python.mypy-type-checker",  // mypy type checker
    "dbaeumer.vscode-eslint",       // ESLint
    "esbenp.prettier-vscode",       // Prettier
    "EditorConfig.EditorConfig",    // EditorConfig
    "ms-python.vscode-pylint"       // Pylint (optional)
  ]
}
```

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.vscode-ruff"
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "explicit"
    },
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "explicit"
    },
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.eol": "\n"
}
```

## CI/CD Integration

Linting runs automatically on:
- Every pull request
- Pushes to `main` and `develop` branches
- Manual trigger via GitHub Actions

### Failing Checks

If linting fails in CI:

1. Check the workflow logs
2. Run the same linter locally
3. Fix issues and push
4. CI will automatically re-run

### GitHub Actions Workflow

Location: `.github/workflows/lint.yml`

Jobs:
- **python-lint**: Ruff, mypy, bandit
- **frontend-lint**: ESLint, TypeScript, Prettier
- **security-scan**: Bandit, Semgrep, Safety
- **config-validation**: YAML, TOML, JSON
- **documentation-lint**: Markdown, spell check

## Team Workflow

### Before Committing

```bash
# 1. Run pre-commit hooks (automatic)
git add .
git commit -m "feat: add new feature"

# 2. If hooks fail, fix and try again
ruff check --fix .
cd frontend && npm run lint:fix
git add .
git commit -m "feat: add new feature"
```

### Code Review Checklist

- [ ] All linting checks pass
- [ ] No `// eslint-disable` or `# noqa` without explanation
- [ ] New code has type hints
- [ ] Security scanning passes
- [ ] Documentation updated
- [ ] Tests added/updated

## Resources

- **Ruff docs**: https://docs.astral.sh/ruff/
- **ESLint docs**: https://eslint.org/
- **Prettier docs**: https://prettier.io/
- **mypy docs**: https://mypy.readthedocs.io/
- **Bandit docs**: https://bandit.readthedocs.io/
- **pre-commit docs**: https://pre-commit.com/
- **EditorConfig**: https://editorconfig.org/

## Emergency Commands

```bash
# Disable all pre-commit hooks (DANGEROUS - only for emergencies)
git commit --no-verify -m "emergency fix"

# Clean all linting caches
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".ruff_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Reinstall pre-commit hooks
pre-commit uninstall
pre-commit install

# Reset to default linting config
git checkout ruff.toml
git checkout frontend/eslint.config.js
```

## Getting Help

1. Check the [Code Quality Standards](/docs/CODE_QUALITY_STANDARDS.md)
2. Search existing issues
3. Ask in team chat
4. Create new issue with label "linting"

---

Last updated: 2026-01-04
