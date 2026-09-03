# 📊 Analytics Event Catalog & Naming Guide

**Version**: 1.0.0
**Last Updated**: 2026-01-21
**Status**: ✅ Active Standard

---

## 🎯 Purpose

This document establishes the **single source of truth** for all analytics events tracked across the PsychSync platform. It defines:

- **Standard event schema** - All events follow this structure
- **Naming convention** - Pattern: `category_action_object` (past tense)
- **Event catalog** - Complete list of all events with properties
- **Best practices** - How to create new events correctly

**Why This Matters**:
- ✅ Consistent data structure for reliable analytics
- ✅ Easy to query and analyze across all events
- ✅ Prevents duplicate/conflicting event names
- ✅ Self-documenting code with clear event meanings
- ✅ Runtime validation prevents malformed events

---

## 📐 Event Schema Standard

### Required Fields

```typescript
interface StandardAnalyticsEvent {
  // Event identification
  event_name: string;        // From EVENT_CATALOG (e.g., 'user_button_clicked')
  event_type: 'track' | 'identify' | 'page' | 'screen';
  timestamp: string;         // ISO 8601 format (auto-populated)

  // Context (auto-populated by tracker)
  user_id?: string;          // Current user ID (if authenticated)
  session_id: string;        // Session identifier (auto-generated)
  page?: string;             // Current page path (auto-populated)
  url?: string;              // Full URL (auto-populated)
  referrer?: string;         // Previous page (auto-populated)

  // Event-specific data
  properties?: Record<string, any>;  // Event-specific properties
}
```

### Auto-Populated Fields

These fields are **automatically added** by the unified tracker. You don't need to include them:

- ✅ `timestamp` - Added when event is tracked
- ✅ `session_id` - Managed by SessionManager
- ✅ `page` - Current `window.location.pathname`
- ✅ `url` - Current `window.location.href`
- ✅ `referrer` - `document.referrer`

Only include these if you need to **override** the automatic value.

---

## 🏷️ Naming Convention

### Pattern: `category_action_object`

All event names follow this pattern:

```typescript
category_action_object
```

#### 1. Category (Required)

Prefix indicating the event type:

| Category | Usage | Examples |
|----------|-------|----------|
| `ab_` | A/B testing events | `ab_variant_assigned`, `ab_exposure` |
| `funnel_` | Conversion funnel steps | `funnel_signup_started`, `funnel_onboarding_completed` |
| `user_` | User-initiated actions | `user_button_clicked`, `user_form_submitted` |
| `system_` | System events | `system_error_occurred`, `system_api_call_failed` |
| `error_` | Error events | `error_api_failed`, `error_validation_failed` |
| `engagement_` | Engagement metrics | `engagement_content_viewed`, `engagement_video_played` |
| `performance_` | Performance metrics | `performance_page_load`, `performance_api_latency` |

#### 2. Action (Required)

Past tense verb describing what happened:

| Action | When to Use | Example |
|--------|-------------|---------|
| `assigned` | Something was allocated | `ab_variant_assigned` |
| `completed` | Process finished successfully | `funnel_onboarding_completed` |
| `clicked` | Element clicked/tapped | `user_button_clicked` |
| `submitted` | Form submitted | `user_form_submitted` |
| `viewed` | Content viewed | `engagement_content_viewed` |
| `failed` | Operation failed | `system_api_call_failed` |
| `started` | Process initiated | `funnel_assessment_started` |
| `converted` | Conversion occurred | `funnel_signup_converted` |
| `dismissed` | Modal/popup closed | `user_modal_dismissed` |
| `opened` | Modal/popup shown | `user_modal_opened` |
| `changed` | Value modified | `user_input_changed` |
| `scrolled` | Scroll action | `user_page_scrolled` |

#### 3. Object (Optional)

Specific item being acted upon:

```typescript
user_button_clicked        // ✅ Good: specific
user_clicked              // ❌ Bad: too generic
user_link_clicked         // ✅ Good: specific
user_cta_clicked          // ✅ Good: call-to-action specific
```

### Examples

```typescript
// ✅ CORRECT: Follows convention
'user_button_clicked'
'funnel_signup_completed'
'ab_variant_assigned'
'engagement_content_viewed'
'system_error_occurred'

// ❌ INCORRECT: Violates convention
'buttonClick'              // Wrong: camelCase
'variant_assigned'         // Wrong: missing category prefix
'user_clicked'             // Wrong: too generic
'conversion'               // Wrong: noun instead of verb, missing prefix
'setup_step_completed'     // Wrong: legacy name, should be 'funnel_setup_completed'
```

---

## 📚 Event Catalog

### A/B Testing Events (`ab_*`)

#### `ab_variant_assigned`
**Description**: User assigned to A/B test variant

**Trigger**: When variant assignment is determined

**Properties**:
```typescript
{
  experiment_name: string;    // e.g., 'cta_button_color_v1'
  variant: string;            // e.g., 'control', 'treatment_a'
  assignment_method: string;  // 'hash', 'random', 'forced'
  segments?: string[];        // User segments if segmented
}
```

**Example**:
```typescript
analytics.track(EVENT_CATALOG.AB_VARIANT_ASSIGNED, {
  experiment_name: 'cta_button_color_v1',
  variant: 'green',
  assignment_method: 'hash',
  segments: ['new_users', 'mobile']
});
```

---

#### `ab_variant_forced`
**Description**: Variant manually overridden (usually for testing)

**Trigger**: When developer/admin forces specific variant

**Properties**:
```typescript
{
  experiment_name: string;
  variant: string;
  forced_by: string;          // 'admin', 'developer', 'qa'
  reason?: string;
}
```

---

### Funnel Events (`funnel_*`)

#### `funnel_signup_started`
**Description**: User initiated registration flow

**Trigger**: When user lands on registration page or opens signup modal

**Properties**:
```typescript
{
  entry_point: string;        // 'header', 'modal', 'direct_link'
  referrer_campaign?: string; // UTM campaign if present
}
```

---

#### `funnel_signup_completed`
**Description**: User successfully completed registration

**Trigger**: After successful registration API response

**Properties**:
```typescript
{
  user_id: string;
  signup_method: string;      // 'email', 'google', 'microsoft'
  time_to_complete: number;   // Seconds from start to finish
  completed_steps: string[];  // Steps in funnel
}
```

---

#### `funnel_onboarding_started`
**Description**: User started onboarding flow

**Trigger**: First onboarding step shown

**Properties**:
```typescript
{
  user_type: string;          // 'individual', 'manager', 'admin'
  onboarding_version: string; // A/B test version if applicable
}
```

---

#### `funnel_onboarding_completed`
**Description**: User completed all onboarding steps

**Trigger**: Final onboarding step submitted

**Properties**:
```typescript
{
  time_to_complete: number;   // Total seconds
  completed_steps: string[];
  skipped_steps: string[];
}
```

---

#### `funnel_assessment_started`
**Description**: User started taking an assessment

**Trigger**: Assessment first question displayed

**Properties**:
```typescript
{
  assessment_id: string;
  assessment_type: string;    // 'big_five', 'mbti', 'custom'
  assessment_name: string;
}
```

---

#### `funnel_assessment_completed`
**Description**: User submitted assessment responses

**Trigger**: Assessment submitted successfully

**Properties**:
```typescript
{
  assessment_id: string;
  assessment_type: string;
  questions_count: number;
  time_to_complete: number;   // Seconds
  completed_questions: number;
}
```

---

### User Action Events (`user_*`)

#### `user_button_clicked`
**Description**: Any button/CTA click

**Trigger**: Button onClick handler

**Properties**:
```typescript
{
  element_id: string;         // Button ID or data attribute
  button_text: string;        // Visible text (for analytics)
  button_type: string;        // 'primary', 'secondary', 'text'
  page_section: string;       // 'header', 'footer', 'modal', etc.
}
```

**Example**:
```typescript
analytics.trackClick('header-signup-btn', {
  button_text: 'Get Started',
  button_type: 'primary',
  page_section: 'header'
});
```

---

#### `user_form_submitted`
**Description**: Form submission (any form)

**Trigger**: Form onSubmit handler

**Properties**:
```typescript
{
  form_id: string;
  form_name: string;
  form_type: string;          // 'login', 'register', 'contact', etc.
  fields_count: number;
  validation_errors?: number; // 0 if valid
}
```

---

#### `user_modal_opened`
**Description**: Modal/popup displayed

**Trigger**: Modal visibility state changes to true

**Properties**:
```typescript
{
  modal_id: string;
  modal_type: string;         // 'info', 'warning', 'form', 'media'
  trigger: string;            // 'button_click', 'auto', 'page_load'
}
```

---

#### `user_modal_closed`
**Description**: Modal/popup dismissed

**Trigger**: Modal close button clicked or overlay clicked

**Properties**:
```typescript
{
  modal_id: string;
  close_method: string;       // 'button', 'overlay', 'escape_key'
  time_open: number;          // Seconds modal was visible
}
```

---

#### `user_link_clicked`
**Description**: Navigation link clicked

**Trigger**: Link onClick handler

**Properties**:
```typescript
{
  link_url: string;
  link_text: string;
  link_type: string;          // 'internal', 'external', 'download'
  page_section: string;
}
```

---

#### `user_tab_changed`
**Description**: Tab switch in tabbed interface

**Trigger**: Tab selection change

**Properties**:
```typescript
{
  tab_container_id: string;
  previous_tab: string;
  new_tab: string;
}
```

---

### System Events (`system_*`)

#### `system_error_occurred`
**Description**: Application error

**Trigger**: Catch block or error boundary

**Properties**:
```typescript
{
  error_message: string;
  error_name: string;         // Error type
  error_stack?: string;       // Stack trace (dev only)
  component?: string;         // React component name
  user_action?: string;       // What user was doing
}
```

---

#### `system_api_call_failed`
**Description**: API request failed

**Trigger**: API error response

**Properties**:
```typescript
{
  endpoint: string;           // API path
  status_code: number;
  error_message: string;
  retry_attempt?: number;
}
```

---

#### `system_api_call_succeeded`
**Description**: API request succeeded (for monitoring)

**Trigger**: Successful API response

**Properties**:
```typescript
{
  endpoint: string;
  status_code: number;
  response_time: number;      // Milliseconds
  cache_hit: boolean;         // Was response cached?
}
```

---

### Engagement Events (`engagement_*`)

#### `engagement_content_viewed`
**Description**: User viewed specific content

**Trigger**: Content appears in viewport (IntersectionObserver)

**Properties**:
```typescript
{
  content_type: string;       // 'article', 'video', 'assessment_result'
  content_id: string;
  view_duration?: number;     // Seconds (tracked on view end)
}
```

---

#### `engagement_video_played`
**Description**: Video playback started

**Trigger**: Video play button clicked

**Properties**:
```typescript
{
  video_id: string;
  video_title: string;
  video_type: string;         // 'tutorial', 'demo', 'intro'
  autoplay: boolean;
}
```

---

#### `engagement_feature_discovered`
**Description**: User discovered new feature (e.g., via tooltip)

**Trigger**: Feature tooltip/guide displayed

**Properties**:
```typescript
{
  feature_name: string;
  discovery_method: string;   // 'tooltip', 'guide', 'exploration'
}
```

---

### Performance Events (`performance_*`)

#### `performance_page_load`
**Description**: Page load performance metrics

**Trigger**: Window load event

**Properties**:
```typescript
{
  page: string;
  load_time: number;          // Total load time (ms)
  dom_content_loaded: number; // DOM ready time (ms)
  first_contentful_paint?: number;
  resources_loaded: number;
}
```

---

#### `performance_api_latency`
**Description**: API response time tracking

**Trigger**: API response received

**Properties**:
```typescript
{
  endpoint: string;
  method: string;             // 'GET', 'POST', etc.
  duration: number;           // Milliseconds
  cache_hit: boolean;
}
```

---

## 🔧 How to Add New Events

### Step 1: Check Event Catalog

First, search this catalog to ensure the event doesn't already exist.

**❌ Don't create duplicate events!**

### Step 2: Follow Naming Convention

Use `category_action_object` pattern:

```typescript
// Example: Adding new event for newsletter signup
const EVENT_NEWSLETTER_SIGNUP = 'user_newsletter_subscribed';
//                       ^user  ^subscribed  ^newsletter
//                       category  action     object
```

### Step 3: Add to EVENT_CATALOG

Add to `src/services/analytics/tracker.ts`:

```typescript
export const EVENT_CATALOG = {
  // ... existing events

  // Your new event
  USER_NEWSLETTER_SUBSCRIBED: 'user_newsletter_subscribed',
} as const;
```

### Step 4: Document in This Catalog

Add event documentation following the template:

```markdown
#### `user_newsletter_subscribed`
**Description**: User subscribed to newsletter

**Trigger**: Newsletter form submitted

**Properties**:
\`\`\`typescript
{
  email: string;
  source: string;             // Where they signed up
  interests?: string[];       // Selected topics
}
\`\`\`
```

### Step 5: Track the Event

```typescript
import { useAnalytics } from '@/services/analytics/tracker';

function MyComponent() {
  const { track } = useAnalytics();

  const handleSubscribe = (email: string) => {
    // ... subscribe logic

    track(EVENT_CATALOG.USER_NEWSLETTER_SUBSCRIBED, {
      email,
      source: 'footer_form',
      interests: ['product', 'tips']
    });
  };

  return <button onClick={handleSubscribe}>Subscribe</button>;
}
```

---

## ✅ Best Practices

### DO ✅

- ✅ Use past tense for actions: `clicked`, `submitted`, `viewed`
- ✅ Use category prefixes: `user_`, `funnel_`, `system_`
- ✅ Be specific: `user_primary_cta_clicked` instead of `user_clicked`
- ✅ Add descriptive properties for context
- ✅ Track both success and failure events
- ✅ Include timing information for funnels
- ✅ Document all events in this catalog

### DON'T ❌

- ❌ Use camelCase event names: `buttonClicked`
- ❌ Use generic names: `click`, `action`, `event`
- ❌ Mix conventions: `user_buttonClick` (inconsistent)
- ❌ Skip category prefixes: `variant_assigned`
- ❌ Use present tense: `click` instead of `clicked`
- ❌ Create events without documenting them
- ❌ Send PII in properties without hashing

---

## 🔍 Migration Guide

### Legacy Events

Old event names are supported for backward compatibility but will be transformed:

| Legacy Name | Standard Name | Category |
|-------------|---------------|----------|
| `variant_assigned` | `ab_variant_assigned` | A/B Testing |
| `conversion` | `funnel_signup_converted` | Funnel |
| `click` | `user_button_clicked` | User Action |
| `view` | `engagement_content_viewed` | Engagement |
| `quick_assessment_completed` | `funnel_assessment_completed` | Funnel |
| `setup_step_completed` | `funnel_onboarding_step_completed` | Funnel |

**To migrate legacy code**:

```typescript
// ❌ OLD
await abTestingService.trackEvent('variant_assigned', testName, {
  variant: assignment.variant
});

// ✅ NEW
import { useAnalytics } from '@/services/analytics/tracker';

const { trackABTest } = useAnalytics();
trackABTest(testName, assignment.variant, 'assigned', {
  segments: assignment.segments
});
```

---

## 📊 Event Examples by Use Case

### A/B Testing

```typescript
// Track variant assignment
trackABTest('headline_v2', 'treatment_a', 'assigned', {
  user_segment: 'new_users'
});

// Track conversion in variant
trackABTest('headline_v2', 'treatment_a', 'conversion', {
  conversion_value: 99.00
});
```

### Funnel Tracking

```typescript
// Funnel step started
trackFunnel('signup', 'started', {
  entry_point: 'header_cta'
});

// Funnel step completed
trackFunnel('signup', 'completed', {
  time_to_complete: 45,
  signup_method: 'email'
});
```

### User Interactions

```typescript
// Button click
track(EVENT_CATALOG.USER_BUTTON_CLICKED, {
  element_id: 'header-cta',
  button_text: 'Get Started Free',
  button_type: 'primary',
  page_section: 'header'
});

// Form submission
track(EVENT_CATALOG.USER_FORM_SUBMITTED, {
  form_id: 'login-form',
  form_type: 'login',
  fields_count: 2,
  validation_errors: 0
});
```

### Error Tracking

```typescript
try {
  await riskyOperation();
} catch (error) {
  trackError(error, {
    component: 'Dashboard',
    user_action: 'loading_data'
  });
}
```

---

## 🛠️ Developer Tools

### Event Validation

The unified tracker validates all events before sending:

```typescript
// ✅ Valid event
tracker.track('user_button_clicked', {
  element_id: 'submit-btn'
});

// ❌ Invalid event (caught in dev mode)
tracker.track('', {}); // Error: event_name cannot be empty
tracker.track('invalid event', {}); // Error: must use snake_case
```

### Development Mode Logging

In development, all events are logged to console:

```
📊 [Analytics] Tracked: user_button_clicked {element_id: 'submit-btn'}
✅ [Analytics] Sent batch of 10 events
```

### Debug Events

To see what events are being tracked, open browser console and filter by `[Analytics]`.

---

## 📈 Analytics Queries

### Example: Track Conversion Rate

```sql
SELECT
  properties->>'experiment_name' as experiment,
  properties->>'variant' as variant,
  COUNT(*) FILTER (WHERE event_name = 'funnel_signup_completed') as conversions,
  COUNT(*) FILTER (WHERE event_name = 'ab_variant_assigned') as total_users,
  ROUND(
    COUNT(*) FILTER (WHERE event_name = 'funnel_signup_completed')::numeric /
    NULLIF(COUNT(*) FILTER (WHERE event_name = 'ab_variant_assigned'), 0) * 100,
    2
  ) as conversion_rate
FROM analytics_events
WHERE event_name IN ('ab_variant_assigned', 'funnel_signup_completed')
GROUP BY experiment, variant;
```

### Example: Funnel Drop-off Analysis

```sql
WITH funnel_steps AS (
  SELECT
    session_id,
    event_name,
    timestamp
  FROM analytics_events
  WHERE event_name LIKE 'funnel_%'
    AND timestamp >= NOW() - INTERVAL '7 days'
)
SELECT
  event_name,
  COUNT(DISTINCT session_id) as users,
  LAG(COUNT(DISTINCT session_id)) OVER (ORDER BY timestamp) - COUNT(DISTINCT session_id) as dropoff
FROM funnel_steps
GROUP BY event_name, timestamp
ORDER BY timestamp;
```

---

## 📞 Support

### Questions?
- **Analytics Team**: #analytics
- **Frontend Team**: #frontend
- **Documentation**: `/docs/analytics/`

### Propose New Event
1. Check this catalog for duplicates
2. Follow naming convention
3. Add to EVENT_CATALOG
4. Document in this file
5. Submit PR for review

---

**Catalog Version**: 1.0.0
**Last Updated**: 2026-01-21
**Maintained By**: Frontend Team
**Review Frequency**: Quarterly

**Next Review**: 2026-04-21
