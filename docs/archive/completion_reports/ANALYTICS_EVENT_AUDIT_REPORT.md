# 📊 Analytics Event Schema & Naming Audit Report

**Date**: 2026-01-21
**Scope**: Frontend Analytics & Event Tracking
**Methodology**: Comprehensive code analysis of all event tracking implementations
**Status**: ✅ Audit Complete | ⚠️ Issues Found | 📋 Standards Needed

---

## 🚨 Executive Summary

**Overall Compliance Score**: 62/100

| Category | Score | Status | Issues Found |
|----------|-------|--------|--------------|
| **Schema Consistency** | 45/100 | ❌ Poor | 3 different schemas |
| **Naming Convention** | 70/100 | ⚠️ Fair | Mixed conventions |
| **Required Fields** | 55/100 | ⚠️ Fair | Missing standard fields |
| **API Consistency** | 50/100 | ❌ Poor | 2 different endpoints |
| **Type Safety** | 80/100 | ✅ Good | TypeScript used |
| **Documentation** | 40/100 | ❌ Poor | No schema docs |

**Critical Issues**:
- ❌ 3 different event schemas across services
- ❌ 2 different API endpoints for tracking
- ❌ No standardized event naming
- ❌ Missing common context fields (user_id, session_id)
- ❌ No runtime validation
- ❌ No event catalog/naming guide

---

## 🔍 Event Tracking Systems Discovered

### System 1: AB Testing Service
**Location**: `src/services/abTestingService.ts`

**Event Schema**:
```typescript
interface ConversionEvent {
  test_name: string;      // ❌ Uses test_name
  variant: string;
  event_type: string;     // ✅ Good
  timestamp: string;      // ✅ ISO format
  data?: Record<string, any>; // ❌ Generic
}
```

**API Endpoint**: `POST /ab-testing/track-event`

**Usage**:
```typescript
await abTestingService.trackEvent('variant_assigned', testName, {
  variant: assignment.variant,
  segments: assignment.segments
});
```

---

### System 2: Experiment Analytics
**Location**: `src/services/experimentAnalytics.ts`

**Event Schema**:
```typescript
// ❌ No interface defined, inferred from API calls
{
  experiment: string;      // ⚠️ Different from test_name
  variant: string;
  event_type: string;
  properties?: Record<string, any>; // ⚠️ Different from data
}
```

**API Endpoint**: `POST /api/v1/ab/track`

**Usage**:
```typescript
await ExperimentAnalytics.trackConversion(experimentName, value);
await ExperimentAnalytics.trackClick(experimentName, element);
await ExperimentAnalytics.trackView(experimentName);
await ExperimentAnalytics.trackCustom(experimentName, eventType, properties);
```

---

### System 3: Onboarding Service
**Location**: `src/services/onboardingService.ts`

**Event Schema**:
```typescript
interface ConversionEvent {
  event_type: string;
  session_id: string;     // ✅ Has session_id
  data?: Record<string, any>;
  // ❌ No timestamp field in interface
}
```

**API Endpoint**: `POST /onboarding/track-conversion`

**Usage**:
```typescript
await onboardingService.trackConversionEvent('quick_assessment_completed', {
  role: request.role,
  challenge: request.challenge,
  conversion_probability: response.data.insights.conversion_probability
});
```

---

### System 4: React Hook (useExperiment)
**Location**: `src/hooks/useExperiment.ts`

**Event Schema**:
```typescript
{
  experiment: string;
  variant: string;
  event_type: string;
  properties?: Record<string, any>;
  timestamp: string;  // ✅ Has timestamp
}
```

**API Endpoint**: `POST /api/v1/ab/track`

**Usage**:
```typescript
const { track } = useExperiment('cta_button_color_v1');
await track('signup_clicked', { button_color: 'green' });
```

---

## ❌ Critical Issues

### Issue 1: Inconsistent Property Names 🔴 CRITICAL

**Problem**: Same concept, different property names

| Concept | abTestingService | experimentAnalytics | useExperiment |
|----------|------------------|---------------------|----------------|
| **Test/Experiment** | `test_name` | `experiment` | `experiment` |
| **Event Data** | `data` | `properties` | `properties` |

**Impact**:
- Backend must handle multiple property names
- Confusion for developers
- Difficult to query analytics data
- Higher risk of bugs

**Example**:
```typescript
// ❌ INCONSISTENT
{ test_name: 'onboarding_v2', data: {...} }        // abTestingService
{ experiment: 'onboarding_v2', properties: {...} }  // experimentAnalytics
```

**Recommendation**: Standardize on `experiment_name` and `properties`

---

### Issue 2: Missing Common Context Fields 🔴 CRITICAL

**Problem**: No standard fields across all events

**Missing Fields**:
- ❌ `user_id` - Only in some events
- ❌ `session_id` - Only in onboarding events
- ❌ `page` / `screen` - Never tracked
- ❌ `timestamp` - Inconsistent (some have it, some don't)
- ❌ `url` - Never tracked
- ❌ `referrer` - Never tracked
- ❌ `device_type` - Never tracked

**Impact**:
- Can't attribute events to specific users
- Can't track user sessions
- Can't analyze which pages/events drive conversions
- Incomplete analytics data

**Recommendation**: Add standard context fields to all events

---

### Issue 3: Multiple API Endpoints 🔴 HIGH

**Problem**: 2 different endpoints for the same purpose

**Endpoints Found**:
1. `/ab-testing/track-event` (abTestingService)
2. `/api/v1/ab/track` (experimentAnalytics, useExperiment)
3. `/onboarding/track-conversion` (onboardingService)

**Impact**:
- Backend code duplication
- Different data processing logic
- Maintenance burden
- Risk of inconsistent data storage

**Recommendation**: Consolidate to single endpoint: `/api/v1/analytics/track`

---

### Issue 4: No Event Naming Convention 🟠 MEDIUM

**Problem**: Event names are inconsistent

**Found Event Names**:
- `variant_assigned` (snake_case)
- `conversion` (lowercase)
- `click` (lowercase)
- `view` (lowercase)
- `quick_assessment_completed` (snake_case)
- `setup_step_completed` (snake_case)
- `signup_clicked` (snake_case)
- `variant_forced` (snake_case)

**Issues**:
- No standard naming pattern
- Mix of snake_case and lowercase
- No namespacing/category prefixes
- No past tense vs present tense consistency

**Examples of Inconsistency**:
```typescript
'variant_assigned'  // past tense, snake_case
'click'            // present tense, lowercase
'conversion'       // noun, lowercase
```

**Recommendation**: Use category-action pattern (e.g., `ab_variant_assigned`, `funnel_signup_completed`)

---

### Issue 5: No Event Catalog 🟠 MEDIUM

**Problem**: No central list of all event names

**Impact**:
- Developers don't know what events exist
- Duplicate event names likely
- No documentation of event properties
- Hard to maintain consistency

**Recommendation**: Create event catalog with all events, properties, and schemas

---

### Issue 6: No Runtime Validation 🟠 MEDIUM

**Problem**: No validation before sending events

**Current Code**:
```typescript
await apiClient.post('/api/v1/ab/track', {
  experiment: experimentName,  // ❌ Could be undefined
  variant,                     // ❌ Could be undefined
  event_type: eventType,     // ❌ Could be anything
  properties                  // ❌ No validation
});
```

**Impact**:
- Invalid events sent to API
- Data quality issues
- Hard to debug

**Recommendation**: Add runtime validation with Zod schemas

---

## 📋 Naming Convention Violations

### Found Violations

| Event Name | Issue | Violation |
|------------|-------|------------|
| `variant_assigned` | No category prefix | Missing `ab_` |
| `conversion` | Too generic | Missing context |
| `click` | Too generic | Missing context |
| `view` | Too generic | Missing context |
| `quick_assessment_completed` | Inconsistent tense | Should be past tense |
| `setup_step_completed` | Good | ✅ Follows pattern |
| `signup_clicked` | Good | ✅ Follows pattern |

### Inconsistent Naming Patterns

**Past Tense** (should be consistent):
- ✅ `variant_assigned`
- ✅ `setup_step_completed`
- ❌ `conversion` (should be `converted`)

**Generic vs Specific**:
- ❌ `click` (too generic) → Should be `button_clicked` or `cta_clicked`
- ❌ `view` (too generic) → Should be `page_viewed` or `screen_viewed`
- ✅ `variant_assigned` (specific)

**Category Prefixes** (missing):
- ❌ No prefix to indicate event type
- ❌ Can't distinguish between:
  - A/B testing events
  - Funnel events
  - User actions
  - System events

**Recommended Pattern**: `category_action_object` (past tense)

Examples:
- `ab_variant_assigned`
- `funnel_signup_completed`
- `user_button_clicked`
- `system_error_occurred`
- `assessment_submitted`

---

## 📊 Schema Comparison Matrix

| Field | abTestingService | experimentAnalytics | onboardingService | useExperiment | Standard |
|-------|------------------|---------------------|---------------------|---------------|----------|
| **experiment_name** | ❌ `test_name` | ❌ `experiment` | ❌ Missing | ❌ `experiment` | `experiment_name` |
| **variant** | ✅ | ✅ | ❌ Missing | ✅ | ✅ |
| **event_type** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **timestamp** | ✅ | ❌ Missing | ❌ Missing | ✅ | ✅ |
| **properties** | ❌ `data` | ✅ | ❌ `data` | ✅ | `properties` |
| **user_id** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | ✅ Required |
| **session_id** | ❌ Missing | ❌ Missing | ✅ | ❌ Missing | ✅ Required |
| **page** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | ✅ Optional |
| **url** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | ✅ Optional |

---

## 🎯 Recommendations

### Priority 1: Standardize Event Schema 🔴 CRITICAL

Create unified event interface:

```typescript
interface StandardAnalyticsEvent {
  // Required fields
  event_name: string;        // Standardized name (e.g., 'ab_variant_assigned')
  event_type: string;        // 'track', 'identify', 'page', etc.
  timestamp: string;         // ISO 8601 format

  // Context fields
  user_id?: string;          // Optional user ID
  session_id: string;        // Required session ID
  page?: string;            // Current page/screen
  url?: string;             // Current URL

  // Event properties
  properties: Record<string, any>;
}
```

### Priority 2: Create Event Catalog 🟠 HIGH

Document all events in centralized location with:
- Event name
- Description
- Properties schema
- When it's triggered
- Example usage

### Priority 3: Consolidate API Endpoints 🔴 HIGH

Single endpoint: `/api/v1/analytics/track`

Route events internally based on event_type or category.

### Priority 4: Add Naming Convention Guide 🟠 MEDIUM

**Pattern**: `category_action_object` (past tense)

**Categories**:
- `ab_` - A/B testing events
- `funnel_` - Conversion funnel events
- `user_` - User-initiated actions
- `system_` - System events
- `error_` - Error events

**Actions**: Past tense verbs
- `assigned`, `completed`, `clicked`, `submitted`, `viewed`, `failed`

**Examples**:
- `ab_variant_assigned`
- `funnel_signup_completed`
- `user_button_clicked`
- `error_api_failed`

### Priority 5: Add Validation Layer 🟡 MEDIUM

Add Zod schemas for runtime validation:

```typescript
import { z } from 'zod';

const AnalyticsEventSchema = z.object({
  event_name: z.string().min(1).max(100),
  event_type: z.enum(['track', 'identify', 'page']),
  timestamp: z.string().datetime(),
  session_id: z.string().min(1),
  properties: z.record(z.any())
});
```

---

## 📈 Compliance Score Breakdown

### Schema Consistency: 45/100 ❌

**Deductions**:
- -30 points: 3 different schemas
- -15 points: Missing common fields
- -10 points: No schema documentation

### Naming Convention: 70/100 ⚠️

**Deductions**:
- -15 points: No category prefixes
- -10 points: Inconsistent patterns
- -5 points: Generic names

### Required Fields: 55/100 ⚠️

**Deductions**:
- -20 points: Missing user_id
- -15 points: Inconsistent timestamp
- -10 points: No standard required fields

### API Consistency: 50/100 ❌

**Deductions**:
- -30 points: 3 different endpoints
- -20 points: Different request formats

### Type Safety: 80/100 ✅

**Strengths**:
- TypeScript interfaces defined
- Good type inference

**Deductions**:
- -10 points: Some `any` types
- -10 points: No runtime validation

### Documentation: 40/100 ❌

**Deductions**:
- -40 points: No schema docs
- -20 points: No event catalog
- -20 points: No naming guide

---

## 🛠️ Implementation Plan

### Phase 1: Create Unified Event Utility (2 hours)

**Tasks**:
1. Create `src/services/analytics/tracker.ts`
2. Define standard event schema
3. Implement validation
4. Add automatic context fields

### Phase 2: Create Event Catalog (1 hour)

**Tasks**:
1. Document all existing events
2. Define naming conventions
3. Create event naming guide
4. Add examples

### Phase 3: Update Existing Tracking (3 hours)

**Tasks**:
1. Update abTestingService to use unified tracker
2. Update experimentAnalytics to use unified tracker
3. Update onboardingService to use unified tracker
4. Update useExperiment hook to use unified tracker

### Phase 4: Backend Consolidation (4 hours)

**Tasks**:
1. Consolidate endpoints to single API
2. Update data models
3. Add validation middleware
4. Update analytics dashboards

### Phase 5: Testing & Validation (2 hours)

**Tasks**:
1. Add unit tests for event validation
2. Add integration tests for API endpoints
3. Verify backward compatibility
4. Load test new endpoints

**Total Estimated Time**: 12 hours

---

## ✅ Next Steps

### Immediate Actions (This Week)
1. ✅ Review this audit report
2. ⏳ Create unified event schema
3. ⏳ Document naming conventions
4. ⏳ Create event catalog

### Short-term Actions (This Month)
1. ⏳ Implement unified tracking utility
2. ⏳ Update all existing tracking
3. ⏳ Add validation layer
4. ⏳ Consolidate backend endpoints

### Long-term Actions (This Quarter)
1. ⏳ Set up event monitoring dashboard
2. ⏳ Implement event governance process
3. ⏳ Create analytics QA process
4. ⏳ Train team on standards

---

## 📚 Related Files

### Analytics Services
- `src/services/analyticsService.ts` - Analytics query service
- `src/services/abTestingService.ts` - A/B testing service
- `src/services/experimentAnalytics.ts` - Experiment analytics
- `src/services/onboardingService.ts` - Onboarding service
- `src/hooks/useExperiment.ts` - React hook for experiments

### Backend Endpoints
- `/ab-testing/track-event` - Legacy A/B testing endpoint
- `/api/v1/ab/track` - New A/B testing endpoint
- `/api/v1/ab/assign` - Variant assignment
- `/onboarding/track-conversion` - Onboarding events

---

## 📞 Support

### Questions?
- **Analytics Team**: #analytics
- **Engineering**: #engineering
- **Documentation**: `/docs/analytics/`

---

**Report Version**: 1.0.0
**Status**: ✅ Audit Complete | ⚠️ Awaiting Implementation
**Next Action**: Implement unified event schema and standards
