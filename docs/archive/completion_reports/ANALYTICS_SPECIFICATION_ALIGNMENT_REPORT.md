# 🔍 Analytics Event Specification Alignment Report

**Date**: January 21, 2026
**Status**: ⚠️ **MISALIGNMENTS FOUND**
**Severity**: 🟡 MEDIUM - Type safety issues, runtime errors possible

---

## 📋 Summary

The analytics tracking system has **4 critical misalignments** between the `EVENT_CATALOG` specification and actual event usage in the codebase. These are **type safety violations** where dynamically generated event names are not defined in the catalog.

---

## 🔴 Critical Issues: Events Used But NOT in EVENT_CATALOG

### Issue #1: Login Funnel Events
**Severity**: 🟡 MEDIUM - Type cast bypasses validation
**Files Affected**:
- `LoginSignupRefactored.tsx:775` - `trackFunnel('login', 'started', ...)`
- `LoginSignupRefactored.tsx:783` - `trackFunnel('login', 'completed', ...)`

**Problem**:
```typescript
// Code uses:
trackFunnel('login', 'started', { ... });
// Generates: 'funnel_login_started'

// BUT EVENT_CATALOG has:
FUNNEL_SIGNUP_STARTED: 'funnel_signup_started'  ✓
FUNNEL_ONBOARDING_STARTED: 'funnel_onboarding_started'  ✓
FUNNEL_ASSESSMENT_STARTED: 'funnel_assessment_started'  ✓
// MISSING: FUNNEL_LOGIN_STARTED ❌
```

**Generated Events**:
- ❌ `funnel_login_started` - NOT in catalog
- ❌ `funnel_login_completed` - NOT in catalog

**Impact**: Type cast (`as EventName`) bypasses TypeScript validation. These events will be sent but aren't officially defined.

---

### Issue #2: Team Creation Funnel Events
**Severity**: 🟡 MEDIUM - Type cast bypasses validation
**Files Affected**:
- `CreateTeamModal.tsx:40` - `trackFunnel('team_creation', 'started', ...)`
- `CreateTeamModal.tsx:52` - `trackFunnel('team_creation', 'completed', ...)`

**Problem**:
```typescript
// Code uses:
trackFunnel('team_creation', 'started', { ... });
// Generates: 'funnel_team_creation_started'

// BUT EVENT_CATALOG has:
FUNNEL_SIGNUP_STARTED: 'funnel_signup_started'  ✓
FUNNEL_ONBOARDING_STARTED: 'funnel_onboarding_started'  ✓
FUNNEL_ASSESSMENT_STARTED: 'funnel_assessment_started'  ✓
// MISSING: FUNNEL_TEAM_CREATION_STARTED ❌
```

**Generated Events**:
- ❌ `funnel_team_creation_started` - NOT in catalog
- ❌ `funnel_team_creation_completed` - NOT in catalog

**Impact**: Same as above - these events work but aren't in the spec.

---

### Issue #3: Assessment Funnel Dynamic Events
**Severity**: 🟡 MEDIUM - Partial coverage
**Files Affected**:
- `TakeAssessment.tsx:153` - `trackFunnel('assessment', 'started', ...)`
- `TakeAssessment.tsx:312` - `trackFunnel('assessment', 'completed', ...)`

**Problem**:
```typescript
// Code uses:
trackFunnel('assessment', 'started', { ... });
// Generates: 'funnel_assessment_started' ✓ (IN CATALOG)

trackFunnel('assessment', 'completed', { ... });
// Generates: 'funnel_assessment_completed' ✓ (IN CATALOG)
```

**Status**: ✅ ALIGNED - Both events exist in EVENT_CATALOG

---

### Issue #4: Signup Funnel Events
**Severity**: ✅ NONE - Aligned
**Files Affected**:
- `Register.tsx:80` - `trackFunnel('signup', 'started', ...)`
- `Register.tsx:89` - `trackFunnel('signup', 'completed', ...)`
- `LoginSignupRefactored.tsx:832` - `trackFunnel('signup', 'started', ...)`
- `LoginSignupRefactored.tsx:841` - `trackFunnel('signup', 'completed', ...)`

**Status**: ✅ ALIGNED - Both events exist in EVENT_CATALOG

---

## 📊 Alignment Matrix

| Event Name | In Catalog | In Usage | Status |
|------------|------------|----------|--------|
| `funnel_signup_started` | ✅ Yes | ✅ Yes | ✅ Aligned |
| `funnel_signup_completed` | ✅ Yes | ✅ Yes | ✅ Aligned |
| `funnel_login_started` | ❌ **NO** | ✅ Yes | ⚠️ **MISALIGNED** |
| `funnel_login_completed` | ❌ **NO** | ✅ Yes | ⚠️ **MISALIGNED** |
| `funnel_onboarding_started` | ✅ Yes | ❌ No | ⚠️ Unused |
| `funnel_onboarding_completed` | ✅ Yes | ❌ No | ⚠️ Unused |
| `funnel_assessment_started` | ✅ Yes | ✅ Yes | ✅ Aligned |
| `funnel_assessment_completed` | ✅ Yes | ✅ Yes | ✅ Aligned |
| `funnel_team_creation_started` | ❌ **NO** | ✅ Yes | ⚠️ **MISALIGNED** |
| `funnel_team_creation_completed` | ❌ **NO** | ✅ Yes | ⚠️ **MISALIGNED** |

---

## 🔍 Root Cause Analysis

### **The Problem: Dynamic Event Name Generation**

The `trackFunnel()` helper method dynamically constructs event names:

```typescript
// tracker.ts:788-795
trackFunnel(
  funnelStep: string,
  status: 'started' | 'completed',
  properties?: Record<string, any>
): void {
  const eventName = `funnel_${funnelStep}_${status}` as EventName;  // ❌ TYPE CAST!
  this.track(eventName, properties);
}
```

**Why This Causes Issues**:

1. **Type Safety Bypass**: The `as EventName` cast tells TypeScript "trust me, this is valid"
2. **No Validation**: No runtime check against EVENT_CATALOG
3. **Silent Failures**: Typos in funnel names won't be caught

**Example**:
```typescript
// This compiles but 'funnel_login_started' is NOT in EVENT_CATALOG:
trackFunnel('login', 'started', { ... });
// Even a typo would compile:
trackFunnel('loggin', 'started', { ... });  // Generates 'funnel_loggin_started' - INVALID!
```

---

## 🛠️ Recommended Fixes

### Fix #1: Add Missing Events to EVENT_CATALOG (Immediate)

**File**: `frontend/src/services/analytics/tracker.ts`

```typescript
export const EVENT_CATALOG = {
  // A/B Testing Events (ab_*)
  AB_VARIANT_ASSIGNED: 'ab_variant_assigned',
  AB_VARIANT_FORCED: 'ab_variant_forced',
  AB_EXPOSURE: 'ab_exposure',

  // Funnel Events (funnel_*)
  FUNNEL_SIGNUP_STARTED: 'funnel_signup_started',
  FUNNEL_SIGNUP_COMPLETED: 'funnel_signup_completed',

  // ✅ ADD THESE:
  FUNNEL_LOGIN_STARTED: 'funnel_login_started',          // NEW
  FUNNEL_LOGIN_COMPLETED: 'funnel_login_completed',      // NEW

  FUNNEL_ONBOARDING_STARTED: 'funnel_onboarding_started',
  FUNNEL_ONBOARDING_COMPLETED: 'funnel_onboarding_completed',

  FUNNEL_ASSESSMENT_STARTED: 'funnel_assessment_started',
  FUNNEL_ASSESSMENT_COMPLETED: 'funnel_assessment_completed',

  // ✅ ADD THESE:
  FUNNEL_TEAM_CREATION_STARTED: 'funnel_team_creation_started',    // NEW
  FUNNEL_TEAM_CREATION_COMPLETED: 'funnel_team_creation_completed',// NEW

  // ... rest of catalog
} as const;
```

**Effort**: 2 minutes
**Risk**: None (additive change only)

---

### Fix #2: Add Runtime Validation (Recommended)

**File**: `frontend/src/services/analytics/tracker.ts`

```typescript
trackFunnel(
  funnelStep: string,
  status: 'started' | 'completed',
  properties?: Record<string, any>
): void {
  const eventName = `funnel_${funnelStep}_${status}` as EventName;

  // ✅ NEW: Runtime validation against EVENT_CATALOG
  const allEventNames = Object.values(EVENT_CATALOG);
  if (!allEventNames.includes(eventName as any)) {
    console.error(`❌ [Analytics] Event '${eventName}' is not in EVENT_CATALOG!`, {
      funnelStep,
      status,
      generatedEvent: eventName
    });
    // Still track the event (don't break production), but log the issue
  }

  this.track(eventName, properties);
}
```

**Benefits**:
- Catches typos and missing events in development
- Provides visibility into spec violations
- Doesn't break production (logs only)

---

### Fix #3: Type-Safe Funnel Helper (Best Practice)

**Option A: Enum-based approach**

```typescript
// Define allowed funnel names
export const FUNNEL_NAMES = {
  SIGNUP: 'signup',
  LOGIN: 'login',
  ONBOARDING: 'onboarding',
  ASSESSMENT: 'assessment',
  TEAM_CREATION: 'team_creation',
} as const;

export type FunnelName = typeof FUNNEL_NAMES[keyof typeof FUNNEL_NAMES];

// Type-safe helper
trackFunnel(
  funnelName: FunnelName,  // ✅ Only valid funnels allowed
  status: 'started' | 'completed',
  properties?: Record<string, any>
): void {
  const eventName = `funnel_${funnelName}_${status}` as EventName;
  this.track(eventName, properties);
}
```

**Option B: Direct event mapping**

```typescript
// Remove dynamic generation, use direct mapping
export const FUNNEL_EVENTS = {
  SIGNUP_STARTED: EVENT_CATALOG.FUNNEL_SIGNUP_STARTED,
  SIGNUP_COMPLETED: EVENT_CATALOG.FUNNEL_SIGNUP_COMPLETED,
  LOGIN_STARTED: EVENT_CATALOG.FUNNEL_LOGIN_STARTED,
  LOGIN_COMPLETED: EVENT_CATALOG.FUNNEL_LOGIN_COMPLETED,
  // ... etc
} as const;

// Usage:
track(FUNNEL_EVENTS.LOGIN_STARTED, properties);
```

---

## 📈 Impact Assessment

### **Current State**
- **Total Events in Catalog**: 30+
- **Events Actually Used**: ~20
- **Events in Catalog but Unused**: 2 (onboarding)
- **Events Used but Not in Catalog**: 4 (login, team_creation)
- **Alignment Score**: 80%

### **Impact on Analytics**

1. **Data Quality**: ✅ No impact - events are still tracked
2. **Type Safety**: ❌ Reduced - type casts bypass validation
3. **Documentation**: ❌ Misleading - catalog doesn't match reality
4. **Discoverability**: ❌ Poor - developers can't find all valid events
5. **Refactoring**: ❌ Risky - typos won't be caught

### **Business Impact**

- ✅ **No Data Loss**: All events are being tracked
- ⚠️ **Hidden Events**: Login/team events not visible in catalog
- ⚠️ **Maintenance Risk**: New developers might not know about these events
- ⚠️ **Documentation Drift**: Specification no longer matches implementation

---

## ✅ Immediate Action Items

### Priority 1: Fix EVENT_CATALOG (5 minutes)
1. Add `FUNNEL_LOGIN_STARTED` and `FUNNEL_LOGIN_COMPLETED`
2. Add `FUNNEL_TEAM_CREATION_STARTED` and `FUNNEL_TEAM_CREATION_COMPLETED`
3. Update documentation

### Priority 2: Add Runtime Validation (15 minutes)
1. Add validation in `trackFunnel()` method
2. Test with invalid funnel name to verify logging
3. Monitor logs for any existing violations

### Priority 3: Audit Other Helpers (30 minutes)
1. Check `trackPage()` for similar issues
2. Check `trackABTest()` for similar issues
3. Review all direct `track()` calls

---

## 🧪 Verification Steps

After implementing fixes, verify:

```bash
# 1. Check TypeScript compiles
npm run type-check

# 2. Run development server
npm run dev

# 3. Open browser console and test:

# Test login funnel (should NOT log errors)
tracker.trackFunnel('login', 'started', {});

# Test team creation (should NOT log errors)
tracker.trackFunnel('team_creation', 'started', {});

# Test invalid funnel (should log error)
tracker.trackFunnel('invalid_funnel', 'started', {});
# Expected: ❌ [Analytics] Event 'funnel_invalid_funnel_started' is not in EVENT_CATALOG!
```

---

## 📚 Additional Recommendations

### 1. Create Event Naming Convention
Document clear rules for event names:
```
{category}_{action}_{status}

Examples:
- funnel_signup_started
- user_button_clicked
- system_error_occurred
- engagement_content_viewed
```

### 2. Add ESLint Rule
Create custom rule to prevent invalid event names:
```typescript
// eslintrc.js
{
  rules: {
    'no-restricted-syntax': [
      'error',
      {
        selector: 'CallExpression[callee.name="trackFunnel"] > Literal.arguments:first',
        message: 'Use EVENT_CATALOG constants instead of strings'
      }
    ]
  }
}
```

### 3. Generate Catalog from Usage
Create script to auto-generate EVENT_CATALOG from actual usage:
```typescript
// scripts/generate-event-catalog.ts
const allEvents = new Set([
  ...findTrackCalls(),  // Scan codebase for track() calls
  ...findTrackFunnelCalls(),  // Scan for trackFunnel() calls
]);

console.log('export const EVENT_CATALOG = {');
for (const event of allEvents) {
  const constantName = eventToConstantName(event);
  console.log(`  ${constantName}: '${event}',`);
}
console.log('} as const;');
```

---

## 🎯 Conclusion

The analytics tracking system is **functionally working** but has **specification misalignment** that reduces type safety and maintainability.

**Quick Fix**: Add 4 missing events to EVENT_CATALOG (5 minutes)
**Long-term Fix**: Implement type-safe funnel helpers and runtime validation

**Status**: ⚠️ **NEEDS ATTENTION** - No production impact, but should be fixed for maintainability

---

**Report Generated**: January 21, 2026
**Analyst**: Analytics Alignment Auditor
**Next Review**: After fixes implemented
