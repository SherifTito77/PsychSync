# In-App Upsell Opportunities
# Strategic Touchpoints for Growth & Revenue

## Overview

This document maps every opportunity in the PsychSync user journey to present upsells, cross-sells, and upgrade prompts. The goal is to increase conversion timing and average revenue per user (ARPU) through contextual, value-driven messaging.

---

## The Upsell Framework

### Three Types of Upsells

1. **Tier Upgrades** (Free → Premium → Enterprise)
   - Unlock more features
   - Remove limits
   - Better value proposition

2. **Feature Add-ons** (Bought separately or bundled)
   - Advanced assessments
   - Custom reports
   - Priority support

3. **Usage Increases** (Within same tier)
   - Buy more assessments
   - Add team members
   - Extend data retention

---

## Upsell Opportunity Map

### Journey Stage 1: First Session (New Users)

#### 📍 Location: After First Assessment Completion

```typescript
// User just completed Big Five assessment
<AssessmentCompleteModal>
  <ConfettiAnimation />
  <h2>Great job completing your Big Five assessment!</h2>

  {/* UPSPELL OPPORTUNITY 1 */}
  <UpsellCard type="value_stair">
    <h3>See Your Results Compared to 50,000+ People</h3>
    <p>
      Upgrade to Premium to see how your personality compares to others
      in your industry, role, and age group.
    </p>
    <ComparisonPreview blurred={true}>
      "You're in the top 20% for Openness to Experience"
    </ComparisonPreview>
    <Button onClick={handleUpgrade}>
      Unlock Comparison →
    </Button>
    <small>Join 2,458 professionals who upgraded today</small>
  </UpsellCard>

  {/* UPSELL OPPORTUNITY 2 */}
  <UpsellCard type="next_step">
    <h3>Your Personality Journey is Just Beginning</h3>
    <p>
      Based on your Big Five results, our AI recommends 2 more assessments
      that will give you a complete picture of your strengths and growth areas.
    </p>
    <RecommendedPath>
      ✅ Big Five (completed)
      ⬜ MBTI - Your communication style
      ⬜ CliftonStrengths - Your top 5 talents
    </RecommendedPath>
    <Button onClick={() => navigate('/assessments/mbti')}>
      Continue Your Journey →
    </Button>
    <small>Free users get 3 assessments/month</small>
  </UpsellCard>
</AssessmentCompleteModal>
```

**Expected Impact:** 15-20% of users click through to second assessment, creating momentum

---

#### 📍 Location: Dashboard - "Assessment Limit Reached" Toast

```typescript
// When user tries to start 4th assessment
{hasHitLimit() && (
  <UpgradeToast>
    <div className="flex items-start gap-4">
      <div className="text-4xl">📊</div>
      <div className="flex-1">
        <h4>You've used your 3 free assessments this month</h4>
        <p className="text-sm text-gray-600 mb-3">
          Upgrade to Premium for unlimited assessments and unlock:
        </p>
        <ul className="text-sm space-y-1 mb-4">
          <li>✓ Unlimited assessments</li>
          <li>✓ Team analytics</li>
          <li>✓ Clinical tools</li>
          <li>✓ Benchmarking reports</li>
        </ul>
        <div className="flex gap-3">
          <Button onClick={handleUpgrade} variant="primary">
            Upgrade Now ($29/mo)
          </Button>
          <Button onClick={dismissToast} variant="ghost" size="sm">
            Maybe Later
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          <OfferTimer countdown="23:59:59">
            Limited time: 20% off annual billing →
          </OfferTimer>
        </p>
      </div>
    </div>
  </UpgradeToast>
)}
```

**Expected Impact:** 25-35% convert at this point (high intent moment)

---

### Journey Stage 2: Team Creation (Cross-Sell)

#### 📍 Location: When User Creates First Team

```typescript
// User just created a team
<TeamCreatedModal>
  <ConfettiAnimation />
  <h2>Team Created! 🎉</h2>
  <p>Your team "Product Design Team" now has 3 members.</p>

  {/* TEAM SIZE UPSELL */}
  <TeamSizeLimit current={3} limit={3} tier="free">
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <h4>💡 Free teams include up to 3 members</h4>
      <p className="text-sm text-gray-600 mb-3">
        Premium includes 25 team members, plus team analytics and collaboration features.
      </p>

      {/* COMPARISON TABLE */}
      <FeatureComparison
        features={[
          { name: 'Team Members', free: '3', premium: '25' },
          { name: 'Team Analytics', free: '❌', premium: '✅' },
          { name: 'Team Comparisons', free: '❌', premium: '✅' },
          { name: 'Collaborative Insights', free: '❌', premium: '✅' },
        ]}
      />

      <Button onClick={handleUpgrade} size="lg">
        Upgrade to Premium - $29/mo
      </Button>
      <p className="text-xs text-gray-500 mt-2">
        Most teams upgrade within 30 days • Cancel anytime
      </p>
    </div>
  </TeamSizeLimit>
</TeamCreatedModal>
```

**Expected Impact:** 40% of team creators upgrade when team hits size limit

---

### Journey Stage 3: Analytics Viewing (Feature Discovery)

#### 📍 Location: Analytics Dashboard - Feature Gate Blur

```typescript
// When Free user tries to access Team Analytics
<FeatureGate feature="canAccessTeamAnalytics">
  <TeamAnalyticsDashboard />

  {/* FALLBACK FOR FREE USERS */}
  <BlurredPreview>
    <div className="relative">
      <TeamAnalyticsDashboard className="blur-sm opacity-50 pointer-events-none" />

      <Overlay>
        <div className="text-center p-8">
          <div className="text-5xl mb-4">📊</div>
          <h3>Unlock Team Analytics</h3>
          <p className="text-gray-600 mb-4">
            See how your team compares on personality, communication styles, and strengths
          </p>

          {/* SOCIAL PROOF */}
          <TestimonialQuote>
            "Team analytics helped us identify our communication gaps and improve collaboration by 40%"
            <br/>
            <small>— Sarah Chen, Product Manager at TechCorp</small>
          </TestimonialQuote>

          <Button onClick={handleUpgrade} size="lg">
            Unlock Team Analytics
          </Button>

          {/* FEATURE PREVIEW */}
          <FeaturePreviewGrid>
            <FeaturePreview icon="📈" title="Personality Distribution">
              See personality types across your team
            </FeaturePreview>
            <FeaturePreview icon="🤝" title="Communication Styles">
              Understand how your team communicates
            </FeaturePreview>
            <FeaturePreview icon="💪" title="Strengths Matrix">
              Visualize team strengths and gaps
            </FeaturePreview>
          </FeaturePreviewGrid>

          <p className="text-sm text-gray-500 mt-4">
            Used by 500+ teams • Upgrade anytime
          </p>
        </div>
      </Overlay>
    </div>
  </BlurredPreview>
</FeatureGate>
```

**Expected Impact:** 35-45% conversion when users see the feature preview

---

### Journey Stage 4: Assessment Selection (Cross-Sell)

#### 📍 Location: Assessment Catalog Page

```typescript
// User browsing available assessments
<AssessmentCatalog>
  <AssessmentGrid>
    {assessments.map(assessment => (
      <AssessmentCard
        key={assessment.id}
        assessment={assessment}
        tier={getTierForAssessment(assessment)}
        onClick={() => handleStartAssessment(assessment)}
      >
        {/* PREMIUM ASSESSMENT BADGE */}
        {assessment.tier === 'premium' && (
          <PremiumBadge>
            <Tooltip content="Premium feature">
              ⭐ Premium
            </Tooltip>
          </PremiumBadge>
        )}

        {/* QUICK UPSELL ON HOVER */}
        {assessment.tier === 'premium' && (
          <HoverUpsell>
            <p>
              <strong>Premium Assessment</strong><br/>
              Unlock {assessment.name} and 15+ others with Premium
            </p>
            <Button size="sm" onClick={(e) => {
              e.stopPropagation();
              handleUpgrade({feature: assessment.id});
            }}>
              Upgrade Now
            </Button>
          </HoverUpsell>
        )}
      </AssessmentCard>
    ))}
  </AssessmentGrid>

  {/* BANNER: MULTIPLE ASSESSMENT VALUE */}
  {hasMultiplePremiumInCart() && (
    <BundleOffer>
      <h3>💰 Save Time with Premium</h3>
      <p>
        You have 3 premium assessments in your queue. Premium gives you
        unlimited access to all 15+ assessments for just $29/month.
      </p>
      <Button onClick={handleUpgrade}>
        Get Premium & Save Time
      </Button>
    </BundleOffer>
  )}
</AssessmentCatalog>
```

**Expected Impact:** 10-15% conversion from catalog browsing

---

### Journey Stage 5: Settings/Account (Retention)

#### 📍 Location: Settings Page - Plan Summary

```typescript
// User viewing their account settings
<SettingsPage>
  <Section title="Your Plan">
    <CurrentPlanCard>
      <PlanName>Free</PlanName>
      <PlanUsage>
        <Metric label="Assessments this month" used={3} limit={3} />
        <Metric label="Team members" used={3} limit={3} />
      </PlanUsage>

      {/* UPGRADE CARD IN SETTINGS */}
      {isAtCapacity() && (
        <UpgradeOpportunity variant="settings">
          <h4>Ready for More?</h4>
          <p>
            You're using all available features on your current plan.
            Upgrade to Premium to unlock:
          </p>
          <ul className="text-sm">
            <li>Unlimited assessments</li>
            <li>25 team members</li>
            <li>Advanced analytics</li>
          </ul>
          <Button onClick={handleUpgrade} variant="primary">
            Compare Plans
          </Button>
        </UpgradeOpportunity>
      )}
    </CurrentPlanCard>
  </Section>
</SettingsPage>
```

**Expected Impact:** 5-10% conversion (lower urgency, but persistent)

---

### Journey Stage 6: Report Export (Add-on Sale)

#### 📍 Location: After Viewing Assessment Results

```typescript
// User just completed assessment, viewing results
<ResultsPage>
  <AssessmentResults />

  <ActionButtons>
    <Button onClick={handleRetake}>Retake Assessment</Button>
    <Button onClick={handleShare}>Share Results</Button>

    {/* ADD-ON: DETAILED REPORT */}
    <Button onClick={handlePurchaseReport} variant="premium">
      Purchase Detailed Report ($9.99)
    </Button>
  </ActionButtons>

  {/* UPSELL: Premium includes reports */}
  <Flyover>
    <p>
      <strong>Premium members get unlimited detailed reports included!</strong>
    </p>
    <p>
      Your last 12 months of reports would cost $119.88 separately,
      but Premium is only $29/month ($348/year).
    </p>
    <Comparison>
      Option A: 12 reports × $9.99 = $119.88
      Option B: Premium = $348/year (includes reports + everything else)
    </Comparison>
    <Button onClick={handleUpgrade}>
      Compare Premium
    </Button>
  </Flyover>
</ResultsPage>
```

**Expected Impact:** 8-12% upgrade when presented with comparison

---

### Journey Stage 7: Billing Page (Downgrade Prevention)

#### 📍 Location: Billing/Cancellation Page

```typescript
// User clicks "Cancel Subscription"
<CancellationPage>
  <CancellationFlow />

  {/* RETENTION OFFER: DOWNGRADE WITH BENEFITS */}
  <RetentionOffer variant="downgrade">
    <h3>Before You Go...</h3>
    <p>
      We noticed you're a power user with 48 assessments completed!
      Have you considered downgrading to our Free tier instead of canceling?
    </p>

    <ComparisonTable>
      <thead>
        <tr>
          <th>Premium (You have)</th>
          <th>Free (Keep value)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>$29/month</td>
          <td>$0/month</td>
        </tr>
        <tr>
          <td>Unlimited assessments</td>
          <td>3 assessments/month</td>
        </tr>
        <tr>
          <td>All your data saved</td>
          <td>Basic reports</td>
        </tr>
        <tr>
          <td>❌ Cancel</td>
          <td>✅ Keep forever</td>
        </tr>
      </tbody>
    </ComparisonTable>

    <OfferHighlight>
      <h4>🎁 Special Offer: Keep 50% Off for Life</h4>
      <p>
      We don't want to lose you! If you downgrade to Free instead of canceling,
      we'll give you 50% off if you ever decide to upgrade again.
    </p>
      <div className="text-6xl font-bold text-green-600">
        $14.50/month
      </div>
      <small>Locked in forever if you downgrade first</small>
    </OfferHighlight>

    <Button onClick={handleDowngrade}>
      Downgrade to Free & Keep Discount
    </Button>
    <Button onClick={continueCancellation} variant="ghost">
      No thanks, cancel anyway
    </Button>
  </RetentionOffer>
</CancellationPage>
```

**Expected Impact:** Saves 30-40% of cancellations

---

### Journey Stage 8: Email Sequences (Automated)

#### 📍 Email Trigger: After 2nd Assessment

```typescript
// Automated email sent 24 hours after 2nd assessment
<EmailTemplate>
  Subject: "You're on a roll! 🔥"

  Hi [Name],

  Congratulations on completing your 2nd assessment! You're making great progress
  on your self-discovery journey.

  <INSIGHT_BOX>
    Most users who complete 2+ assessments report 3x more insights about themselves
    and their team. You're building momentum!
  </INSIGHT_BOX>

  <UPSELL_BOX>
    <h4>Don't Stop Now</h4>
    <p>
      Based on your MBTI results, our AI recommends the Enneagram assessment next.
      It will reveal your core motivations and help you understand why you make the
      decisions you do.
    </p>

    <Button>Take Enneagram Assessment →</Button>

    <small>You have 1 free assessment remaining this month</small>

    <p>
      Or, <strong>upgrade to Premium</strong> for unlimited access and unlock:
    </p>
    <ul>
      <li>Unlimited assessments</li>
      <li>Personality comparison tools</li>
      <li>Team analytics (if you have a team)</li>
      <li>Benchmarking against 50,000+ users</li>
    </ul>

    <Link to="/pricing?utm_source=email&utm_campaign=assessment_2">
      View Plans →
    </Link>
  </UPSELL_BOX>

  Keep growing!

  The PsychSync Team
</EmailTemplate>
```

**Expected Impact:** 12-18% open rate, 8-12% click-through, 3-5% conversion

---

## Advanced Upsell Techniques

### 1. The "Upgrade Later" Deferred Prompt

```typescript
// Let user upgrade at their own pace
<DeferredUpgradePrompt>
  <Button onClick={handleUpgrade} variant="primary">
    Upgrade Now
  </Button>
  <Button onClick={handleDeferredUpgrade}>
    {/* Save upgrade intent for later */}
    <span onClick={() => saveUpgradeIntent('team_analytics')}>
      Maybe Later
    </span>
  </Button>
</DeferredUpgradePrompt>

// Later, when user visits relevant page:
{hasUpgradeIntent('team_analytics') && (
  <UpgradeReminder>
    <p>
      Earlier you showed interest in Team Analytics.
      <strong>Now's a great time to unlock it!</strong>
    </p>
    <Button onClick={handleUpgrade}>Upgrade Now</Button>
  </UpgradeReminder>
)}
```

### 2. The "Limited Time" Offer (Real Urgency)

```typescript
// Show limited-time offers sparingly (not false urgency)
<LimitedTimeOffer>
  <div className="bg-gradient-to-r from-orange-50 to-red-50 border-2 border-orange-300 rounded-lg p-6">
    <div className="flex items-start gap-4">
      <div className="text-4xl">⏰</div>
      <div>
        <h4 className="font-bold text-orange-900">January Special: 20% Off Annual Plans</h4>
        <p className="text-orange-700 mb-3">
          Start your new year with PsychSync. Save $70 on an annual Premium plan.
        </p>

        <CountdownTimer endDate="2025-01-31" />

        <Button onClick={handleUpgrade} variant="primary">
          Get 20% Off Annual
        </Button>

        <p className="text-xs text-orange-600 mt-2">
          Offer ends January 31, 2025 • No code needed
        </p>
      </div>
    </div>
  </div>
</LimitedTimeOffer>
```

### 3. The "Social Proof" Upsell

```typescript
// Use social proof to reduce perceived risk
<SocialProofUpsell>
  <h3>Join 10,000+ Professionals Growing with PsychSync</h3>

  <TestimonialCarousel>
    <Testimonial name="Sarah Chen" role="Product Manager" company="TechCorp">
      "Our team's communication improved 40% after using PsychSync's team analytics"
    </Testimonial>

    <Testimonial name="Michael Ross" role="HR Director" company="FinanceHub">
      "We reduced hiring bias by 35% using PsychSync's behavioral assessments"
    </Testimonial>

    <Testimonial name="Lisa Wang" role="Team Lead" company="StartupXYZ">
      "The personality insights helped us build a more diverse and balanced team"
    </Testimonial>
  </TestimonialCarousel>

  <CompanyLogos>
    <img src="/logos/techcorp.png" alt="TechCorp" />
    <img src="/logos/financehub.png" alt="FinanceHub" />
    <img src="/logos/startupxyz.png" alt="StartupXYZ" />
  </CompanyLogos>

  <p className="text-sm text-gray-600 text-center">
    Companies like yours are growing with PsychSync
  </p>
</SocialProofUpsell>
```

---

## Upsell Timing Strategy

### Best Times to Present Upsells

1. **High Intent Moments** (Highest Conversion)
   - After hitting a limit (3rd assessment, 4th team member)
   - When trying to access premium features
   - After experiencing value (first assessment complete)

2. **Discovery Moments** (Medium Conversion)
   - Browsing assessment catalog
   - Viewing pricing page
   - Reading feature comparisons

3. **Maintenance Moments** (Low Conversion but Important)
   - Settings/account page
   - Billing page
   - Monthly summary emails

### Worst Times to Present Upsells

❌ **Avoid:**
- During onboarding (too overwhelming)
- During assessment (interrupts flow)
- When user is frustrated (bugs, errors)
- Immediately after cancellation request (tone deaf)

---

## Microcopy for Upsell Prompts

### Short & Punchy (Buttons)

```typescript
// ✅ Good: Action-oriented
"Unlock Team Analytics"
"See How You Compare"
"Get Unlimited Access"

// ❌ Bad: Vague or passive
"Upgrade here"
"Click to upgrade"
"Consider upgrading"
```

### Benefit-Focused (Descriptions)

```typescript
// ✅ Good: Clear benefit
"Compare your personality with 50,000+ people in your industry"
"Unlimited assessments means unlimited self-discovery"

// ❌ Bad: Feature-focused
"Access our benchmarking database"
"No more assessment limits"
```

### Social Proof (Testimonials)

```typescript
// ✅ Good: Specific and relatable
"Teams like yours improved collaboration by 40% using team analytics"
"95% of Premium users say it's worth every penny"

// ❌ Bad: Generic or unbelievable
"Everyone loves Premium"
"Best tool ever"
```

---

## Measuring Upsell Performance

### Track These Metrics

```typescript
interface UpsellMetrics {
  // Exposure
  impressions: number;           // How many times shown
  uniqueUsersExposed: number;     // How many unique users

  // Engagement
  clickRate: number;             // Clicks / impressions
  ctrByVariant: Record<string, number>;
  ctrByLocation: Record<string, number>;

  // Conversion
  conversionRate: number;        // Upgrades / impressions
  timeToConvert: number;         // Average days to upgrade

  // Revenue
  immediateRevenue: number;      // Direct upsell revenue
  attributedRevenue: number;     // Attributed revenue (30-day window)

  // Sentiment
  positiveSentiment: number;     // % positive feedback
  negativeSentiment: number;     // % negative feedback
  complaintRate: number;         // % of users who complain
}
```

---

## Summary: The Upsell Funnel

```
1. EXPOSURE (100% of users)
   └─ First touchpoint: Assessment complete
   └─ Show: Value-based next step or upgrade option

2. INTEREST (40% engage)
   └─ User clicks "Learn More" or preview
   └─ Show: Feature comparison, social proof

3. INTENT (15% show high intent)
   └─ User hits limit, tries to access premium feature
   └─ Show: Urgency + clear benefits + easy action

4. CONVERSION (5-8% upgrade)
   └─ User completes purchase
   └─ Celebrate: Show upgrade benefits, onboarding
```

**Key Insight:** The more specific and contextual the upsell, the higher the conversion. Generic "upgrade now" prompts perform 3-5x worse than targeted, value-driven upsells.

**Golden Rule:** Always answer "What's in it for me?" before asking for money.
