# GitHub Issues to Create - Pre-existing Code Quality Issues

**Date:** 2026-01-18
**Context:** These issues were discovered during CI investigation for PR #1
**Status:** Pre-existing issues, NOT caused by boundary condition fixes

---

## 🔴 HIGH PRIORITY ISSUES

### Issue #1: Frontend - File Casing Conflicts Breaking TypeScript

**Title:** [Frontend] Fix file casing conflicts (Badge.tsx vs badge.tsx, Input.tsx vs input.tsx)

**Type:** Bug
**Priority:** High
**Component:** Frontend UI Components

**Description:**
TypeScript is throwing errors due to file casing inconsistencies. On case-insensitive filesystems (macOS, Windows), this causes import conflicts.

**Files Affected:**
- `src/components/ui/Badge.tsx` vs `src/components/ui/badge.tsx`
- `src/components/ui/Input.tsx` vs `src/components/ui/input.tsx`
- `src/components/ui/Select.tsx` vs `src/components/ui/select.tsx`

**Error Messages:**
```
error TS1149: File name 'Badge.tsx' differs from already included file name 'badge.tsx' only in casing.
error TS1149: File name 'Input.tsx' differs from already included file name 'input.tsx' only in casing.
error TS1149: File name 'Select.tsx' differs from already included file name 'select.tsx' only in casing.
```

**Impact:**
- Blocks TypeScript compilation
- Fails CI linting checks
- Causes confusion in imports

**Solution:**
1. Choose consistent casing (recommend lowercase: `badge.tsx`, `input.tsx`, `select.tsx`)
2. Rename files to match chosen convention
3. Update all imports across the codebase

**Estimated Effort:** 2-3 hours

**Files to Modify:**
- Rename files in `src/components/ui/`
- Update imports in:
  - `src/components/admin/SecurityDashboard.tsx`
  - `src/components/analytics/SkillGapAnalysis.tsx`
  - `src/components/admin/SuccessionPlanning.tsx`
  - Any other files importing these components

---

### Issue #2: Frontend - Button Variant Type Mismatches

**Title:** [Frontend] Fix Button variant "destructive" vs "danger" type inconsistencies

**Type:** Bug
**Priority:** High
**Component:** Frontend UI Components

**Description:**
Multiple components are using `variant="destructive"` but the Button component only accepts `"danger"` as the error variant.

**Files Affected:**
- `src/components/ai/MentalHealthChatbot.tsx` (lines 231, 247)
- `src/components/analytics/ClinicalAnalyticsDashboard.tsx` (lines 312, 393)
- `src/components/analytics/PopulationHealthDashboard.tsx` (line 417)
- `src/components/analytics/SkillGapAnalysis.tsx` (line 540)

**Error Messages:**
```
Type '"destructive"' is not assignable to type '"link" | "default" | "primary" | "secondary" | "danger" | "outline" | "ghost"'
Type '"destructive"' is not assignable to type '"success" | "warning" | "error" | "default" | "primary" | "secondary" | "outline"'
```

**Impact:**
- Type errors prevent TypeScript compilation
- Inconsistent button styling across the app

**Solution:**
Global find-and-replace:
```bash
# In frontend directory
find . -name "*.tsx" -type f -exec sed -i '' 's/variant="destructive"/variant="danger"/g' {} \;
```

**Estimated Effort:** 30 minutes

---

### Issue #3: Frontend - Missing Module exports and Imports

**Title:** [Frontend] Fix securityService import and missing exports

**Type:** Bug
**Priority:** High
**Component:** Frontend Security Monitoring

**Description:**
`SecurityMonitoringDashboard.tsx` is trying to import `securityService` which doesn't exist in the securityService module.

**Files Affected:**
- `src/components/admin/SecurityMonitoringDashboard.tsx` (line 15)

**Error Message:```
'"../../services/securityService"' has no exported member named 'securityService'. Did you mean to use 'import api from "@/services/api"' instead?
```

**Impact:**
- Security monitoring dashboard cannot compile
- Blocker for security features

**Solution:**
1. Check what's actually exported from `securityService`
2. Either:
   - Add missing export to securityService module, OR
   - Fix the import to use the correct export name

**Estimated Effort:** 1 hour

---

### Issue #4: Frontend - Missing Common UI Components

**Title:** [Frontend] Fix missing './common/card' import in SecurityMonitoringDashboard

**Type:** Bug
**Priority:** High
**Component:** Frontend Security Monitoring

**Description:**
`SecurityMonitoringDashboard.tsx` is trying to import `'./common/card'` which doesn't exist.

**Files Affected:**
- `src/components/admin/SecurityMonitoringDashboard.tsx` (line 14)

**Error Message:**
```
error TS2307: Cannot find module './common/card' or its corresponding type declarations.
```

**Impact:**
- Security monitoring dashboard cannot compile

**Solution:**
1. Create the missing `common/card.tsx` component, OR
2. Update import to use existing Card component from `@/components/ui/card`

**Estimated Effort:** 1-2 hours

---

## 🟡 MEDIUM PRIORITY ISSUES

### Issue #5: Frontend - Type Safety Issues with Unknown Types

**Title:** [Frontend] Add proper typing for API responses (unknown type issues)

**Type:** Technical Debt
**Priority:** Medium
**Component:** Frontend Type Safety

**Description:**
Multiple components are accessing properties on `unknown` type, which defeats TypeScript's type checking.

**Files Affected:**
- `src/components/analytics/ClinicalAnalyticsDashboard.tsx:82` - `.data` on unknown
- `src/components/analytics/PopulationHealthDashboard.tsx:348,359` - `.trend_data` issues
- `src/components/analytics/PredictiveAnalyticsDashboard.tsx:579` - `.category` on unknown

**Error Messages:**
```
error TS2339: Property 'data' does not exist on type 'unknown'.
error TS2339: Property 'trend_data' does not exist on type 'SummaryStatistics'.
error TS2345: Argument of type 'unknown' is not assignable to parameter of type 'SetStateAction<SummaryStatistics>'.
```

**Impact:**
- Reduced type safety
- Runtime errors possible
- Harder to maintain code

**Solution:**
1. Create proper TypeScript interfaces for API responses
2. Use `zod` or similar for runtime validation
3. Add type assertions with proper guards

**Estimated Effort:** 4-6 hours

---

### Issue #6: Frontend - Missing Component Properties

**Title:** [Frontend] Fix missing required props in App.refactored.tsx

**Type:** Bug
**Priority:** Medium
**Component:** Frontend App Routing

**Description:**
`App.refactored.tsx` is rendering components without required props.

**Files Affected:**
- `src/App.refactored.tsx` (lines 116, 117, 118)

**Error Messages:**
```
error TS2741: Property 'onGetStarted' is missing in type '{}' but required in type 'ImprovedLandingProps'.
error TS2739: Type '{}' is missing properties from type 'ProgressiveDashboardProps': initialRole, initialChallenge
error TS2739: Type '{}' is missing properties from type 'StreamlinedRegisterProps': userRole, challenge
```

**Impact:**
- Components won't render correctly
- Missing critical functionality

**Solution:**
1. Identify what values should be passed for these props
2. Add proper state management for props
3. Connect to appropriate data sources

**Estimated Effort:** 2-3 hours

---

### Issue #7: Frontend - PWA Manager Type Mismatches

**Title:** [Frontend] Fix PWAManager interface or remove unused code

**Type:** Technical Debt
**Priority:** Medium
**Component:** Frontend PWA Features

**Description:**
Code is calling `.register` and `.unregister` on PWAManager but the interface doesn't define these methods.

**Files Affected:**
- `src/App.refactored.tsx` (lines 84, 88)

**Error Messages:**
```
error TS2339: Property 'register' does not exist on type 'PWAManager'.
error TS2339: Property 'unregister' does not exist on type 'PWAManager'.
```

**Impact:**
- PWA features may not work
- Type safety compromised

**Solution:**
1. Update PWAManager interface to include register/unregister methods, OR
2. Remove unused PWA code if not needed

**Estimated Effort:** 1 hour

---

## 🟢 LOW PRIORITY ISSUES

### Issue #8: Backend - Missing app.core.email Module

**Title:** [Backend] Create app.core.email module or fix imports in crisis_templates

**Type:** Technical Debt
**Priority:** Low
**Component:** Backend Notifications

**Description:**
`app/services/notifications.py` imports `app.core.email` which doesn't exist.

**Files Affected:**
- `app/services/notifications.py` (line 15)

**Error Message:**
```
ModuleNotFoundError: No module named 'app.core.email'
```

**Impact:**
- Notification service can't be imported
- Crisis notification features may be broken

**Solution:**
1. Create `app/core/email.py` with `send_email_async` function, OR
2. Update import to use existing email sending code

**Estimated Effort:** 2-3 hours

---

### Issue #9: Backend - Duplicate Test Fixtures

**Title:** [Backend] Remove duplicate fixtures in test files

**Type:** Code Quality
**Priority:** Low
**Component:** Testing Infrastructure

**Description:**
Test files have duplicate fixture definitions causing potential conflicts.

**Files Affected:**
- `tests/api/test_growth.py` - client, db_session, test_user, auth_headers duplicated
- `tests/api/test_longitudinal_analysis.py` - same fixtures duplicated

**Impact:**
- Test confusion
- Maintenance burden
- Possible test failures

**Solution:**
1. Move fixtures to `tests/conftest.py` for sharing
2. Remove duplicates from individual test files

**Estimated Effort:** 1 hour

---

### Issue #10: Frontend - Progress Component Type Mismatch

**Title:** [Frontend] Fix Progress component props type mismatch

**Type:** Bug
**Priority:** Low
**Component:** Frontend UI Components

**Description:**
SkillGapAnalysis is passing wrong props to Progress component.

**Files Affected:**
- `src/components/analytics/SkillGapAnalysis.tsx` (line 882)

**Error Message:**
```
error TS2322: Type '{ value: number; max: number; className: string; }' is not assignable to type 'IntrinsicAttributes & ProgressProps'.
```

**Impact:**
- Progress bars may not display correctly

**Solution:**
1. Check Progress component's actual props interface
2. Update props to match component requirements

**Estimated Effort:** 30 minutes

---

## 📋 Summary

**Total Issues:** 10
- 🔴 High Priority: 4 (blocking compilation)
- 🟡 Medium Priority: 3 (type safety issues)
- 🟢 Low Priority: 3 (nice to have)

**Recommended Action Plan:**
1. **Phase 1 (This Week):** Fix all High Priority issues (Issues #1-4)
2. **Phase 2 (Next Week):** Fix Medium Priority issues (Issues #5-7)
3. **Phase 3 (Backlog):** Fix Low Priority issues during maintenance time (Issues #8-10)

**Total Estimated Effort:** 17-23 hours across all issues

**Note:** None of these issues were introduced by the boundary condition fixes in PR #1. They are pre-existing technical debt that should be tracked separately.
