# Onboarding Experiments Framework
# PsychSync User Onboarding Optimization Guide

## Overview

This document provides a comprehensive framework for designing, implementing, and analyzing onboarding experiments. The goal is to optimize the user's first experience to maximize activation, retention, and long-term engagement.

---

## Table of Contents

1. [Onboarding Experiment Strategy](#onboarding-experiment-strategy)
2. [Current Baseline Metrics](#current-baseline-metrics)
3. [Experiment Priority Matrix](#experiment-priority-matrix)
4. [Ready-to-Run Experiments](#ready-to-run-experiments)
5. [Experiment Implementation Guide](#experiment-implementation-guide)
6. [Analysis & Success Criteria](#analysis--success-criteria)
7. [Experiment Calendar](#experiment-calendar)

---

## Onboarding Experiment Strategy

### Hypothesis Framework

All onboarding experiments follow this structure:

```
IF we [change made to onboarding]
THEN users will [expected behavior change]
BECAUSE [psychological or UX rationale]
```

### Key Metrics to Optimize

**Primary Metrics (North Star):**
- **Activation Rate**: % of signups who complete first assessment within 24 hours
- **Time to First Value (TTFV)**: Minutes from signup to viewing first results

**Secondary Metrics:**
- **Onboarding Completion Rate**: % who finish all onboarding steps
- **Day 7 Retention**: % who return within 7 days
- **First Assessment Completion Rate**: % who start and finish first assessment
- **Team Invitation Rate**: % who invite at least one team member

**Guardrail Metrics (must not degrade):**
- **Day 1 Retention**: % who return next day (baseline: 45%)
- **Assessment Accuracy**: % passing attention checks (baseline: 92%)
- **User Satisfaction**: Post-onboarding NPS (baseline: 38)

---

## Current Baseline Metrics

### Funnel Performance (December 2024)

```
Signups:                          10,000          (100%)
├─ Email verified:                8,500           (85%)
├─ Onboarding questions started:  7,200           (72%)
├─ Onboarding questions completed:6,500           (65%)
├─ First assessment started:      5,500           (55%)
├─ First assessment completed:    4,200           (42%) ← ACTIVATION
├─ Results viewed:                4,000           (40%)
└─ Team invite sent:              1,200           (12%)

Time to First Value (TTFV):        18.5 minutes
Day 7 Retention:                  28%
Day 30 Retention:                 15%
```

### Drop-off Analysis

**Highest Drop-off Points:**
1. **Signup → Email verification** (15% drop-off)
2. **Onboarding questions → Assessment start** (10% drop-off)
3. **Assessment start → Assessment complete** (13% drop-off)

**Biggest Opportunity:**
- Reducing assessment drop-off (13% = 1,300 users/month)
- Improving email verification (15% = 1,500 users/month)

---

## Experiment Priority Matrix

### Impact vs. Effort Matrix

| Experiment | Expected Impact | Effort | Priority |
|------------|----------------|--------|----------|
| Reduce form fields | High (12% lift) | Low | ⭐⭐⭐ P0 |
- Email verification flow | High (10% lift) | Medium | ⭐⭐⭐ P0
- Assessment-first onboarding | Medium (8% lift) | High | ⭐⭐ P1
- Progress indicators | Medium (5% lift) | Low | ⭐⭐ P1
- Social proof injection | Medium (4% lift) | Low | ⭐⭐ P1
- Interactive tutorial | Low (3% lift) | High | ⭐ P2 |
- Gamification elements | Low (2% lift) | Medium | ⭐ P2 |
- Multi-language support | High (15% lift) | Very High | ⭐⭐ P1* |

*^ High impact but significant effort; prioritize for international expansion

---

## Ready-to-Run Experiments

## Experiment 1: Streamlined Signup Flow

**Hypothesis:** Reducing signup form fields from 5 to 2 will increase email verification rate by 12% because fewer fields reduce cognitive load and signup friction.

**Variants:**

**Control (Current):**
```
Fields Required:
1. Full name
2. Email
3. Password
4. Company name
5. Role (dropdown)
6. Confirm password

Time to complete: ~2 minutes
Drop-off: 15%
```

**Variant A (Minimal):**
```
Fields Required:
1. Email
2. Password

Fields moved to post-signup:
- Full name (asked after first assessment)
- Company name (asked during team invitation)
- Role (asked during onboarding questions)

Time to complete: ~45 seconds
Target: <10% drop-off
```

**Variant B (Social First):**
```
Fields Required:
- "Continue with Google" (primary)
- "Continue with email" (secondary)

If email: Email only (no password required - magic link sent)

Time to complete: ~20 seconds
Target: <8% drop-off
```

**Implementation:**
```typescript
// Experiment configuration
const EXPERIMENT_NAME = 'signup_streamline_v1';
const TRAFFIC_SPLIT = { control: 0.5, variant_a: 0.25, variant_b: 0.25 };

// Sample size calculator
const baselineConversion = 0.85; // 85% verify email
const mde = 0.03; // Detect 3% absolute lift (3.5% relative lift)
const alpha = 0.05;
const power = 0.8;

// Required sample: ~6,000 per variant (24,000 total signups)
// Estimated duration: 6-8 weeks at 3,000 signups/week
```

**Success Criteria:**
- **Primary:** Email verification rate increases by ≥5% (statistically significant)
- **Secondary:** Time to account creation decreases by ≥30%
- **Guardrail:** Day 1 retention does not decrease (>43%)

**Tracking:**
```typescript
interface SignupFunnelEvents {
  signup_viewed: string;
  signup_started: string;
  signup_completed: string;
  verification_email_sent: string;
  verification_email_clicked: string;
  account_verified: string;
  onboarding_started: string;
}

// Example event
analytics.track('signup_completed', {
  experiment: EXPERIMENT_NAME,
  variant: 'variant_a',
  fields_count: 2,
  time_to_complete: 45, // seconds
  signup_method: 'email' | 'google'
});
```

---

## Experiment 2: Value-First Onboarding

**Hypothesis:** Moving the assessment to the beginning of onboarding (before questions) will increase activation rate by 8% because users experience value earlier, increasing motivation to complete remaining steps.

**Variants:**

**Control (Current Flow):**
```
1. Create account
2. Answer 3 onboarding questions (role, team size, goals)
3. Browse assessment catalog
4. Start and complete assessment
5. View results

Activation: 42%
TTFV: 18.5 minutes
```

**Variant A (Assessment First):**
```
1. Create account
2. Auto-start recommended assessment
3. Complete assessment (get value immediately)
4. View results (AH HA moment)
5. Answer onboarding questions (context: "Now that we know your personality...")
6. Browse additional assessments

Target: 50% activation (+8 points)
TTFV: 12 minutes
```

**Variant B (Guided Assessment):**
```
1. Create account
2. "Let's discover your personality in 8 minutes"
3. Assessment starts with intro overlay explaining what to expect
4. Progress milestone celebrations (25%, 50%, 75%)
5. Results revealed with "What's Next" guide
6. Onboarding questions framed as personalization

Target: 52% activation (+10 points)
TTFV: 14 minutes
```

**Implementation:**
```typescript
// Route configuration
const onboardingRoutes = {
  control: '/signup → /onboarding/questions → /assessments/browse',
  variant_a: '/signup → /assessments/auto-start',
  variant_b: '/signup → /assessments/guided-intro'
};

// Auto-start logic
const shouldAutoStartAssessment = (user: User) => {
  const experimentVariant = getExperimentVariant(user.id, 'value_first_onboarding');
  return experimentVariant !== 'control';
};

// Assessment recommendation based on zero data
const getDefaultAssessment = () => {
  // Big Five has highest completion rate (82%)
  return 'big_five';
};
```

**Success Criteria:**
- **Primary:** Activation rate increases by ≥5% (statistically significant)
- **Secondary:** TTFV decreases by ≥20%
- **Secondary:** Assessment completion rate increases by ≥3%
- **Guardrail:** Onboarding question completion rate does not drop below 55%

---

## Experiment 3: Progress & Momentum

**Hypothesis:** Adding a visual progress indicator with momentum messaging throughout onboarding will increase completion rate by 5% by leveraging the goal-gradient effect (people work harder as they perceive progress toward a goal).

**Variants:**

**Control (Current):**
```
No progress indicator during onboarding questions
```

**Variant A (Step Progress):**
```
Top of screen:
━━━●━━━●━━━○━━━○  (Step 2 of 5)
     Role  Team  Goals

Messaging: "Almost there! Just 2 more questions."
```

**Variant B (Percentage Progress):**
```
Circular progress indicator:
[░░░░░] 40% complete

Dynamic messaging based on progress:
- 20%: "Great start!"
- 40%: "You're building momentum..."
- 60%: "Over halfway there!"
- 80%: "Just one more step!"
- 100%: "You're all set! 🎉"
```

**Variant C (Progress + Preview):**
```
Progress bar with upcoming steps preview:
━━━━━━━━━━━━●━━  60% done

Up next:
  ✓ Your role
  ✓ Team size
  → Your goals (current)
  ○ Choose assessment
  ○ View results

Messaging: "You're 3 quick questions from your personality insights"
```

**Implementation:**
```typescript
interface ProgressConfig {
  currentStep: number;
  totalSteps: number;
  showPercentage: boolean;
  showPreview: boolean;
  momentumMessaging: boolean;
}

const progressMessages = {
  step_start: [
    "Let's get started!",
    "First step toward understanding your team."
  ],
  step_middle: [
    "Great progress!",
    "You're building momentum...",
    "Keep going, you're doing great!"
  ],
  step_almost_done: [
    "Almost there!",
    "Just one more step.",
    "Final stretch!"
  ],
  step_complete: [
    "You're all set! 🎉",
    "Amazing progress!"
  ]
};

const getMomentumMessage = (progress: number) => {
  if (progress < 0.3) return randomFrom(progressMessages.step_start);
  if (progress < 0.7) return randomFrom(progressMessages.step_middle);
  if (progress < 1.0) return randomFrom(progressMessages.step_almost_done);
  return randomFrom(progressMessages.step_complete);
};
```

**Success Criteria:**
- **Primary:** Onboarding completion rate increases by ≥3%
- **Secondary:** Time to completion decreases by ≥15%
- **Secondary:** Drop-off between steps decreases by ≥20%

---

## Experiment 4: Social Proof Injection

**Hypothesis:** Injecting social proof at key decision points will increase assessment start rate by 6% by leveraging social validation and reducing uncertainty.

**Social Proof Locations:**

**Location 1: Assessment Browser**
```
Control:
[Assessment cards with descriptions only]

Variant A (User Count):
Big Five Personality Test
⭐ Most Popular
12,453 people completed this month
8-10 minutes • 75 questions

[Start Assessment →]
```

**Location 2: Before Starting Assessment**
```
Control:
[Assessment start screen with tips]

Variant A (Social Proof):
"Join 12,453 people who discovered their Big Five results this month"

[Start Assessment →]

Variant B (Testimonial):
"The Big Five gave me insights I use every day in management."
— Sarah K., Engineering Manager at TechCorp

[Start Assessment →]
```

**Location 3: After Assessment Complete**
```
Control:
"Assessment complete! View your results."

Variant A (Share Potential):
"Your results are ready! 89% of people share their insights with their team."

[View Results] [Share with Team]
```

**Implementation:**
```typescript
interface SocialProofConfig {
  showUserCount: boolean;
  showTestimonial: boolean;
  showShareRate: boolean;
}

const socialProofData = {
  big_five: {
    completions_this_month: 12453,
    completion_rate: 0.82,
    avg_rating: 4.7,
    testimonials: [
      {
        text: "The Big Five gave me insights I use every day.",
        author: "Sarah K.",
        role: "Engineering Manager",
        company: "TechCorp"
      }
    ]
  },
  // ... other assessments
};

const formatSocialProof = (count: number) => {
  if (count > 10000) return `${(count / 1000).toFixed(1)}K people`;
  if (count > 1000) return `${(count / 1000).toFixed(1)}K people`;
  return `${count} people`;
};
```

**Success Criteria:**
- **Primary:** Assessment start rate increases by ≥4%
- **Secondary:** Assessment completion rate increases by ≥2%
- **Secondary:** Share with team rate increases by ≥5%

---

## Experiment 5: Email Verification Optimization

**Hypothesis:** Sending email verification immediately after email field entry (instead of after form submission) will increase verification rate by 10% because users can verify while completing other fields.

**Variants:**

**Control (Current):**
```
1. User fills entire form (name, email, password, company, role)
2. Submits form
3. Email sent
4. User checks email and clicks link
Verification rate: 85%
Time to verify: ~5 minutes
```

**Variant A (Early Send):**
```
1. User enters email address
2. Email sent immediately (debounced: 3 seconds after typing stops)
3. User completes rest of form
4. User submits form
5. If email verified: proceed to onboarding
6. If not verified: "Please check your email and click the verification link"

Target: 93% verification rate (+8 points)
Time to verify: ~3 minutes (happens in parallel)
```

**Variant B (Magic Link):**
```
1. User enters email only
2. "We've sent a magic link to your email. Click it to sign in instantly."
3. Email contains magic link (auto-authenticates on click)
4. User lands in app, authenticated

Target: 88% verification rate (+3 points)
Time to verify: ~2 minutes
```

**Implementation:**
```typescript
// Backend API: Send verification email early
app.post('/api/send-verification', async (req, res) => {
  const { email } = req.body;

  // Validate email format
  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  // Check if already verified
  const existingUser = await db.users.findOne({ email });
  if (existingUser?.verified) {
    return res.json({ alreadyVerified: true });
  }

  // Send verification email
  const token = generateVerificationToken();
  await sendEmail({
    to: email,
    template: 'verification',
    data: { token }
  });

  // Store token with 15-minute expiration
  await redis.setex(`verify:${email}`, 900, token);

  res.json({ sent: true });
});

// Frontend: Debounced email verification
const EmailInput = () => {
  const [email, setEmail] = useState('');
  const [verificationSent, setVerificationSent] = useState(false);

  const debouncedSendVerification = useMemo(
    () => debounce(async (email) => {
      if (isValidEmail(email)) {
        await api.sendVerification(email);
        setVerificationSent(true);
      }
    }, 3000),
    []
  );

  useEffect(() => {
    if (email && !verificationSent) {
      debouncedSendVerification(email);
    }
  }, [email]);

  return (
    <input
      type="email"
      value={email}
      onChange={(e) => setEmail(e.target.value)}
      placeholder="work@example.com"
    />
  );
};
```

**Success Criteria:**
- **Primary:** Email verification rate increases by ≥5%
- **Secondary:** Time to verification decreases by ≥40%
- **Guardrail:** Spam complaints do not increase (>0.1%)

---

## Experiment 6: Assessment Momentum

**Hypothesis:** Breaking assessments into milestones with micro-celebrations will increase completion rate by 7% by leveraging the goal-gradient effect and creating small wins.

**Variants:**

**Control (Current):**
```
Linear progress: "Question 35 of 75"
No celebrations until end
Drop-off: 18%
```

**Variant A (Milestone Celebrations):**
```
Milestones at: 25%, 50%, 75%, 100%

At 25%:
[Modal: 25% Complete! 🎯]
"You're making great progress. Keep it up!"
[Continue]

At 50%:
[Modal: Halfway There! 🔥]
"You're halfway to discovering your personality insights."
[Continue]

At 75%:
[Modal: Almost Done! 🏁]
"Just 25% more. You've got this!"
[Continue]

At 100%:
[Modal: Assessment Complete! 🎉]
["Your results are ready!" with confetti]
[View Results]
```

**Variant B (Progress Visualization):**
```
Visual roadmap:

[Start] → [25%] → [50%] → [75%] → [Finish]
   ●         ●         ○         ○         ○
(current position)

Sidebar: "You're on question 35 of 75"
Mini-progress: [████████░░░░░░░] 47%

Encouragement messages:
- After streak of 10 answers: "On fire! 🔥"
- After slow section: "Taking your time is okay ✓"
- Near milestone: "Just 5 more questions to 50%!"
```

**Implementation:**
```typescript
interface MilestoneConfig {
  percentage: number;
  showCelebration: boolean;
  message: string;
  confetti?: boolean;
}

const milestones: MilestoneConfig[] = [
  { percentage: 25, showCelebration: true, message: "25% Complete! 🎯" },
  { percentage: 50, showCelebration: true, message: "Halfway There! 🔥", confetti: true },
  { percentage: 75, showCelebration: true, message: "Almost Done! 🏁" },
  { percentage: 100, showCelebration: true, message: "Assessment Complete! 🎉", confetti: true }
];

const checkMilestone = (currentQuestion: number, totalQuestions: number) => {
  const progress = currentQuestion / totalQuestions;
  return milestones.find(m => progress >= m.percentage && !m.seen);
};

// Confetti animation
const triggerConfetti = () => {
  // Use canvas-confetti library
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 }
  });
};
```

**Success Criteria:**
- **Primary:** Assessment completion rate increases by ≥5%
- **Secondary:** Time to completion decreases by ≥10%
- **Secondary:** Drop-off at milestones decreases by ≥30%

---

## Experiment Implementation Guide

### Step 1: Experiment Setup

**Define experiment:**
```typescript
// experiments.config.ts
export const ONBOARDING_EXPERIMENTS = {
  signup_streamline_v1: {
    name: 'Signup Streamline',
    description: 'Reduce signup fields from 5 to 2',
    variants: ['control', 'variant_a', 'variant_b'],
    traffic_split: { control: 0.5, variant_a: 0.25, variant_b: 0.25 },
    start_date: '2025-01-15',
    end_date: '2025-03-15', // 8 weeks
    target_metrics: ['email_verification_rate', 'time_to_verify'],
    guardrail_metrics: ['day_1_retention', 'spam_complaints']
  },
  // ... other experiments
};
```

### Step 2: User Assignment

**Consistent variant assignment:**
```typescript
// services/assignment.ts
import crypto from 'crypto';

export const assignVariant = (userId: string, experimentName: string): string => {
  // Get experiment config
  const experiment = ONBOARDING_EXPERIMENTS[experimentName];
  if (!experiment) return 'control';

  // Hash user ID + experiment name for consistency
  const hash = crypto
    .createHash('md5')
    .update(`${userId}-${experimentName}`)
    .digest('hex');

  // Convert to 0-1 range
  const bucket = parseInt(hash.substring(0, 8), 16) / 0xffffffff;

  // Assign variant based on traffic split
  let cumulative = 0;
  for (const [variant, split] of Object.entries(experiment.traffic_split)) {
    cumulative += split;
    if (bucket < cumulative) return variant;
  }

  return 'control';
};

// Usage
const variant = assignVariant(user.id, 'signup_streamline_v1');
```

### Step 3: Event Tracking

**Comprehensive event tracking:**
```typescript
// services/analytics.ts
interface ExperimentEvent {
  experiment_name: string;
  variant: string;
  user_id: string;
  event_type: string;
  timestamp: string;
  properties?: Record<string, any>;
}

export const trackExperimentEvent = (
  experimentName: string,
  eventType: string,
  properties?: Record<string, any>
) => {
  const variant = assignVariant(currentUser.id, experimentName);

  analytics.track(eventType, {
    experiment: experimentName,
    variant,
    user_id: currentUser.id,
    timestamp: new Date().toISOString(),
    ...properties
  });
};

// Example tracking
trackExperimentEvent('signup_streamline_v1', 'signup_completed', {
  fields_count: 2,
  time_to_complete: 45,
  signup_method: 'email'
});
```

### Step 4: Feature Flagging

**Remote configuration for experiments:**
```typescript
// services/featureFlags.ts
export const isExperimentEnabled = (experimentName: string): boolean => {
  const experiment = ONBOARDING_EXPERIMENTS[experimentName];
  if (!experiment) return false;

  const now = new Date();
  const start = new Date(experiment.start_date);
  const end = new Date(experiment.end_date);

  return now >= start && now <= end;
};

export const getExperimentVariant = (userId: string, experimentName: string): string => {
  if (!isExperimentEnabled(experimentName)) return 'control';
  return assignVariant(userId, experimentName);
};

// Usage in components
const SignupForm = () => {
  const variant = getExperimentVariant(user.id, 'signup_streamline_v1');

  if (variant === 'control') {
    return <FullSignupForm />;
  } else if (variant === 'variant_a') {
    return <MinimalSignupForm />;
  } else if (variant === 'variant_b') {
    return <SocialSignupForm />;
  }
};
```

---

## Analysis & Success Criteria

### Statistical Significance Calculator

```typescript
// utils/stats.ts
export const calculateSignificance = (
  controlConversions: number,
  controlTotal: number,
  variantConversions: number,
  variantTotal: number
): {
  controlRate: number;
  variantRate: number;
  lift: number;
  pValue: number;
  significant: boolean;
} => {
  const controlRate = controlConversions / controlTotal;
  const variantRate = variantConversions / variantTotal;
  const lift = ((variantRate - controlRate) / controlRate) * 100;

  // Two-proportion z-test
  const p1 = controlRate;
  const p2 = variantRate;
  const n1 = controlTotal;
  const n2 = variantTotal;

  const pooledP = (controlConversions + variantConversions) / (n1 + n2);
  const se = Math.sqrt(pooledP * (1 - pooledP) * (1/n1 + 1/n2));
  const z = (p2 - p1) / se;

  // Calculate p-value (two-tailed)
  const pValue = 2 * (1 - normalCDF(Math.abs(z)));

  return {
    controlRate,
    variantRate,
    lift,
    pValue,
    significant: pValue < 0.05
  };
};
```

### Sample Size Calculator

```typescript
// utils/sampleSize.ts
export const calculateSampleSize = (
  baselineRate: number,
  minimumDetectibleEffect: number, // e.g., 0.03 for 3% absolute lift
  alpha: number = 0.05,
  power: number = 0.8
): number => {
  // Z-scores
  const zAlpha = 1.96; // For alpha = 0.05
  const zBeta = 0.84;  // For power = 0.8

  const p1 = baselineRate;
  const p2 = baselineRate + minimumDetectibleEffect;

  const pooledP = (p1 + p2) / 2;

  const sampleSizePerVariant =
    (2 * pooledP * (1 - pooledP) * Math.pow(zAlpha + zBeta, 2)) /
    Math.pow(p2 - p1, 2);

  return Math.ceil(sampleSizePerVariant);
};

// Example: Email verification rate experiment
const baselineRate = 0.85; // 85%
const mde = 0.03; // Want to detect 3% absolute improvement
const requiredSample = calculateSampleSize(baselineRate, mde);
// Result: ~4,300 per variant, ~8,600 total for 2 variants
```

### Dashboard Integration

```typescript
// components/ExperimentDashboard.tsx
interface ExperimentResults {
  experiment_name: string;
  variant: string;
  total_users: number;
  conversions: number;
  conversion_rate: number;
  lift_vs_control?: number;
  p_value?: number;
  significant?: boolean;
}

const ExperimentDashboard = () => {
  const [results, setResults] = useState<ExperimentResults[]>([]);

  useEffect(() => {
    // Fetch experiment results
    fetch('/api/experiments/signup_streamline_v1/results')
      .then(r => r.json())
      .then(setResults);
  }, []);

  return (
    <div>
      <h2>Experiment Results</h2>
      <table>
        <thead>
          <tr>
            <th>Variant</th>
            <th>Users</th>
            <th>Conversion Rate</th>
            <th>Lift vs Control</th>
            <th>P-Value</th>
            <th>Significant</th>
          </tr>
        </thead>
        <tbody>
          {results.map(r => (
            <tr key={r.variant}>
              <td>{r.variant}</td>
              <td>{r.total_users.toLocaleString()}</td>
              <td>{(r.conversion_rate * 100).toFixed(2)}%</td>
              <td>{r.lift_vs_control ? `${r.lift_vs_control.toFixed(2)}%` : '-'}</td>
              <td>{r.p_value ? r.p_value.toFixed(4) : '-'}</td>
              <td>{r.significant ? '✅ Yes' : '❌ No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## Experiment Calendar

### Q1 2025 Onboarding Experiments

| Week | Experiment | Status | Results |
|------|-----------|--------|---------|
| Jan 15-21 | Setup: Signup Streamline | 🟡 In Progress | - |
| Jan 22-Feb 5 | Run: Signup Streamline (Weeks 1-2) | 🔵 Scheduled | - |
| Feb 6-12 | Run: Signup Streamline (Weeks 3-4) | 🔵 Scheduled | Interim analysis |
| Feb 13-Mar 5 | Run: Signup Streamline (Weeks 5-7) | 🔵 Scheduled | - |
| Mar 6-12 | Analyze: Signup Streamline | 🔵 Scheduled | Final decision |
| Mar 13-19 | Winner rollout | 🔵 Scheduled | - |
| Mar 20-26 | Setup: Email Verification | 🔵 Scheduled | - |
| Mar 27-Apr 16 | Run: Email Verification | 🔵 Scheduled | - |

### Q2 2025 Onboarding Experiments

| Week | Experiment | Priority |
|------|-----------|----------|
| Apr 17-May 7 | Value-First Onboarding | ⭐⭐⭐ |
| May 8-28 | Progress & Momentum | ⭐⭐ |
| May 29-Jun 18 | Social Proof Injection | ⭐⭐ |
| Jun 19-Jul 9 | Assessment Momentum | ⭐⭐⭐ |

---

## Summary

This onboarding experiments framework provides:

✅ **6 Ready-to-Run Experiments** – Fully designed with hypotheses, variants, and implementation code
✅ **Statistical Rigor** – Sample size calculators, significance testing, proper experiment design
✅ **Implementation Guide** – Assignment logic, tracking, feature flags
✅ **Success Criteria** – Primary, secondary, and guardrail metrics defined
✅ **Experiment Calendar** – Q1-Q2 2025 execution schedule

**Expected Impact if All Experiments Successful:**
- **Activation Rate:** 42% → 58% (+16 points, +38% lift)
- **Time to First Value:** 18.5 min → 11 min (-40%)
- **Day 7 Retention:** 28% → 35% (+25% lift)

**Next Steps:**
1. Prioritize Experiment 1 (Signup Streamline) for Week 1
2. Set up experiment tracking infrastructure
3. Document baseline metrics before launching
4. Create experiment review cadence (weekly check-ins)

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Next Review:** April 2025
**Maintained By:** Product & Growth Team
