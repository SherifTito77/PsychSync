# Code Quality Improvements & Monitoring Tools

**Date**: 2025-01-19
**Status**: ✅ Implemented

---

## 🎯 Overview

This document summarizes the code quality improvements made and monitoring tools created for the PsychSync backend codebase.

---

## 📊 Current Status

### ✅ **Completed Improvements**

| Category | Item | Status | Impact |
|----------|------|--------|--------|
| **Circular Dependencies** | Detection analysis | ✅ Complete | 0 circular dependencies found |
| **Import Patterns** | Relative → Absolute conversion | ✅ Complete | 6 files converted |
| **Transaction Safety** | Standardized to transaction manager | ✅ Complete | 24 functions refactored |
| **CI/CD Tools** | Import complexity checker | ✅ Complete | Automated monitoring |
| **Monitoring** | File growth tracker | ✅ Complete | 4 critical files identified |

### ⚠️ **Issues Requiring Attention**

| File | Lines | Issue | Priority |
|------|-------|-------|----------|
| `app/api/v1/endpoints/assessments.py` | 1644 | Too large | 🔴 Critical |
| `app/api/v1/endpoints/clinical_assessments.py` | 1440 | Too large | 🔴 High |
| `app/api/v1/endpoints/monitoring.py` | 1148 | Too large | 🔴 High |
| `app/api/v1/endpoints/screening.py` | 1095 | Too large | 🔴 High |

---

## 🛠️ Tools Created

### 1. **Import Complexity Checker** ✅

**File**: `scripts/check_import_complexity.py`

**Purpose**: Monitor import complexity and detect code quality issues in CI/CD

**Features**:
- ✅ Configurable import count threshold
- ✅ Detects relative vs absolute imports
- ✅ Reports top modules by import count
- ✅ CI/CD friendly with proper exit codes

**Usage**:
```bash
# Run with defaults (max 20 imports)
python scripts/check_import_complexity.py

# Custom threshold
python scripts/check_import_complexity.py --max-imports 25

# Fail on warnings in CI/CD
python scripts/check_import_complexity.py --fail-on-warnings

# Verbose output
python scripts/check_import_complexity.py --verbose
```

**Current Findings** (max 25 imports):
- 6 files exceed threshold
- `main.py`: 49 imports (expected for entry point)
- Average: 8.8 imports per module

**CI/CD Integration**:
```yaml
# .github/workflows/code-quality.yml
- name: Check Import Complexity
  run: python scripts/check_import_complexity.py --max-imports 25 --fail-on-warnings
```

---

### 2. **File Growth Monitor** ✅

**File**: `scripts/monitor_file_growth.py`

**Purpose**: Track file growth over time to detect code bloat

**Features**:
- ✅ Tracks file size (non-empty lines)
- ✅ Detects rapid growth
- ✅ Maintains baseline history
- ✅ Provides actionable recommendations

**Usage**:
```bash
# Check endpoint files
python scripts/monitor_file_growth.py

# Check specific file
python scripts/monitor_file_growth.py --check app/api/v1/endpoints/users.py

# Update baseline
python scripts/monitor_file_growth.py --update-baseline

# Show all files
python scripts/monitor_file_growth.py --all
```

**Thresholds**:
- 🟢 Warning: 500 lines
- 🟡 Critical: 1000 lines
- 🔴 Unmanageable: 1500 lines

**Current Findings**:
- 4 files require splitting
- 103 endpoint files analyzed
- Total: 44,763 lines of endpoint code

---

## 📈 Import Complexity Analysis

### **Top 10 Modules by Import Count** (from app directory)

| Rank | Module | Imports | Status |
|------|--------|---------|--------|
| 1 | `main` | 49 | ⚠️ Expected (entry point) |
| 2 | `core.security` | 38 | 🔴 Exceeds threshold |
| 3 | `core.distributed_tracing` | 28 | 🟡 Monitor |
| 4 | `services.sentry_service` | 28 | 🟡 Monitor |
| 5 | `services.prediction_service` | 27 | 🟡 Monitor |
| 6 | `services.data_export_service` | 26 | 🟡 Monitor |
| 7 | `api.v1.endpoints.auth_unified` | 25 | ✅ At threshold |
| 8 | `api.v1.endpoints.clinical_assessments_extended` | 25 | ✅ At threshold |
| 9 | `core.application_factory` | 24 | ✅ OK |
| 10 | `monitoring.audit_logger` | 23 | ✅ OK |

**Average**: 8.8 imports per module

---

## 🔴 Critical Files Requiring Splitting

### **1. app/api/v1/endpoints/assessments.py** (1644 lines)

**Issue**: File is unmanageable and difficult to maintain

**Recommended Split**:
```
app/api/v1/endpoints/assessments/
├── __init__.py              # Route aggregation
├── crud.py                  # Create, read, update, delete
├── scoring.py               # Assessment scoring endpoints
├── templates.py             # Template management
└── analytics.py             # Assessment analytics & insights
```

### **2. app/api/v1/endpoints/clinical_assessments.py** (1440 lines)

**Issue**: Too large, mixing multiple concerns

**Recommended Split**:
```
app/api/v1/endpoints/clinical_assessments/
├── __init__.py
├── phq9.py                  # PHQ-9 specific endpoints
├── gad7.py                  # GAD-7 specific endpoints
├── asrs.py                  # ASRS specific endpoints
├── crisis.py                # Crisis detection & intervention
└── scoring.py               # Clinical scoring logic
```

### **3. app/api/v1/endpoints/monitoring.py** (1148 lines)

**Issue**: Too large

**Recommended Split**:
```
app/api/v1/endpoints/monitoring/
├── __init__.py
├── performance.py           # Performance metrics
├── errors.py                # Error tracking
├── usage.py                 # Usage analytics
└── alerts.py                # Alert management
```

### **4. app/api/v1/endpoints/screening.py** (1095 lines)

**Issue**: Too large

**Recommended Split**:
```
app/api/v1/endpoints/screening/
├── __init__.py
├── assessments.py           # Screening assessments
├── results.py               # Result processing
└── recommendations.py        # Clinical recommendations
```

---

## 🎓 Best Practices Documented

### **1. Import Guidelines**

✅ **Preferred**: Absolute imports
```python
from app.services.user_service import UserService
from app.db.models.user import User
```

❌ **Avoid**: Relative imports (except in small packages)
```python
from .user_service import UserService
from ..models import User
```

### **2. File Size Guidelines**

- **Target**: < 500 lines per file
- **Warning**: 500-1000 lines
- **Critical**: 1000-1500 lines
- **Unmanageable**: > 1500 lines (split immediately)

### **3. Module Complexity**

- **Target**: < 15 imports per module
- **Monitor**: 15-25 imports
- **Action Required**: > 25 imports (refactor)

### **4. Transaction Management**

✅ **Use**: Transaction manager decorator
```python
@transaction_manager.transaction
async def create_item(db: AsyncSession, ...):
    db.add(item)
    await db.flush()
    return item
```

❌ **Avoid**: Manual commit/rollback
```python
async def create_item(db: AsyncSession, ...):
    try:
        db.add(item)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise
```

---

## 📋 CI/CD Integration Checklist

Add these checks to your CI/CD pipeline:

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Checks

on: [pull_request, push]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check Import Complexity
        run: |
          python scripts/check_import_complexity.py \
            --max-imports 25 \
            --fail-on-warnings

      - name: Monitor File Growth
        run: |
          python scripts/monitor_file_growth.py
          # Exit with error if critical files found
          python scripts/monitor_file_growth.py || exit 1

      - name: Check for Circular Dependencies
        run: |
          python scripts/check_circular_dependencies.py
```

---

## 🚀 Next Steps

### **Immediate** (Required)

1. ✅ **Import Complexity Checker** - Deploy to CI/CD
2. ✅ **File Growth Monitor** - Run regularly (weekly)
3. 🔴 **Split Critical Files** - Start with assessments.py

### **Short Term** (Recommended)

4. ⚠️ **Split clinical_assessments.py** (1440 lines)
5. ⚠️ **Split monitoring.py** (1148 lines)
6. ⚠️ **Split screening.py** (1095 lines)
7. 📊 **Add automated dependency graph visualization**

### **Medium Term** (Optional)

8. 📈 **Module ownership documentation**
9. 🔍 **Code review complexity metrics**
10. 📝 **Refactoring guidelines document**

---

## 📚 Related Documentation

- **Transaction Management**: See `DATABASE_TRANSACTION_IMPROVEMENTS.md`
- **Circular Dependency Analysis**: See `CIRCULAR_DEPENDENCY_ANALYSIS.md`
- **Architecture Guidelines**: See `CLAUDE.md`

---

## 🎯 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Circular Dependencies | 0 | 0 | ✅ |
| Average Imports/Module | < 10 | 8.8 | ✅ |
| Files > 1000 lines | 0 | 4 | 🔴 |
| Relative Imports | < 10 | 30 | ⚠️ |
| Test Coverage | > 80% | TBD | 📊 |

---

## 📞 Support

For questions or issues with these tools:

1. Run with `--verbose` flag for detailed output
2. Check existing issues in GitHub
3. Consult this documentation
4. Review tool-specific help: `python scripts/<script>.py --help`

---

**Last Updated**: 2025-01-19
**Maintained By**: Development Team
**Version**: 1.0
