# Refactoring Plan: assessments.py Split

**File**: `app/api/v1/endpoints/assessments.py`
**Current Size**: 1644 lines
**Target**: Split into 4 focused modules

---

## 📊 Analysis

### Current Endpoint Distribution

| Functional Area | Endpoints | Lines (approx) | % of File |
|----------------|-----------|----------------|-----------|
| **CRUD Operations** | 10 | 350 | 21% |
| **Assessment Questions** | 7 | 990 | 60% |
| **Assignments & Responses** | 4 | 200 | 12% |
| **Section/Question Management** | 6 | 104 | 6% |

### Dependencies

The file imports:
- **Models**: `Assessment`, `Assignment`, `Response`, `Section`, `Question`
- **Schemas**: Various assessment-related schemas
- **Services**: `assessment_service`, `response_service`
- **Utilities**: Validation helpers, error handlers

---

## 🎯 Recommended Split Structure

```
app/api/v1/endpoints/assessments/
├── __init__.py              # Router aggregation
├── crud.py                  # CRUD operations (~350 lines)
├── questions.py             # Framework questions (~990 lines)
└── responses.py             # Assignments & responses (~300 lines)
```

**Note**: Section/question management endpoints are few and can stay in `crud.py`

---

## 📝 Module Breakdown

### **1. crud.py** (~350 lines)

**Purpose**: Core assessment CRUD operations

**Endpoints**:
- `GET /` - List assessments
- `POST /` - Create assessment
- `GET /{assessment_id}` - Get assessment details
- `PUT /{assessment_id}` - Update assessment
- `DELETE /{assessment_id}` - Delete assessment
- `POST /{assessment_id}/publish` - Publish assessment
- `POST /{assessment_id}/archive` - Archive assessment
- `POST /` - Duplicate assessment
- `POST /{assessment_id}/sections` - Add section
- `DELETE /{assessment_id}/sections/{section_id}` - Delete section
- `POST /{assessment_id}/questions` - Add question
- `DELETE /{assessment_id}/questions/{question_id}` - Delete question

**Router Prefix**: `/assessments` (same as parent)

**Dependencies**:
- `app.db.models.assessment`
- `app.db.models.question`
- `app.services.assessment_service`
- `app.schemas.assessment`

---

### **2. questions.py** (~990 lines)

**Purpose**: Assessment questions for different personality frameworks

**Endpoints**:
- `GET /assessment-questions/mbti` - MBTI questions
- `GET /assessment-questions/enneagram` - Enneagram questions
- `GET /assessment-questions/big-five` - Big Five questions
- `GET /assessment-questions/disc` - DISC questions
- `GET /assessment-questions/predictive-index` - Predictive Index questions
- `GET /assessment-questions/social-styles` - Social Styles questions
- `GET /assessment-questions/strengthsfinder` - StrengthsFinder questions

**Router Prefix**: `/assessments`

**Dependencies**:
- `app.db.models.question`
- `app.schemas.question`
- Framework-specific question generators

---

### **3. responses.py** (~300 lines)

**Purpose**: Assignment management and response submission

**Endpoints**:
- `POST /{assessment_id}/assign` - Create assignment
- `GET /assignments/me` - Get my assignments
- `POST /{assessment_id}/responses` - Submit response
- `GET /{assessment_id}/responses` - Get assessment responses

**Router Prefix**: `/assessments`

**Dependencies**:
- `app.db.models.assignment`
- `app.db.models.response`
- `app.services.response_service`
- `app.schemas.assignment`

---

### **4. __init__.py** (Router aggregation)

**Purpose**: Aggregate all routers into single router

**Code**:
```python
from fastapi import APIRouter

from .crud import router as crud_router
from .questions import router as questions_router
from .responses import router as responses_router

# Create main router
router = APIRouter(prefix="/assessments", tags=["assessments"])

# Include all sub-routers
router.include_router(crud_router)
router.include_router(questions_router)
router.include_router(responses_router)

# Export main router
__all__ = ["router"]
```

---

## 🔧 Implementation Steps

### **Step 1**: Create Directory Structure
```bash
mkdir -p app/api/v1/endpoints/assessments
```

### **Step 2**: Create Module Files
1. Create `crud.py` with CRUD endpoints
2. Create `questions.py` with framework question endpoints
3. Create `responses.py` with assignment/response endpoints
4. Create `__init__.py` to aggregate routers

### **Step 3**: Update Main Router
In `app/api/v1/endpoints/__init__.py`:
```python
# Remove old import
# from .assessments import router as assessments_router

# Add new import
from .assessments import router as assessments_router
```

### **Step 4**: Test
```bash
# Check imports
python -c "from app.api.v1.endpoints.assessments import router"

# Run tests
pytest tests/api/test_assessments.py -v
```

### **Step 5**: Cleanup
```bash
# Remove old file after verification
git rm app/api/v1/endpoints/assessments.py
git commit -m "refactor: split assessments.py into focused modules"
```

---

## 📋 Detailed File Creation Guides

### **crud.py Template**

```python
"""
Assessment CRUD Endpoints
Handles create, read, update, delete operations for assessments
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.assessment import Assessment
from app.schemas.assessment import AssessmentSchema, AssessmentCreate

router = APIRouter(prefix="/assessments", tags=["assessments-crud"])

# Move endpoints from lines 250-600 approximately

@router.get("/")
async def get_assessments(...):
    """List all assessments"""
    pass

@router.post("/")
async def create_assessment(...):
    """Create new assessment"""
    pass

# ... other CRUD endpoints
```

### **questions.py Template**

```python
"""
Assessment Questions Endpoints
Provides questions for different personality assessment frameworks
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/assessments", tags=["assessment-questions"])

# Move endpoints from lines 682-1672 approximately

@router.get("/assessment-questions/mbti")
async def get_mbti_assessment_questions() -> Dict[str, Any]:
    """Get MBTI assessment questions"""
    pass

# ... other framework endpoints
```

### **responses.py Template**

```python
"""
Assessment Assignment and Response Endpoints
Handles assessment assignments and response submissions
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.assignment import Assignment
from app.db.models.response import Response

router = APIRouter(prefix="/assessments", tags=["assessment-responses"])

# Move endpoints from lines 589-665 approximately

@router.post("/{assessment_id}/assign")
async def create_assignment(...):
    """Create assessment assignment"""
    pass

# ... other assignment/response endpoints
```

---

## ⚠️ Important Considerations

### **1. Import Paths**

When moving code, ensure all imports use absolute paths:
```python
# ✅ Correct
from app.services.assessment_service import AssessmentService
from app.db.models.assessment import Assessment

# ❌ Avoid (relative imports)
from ...services.assessment_service import AssessmentService
```

### **2. Shared Utilities**

If there are shared utility functions in the original file:
- Move to a separate `utils.py` in the assessments module
- Or move to `app/api/v1/utils.py` if used across multiple endpoints

### **3. Dependencies**

Check for dependencies on:
- Other endpoints in the same file (rare, but possible)
- Shared state or configuration
- Common validation logic

### **4. Database Models**

Ensure all models are imported:
```python
from app.db.models.assessment import Assessment
from app.db.models.assignment import Assignment
from app.db.models.response import Response
from app.db.models.section import Section
from app.db.models.question import Question
```

---

## 🧪 Testing Checklist

After splitting, verify:

- [ ] All endpoints accessible via Swagger UI (`/docs`)
- [ ] All existing tests pass
- [ ] No broken imports
- [ ] No circular dependencies
- [ ] Router aggregation works correctly
- [ ] All tags appear correctly in API docs

---

## 📊 Expected Results

After refactoring:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **File size** | 1644 lines | 350, 990, 300 | 78% reduction in max file |
| **Maintainability** | Low | High | Easier to navigate |
| **Merge conflicts** | High | Low | Reduced conflicts |
| **Test coverage** | Monolithic | Modular | Easier to test |
| **Code review** | Difficult | Easier | Focused reviews |

---

## 🎯 Success Criteria

✅ **Split is successful if**:
1. All endpoints work correctly
2. No broken imports
3. Tests pass
4. Router aggregation transparent
5. File sizes under 1000 lines
6. No functionality lost

---

## 🔄 Rollback Plan

If issues arise:
```bash
# Rollback immediately
git checkout HEAD -- app/api/v1/endpoints/assessments.py
rm -rf app/api/v1/endpoints/assessments/

# Verify
pytest tests/api/test_assessments.py -v
```

---

**Next Steps**:
1. ✅ Review and approve this plan
2. ⚠️ Execute split incrementally (one module at a time)
3. ✅ Test thoroughly after each module
4. ✅ Commit and push changes
5. 📊 Update baselines in file growth monitor

---

**Created**: 2025-01-19
**Status**: 📋 Ready for implementation
