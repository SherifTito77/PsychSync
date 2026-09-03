# Component Splitting Roadmap - Frontend Optimization

## Overview

The frontend has **20 oversized components** (>1,000 lines) that need to be split for maintainability, performance, and developer experience.

---

## Priority Matrix

### ✅ COMPLETED (1 component)

| Component | Lines | Status | Location |
|-----------|-------|--------|----------|
| **ClinicalResults** | 1,928 | ✅ **DONE** | `pages/clinical-results/` |

---

## 🔴 CRITICAL PRIORITY (>1,300 lines)

### 1. ClinicalAssessment.tsx (1,417 lines)

**Location**: `frontend/src/pages/ClinicalAssessment.tsx`

**Impact**: 🔴 **CRITICAL** - Core clinical workflow

**Analysis Needed**:
- How many different assessment types?
- Is there shared question rendering logic?
- Can question data be extracted to constants?
- Are there reusable validation/scoring functions?

**Estimated Split Time**: 6-8 hours

**Proposed Structure**:
```
pages/clinical-assessment/
├── index.tsx (orchestrator)
├── hooks/
│   ├── useAssessmentFlow.ts
│   └── useQuestionValidation.ts
├── components/
│   ├── QuestionCard.tsx
│   ├── QuestionNavigator.tsx
│   ├── ProgressBar.tsx
│   └── AssessmentSummary.tsx
├── utils/
│   ├── questionData.ts (export question arrays)
│   ├── validation.ts
│   └── scoring.ts
└── types.ts
```

---

### 2. WellbeingAssessment.tsx (1,373 lines)

**Location**: `frontend/src/pages/WellbeingAssessment.tsx`

**Impact**: 🟡 **HIGH** - User-facing, used frequently

**Current Structure** (from analysis):
- 54 wellbeing questions across 7 categories
- State: currentCategoryIndex, currentGroupIndex, responses
- Features: results, goals, history, streak tracking, progress
- Uses: wellnessStorage utility, exportUtils

**Estimated Split Time**: 5-6 hours

**Proposed Structure**:
```
pages/wellbeing-assessment/
├── index.tsx (main orchestrator)
├── hooks/
│   ├── useWellbeingAssessment.ts
│   ├── useGoalSetting.ts
│   └── useProgressTracking.ts
├── components/
│   ├── QuestionFlow.tsx (question progression)
│   ├── ResultsDisplay.tsx (category scores)
│   ├── GoalModal.tsx
│   ├── StreakTracker.tsx
│   └── ProgressChart.tsx
├── utils/
│   ├── questionData.ts (54 questions)
│   ├── scoring.ts (category calculation)
│   └── categorization.ts
└── types.ts
```

**Key Extraction Opportunities**:
1. **Question Data**: Lines 25-93 (54 questions) → `utils/questionData.ts`
2. **Scoring Logic**: Calculate category scores → `utils/scoring.ts`
3. **Goal Setting**: Goal modal and logic → `components/GoalModal.tsx` + hook
4. **Progress Tracking**: Streak and history → separate hook

---

### 3. WellnessPlanGenerator.tsx (1,257 lines)

**Location**: `frontend/src/components/clinical/WellnessPlanGenerator.tsx`

**Impact**: 🟡 **HIGH** - Clinical feature, AI-powered

**Estimated Split Time**: 6-8 hours

**Proposed Structure**:
```
components/clinical/wellness-plan-generator/
├── index.tsx (orchestrator)
├── hooks/
│   ├── useWellnessPlan.ts
│   └── useAIRecommendations.ts
├── components/
│   ├── PlanForm.tsx
│   ├── RecommendationCards.tsx
│   ├── ActionItems.tsx
│   └── ProgressTracker.tsx
├── utils/
│   ├── planTemplates.ts
│   └── recommendationLogic.ts
└── types.ts
```

---

### 4. TeamCompositionOptimizer.tsx (1,253 lines)

**Location**: `frontend/src/components/teams/TeamCompositionOptimizer.tsx`

**Impact**: 🟡 **HIGH** - Team analytics, business-critical

**Estimated Split Time**: 6-8 hours

**Proposed Structure**:
```
components/teams/team-optimizer/
├── index.tsx (orchestrator)
├── hooks/
│   ├── useTeamOptimization.ts
│   └── useMemberAnalysis.ts
├── components/
│   ├── TeamRadarChart.tsx
│   ├── MemberList.tsx
│   ├── OptimizationSuggestions.tsx
│   └── RoleRecommendations.tsx
├── utils/
│   ├── teamMetrics.ts
│   └── optimizationAlgorithms.ts
└── types.ts
```

---

## 🟠 HIGH PRIORITY (1,100-1,300 lines)

### 5. RealWorldScenarios.tsx (1,225 lines)
**Location**: `frontend/src/testing/RealWorldScenarios.tsx`
**Impact**: 🟢 **MEDIUM** - Testing utility (less urgent)
**Note**: Can be deferred if not in production path

### 6. AuditTrail.tsx (1,172 lines)
**Location**: `frontend/src/components/compliance/AuditTrail.tsx`
**Impact**: 🟡 **HIGH** - Compliance feature
**Split Time**: 4-5 hours

### 7. ExperimentalFeaturesLab.tsx (1,140 lines)
**Location**: `frontend/src/components/experimental/ExperimentalFeaturesLab.tsx`
**Impact**: 🟢 **LOW** - Experimental features
**Note**: Can be deferred

### 8. SuccessionPlanning.tsx (1,135 lines)
**Location**: `frontend/src/components/analytics/SuccessionPlanning.tsx`
**Impact**: 🟡 **HIGH** - HR/Business analytics
**Split Time**: 4-5 hours

### 9. VoiceVideoAnalysis.tsx (1,120 lines)
**Location**: `frontend/src/components/voiceanalysis/VoiceVideoAnalysis.tsx`
**Impact**: 🟡 **HIGH** - AI feature
**Split Time**: 5-6 hours

### 10. Reporting.tsx (1,104 lines)
**Location**: `frontend/src/pages/Reporting.tsx`
**Impact**: 🟡 **HIGH** - Core reporting feature
**Split Time**: 5-6 hours

---

## 🟡 MEDIUM PRIORITY (1,000-1,100 lines)

### 11. App.tsx (1,104 lines)
**Location**: `frontend/src/App.tsx`
**Impact**: 🟡 **HIGH** - Main router
**Note**: Already updated ClinicalResults import ✅
**Action**: Extract route definitions to separate modules

### 12. AdminDashboard.tsx (1,092 lines)
**Location**: `frontend/src/components/compliance/AdminDashboard.tsx`
**Impact**: 🟡 **HIGH** - Admin feature
**Split Time**: 4-5 hours

### 13. DocumentManagement.tsx (1,088 lines)
**Location**: `frontend/src/components/compliance/DocumentManagement.tsx`
**Impact**: 🟡 **MEDIUM** - Compliance feature
**Split Time**: 4-5 hours

### 14. PredictiveAnalyticsDashboard.tsx (1,077 lines)
**Location**: `frontend/src/components/analytics/PredictiveAnalyticsDashboard.tsx`
**Impact**: 🟡 **HIGH** - Analytics feature
**Split Time**: 4-5 hours

### 15. IntegrationHub.tsx (1,073 lines)
**Location**: `frontend/src/components/compliance/IntegrationHub.tsx`
**Impact**: 🟡 **MEDIUM** - Integration management
**Split Time**: 4-5 hours

---

## 🟢 LOWER PRIORITY (<1,100 lines)

16. ReportBuilder.tsx (1,017 lines) - Compliance
17. LoginSignupRefactored.tsx (1,005 lines) - Auth (already refactored?)
18. ReliabilityValidity.tsx (972 lines) - Analytics

---

## Recommended Splitting Order

### Phase 1: Critical Clinical Components (Week 1)
1. ✅ **ClinicalResults** - COMPLETED
2. **ClinicalAssessment** (1,417 lines) - Next priority
3. **WellbeingAssessment** (1,373 lines) - User-facing

**Why**: These are in the critical clinical workflow and impact user experience directly.

### Phase 2: Business-Critical Features (Week 2)
4. **TeamCompositionOptimizer** (1,253 lines) - HR/Business
5. **Reporting** (1,104 lines) - Core reporting
6. **VoiceVideoAnalysis** (1,120 lines) - AI feature
7. **SuccessionPlanning** (1,135 lines) - HR analytics

**Why**: High-value business features used by enterprise customers.

### Phase 3: Compliance & Admin (Week 3)
8. **WellnessPlanGenerator** (1,257 lines) - Clinical
9. **AdminDashboard** (1,092 lines) - Admin
10. **PredictiveAnalyticsDashboard** (1,077 lines) - Analytics
11. **AuditTrail** (1,172 lines) - Compliance

**Why**: Important for enterprise compliance and administration.

### Phase 4: Infrastructure & Lower Priority (Week 4)
12. **App.tsx** router extraction
13. **DocumentManagement** (1,088 lines)
14. **IntegrationHub** (1,073 lines)
15. Remaining components

**Why**: Infrastructure improvements and lower-impact features.

---

## Impact Analysis

### Before Splitting
- **Average component size**: 1,100+ lines
- **Maintainability**: Very poor
- **Testing**: Nearly impossible
- **Performance**: Slow renders
- **Developer velocity**: Slow (fear of breaking things)

### After Splitting All Components
- **Average component size**: ~200 lines (main orchestrator)
- **Maintainability**: Excellent
- **Testing**: Easy (unit test utilities, hooks, components)
- **Performance**: Fast (targeted re-renders)
- **Developer velocity**: Fast (isolated changes)

### Estimated Metrics
- **Total lines to refactor**: ~20,000 lines
- **Time investment**: 120-160 hours (4 weeks full-time)
- **Components created**: ~200 new modular files
- **Test coverage potential**: 80%+ (from near 0%)

---

## Splitting Template

For each component, use this proven pattern:

```bash
# 1. Create directory structure
mkdir -p src/pages/[component-name]/{hooks,components,utils}

# 2. Extract types first
# Create types.ts with all interfaces

# 3. Extract utility functions
# Move pure functions to utils/

# 4. Create custom hooks
# Extract React logic to hooks/

# 5. Create sub-components
# Build presentational components

# 6. Create orchestrator
# Build main index.tsx that coordinates everything

# 7. Update imports
# Update App.tsx and other imports

# 8. Test thoroughly
# Verify all functionality works

# 9. Remove old file
# Backup and delete original
```

---

## Success Metrics

For each split component:
- ✅ Main orchestrator < 200 lines
- ✅ All sub-components < 150 lines
- ✅ Each file has single responsibility
- ✅ All files individually testable
- ✅ No prop drilling > 3 levels
- ✅ Performance improved (faster renders)

---

## Tools to Use

1. **Line counter**: `wc -l file.tsx`
2. **Component analysis**: Read file, identify responsibilities
3. **Split planning**: Document structure before implementing
4. **Testing**: Test each split component thoroughly
5. **TypeScript**: Use strict typing throughout

---

**Total Progress**: 1/20 components completed (5%)

**Next Action**: Split **ClinicalAssessment.tsx** (1,417 lines)

**Estimated Completion Time**: 4 weeks for all 20 components

**Priority Focus**: Complete Phase 1 (Critical Clinical Components) first
