# Clinical Assessments Module Refactoring Plan

## Original File
`app/api/v1/endpoints/clinical_assessments.py` (1743 lines)

## Module Breakdown

### 1. consent.py (~100 lines)
**Endpoint**: POST /consent
**Lines**: 66-162
**Purpose**: Clinical consent management

### 2. screening.py (~400 lines)
**Endpoints**:
- POST /screening/mental-health (lines 163-282)
- GET /screening/tools (lines 668-779)
- GET /screening/questions/{assessment_type} (lines 780-803)
- POST /screening/submit (lines 804-845)

**Purpose**: Mental health screening (PHQ-9, GAD-7, ASRS)

### 3. wellness.py (~200 lines)
**Endpoints**:
- POST /wellness/assessment (lines 283-381)
- GET /wellness/questions (lines 846-865)
- POST /wellness/submit (lines 866-904)

**Purpose**: Wellness assessments and monitoring

### 4. crisis.py (~350 lines)
**Endpoints**:
- POST /crisis/alert (lines 382-471)
- POST /crisis/assessment (lines 1416-1489)
- POST /crisis/create-safety-plan (lines 1490-1546)
- GET /crisis/safety-plan (lines 1547-1573)
- GET /crisis/resources (lines 1574-1693)
- POST /crisis/check-in (lines 1694-1743)

**Purpose**: Crisis intervention and safety planning

### 5. trends.py (~250 lines)
**Endpoints**:
- POST /trends/mental-health (lines 472-536)
- GET /trends/data (lines 905-933)
- GET /trends/comparison (lines 934-960)
- GET /trends/summary (lines 961-1034)

**Purpose**: Mental health trend analysis

### 6. planning.py (~400 lines)
**Endpoints**:
- POST /wellness/plan (lines 537-602)
- GET /wellness/plan/existing (lines 1035-1057)
- POST /wellness/plan/generate (lines 1058-1100)
- PUT /wellness/plan/{plan_id}/update (lines 1101-1132)
- GET /wellness/plan/templates (lines 1133-1220)
- GET /wellness/plan/goal-suggestions (lines 1221-1415)

**Purpose**: Wellness plan generation and management

### 7. resources.py (~100 lines)
**Endpoint**: GET /resources/clinical (lines 603-667)
**Purpose**: Clinical resources and information

## Implementation Steps

1. Move code from original file to each module
2. Update imports in each module
3. Keep helper functions and models in appropriate modules
4. Test each module independently
5. Update api.py to use new modular structure
6. Rename original file to .old

## Estimated Impact
- **Maintainability**: HIGH → LOW ✅
- **File Size**: 1743 lines → 7 modules (avg 250 lines each) ✅
- **Testing**: Easier to test individual components ✅
