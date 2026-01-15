# Feature Sunset Process
# PsychSync Product Lifecycle Management

## Overview

This document defines the process for deprecating and removing features from PsychSync. A structured sunset process minimizes user frustration while maintaining product quality.

---

## Sunset Triggers

A feature should be considered for sunset when ANY of the following are met:

### 1. Usage Metrics
- **< 5% of active users** have used the feature in the past 90 days
- **< 2% of total sessions** include the feature
- **Declining usage** for 3 consecutive months with no upward trend
- **Feature redundancy**: Newer feature fulfills the same use case 2x better

### 2. Technical Debt
- **Maintenance burden**: Feature costs > 2x value delivered
- **Security vulnerabilities** that cannot be reasonably patched
- **Dependencies deprecated** with no migration path
- **Code complexity**: Feature blocks other improvements

### 3. Strategic Misalignment
- **Doesn't support core value proposition**
- **Appeals to < 1% of user base**
- **Conflicts with product direction**
- **Better alternatives exist in market**

---

## Sunset Process Flow

```
1. IDENTIFY
   └─ Data review → Product decision → Sunset candidate list

2. VALIDATE
   └─ User research → Impact analysis → Stakeholder sign-off

3. ANNOUNCE
   └─ User communication → Timeline published → FAQ created

4. MIGRATE
   └─ Export tools → Migration guides → Alternative features promoted

5. DEPRECATE
   └─ Feature warnings → "Legacy" badge → No new users

6. REMOVE
   └─ Code deleted → Data archived → Documentation updated
```

---

## Phase 1: Identification (Weeks 1-2)

### Data Collection Required

```typescript
// Sunset evaluation metrics:
interface SunsetMetrics {
  featureName: string;
  activeUsers: number;           // MAU using feature
  totalUsers: number;            // Total user base
  usagePercentage: number;        // activeUsers / totalUsers
  trend: 'increasing' | 'stable' | 'decreasing';
  maintenanceCost: number;        // Hours/month
  supportTickets: number;         // Tickets/month
  npsImpact: number;             // NPS contribution (-10 to +10)
  lastMajorUpdate: string;        // Date
 替代方案: string;               // Alternative feature
}
```

### Decision Matrix

| Metric | Green Light | Yellow Light | Red Light |
|--------|-------------|--------------|-----------|
| Usage | > 10% | 5-10% | < 5% |
| Trend | Increasing | Stable | Decreasing |
| Maintenance | Low | Medium | High |
| Strategic Fit | Core | Support | Misaligned |
| **Decision** | **Keep** | **Monitor** | **Sunset** |

---

## Phase 2: Validation (Weeks 3-4)

### Stakeholder Approval Required

Before proceeding, get sign-off from:

- **Product**: Product Manager
- **Engineering**: Tech Lead
- **Support**: Customer Support Lead
- **Sales**: Enterprise Sales (if affects customers)
- **Legal**: Legal Counsel (if contract obligations)

### User Research Questions

Ask affected users:

1. "How would you be impacted if [feature] was removed?"
2. "What alternatives would you use?"
3. "What would make this transition acceptable?"
4. "How much notice would you need?"

**Sample size**: Interview at least 10 affected users or 20% of user base, whichever is smaller.

### Impact Assessment

```typescript
interface SunsetImpact {
  usersAffected: number;
  usersAtRiskOfChurn: number;
  migrationOptions: string[];
  requiredNoticePeriod: number;  // days
  estimatedSupportVolume: number;
  migrationCost: number;
  savingsAfterSunset: number;
}
```

---

## Phase 3: Announcement (Weeks 5-6)

### Communication Timeline

#### **30 Days Before Sunset**
```typescript
// In-app notification
{
  type: 'warning',
  title: 'Important: [Feature Name] is being deprecated',
  message: 'This feature will be removed on [Date]. Here\'s what you need to know.',
  actions: ['Learn More', 'See Alternatives']
}
```

#### **Email to Affected Users**
```
Subject: Important Changes to [Feature Name]

Hi [User Name],

We're writing to let you know that [Feature Name] will be deprecated on [Date].

We understand this feature may be important to you, so we wanted to give you plenty of time to adjust.

**What's Happening:**
[Clear explanation of why]

**Your Options:**
1. [Alternative Feature 1] - [Brief description]
2. [Alternative Feature 2] - [Brief description]
3. Export your data before [Date] - [Link to export]

**Why This Change:**
[Reason - be honest]

**Need Help?**
- Reply to this email with questions
- Schedule a call with our team: [Calendly link]
- Read our FAQ: [Help center link]

We're committed to making this transition as smooth as possible.

Best,
The PsychSync Team
```

#### **In-App Banner (90 days before sunset)**
```tsx
<DeprecationNotice
  feature="Old Assessment Viewer"
  sunsetDate="2025-06-01"
  alternative="New Analytics Dashboard"
  migrationGuide="/help/migrate-from-old-viewer"
/>
```

---

## Phase 4: Migration Period (Varies)

### Migration Support Options

#### **Option 1: Automatic Migration**
```typescript
// For features with direct equivalent
if (user.usesOldFeature) {
  showBanner: {
    message: "We've upgraded your experience! Your data is now in [New Feature].",
    action: "Take a Tour",
    dismissible: false
  }
}
```

#### **Option 2: Assisted Migration**
```typescript
// For features requiring user action
<MigrationWizard
  oldFeature="Old Assessment Viewer"
  newFeature="Analytics Dashboard"
  steps={[
    "Review your old reports",
    "Export data (optional)",
    "Try new dashboard",
    "Confirm migration"
  ]}
/>
```

#### **Option 3: Manual Export**
```typescript
// For features without equivalent
<DataExportTool
  feature="Old Feature"
  exportFormats={['csv', 'json', 'pdf']}
  retentionPeriod={90}  // days after sunset
/>
```

### Success Metrics

- **> 90%** of affected users migrated
- **< 5%** increase in support tickets
- **< 2%** churn directly attributed to sunset
- **> 80%** positive sentiment on migration feedback

---

## Phase 5: Deprecation (30-90 Days)

### Feature States

#### **State 1: Warnings Only (90-60 days before)**
```tsx
<FeatureWarning>
  ⚠️ This feature will be deprecated on [Date].
  <Link to="/help/feature-sunset">Learn more</Link>
</FeatureWarning>
```

#### **State 2: "Legacy" Badge (60-30 days before)**
```tsx
<Badge variant="warning" className="ml-2">
  Legacy - Being replaced on [Date]
</Badge>

<Button disabled>
  This feature is being deprecated
  <Tooltip>See [New Feature] instead</Tooltip>
</Button>
```

#### **State 3: New Users Blocked (30 days before)**
```typescript
// Only existing users can access
{user.hasUsedFeatureBefore && <OldFeature />}

// New users see:
<FeatureGate>
  <NewFeature />
  <UpgradePrompt message="This feature is only available to legacy users" />
</FeatureGate>
```

---

## Phase 6: Removal (Day 0)

### Removal Checklist

```typescript
interface SunsetChecklist {
  // Technical
  codeRemoved: boolean;
  databaseMigrations: string[];
  apiEndpointsDeleted: string[];
  dependenciesRemoved: string[];

  // User Experience
  redirectRoutes: Map<string, string>;  // old path → new path
  alternativeFeatures: Map<string, string>;
  helpCenterArticles: string[];

  // Data
  userDataArchived: boolean;
  dataRetentionPeriod: number;  // days
  exportToolAvailable: boolean;

  // Communication
  emailSent: boolean;
  blogPostPublished: boolean;
  releaseNotesUpdated: boolean;

  // Support
  supportTeamNotified: boolean;
  faqPublished: boolean;
  migrationSupportAvailable: boolean;
}
```

### User Experience on Removal Day

```typescript
// Old route redirects to new feature
app.get('/old-feature', (req, res) => {
  res.redirect('/new-feature?migrated=true');
});

// With helpful message
<MigrationNotice>
  The Old Feature has been retired. Your data is available in the New Feature.
  <Button onClick={() => navigate('/new-feature')}>Take Me There</Button>
</MigrationNotice>
```

---

## Real-World Example: Sunset Process

### Feature to Sunset: "Basic Assessment Viewer"

#### **Phase 1: Identification** (Week 1)
- **Usage**: 3.2% of users (down from 8% last year)
- **Maintenance**: 12 hours/month
- **Strategic fit**: Replaced by "Analytics Dashboard"
- **Decision**: Sunset (Red Light)

#### **Phase 2: Validation** (Weeks 2-3)
- **Users affected**: 1,245 users
- **Research findings**: 80% already using Analytics Dashboard
- **Impact**: Low - most users migrated organically
- **Sign-off**: All stakeholders approved

#### **Phase 3: Announcement** (Week 4)
```typescript
// Email sent to 1,245 affected users
// In-app banner shown to all users
// Blog post: "Upgrading Your Assessment Viewing Experience"
// FAQ created with 8 common questions
```

#### **Phase 4: Migration** (Weeks 5-8)
```typescript
// Auto-migration script
// Export tool available for custom reports
// 1,156 users migrated (93%)
// 89 users needed manual support
```

#### **Phase 5: Deprecation** (Weeks 9-12)
```typescript
// Week 9-10: Warning banners
// Week 11-12: "Legacy" badge, no new users
```

#### **Phase 6: Removal** (Week 13)
```typescript
// Code deleted
// Database archived (retained 1 year)
// Redirects in place
// Support team briefed
```

#### **Results**
- ✅ 93% migration success
- ✅ 2 users churned (< 1%)
- ✅ Support tickets increased 15% (within acceptable range)
- ✅ Saved 12 engineering hours/month
- ✅ User sentiment: Neutral (slightly positive due to improved UX)

---

## Sunset Timeline Templates

### **Quick Sunset (3 months)** - Low usage, low value
```
Month 1: Announcement + Migration
Month 2: Deprecation warnings
Month 3: Removal
```

### **Standard Sunset (6 months)** - Moderate usage
```
Month 1: Announcement
Month 2-3: Migration period
Month 4-5: Deprecation warnings
Month 6: Removal
```

### **Extended Sunset (12 months)** - High usage, contractual
```
Quarter 1: Announcement + Migration
Quarter 2-3: Support both features
Quarter 3: Deprecation warnings
Quarter 4: Removal
```

---

## Sunset Decision Framework

### Go/No-Go Criteria

**Approve Sunset If:**
- ✅ Alternative feature available or planned
- ✅ Usage < 5% AND declining
- ✅ Migration path exists for 80%+ of use cases
- ✅ Legal review complete
- ✅ Support team capacity available

**Delay Sunset If:**
- ⏸️ Contractual obligations to enterprise customers
- ⏸️ No migration path for > 20% of use cases
- ⏸️ Seasonal usage peak coming up
- ⏸️ Legal or compliance concerns

**Cancel Sunset If:**
- ❌ Usage suddenly increases (> 50% MoM)
- ❌ Major customer complaint escalates
- ❌ Security vulnerability discovered in replacement
- ❌ Alternative feature not ready

---

## Communication Templates

### Email Templates

#### **Initial Announcement (90 days before)**
```
Subject: [Feature] Updates Coming

We're evolving [Feature] to better serve your needs.

What's happening: [Explain]
When: [Timeline]
Why: [Reason]
What you need to do: [Action items]

Questions? Reply to this email.
```

#### **Final Notice (30 days before)**
```
Subject: Final Reminder: [Feature] Retirement on [Date]

This is your final reminder that [Feature] will be removed on [Date].

[Deadline details]

Your data: [What happens to your data]
Questions: [Support link]
```

### In-App Messaging Templates

```tsx
// Warning Banner (90 days)
<Alert severity="warning" className="mb-4">
  <AlertTitle>[Feature] is being deprecated on {sunsetDate}</AlertTitle>
  <p>
    We've upgraded to <Link to="/new-feature">[New Feature]</Link> with improved capabilities.
    <Button onClick={() => setShowMigrationModal(true)}>
      Learn how to migrate
    </Button>
  </p>
</Alert>

// Legacy Badge (60 days)
<Badge variant="warning" className="ml-2">
  Deprecated • Removed {sunsetDate}
</Badge>

// Blocked (Day of removal)
<SunsetNotice>
  <Icon name="info" />
  <p>
    <strong>{featureName}</strong> has been retired.
    <Link to={alternativePath}>Use {alternativeName} instead</Link>
  </p>
</SunsetNotice>
```

---

## Metrics & Success Criteria

### Track These Metrics Throughout Sunset Process

```typescript
interface SunsetMetrics {
  // Pre-sunset
  baselineUsage: number;
  baselineUsers: number;
  baselineRevenue: number;

  // During process
  migrationRate: number;
  supportTicketIncrease: number;
  userSentiment: number;  // NPS
  churnAttribution: number;

  // Post-sunset
  actualSavings: number;
  userRetention: number;
  supportTicketsReturned: number;
  feedbackScore: number;
}
```

### Success Criteria

| Metric | Target | Stretch Goal |
|--------|--------|-------------|
| Migration Rate | > 80% | > 90% |
| Churn Attributed to Sunset | < 5% | < 2% |
| Support Ticket Increase | < 20% | < 10% |
| User Sentiment (NPS) | > 0 | > 20 |
| Engineering Hours Saved | As projected | > projected |

---

## Post-Sunset Review

### Conduct at 30, 90, 180 days post-removal

```typescript
interface PostSunsetReview {
  date: string;
  feature: string;

  // Metrics
  usersMigrated: number;
  usersLost: number;
  supportVolume: number;
  sentimentScore: number;

  // Learnings
  whatWentWell: string[];
  whatCouldBeImproved: string[];
  unexpectedOutcomes: string[];

  // Recommendations
  wouldSunsetAgain: boolean;
  timelineAppropriate: boolean;
  communicationEffective: boolean;
}
```

### Questions to Answer

1. Did we maintain user trust?
2. Was the timeline adequate?
3. What feedback surprised us?
4. How can we improve the process?
5. Any legal or compliance issues?

---

## Emergency Sunset Process

### When You Must Sunset Immediately

**Triggers:**
- Critical security vulnerability
- Legal/regulatory violation
- Third-party dependency shutdown
- Data breach in feature

**Process:**
```
0-24 hours: Feature disabled, emergency announcement
24-48 hours: Hotfix or workaround released
48-72 hours: Permanent fix or sunset decision
```

**Emergency Communication:**
```typescript
<EmergencyNotice severity="critical">
  <AlertTitle>[Feature] Temporarily Unavailable</AlertTitle>
  <p>
    We've discovered a security issue affecting [Feature].
    The feature has been temporarily disabled while we address this.
    We apologize for the inconvenience.
  </p>
  <p>
    <strong>Timeline for restoration:</strong> [Expected date]
    <strong>Questions?</strong> <Link to="/contact">Contact Support</Link>
  </p>
</EmergencyNotice>
```

---

## Documentation Updates

### Required Documentation Changes

1. **User Documentation**
   - Remove feature from user guides
   - Add migration guides
   - Update feature comparison tables
   - Archive old docs (don't delete)

2. **API Documentation**
   - Deprecate endpoints (return 410 Gone)
   - Document sunset timeline
   - Provide migration endpoints
   - Update changelog

3. **Internal Documentation**
   - Update architecture diagrams
   - Archive feature specs
   - Document sunset process
   - Create runbook for future sunsets

---

## Sunset Decision Log

### Track All Sunset Decisions

```typescript
interface SunsetDecision {
  id: string;
  featureName: string;
  proposedDate: string;
  decisionMaker: string;
  rationale: string;
  data: SunsetMetrics;
  stakeholderApprovals: string[];
  userResearchFindings: string;
  timeline: string;
  outcome: 'approved' | 'rejected' | 'deferred';
  actualSunsetDate?: string;
  postSunsetReview?: PostSunsetReview;
}
```

---

## Summary

A well-executed feature sunset:

✅ **Reduces technical debt** - Removes unused code
✅ **Improves focus** - Team can focus on core features
✅ **Maintains trust** - Transparent communication
✅ **Minimizes churn** - Proper migration support
✅ **Saves resources** - Engineering hours redirected
✅ **Improves UX** - Removes confusion from redundant features

**Poorly executed sunset:**

❌ **Breaks trust** - Surprise removal
❌ **Causes churn** - No migration support
❌ **Creates backlash** - Poor communication
❌ **Wastes resources** - Support nightmare
❌ **Loses customers** - Enterprise escalations

**The key is: Communication, Migration, and Empathy.**
