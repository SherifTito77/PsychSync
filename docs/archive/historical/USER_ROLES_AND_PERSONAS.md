# PsychSync User Roles & Personas
**Comprehensive User Archetype Framework**

**Version:** 1.0
**Last Updated:** 2025-01-12
**Owner:** Product & UX Team

---

## Executive Summary

PsychSync serves a multi-sided ecosystem with **6 primary user roles** across **3 organizational tiers** (Individual Contributors, Managers, Enterprise Leaders). Each role has distinct goals, pain points, and success metrics. Understanding these personas is critical for feature prioritization, UX design, and go-to-market strategy.

**Key Insight:** B2B SaaS platforms succeed when they address the **triangle of value**: Individual Growth → Team Performance → Organizational Outcomes. PsychSync's personas span all three dimensions.

---

## Part 1: Role-Based Access Control (RBAC) Framework

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                    PLATFORM ADMIN                        │
│         (System-level: PsychSync team only)             │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────┴────────┐    ┌────────┴────────┐
│  ORG ADMIN      │    │  TEAM ADMIN     │
│  (Enterprise)   │    │  (Team Lead)    │
└────────┬────────┘    └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
            ┌────────┴────────┐
            │   TEAM MEMBER   │
            │  (Individual)   │
            └─────────────────┘
```

### Permission Matrix

| Permission | Org Admin | Team Admin | Team Member | Guest |
|------------|-----------|------------|-------------|-------|
| Create/edit teams | ✅ | ✅ | ❌ | ❌ |
| Invite/remove members | ✅ | ✅ | ❌ | ❌ |
| Manage billing | ✅ | ❌ | ❌ | ❌ |
| Create assessments | ✅ | ✅ | ❌ | ❌ |
| View team analytics | ✅ | ✅ | ✅ (own) | ❌ |
| View own results | ✅ | ✅ | ✅ | ✅ |
| Export reports | ✅ | ✅ | ✅ (own) | ❌ |
| Manage integrations | ✅ | ✅ | ❌ | ❌ |
| Configure SSO | ✅ | ❌ | ❌ | ❌ |

---

## Part 2: Detailed User Personas

### Persona 1: The Team Lead (Primary B2B Buyer)

**Profile:**
- **Name:** Sarah Chen
- **Age:** 34
- **Role:** Engineering Manager / Team Lead
- **Company Size:** 20-200 employees (SaaS, Tech, Healthcare)
- **Tech Savviness:** High (former developer or product manager)

**Goals:**
1. Build high-performing, cohesive teams
2. Reduce conflict and communication breakdowns
3. Make data-driven hiring and promotion decisions
4. Identify burnout and engagement risks early
5. Justify team performance to upper management

**Pain Points:**
- "My team is talented but can't work together"
- "I don't know how to handle personality conflicts"
- "Performance reviews feel subjective and biased"
- "New hires take 6 months to ramp up"
- "I have no visibility into team morale until someone quits"

**Behaviors:**
- Logs in 2-3x per week to check team insights
- Shares personality reports in 1:1 meetings
- Uses data to justify promotions and role changes
- Frequently exports reports for leadership presentations
- Attends webinars on team management best practices

**Success Metrics:**
- Team retention rate >85%
- Employee satisfaction score >8/10
- Productivity metrics (velocity, OKRs) improving
- Reduced conflict escalations to HR

**Feature Priorities:**
1. Team Analytics Dashboard (HIGH)
2. Conflict Prediction Alerts (HIGH)
3. New Member Onboarding Templates (MEDIUM)
4. Performance Benchmarking (MEDIUM)
5. ROI Calculator for Leadership (HIGH)

**Quote:**
> "I don't need another tool that tells me my team is 'unique.' I need actionable insights on how to manage the introvert-extrovert dynamic that's killing our standups."

---

### Persona 2: The HR Business Partner

**Profile:**
- **Name:** Marcus Johnson
- **Age:** 41
- **Role:** HRBP / Talent Development Manager
- **Company Size:** 200-2000 employees (Mid-Market to Enterprise)
- **Tech Savviness:** Medium (comfortable with HRIS, analytics tools)

**Goals:**
1. Scale talent development programs across departments
2. Reduce turnover (especially of high performers)
3. Build diverse, inclusive teams
4. Standardize hiring and promotion criteria
5. Demonstrate HR's impact on business outcomes

**Pain Points:**
- "Every department uses different assessment tools - no centralized data"
- "Hiring bias accusations - we need objective criteria"
- "We promote people based on tenure, not readiness"
- "Training programs have no measurable impact"
- "Leadership asks for ROI on our initiatives - I have no data"

**Behaviors:**
- Manages 10-20 team assessments simultaneously
- Cross-references personality data with performance reviews
- Builds custom assessment templates for different roles
- Requests feature customizations and integrations
- Advocates for PsychSync expansion to new departments

**Success Metrics:**
- Company-wide retention >90%
- Promotion success rate >80%
- Diversity in leadership roles
- Assessment completion rate >85%

**Feature Priorities:**
1. Multi-Team Management Dashboard (HIGH)
2. Custom Assessment Builder (HIGH)
3. DEI Analytics & Reports (HIGH)
4. Integration with HRIS (Workday, BambooHR) (HIGH)
5. Leadership Development Program Templates (MEDIUM)

**Quote:**
> "I manage 15 teams across 4 departments. I need one platform that gives me a unified view of talent - not 15 different spreadsheets."

---

### Persona 3: The Individual Contributor (IC)

**Profile:**
- **Name:** Jessica Lee
- **Age:** 27
- **Role:** Software Engineer / Designer / Marketer
- **Experience:** 3-7 years in field
- **Tech Savviness:** High (digital native)

**Goals:**
1. Understand personal strengths and growth areas
2. Improve collaboration with difficult teammates
3. Identify career paths aligned with personality
4. Receive feedback that feels fair and personalized
5. Feel seen and understood by management

**Pain Points:**
- "My manager thinks I'm 'difficult' because I'm direct - but that's just my communication style"
- "I have no idea what roles I'd be good at - I fell into this career"
- "Performance reviews are generic - 'great job, keep it up'"
- "I clash with one specific coworker and don't know why"
- "I want to grow but don't know what to work on"

**Behaviors:**
- Completes assessments when assigned (reluctantly at first)
- Revisits personal results 2-3 times after receiving insights
- Shares results with close colleagues for validation
- Explores career recommendations based on personality
- Appreciates detailed breakdowns (not just "you're an INTJ")

**Success Metrics:**
- Personal growth goals met
- Improved collaboration scores
- Clarity on career direction
- Feeling valued and understood

**Feature Priorities:**
1. Detailed Personal Insights (HIGH)
2. Career Path Recommendations (HIGH)
3. Collaboration Tips with Specific Coworkers (HIGH)
4. Private Self-Reflection Journal (MEDIUM)
5. Skill Development Recommendations (MEDIUM)

**Quote:**
> "I was skeptical about personality tests until PsychSync told me exactly why I clash with my product manager - and how to fix it. That's when I became a believer."

---

### Persona 4: The C-Suite Executive

**Profile:**
- **Name:** Robert Kim
- **Age:** 52
- **Role:** VP of Engineering / CTO / Chief People Officer
- **Company Size:** 500-5000 employees (Enterprise)
- **Tech Savviness:** Low-Medium (delegates to teams)

**Goals:**
1. Scale organizational culture during rapid growth
2. Reduce turnover costs (estimated at $2M/year)
3. Build leadership pipeline from within
4. Make evidence-based people decisions
5. Demonstrate culture health to board

**Pain Points:**
- "We've grown from 50 to 500 employees - culture is eroding"
- "We promote great individual contributors who fail as managers"
- "Every department claims they need more headcount - is it real?"
- "Board asks: 'Is our culture healthy?' I have anecdotes, not data"
- "We've had 3 VPs quit in 6 months - what's the pattern?"

**Behaviors:**
- Reviews high-level dashboards monthly
- Requests executive summaries and trend analysis
- Authorizes large contracts ($50K-$500K)
- Asks for competitive benchmarking
- Demands SOC 2 and security compliance

**Success Metrics:**
- Company-wide engagement scores
- Leadership retention
- Time-to-fill for key roles
- Diversity metrics in leadership
- Culture health score trends

**Feature Priorities:**
1. Executive Dashboard with Trends (HIGH)
2. Organizational Network Analysis (HIGH)
3. Leadership Succession Planning (HIGH)
4. Competitive Benchmarking (MEDIUM)
5. Enterprise Security & Compliance (CRITICAL)

**Quote:**
> "I don't need to see every team's personality data. Give me a red-yellow-green dashboard showing where the culture risks are - and what to do about them."

---

### Persona 5: The New Hire

**Profile:**
- **Name:** Alejandro Martinez
- **Age:** 24
- **Role:** Junior Developer / Analyst
- **Tenure:** 0-90 days at company
- **Tech Savviness:** High

**Goals:**
1. Accelerate onboarding and team integration
2. Understand team culture and norms quickly
3. Avoid early mistakes from miscommunication
4. Build relationships with key colleagues
5. Demonstrate fit and cultural alignment

**Pain Points:**
- "I don't know how to communicate with my introverted lead"
- "Everyone seems to know the unspoken rules except me"
- "I'm afraid to speak up in meetings because I don't know the style"
- "I want to make a good impression but feel awkward"
- "Onboarding was all about tools - nothing about how we work"

**Behaviors:**
- Eagerly completes first assessment (high completion rate: 95%)
- Shares results with manager proactively
- Explores team composition to understand dynamics
- Uses collaboration tips for early interactions
- Most receptive to PsychSync value (first impression critical)

**Success Metrics:**
- Time-to-productivity <30 days
- Social integration (team connections)
- Early performance reviews
- Retention at 6 months

**Feature Priorities:**
1. New Hire Onboarding Checklist (HIGH)
2. Team Composition Overview (HIGH)
3. Communication Style Guides for Team (HIGH)
4. "Meet Your Team" Personalized Intro (MEDIUM)
5. 30-60-90 Day Goal Recommendations (MEDIUM)

**Quote:**
> "PsychSync told me my lead is a 'think-first, speak-later' type. I now write out my questions before our 1:1s - our meetings are way more productive."

---

### Persona 6: The Consultant / Coach

**Profile:**
- **Name:** Priya Sharma
- **Age:** 38
- **Role:** Organizational Development Consultant
- **Clients:** 5-10 concurrent companies
- **Tech Savviness:** High (power user)

**Goals:**
1. Deliver measurable client outcomes (revenue, retention)
2. Scale coaching impact beyond 1:1 sessions
3. Use data to justify consulting fees
4. Build long-term client relationships
5. Differentiate from competitors

**Pain Points:**
- "Clients cancel after initial engagement - no ongoing value"
- "I spend 80% of time gathering data, 20% on insights"
- "Hard to prove ROI - clients see coaching as 'fluff'"
- "Each client wants different assessments - too many tools"
- "I can't scale - limited by 1:1 coaching hours"

**Behaviors:**
- Deep customization of assessments for clients
- Frequent report generation and export
- Requests API access for custom integrations
- Uses PsychSync data to build business case
- Becomes champion for enterprise deals

**Success Metrics:**
- Client retention >12 months
- Projectable client outcomes (e.g., turnover reduction)
- Utilization rate (clients active/total)
- Revenue per client

**Feature Priorities:**
1. White-Label Reports (HIGH)
2. API Access (HIGH)
3. Custom Assessment Builder (HIGH)
4. Multi-Client Dashboard (HIGH)
5. Automated Progress Tracking (MEDIUM)

**Quote:**
> "PsychSync allows me to offer a data-backed leadership development program at 1/10th the cost of traditional consulting. My clients see ROI in month 3."

---

## Part 3: Secondary / Emerging Personas

### Persona 7: The Skeptic

**Profile:** Individual contributor, skeptical of personality science
**Behavior:** Rushes through assessments, gives inconsistent answers
**Strategy:** Gamification + social proof (team adoption) + immediate value delivery
**Conversion Rate:** 30% → 70% after seeing team insights

### Persona 8: The Power User

**Profile:** Team lead who uses PsychSync daily for all decisions
**Behavior:** Requests advanced features, becomes internal champion
**Strategy:** Early access, co-design, customer advisory board
**Value:** 10x referral rate, influences enterprise deals

### Persona 9: The Guest / External Collaborator

**Profile:** Contractor, freelancer, or client partner
**Behavior:** Limited access, completes assessment for project team
**Strategy:** Lightweight onboarding, guest accounts, limited-time access
**Conversion:** 15% convert to full team member after project success

---

## Part 4: Persona-Based Feature Prioritization

### Urgent Needs (Weeks 1-8)

| Persona | Critical Feature | Why |
|---------|-----------------|-----|
| Team Lead | Conflict Prediction | Reduces #1 pain point (team conflict) |
| HRBP | Multi-Team Dashboard | Manages 10+ teams efficiently |
| IC | Detailed Personal Insights | First value moment, builds trust |
| New Hire | Onboarding Templates | Accelerates time-to-productivity |
| C-Suite | Executive Dashboard | Justifies investment to board |

### High-Value Needs (Weeks 9-16)

| Persona | High-Impact Feature | Why |
|---------|-------------------|-----|
| Team Lead | Career Path Recommendations | Retention lever (internal mobility) |
| HRBP | Custom Assessment Builder | Industry-specific assessments |
| IC | Team Comparison/Benchmarking | Social proof, engagement |
| C-Suite | Leadership Succession Planning | Risk mitigation |

### Strategic Needs (Weeks 17-24)

| Persona | Strategic Feature | Why |
|---------|------------------|-----|
| HRBP | HRIS Integration (Workday) | Enterprise requirement |
| Consultant | White-Label Reports | Partnership model |
| C-Suite | Organizational Network Analysis | Strategic insights |
| Team Lead | Advanced ML Predictions | Competitive differentiator |

---

## Part 5: Persona Journey Maps

### Journey Map: Team Lead (Sarah Chen)

| Stage | Touchpoints | Emotions | Pain Points | Opportunities |
|-------|-------------|-----------|-------------|---------------|
| **Discovery** | LinkedIn ad, peer recommendation | Curious, skeptical | "Is this legit science?" | Social proof, case studies |
| **Signup** | 3-question team assessment | Excited | "Will my team do this?" | Pre-built templates, low friction |
| **Onboarding** | Team dashboard, first insights | Delighted | "What do I do with this?" | Actionable playbooks |
| **Adoption** | Weekly digests, conflict alerts | Empowered | "Team resists assessments" | Gamification, team competition |
| **Value Realization** | Improved collaboration metrics | Satisfied | "How do I show ROI?" | Automated reports for leadership |
| **Renewal** | Annual ROI summary | Confident | "Is it worth the cost?" | Clear savings calculation |

---

### Journey Map: Individual Contributor (Jessica Lee)

| Stage | Touchpoints | Emotions | Pain Points | Opportunities |
|-------|-------------|-----------|-------------|---------------|
| **Invitation** | Email from manager | Annoyed, skeptical | "Not another test" | Emphasize time-saving, collaboration benefits |
| **Assessment** | 10-minute questionnaire | Indifferent | "Rushing to finish" | Engaging questions, progress bar |
| **Results** | Detailed personality breakdown | Surprised, validated | "Is this accurate?" | Comparison to friends/colleagues |
| **Exploration** | Career recommendations, team tips | Curious | "What can I do with this?" | Actionable next steps |
| **Application** | Collaboration advice, 1:1 discussion | Empowered | "Does this actually work?" | Quick wins, visible improvements |
| **Advocacy** | Sharing with team | Enthusiastic | "Don't want to seem pushy" | Social sharing, team challenges |

---

## Part 6: Persona-Based Messaging Strategy

### For Team Leads (Sarah Chen)
**Headline:** "Build Teams That Work Together"
**Subhead:** "Data-driven insights to reduce conflict, improve communication, and accelerate performance"
**CTA:** "See Your Team's Personality Map - Free Assessment"

### For HRBPs (Marcus Johnson)
**Headline:** "Scale Talent Development Across Your Organization"
**Subhead:** "Unified assessment platform with DEI analytics, leadership planning, and ROI tracking"
**CTA:** "Request Demo for HR Leadership"

### For Individual Contributors (Jessica Lee)
**Headline:** "Understand Your Work Style - And Your Team's"
**Subhead:** "Discover your strengths, improve collaboration, and find your ideal career path"
**CTA:** "Take the Free Assessment"

### For C-Suite (Robert Kim)
**Headline:** "Data-Backed Culture Health at Scale"
**Subhead:** "Reduce turnover costs, build leadership pipelines, and prove culture ROI to the board"
**CTA:** "Executive Briefing: Culture Analytics Platform"

---

## Part 7: Anti-Personas (Not Our Users)

### Anti-Persona 1: The Gig Worker
**Why:** No team context, short-term engagements
**Verdict:** Not a fit - PsychSync requires ongoing team dynamics

### Anti-Persona 2: The Solopreneur
**Why:** No team to analyze, individual assessments don't provide recurring value
**Verdict:** Not a fit - B2B focus, team features

### Anti-Persona 3: The Traditional HR Executive
**Why:** Prefers established vendors (SHL, Korn Ferry), resistant to new tools
**Verdict:** Secondary market - focus on tech-forward, data-driven HR

### Anti-Persona 4: The Privacy Fundamentalist
**Why:** Will not share personality data with employer
**Verdict:** Respect choice - emphasize privacy controls, data ownership

---

## Part 8: Persona Validation Plan

### Validation Methods

1. **Customer Interviews** (n=20)
   - 5 Team Leads, 5 HRBPs, 5 ICs, 5 C-Suite
   - Focus: Pain point validation, feature prioritization
   - Timeline: Weeks 1-4

2. **Survey Research** (n=500)
   - Job function: Manager, HR, IC, Executive
   - Focus: Willingness to pay, feature importance, assessment preferences
   - Timeline: Weeks 2-6

3. **Persona Testing**
   - Create landing pages for each persona
   - A/B test messaging and CTAs
   - Measure conversion by segment
   - Timeline: Weeks 4-8

4. **Behavioral Analytics**
   - Track feature usage by role
   - Identify power users vs. low-engagement segments
   - Iterative refinement based on real behavior
   - Timeline: Ongoing

### Success Metrics for Personas

| Metric | Target | Timeline |
|--------|--------|----------|
| Persona accuracy (interview validation) | ≥80% match | Week 6 |
| Conversion rate by persona (top 3) | ≥5% signup → paid | Week 12 |
| Feature usage match to persona priorities | ≥70% correlation | Week 8 |
| Churn rate by persona | <15% variance | Month 6 |

---

## Part 9: Persona Evolution Roadmap

### Phase 1: Core Personas (Weeks 1-12)
- **Focus:** Team Lead, HRBP, Individual Contributor
- **Goal:** 80% of user base fits these 3 personas
- **Features:** Team analytics, assessments, personal insights

### Phase 2: Enterprise Expansion (Weeks 13-20)
- **Focus:** C-Suite Executive, Consultant
- **Goal:** 15% of revenue from enterprise deals
- **Features:** Executive dashboards, white-labeling, integrations

### Phase 3: Niche Segments (Weeks 21-28)
- **Focus:** Industry-specific personas (Healthcare, Education, Finance)
- **Goal:** Vertical market penetration
- **Features:** Industry templates, compliance features

---

## Appendix: Persona Cards for Design Sprints

### Print-and-Cut Persona Cards (for workshops)

```
┌─────────────────────────────────────┐
│  SARAH CHEN                         │
│  Team Lead / Engineering Manager    │
│  Age: 34 | Tech SaaS | 50-person team│
├─────────────────────────────────────┤
│                                     │
│  "My team is talented but can't     │
│   work together"                    │
│                                     │
│  GOALS:                             │
│  • Build cohesive teams             │
│  • Reduce conflict                  │
│  • Data-driven decisions            │
│                                     │
│  PAIN POINTS:                       │
│  • Personality clashes              │
│  • Subjective performance reviews   │
│  • Low visibility into morale       │
│                                     │
│  FEATURES NEEDED:                   │
│  ✓ Team Analytics Dashboard         │
│  ✓ Conflict Prediction              │
│  ✓ Onboarding Templates             │
│                                     │
└─────────────────────────────────────┘
```

[Repeat for other 5 personas]

---

**Next Steps:**
1. Validate personas with 20 customer interviews
2. Create persona-based landing page variants
3. Prioritize features using persona-weighted scoring
4. Train customer success team on persona-specific playbooks
5. Measure actual user behavior vs. persona assumptions (Month 1-3)

---

*For questions or feedback, contact: product@psychsync.io*
