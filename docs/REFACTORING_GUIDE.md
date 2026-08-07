# 🏗️ Code Refactoring Guide
## Complete Roadmap for Reducing Technical Debt

This guide provides a structured approach to reducing code complexity across the PsychSync codebase.

---

## 📊 Current State Analysis

### **Critical Complexity Hotspots** (Priority Order)

| # | File | Lines | Top Complexity | Impact | Effort |
|---|------|-------|----------------|--------|--------|
| 1 | `app/services/clinical/scoring_algorithms.py` | 1,835 | PHQ9Scorer.score() (72 lines) | **HIGH** (patient safety) | 2 weeks |
| 2 | `frontend/src/App.tsx` | 1,805 | All routes inline | **HIGH** (maintainability) | 1 week |
| 3 | `app/core/security_monitoring.py` | 1,244 | `__init__` (78 lines) | **MEDIUM** | 3 days |
| 4 | `frontend/src/pages/ClinicalResults.tsx` | 1,929 | Monolithic component | **MEDIUM** | 1 week |
| 5 | `app/services/longitudinal_analysis.py` | 1,403 | Complex statistical methods | **MEDIUM** | 1 week |

---

## 🎯 Refactoring Strategy: The "Scorched Earth" Approach

### **Phase 1: Foundation (Week 1)**
**Goal**: Set up infrastructure to prevent future complexity

#### ✅ Already Completed:
- [x] Created base classes for scoring system
- [x] Implemented configuration objects
- [x] Separated crisis detection logic
- [x] Created test templates
- [x] Set up CI/CD complexity checks
- [x] Created PR template with complexity requirements

#### 🚧 Next Steps:

**Step 1: Install Complexity Tools**
```bash
# Python complexity analysis
pip install radon mccabe

# TypeScript complexity analysis
npm install -g complexity-report

# Make complexity check script executable
chmod +x scripts/check-complexity.sh
```

**Step 2: Run Baseline Analysis**
```bash
# Check current complexity state
./scripts/check-complexity.sh

# Generate detailed report
radon cc app/ -o complexity_baseline.html
radon mi app/ -o maintainability_baseline.html
```

**Step 3: Create Refactoring Branch**
```bash
git checkout -b refactor/reduce-complexity
git push -u origin refactor/reduce-complexity
```

---

### **Phase 2: Clinical Scoring Refactor (Weeks 2-3)**

### **Step-by-Step Implementation**

#### **Step 1: Migrate PHQ-9 to New Architecture**

**Current file**: `app/services/clinical/scoring_algorithms.py` (lines 82-154)

**Action Plan**:

1. **Create factory pattern for scoring**:
```python
# New file: app/services/clinical/scoring/factory.py
class ScoringFactory:
    """Factory for creating appropriate scoring strategies"""

    _scorers = {
        "PHQ9": PHQ9Scorer,
        "GAD7": GAD7Scorer,
        # ... other instruments
    }

    @classmethod
    def get_scorer(cls, instrument_name: str) -> BaseScoringStrategy:
        if instrument_name not in cls._scorers:
            raise ValueError(f"Unknown instrument: {instrument_name}")
        return cls._scorers[instrument_name]()
```

2. **Refactor existing endpoints to use new system**:
```python
# Before (in API endpoint)
from app.services.clinical.scoring_algorithms import PHQ9Scorer
result = PHQ9Scorer.score(responses)

# After (clean and testable)
from app.services.clinical.scoring import ScoringFactory
scorer = ScoringFactory.get_scorer("PHQ9")
result = scorer.score(responses)
```

3. **Maintain backward compatibility**:
```python
# Keep old interface as wrapper
# app/services/clinical/scoring_algorithms.py
class PHQ9Scorer:
    @staticmethod
    def score(responses):
        """Backward compatible wrapper"""
        from app.services.clinical.scoring import ScoringFactory
        scorer = ScoringFactory.get_scorer("PHQ9")
        result = scorer.score(responses)
        return result  # Old format
```

#### **Step 2: Test Migration**

**Run existing tests to ensure no regressions**:
```bash
# Run clinical scoring tests
pytest tests/clinical/ -v

# Run with coverage
pytest tests/clinical/ --cov=app/services/clinical --cov-report=html
```

**Add new tests for refactored code**:
```bash
# Tests already created in:
# tests/scoring/test_phq9_refactored.py

pytest tests/scoring/test_phq9_refactored.py -v
```

#### **Step 3: Migrate Remaining Instruments**

For each instrument (GAD-7, CSSRS, etc.):

1. Create new scorer class inheriting from `BaseScoringStrategy`
2. Define configuration in `config.py`
3. Create tests in `tests/scoring/`
4. Update factory to register new scorer
5. Verify existing tests pass

---

### **Phase 3: Frontend Refactor (Week 4)**

### **Step 1: Refactor App.tsx**

**Create route configuration**:
```typescript
// File: frontend/src/config/routes.ts
export const ROUTE_CONFIG = {
  clinical: {
    path: '/clinical',
    routes: [
      {
        path: 'results',
        component: () => import('./pages/ClinicalResults'),
        protected: true,
      },
      // ... other clinical routes
    ],
  },
  // ... other domains
};
```

**Create route builder**:
```typescript
// File: frontend/src/routes/RouteBuilder.tsx
// Already designed - see previous section
```

**Update App.tsx**:
```typescript
// Before: 1,805 lines
// After: ~50 lines
```

### **Step 2: Break Down Large Components**

**Target**: `ClinicalResults.tsx` (1,929 lines)

**Decomposition strategy**:
```
ClinicalResults/
├── index.tsx (container, ~100 lines)
├── ClinicalResultsHeader.tsx (~100 lines)
├── ClinicalResultsCharts.tsx (~200 lines)
├── ClinicalResultsTable.tsx (~150 lines)
├── ClinicalResultsActions.tsx (~80 lines)
├── hooks/
│   └── useClinicalData.ts (~100 lines)
└── utils/
    └── dataTransformers.ts (~150 lines)
```

---

### **Phase 4: Security Monitoring Refactor (Week 5)**

### **Simplify Configuration**

**Already designed**: See `SecurityMonitoringConfig` dataclass above

**Implementation**:
1. Replace `__init__` parameters with config object
2. Add validation in `__post_init__`
3. Update tests to use config objects
4. Update instantiation in application

---

## 📈 Measuring Success

### **Complexity Metrics to Track**

| Metric | Current | Target | Tool |
|--------|---------|--------|------|
| Max cyclomatic complexity | 72 | <15 | `radon cc` |
| Avg function length | 45 lines | <30 lines | Custom script |
| Max nesting level | 5 | <3 | `radon cc` |
| Test coverage | ~40% | >80% | `pytest --cov` |
| Maintainability index | ~40 | >70 | `radon mi` |

### **Tracking Dashboard**

```bash
# Generate weekly complexity report
./scripts/generate-complexity-report.sh > reports/week-$(date +%Y-%m-%d).txt

# Compare to baseline
diff reports/week-start.txt reports/week-end.txt
```

---

## 🚀 Quick Wins (Can be done in <1 day)

### **1. Extract Helper Functions**
**File**: `scoring_algorithms.py`
```python
# Before (72 lines in one function)
def score(responses):
    # validation
    # scoring
    # severity
    # crisis detection
    # interpretation
    # recommendations
    pass

# After (3 focused functions)
def score(responses):
    self.validate(responses)
    return self._calculate_score(responses)

def _calculate_score(self, responses):
    return self._apply_severity_classification(
        self._detect_crisis(responses)
    )
```

### **2. Add Configuration Objects**
**File**: `security_monitoring.py`
**Time**: 1 hour
**Impact**: Reduces `__init__` from 78 to 15 lines

### **3. Create Route Configuration**
**File**: `App.tsx`
**Time**: 2 hours
**Impact**: Reduces from 1,805 to ~50 lines

### **4. Split Large Components**
**File**: `ClinicalResults.tsx`
**Time**: 4 hours
**Impact**: Reduces from 1,929 to ~100 lines (container)

---

## 🎓 Learning Resources

### **Key Patterns Used**

1. **Strategy Pattern**: Interchangeable algorithms
2. **Factory Pattern**: Object creation
3. **Dataclasses**: Configuration with validation
4. **Compound Components**: UI decomposition
5. **Single Responsibility Principle**: One job per function

### **Further Reading**

- **Refactoring** by Martin Fowler
- **Clean Code** by Robert C. Martin
- **Design Patterns** by Gang of Four
- **Working Effectively with Legacy Code** by Michael Feathers

---

## ✅ Completion Checklist

- [ ] All complexity hotspots identified and prioritized
- [ ] Refactoring plan approved by team
- [ ] Baseline metrics established
- [ ] CI/CD checks configured
- [ ] PR template updated
- [ ] Team training on patterns completed
- [ ] First priority refactoring completed (scoring)
- [ ] Test coverage >80% for refactored code
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Metrics showing improvement

---

## 🤝 Team Coordination

### **How to Coordinate Without Conflicts**

1. **Create feature branches**: `refactor/<module-name>`
2. **Work on different modules** simultaneously
3. **Merge frequently** to avoid divergence
4. **Use TODO(human)** comments for collaborative work
5. **Code review** all refactoring changes

### **Suggested Work Distribution**

| Developer | Module | Duration |
|-----------|--------|----------|
| Dev 1 | Clinical scoring (PHQ9, GAD7) | 2 weeks |
| Dev 2 | Frontend routing (App.tsx) | 1 week |
| Dev 3 | Security monitoring config | 3 days |
| Dev 4 | Large component decomposition | 1 week |

---

## 🎯 Expected Outcomes

### **After Complete Refactoring**

✅ **Code Quality**:
- Max function complexity: <15
- Max function length: <50 lines
- Test coverage: >80%
- Maintainability index: >70

✅ **Developer Experience**:
- Faster onboarding
- Easier debugging
- Safer refactoring
- Better tests

✅ **Business Value**:
- Reduced bugs in critical code
- Faster feature development
- Easier compliance (clinical validation)
- Lower technical debt interest

---

## 📞 Getting Help

**Questions about refactoring approach?**
- Review: `REFACTORING_GUIDE.md`
- Examples: `app/services/clinical/scoring/`
- Tests: `tests/scoring/test_phq9_refactored.py`

**Stuck on a specific pattern?**
- Check existing refactored code
- Ask team for code review
- Reference design pattern documentation

**Need to bypass complexity check?**
⚠️ **Only for emergency fixes**
- Add `# radon: ignore` with explanation
- Create follow-up issue for refactoring
- Get team lead approval

---

*Last updated: 2026-01-17*
*Maintained by: Development Team*
