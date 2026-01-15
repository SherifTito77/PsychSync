# Product Operations Team Training Guide

## Welcome to Product Operations at PsychSync

This guide will teach you how to use the product operations systems we've built to:
- Run A/B tests to optimize conversion and user experience
- Identify and reduce churn with predictive analytics
- Manage feature requests with data-driven prioritization
- Track user activation metrics

---

## Table of Contents

1. [A/B Testing](#1-ab-testing)
2. [Churn Prediction](#2-churn-prediction)
3. [Feature Request Management](#3-feature-request-management)
4. [User Activation Tracking](#4-user-activation-tracking)
5. [Best Practices](#5-best-practices)

---

## 1. A/B Testing

### What is A/B Testing?

A/B testing (or split testing) compares two versions of something to see which performs better. We show different variants to different users and measure which one leads to better outcomes.

### When to Use A/B Testing

✅ **Good for A/B testing:**
- Testing different CTA button colors or text
- Comparing signup form lengths
- Testing onboarding flow variations
- Pricing page layout changes
- Email subject lines
- Feature discoverability changes

❌ **Not suitable for A/B testing:**
- Major product changes (affects too many variables)
- Very small changes (not worth the engineering effort)
- Changes to backend performance (hard to measure user impact)
- UI bugs or accessibility fixes (just fix them!)

### How to Run an A/B Test

#### Step 1: Define Your Hypothesis

Start with a clear, testable hypothesis:

> **Example**: "If we change the CTA button from blue to green, click-through rate will increase by 5% because green signals 'go' and action."

Use this format:
- **If** [change we're making]
- **Then** [expected outcome]
- **Because** [rationale]

#### Step 2: Determine Key Metrics

What will you measure?

**Primary Metric**: The main success indicator
- Example: Sign-up conversion rate, CTR, time to first assessment

**Secondary Metrics**: Additional context
- Example: Bounce rate, session length, support tickets

**Guardrail Metrics**: Things to watch for negative impact
- Example: Page load time, error rate, unsubscribe rate

#### Step 3: Create the Experiment

1. Navigate to **Product Operations Dashboard** → **A/B Experiments**
2. Click **Create New Experiment**
3. Fill in:
   - **Name**: Unique identifier (e.g., `cta_green_v1`)
   - **Description**: What you're testing and why
   - **Hypothesis**: Your hypothesis statement
   - **Variants**: Define control and test variants
   - **Traffic Split**: Percentage allocation (e.g., 50/50 or 70/30)
   - **Duration**: How long to run the test

4. Click **Create**

#### Step 4: Implement the Variants

**Backend Implementation:**
```python
# In your endpoint or service
from app.services.ab_testing_service import assign_variant

# Get user's variant
variant = await assign_variant(
    user_id=current_user.id,
    experiment_name="cta_green_v1"
)

# Show different content based on variant
if variant == "control":
    button_color = "blue"
else:
    button_color = "green"
```

**Frontend Implementation:**
```typescript
import { useExperiment } from '@/hooks/useExperiment';

function SignupPage() {
  const { variant } = useExperiment('cta_green_v1');

  return (
    <button
      className={variant === 'control' ? 'bg-blue-600' : 'bg-green-600'}
    >
      Sign Up Now
    </button>
  );
}
```

#### Step 5: Launch and Monitor

1. Start the experiment in the dashboard
2. Monitor daily for:
   - **Equal traffic distribution**: Are variants getting equal users?
   - **No errors**: Are there any technical issues?
   - **Guardrail metrics**: Any negative side effects?

3. Run for at least **2 full weeks** or until you have **statistical significance**

#### Step 6: Analyze Results

**Statistical Significance**:
- Look for p-value < 0.05 (95% confidence)
- Check confidence intervals don't overlap
- Ensure sample size is large enough

**Practical Significance**:
- Even if statistically significant, is the improvement meaningful?
- A 0.1% improvement might not be worth implementing

**Decision Framework**:

| Result | Action |
|--------|--------|
| Significant positive uplift | Roll out winner to 100% |
| No significant difference | Keep control (simpler is better) |
| Significant negative uplift | Roll back to control immediately |

#### Step 7: Document and Share

Create a brief summary:
- What did you test?
- What was the result?
- What did you learn?
- What's next?

Share with the team in Slack/email.

---

## 2. Churn Prediction

### What is Churn Prediction?

Churn prediction uses behavioral signals to identify users likely to leave (cancel, downgrade, become inactive). This allows us to proactively intervene.

### Churn Risk Levels

We calculate a churn risk score (0-100) for each user:

| Risk Level | Score Range | Action |
|------------|-------------|--------|
| **Safe** | 0-19 | No action needed |
| **Low** | 20-39 | Monitor |
| **Medium** | 40-59 | Automated nurturing |
| **High** | 60-79 | Customer success outreach |
| **Critical** | 80-100 | Immediate intervention |

### Behavioral Signals

We track 8 signals to calculate churn risk:

1. **Usage Decline** (25% weight)
   - Comparing assessments taken in last 30 days vs previous 30 days
   - >50% decline is concerning

2. **Login Frequency** (20% weight)
   - Fewer logins than before
   - >14 days since last login is concerning

3. **Competitor Research** (15% weight)
   - Mentioned competitors in support tickets
   - Viewed competitor comparison pages
   - Exported data (preparing to leave)

4. **Failed Conversion** (12% weight)
   - Started checkout but didn't complete
   - Clicked upgrade button multiple times but didn't subscribe

5. **Assessment Limit** (10% weight)
   - Hit monthly assessment limit
   - Not viewing pricing page (unaware of value)

6. **Support Sentiment** (8% weight)
   - Multiple negative sentiment tickets
   - Increased support frequency

7. **Adoption Stagnation** (5% weight)
   - Only using basic features
   - Haven't tried advanced features in 60+ days

8. **Survey Sentiment** (5% weight)
   - Low NPS score (≤6)
   - Mentioned cancellation or competitors

### How to Use Churn Predictions

#### Daily Churn Review

1. Navigate to **Product Operations Dashboard**
2. Check **High-Risk Users** list
3. For each critical/high-risk user:
   - Review their risk factors
   - Check recent activity
   - Determine appropriate intervention

#### Intervention Strategies

**Critical Risk (80-100)**:
- ✉️ Personal email from customer success
- 📞 Schedule call within 24 hours
- 🎁 Offer discount or incentive
- 👤 Assign dedicated account manager

**High Risk (60-79)**:
- ✉️ Personalized email series
- 📚 Offer training/resources
- 🔍 Check for unresolved support issues
- 📞 Schedule call within 72 hours

**Medium Risk (40-59)**:
- 📧 Automated nurturing campaign
- 🎯 Feature highlight newsletter
- 📅 Invite to webinar/training
- 👀 Continue monitoring

#### Monitoring Churn Trends

Run weekly:
```bash
python -m app.services.churnScheduler --mode summary
```

Watch for:
- Increasing % of high-risk users
- New risk factors appearing
- Seasonal patterns

---

## 3. Feature Request Management

### RICE Scoring Model

We use the RICE model to prioritize features:

**RICE Score = (Reach × Impact × Confidence) ÷ Effort**

| Component | Scale | Description |
|-----------|-------|-------------|
| **Reach** | 3 = >1000 users, 2 = 500-1000, 1 = <500, 0 = <100 | How many users will benefit? |
| **Impact** | 3 = Massive, 2 = High, 1 = Medium, 0.5 = Low, 0.25 = Minimal | How much will it benefit them? |
| **Confidence** | 1.0 = High, 0.8 = Medium, 0.5 = Low | How sure are you? |
| **Effort** | In months/person-months | How much work? |

### How to Score a Feature Request

**Example: Dark Mode Support**

1. **Reach**: 3 (would benefit >1000 users)
2. **Impact**: 1 (medium improvement - reduces eye strain but doesn't add new functionality)
3. **Confidence**: 0.8 (confident users want it, but unsure of actual usage)
4. **Effort**: 3 (1-2 weeks = ~0.5 person-months)

```
RICE = (3 × 1 × 0.8) ÷ 3 = 0.8
```

This is a **high priority** feature!

### Feature Request Workflow

```
[Backlog] → [Planned] → [In Development] → [Released]
    ↓
[Declined]
```

**Status Definitions**:
- **Backlog**: Requested, not yet prioritized
- **Planned**: Prioritized for upcoming release
- **In Development**: Currently being worked on
- **Released**: Shipped to users
- **Declined**: Not going to implement (document reason)

### Managing Feature Requests

#### Creating Requests

1. Navigate to **Product Operations Dashboard** → **Feature Requests**
2. Click **New Request**
3. Fill in:
   - Title and description
   - Theme (UX, Performance, etc.)
   - Type (New feature, Enhancement, Bug fix)
   - Source (Customer, Internal, Data-driven)

#### Scoring Requests

1. Click on a request
2. Edit RICE scores
3. Consider:
   - **Reach**: Check analytics for user counts
   - **Impact**: Talk to customer success team
   - **Confidence**: Do you have data or is it a guess?
   - **Effort**: Consult engineering team

4. Save - requests auto-sort by RICE score

#### Voting System

Users can vote on requests (1 vote per request). Use votes as:
- **Popularity signal**: Many votes = many people want it
- **Not prioritization**: A feature with 100 votes and RICE 0.1 loses to a feature with 10 votes and RICE 2.0

---

## 4. User Activation Tracking

### What is User Activation?

Activation is the "aha moment" when a user realizes value. For PsychSync, **activation = viewing first assessment results**.

### Activation Funnel

We track users through these steps:

```
1. Sign up
2. Complete first assessment
3. View first results
4. [Activated]
```

### Key Metrics

- **Activation Rate**: % of signups who activate
- **Time to Activate (TTA)**: Median/average time from signup to activation
- **Funnel Drop-off**: Where do users abandon?

### Target Activation Rates

| Segment | Target | Current | Gap |
|---------|--------|---------|-----|
| Individual Free | 60% | TBD | TBD |
| Individual Premium | 75% | TBD | TBD |
| Team | 70% | TBD | TBD |
| Enterprise | 85% | TBD | TBD |

### Improving Activation

**If funnel drop-off is at step 1 (Sign up → First assessment):**
- Improve onboarding flow
- Add assessment tutorial
- Send reminder emails
- Make first assessment prominent

**If funnel drop-off is at step 2 (First assessment → View results):**
- Speed up assessment processing
- Send notification when ready
- Improve results presentation
- Add social proof ("9,000 people got this result!")

---

## 5. Best Practices

### A/B Testing Do's and Don'ts

✅ **DO:**
- Run tests for at least 2 weeks
- Wait for statistical significance
- Test one variable at a time
- Document hypotheses and results
- Consider practical significance
- Monitor guardrail metrics

❌ **DON'T:**
- Stop tests early when you see a trend (peeking)
- Test too many variants (requires huge sample)
- Ignore statistical significance
- Run tests during holidays (atypical behavior)
- Make decisions based on tiny sample sizes

### Churn Prediction Best Practices

✅ **DO:**
- Act on high-risk predictions quickly
- Personalize interventions
- Document what works
- Monitor for false positives
- Respect user privacy

❌ **DON'T:**
- Spam users with interventions
- Ignore medium-risk users (they become high-risk!)
- Override predictions without data
- Share individual scores publicly
- Use scores for performance evaluation

### Feature Request Priorization

✅ **DO:**
- Score all requests consistently
- Update scores as you learn more
- Consider quick wins (low effort, decent impact)
- Say no politely (decline with reason)
- Review quarterly

❌ **DON'T:**
- Prioritize by votes alone
- Forget to score new requests
- Ignore effort estimates
- Keep unclear requests (ask for clarification)
- Say yes to everything (you can't build it all)

### Data-Driven Decision Making

**Before making any product change:**

1. **Check existing data**:
   - Look at analytics
   - Review past experiments
   - Check similar features

2. **Form a hypothesis**:
   - What do you think will happen?
   - Why do you think that?

3. **Design an experiment**:
   - What will you measure?
   - How will you measure it?
   - What sample size do you need?

4. **Run the experiment**:
   - Don't stop early
   - Monitor for issues
   - Document everything

5. **Make a decision**:
   - Let data guide you
   - Consider practical impact
   - Document the outcome

---

## Quick Reference

### Common Commands

```bash
# Run churn scoring
python -m app.services.churnScheduler --mode summary

# Seed test data
python -m app.scripts.seed_experiments
python -m app.scripts.seed_feature_requests_only

# Check database
psql -U psychsync_user -d psychsync_db -c "SELECT COUNT(*) FROM ab_experiments;"
```

### Dashboard URLs

- **Product Operations Dashboard**: `/admin/product-ops`
- **A/B Experiment Results**: `/admin/product-ops?tab=results`
- **Feature Requests**: `/admin/product-ops?tab=feature-requests`

### Key People

- **Product Manager**: Approves experiments, prioritizes features
- **Data Analyst**: Reviews experiment results, monitors churn
- **Customer Success**: Acts on churn predictions
- **Engineering Team**: Implements experiments and features

---

## Getting Help

**Questions?**
- Check this guide first
- Search Slack #product-ops
- DM the product ops team

**Found a bug?**
- Report in GitHub Issues
- Tag @product-ops

**Want to suggest an improvement?**
- Submit a feature request in the dashboard
- We use RICE scoring too!

---

**Remember**: The goal of product operations is to make **data-driven decisions** that improve user experience and business outcomes. Trust the data, but don't forget to talk to users!

Last updated: 2025-01-12
