# Cross-Team Collaboration Workflows
**Operational Framework for Team Synergy at PsychSync**

**Date:** January 12, 2025
**Status:** Active Framework
**Audience:** All Teams (Product, Engineering, Sales, CS, Marketing, Data Science, Executive)

---

## 🎯 Purpose

As PsychSync scales from 500 to 50,000 teams, we can't rely on ad-hoc collaboration. We need **structured workflows** that ensure:

1. **Clear ownership** (who does what)
2. **Smooth handoffs** (no balls dropped between teams)
3. **Fast feedback loops** (learn quickly, iterate faster)
4. **Conflict-free collaboration** (decisions get made, not debated endlessly)

**Core Principles:**
- **Documentation over conversation** (write it down, don't just meet)
- **Async over sync** (respect deep work time)
- **Decisive over democratic** (empowered owners, not committees)
- **Customer-informed, not customer-driven** (listen to customers, but don't let them design the product)

---

## 📊 Team Structure & Ownership

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PSYCHSYNC TEAM STRUCTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐     ┌────────────┐     ┌─────────┐     ┌────────────┐     │
│  │ PRODUCT │ ←→ │ ENGINEERING│ ←→ │ DATA    │ ←→ │  DESIGN     │     │
│  │ TEAM    │     │ TEAM       │     │ SCIENCE │     │  TEAM       │     │
│  └─────────┘     └────────────┘     └─────────┘     └────────────┘     │
│       ↑               ↑                  ↑                ↑              │
│       │               │                  │                │              │
│       └───────────────┴──────────────────┴────────────────┘             │
│                       ↓                                                │
│              ┌─────────────────┐                                       │
│              │  CUSTOMER       │                                       │
│              │  SUCCESS        │                                       │
│              └─────────────────┘                                       │
│                       ↑                                                │
│                       │                                                │
│              ┌─────────────────┐     ┌────────────┐                   │
│              │  SALES          │ ←→ │  MARKETING │                   │
│              └─────────────────┘     └────────────┘                   │
│                       ↑                                                │
│                       │                                                │
│              ┌─────────────────┐                                       │
│              │  EXECUTIVE      │                                       │
│              └─────────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Core Collaboration Workflows

### Workflow 1: Product ↔ Engineering (Feature Delivery)

**Purpose:** Ship features fast without sacrificing quality

**Phase 1: Requirements (Product → Engineering)**
- **Output:** PRD (Product Requirements Document)
- **Template:** See `PRD_TEMPLATE.md` (create if not exists)
- **Sections Required:**
  - Problem statement (customer pain)
  - Success metrics (KPIs, targets)
  - User stories (acceptance criteria)
  - Technical considerations (performance, security, scalability)
  - Dependencies (other teams, third-party APIs)
  - Risks (what could go wrong)
- **Timeline:** 1-2 days before sprint planning

**Phase 2: Technical Design (Engineering → Product)**
- **Output:** Technical Design Document (TDD)
- **Owner:** Senior/Tech Lead engineer
- **Sections Required:**
  - Architecture diagram (system components, data flow)
  - Database schema changes (tables, indexes, migrations)
  - API endpoints (request/response, authentication)
  - Frontend components (React components, state management)
  - Testing strategy (unit, integration, E2E tests)
  - Rollout plan (feature flags, gradual rollout)
  - Performance estimates (p95 latency, p99 latency, throughput)
- **Timeline:** 2-3 days before sprint start

**Phase 3: Sprint Planning (Product + Engineering)**
- **Frequency:** Every 2 weeks (Monday 9-11 AM)
- **Attendees:** Product Manager, Engineers (5-7), Designer (if applicable)
- **Agenda:**
  1. Review PRD + TDD (15 min) — PM explains, engineers ask clarifying questions
  2. Estimate story points (30 min) — Planning poker, reach consensus
  3. Assign tasks (15 min) — Engineers self-assign based on capacity
  4. Define sprint goal (10 min) — "This sprint we'll ship [feature] to [X%] of users"
  5. Identify risks (10 min) — "What could block us? What's our backup plan?"

**Phase 4: Development (Engineering → Product)**
- **Cadence:** Daily standup (9:30 AM, 15 min, async preferred)
- **Update Format (Slack):**
  ```
  @sprint-channel
  Yesterday: [what you did]
  Today: [what you'll do]
  Blockers: [what's blocking you]
  ```
- **PM Role:** Review PRs, answer questions, unblock engineers (not micromanage)

**Phase 5: QA & Testing (Engineering → Product → QA)**
- **Engineering Checklist:** Unit tests pass, integration tests pass, code reviewed
- **Product Checklist:** QA testing complete, user acceptance criteria met, bugs logged
- **QA Checklist:** Test plan executed, edge cases covered, accessibility tested
- **Timeline:** 2-3 days before sprint end

**Phase 6: Launch (Product + Engineering + Marketing)**
- **Launch Readiness Review (LRR):** 2 days before launch
  - [ ] Feature is bug-free (P0/P1 bugs resolved)
  - [ ] Documentation is complete (help center, API docs)
  - [ ] Marketing assets are ready (blog, email, social)
  - [ ] Sales/CS are trained (battle card, FAQ)
  - [ ] Monitoring is set up (errors, latency, adoption)
- **Launch Execution:** See `PRODUCT_ANNOUNCEMENT_PLAYBOOK.md`

**Phase 7: Post-Launch Review (Product + Engineering)**
- **Timing:** 7 days after launch
- **Attendees:** PM, Engineers, Designer, Data Analyst
- **Metrics Review:**
  - Adoption (users, teams, % of total)
  - Engagement (sessions, retention, feature usage)
  - Quality (bugs, crashes, latency)
  - Business impact (retention, revenue, NPS)
- **Retrospective:** What went well? What didn't? Action items for next sprint

**Handoff Rituals:**
- **Daily:** Async standup updates (Slack #sprint-updates)
- **Weekly:** Sprint progress review (Friday 3 PM, 30 min)
- **Bi-weekly:** Sprint planning + sprint review (Monday + Friday)
- **Quarterly:** Product strategy offsite (1 day, align on roadmap)

---

### Workflow 2: Sales ↔ Customer Success (Customer Handoff)

**Purpose:** Ensure seamless customer experience from sale to success

**Phase 1: Opportunity Qualification (Sales → Sales)**
- **Trigger:** Prospect requests demo or trial
- **Qualification Criteria (BANT):**
  - **Budget:** Do they have budget? (Can they afford $15K-50K/year?)
  - **Authority:** Are you talking to the decision-maker? (Team Lead, VP People, CHRO)
  - **Need:** Do they have the pain we solve? (Team conflict, turnover, low engagement)
  - **Timeline:** Can they buy in <90 days? (or is this a 2026 project?)
- **Output:** Qualified opportunity in Salesforce (Stage: "Qualified")

**Phase 2: Discovery Call (Sales → Prospect)**
- **Duration:** 30 minutes
- **Agenda:**
  1. Rapport (5 min) — "Tell me about your team"
  2. Pain discovery (10 min) — "What challenges are you facing?"
  3. PsychSync overview (5 min) — "Here's how we help"
  4. Next steps (10 min) — "Can I show you a demo next week?"
- **Output:** Discovery notes in Salesforce (pain points, use cases, budget, timeline)

**Phase 3: Demo (Sales → Prospect)**
- **Duration:** 45 minutes
- **Structure:**
  1. Hook (5 min) — "70% of teams fail due to people issues"
  2. Discovery recap (5 min) — "You mentioned [pain], let me show you how we solve that"
  3. Demo (20 min) — Live walkthrough of relevant features (Team Map, Conflict Prediction, Playbooks)
  4. Social proof (5 min) — "Here's how [Customer] solved this problem"
  5. Next steps (10 min) — "Can we get started next week?"
- **Output:** Demo feedback logged (interested, objections, timeline to close)

**Phase 4: Proposal & Negotiation (Sales → Prospect)**
- **Trigger:** Prospect requests pricing or contract
- **Deliverables:**
  - Proposal (PDF or via Salesforce CPQ)
  - Contract (MSA, SOW, DPA — if enterprise)
  - Security questionnaire (if enterprise)
- **Timeline:** 2-5 days (depending on deal complexity)

**Phase 5: Closed-Won → CS Handoff (Sales → CS)**
- **Timing:** Within 24 hours of deal close
- **Handoff Meeting:** 30 min (AE + CSM)
- **Handoff Document:** (See template below)
- **Salesforce Handoff:** AE updates opportunity (Stage: "Closed Won"), assigns CSM owner

**CS Handoff Template:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  CUSTOMER HANDOFF DOCUMENT                                              │
├─────────────────────────────────────────────────────────────────────────┤
│  Customer Name: [Company]                                               │
│  Deal Size: [$XX,XXX ARR]                                               │
│  Tier: [Starter / Team / Enterprise]                                    │
│  Deal Close Date: [Date]                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  BUYING TEAM                                                            │
│  Economic Buyer: [Name, Title]                                         │
│  Technical Buyer: [Name, Title] (if applicable)                         │
│  User Champion: [Name, Title]                                           │
│  Detractor: [Name, Title] (if any)                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  WHY THEY BOUGHT                                                         │
│  Primary Pain Point: [Conflict / Turnover / Engagement / Scaling]       │
│  Secondary Pain Points: [List]                                          │
│  Key Use Cases: [List 3-5 specific use cases discussed in sales cycle]  │
│  Success Metrics: [What metrics will they track? Engagement, Retention] │
├─────────────────────────────────────────────────────────────────────────┤
│  IMPLEMENTATION PLAN                                                     │
│  Go-Live Date: [Target date]                                            │
│  Users: [XX users, XX teams]                                            │
│  Integration Needs: [Slack, Teams, SSO, SCIM, etc.]                     │
│  Training Needs: [Onboarding call, webinar, custom training?]           │
│  Custom Requirements: [Any special requests?]                           │
├─────────────────────────────────────────────────────────────────────────┤
│  RISK FACTORS                                                            │
│  High-Risk Factors: [e.g., Detractor in procurement, tight timeline]    │
│  Mitigation Plan: [How will we address risks?]                          │
├─────────────────────────────────────────────────────────────────────────┤
│  AE NOTES                                                               │
│  [Any additional context for CSM — personality, preferences, warnings]  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Phase 6: Customer Onboarding (CS → Customer)**
- **Timeline:** Days 1-30 after deal close
- **Milestones:**
  - **Day 1:** Welcome email + account setup (CSM)
  - **Day 3:** Kickoff call (30 min) — Meet team, set goals, timeline
  - **Day 7:** First assessment completed (Customer)
  - **Day 14:** Team Personality Map viewed (Customer)
  - **Day 30:** Value realized — Conflict reduced, engagement improved (Customer)
- **CSM Role:** Guide customer, remove friction, celebrate wins

**Phase 7: Ongoing Success (CS → Customer)**
- **Cadence:**
  - **Weeks 1-4:** Weekly check-ins (15 min, async preferred)
  - **Months 2-3:** Bi-weekly check-ins (30 min)
  - **Month 4+:** Monthly check-ins (30 min) + Quarterly Business Reviews (QBRs)
- **QBR Agenda (Quarterly, 60 min):**
  1. Executive summary (10 min) — "Here's your impact this quarter"
  2. Metric review (20 min) — Engagement, retention, feature adoption
  3. Success stories (10 min) — "Here's what worked well"
  4. Roadmap preview (10 min) — "Here's what's coming"
  5. Feedback (10 min) — "What can we do better?"

**Handoff Rituals:**
- **Weekly:** Sales-CS sync (Monday 4 PM, 30 min) — Review pipeline, handoffs, at-risk accounts
- **Monthly:** CS leadership reviews (Friday 3 PM, 60 min) — Review churn, retention, expansion
- **Quarterly:** Sales-CS offsite (1 day) — Align on strategy, resolve friction

---

### Workflow 3: Product ↔ Sales (Feature Feedback)

**Purpose:** Ensure product builds what customers will buy

**Phase 1: Customer Feedback Collection (Sales → Product)**
- **Channels:**
  - **Salesforce:** AE logs feature requests in opportunity notes
  - **Slack #sales-feedback:** AE posts real-time feedback from calls
  - **Weekly Sales Call Review:** AE shares recording/note from prospect call (Fridays 2 PM)
- **Feedback Template:**
  ```
  Customer: [Company]
  Pain Point: [What problem are they trying to solve?]
  Requested Feature: [What did they ask for?]
  Value: [How much would they pay for this? Deal impact?]
  Frequency: [How many customers have asked for this?]
  ```

**Phase 2: Feedback Synthesis (Product → Sales)**
- **Cadence:** Monthly feedback review (Last Friday of month, 60 min)
- **Attendees:** PM, Sales Leadership, AEs (rotating)
- **Process:**
  1. Review all feedback from past month (categorize by theme)
  2. Identify top 5 requested features (by frequency + deal impact)
  3. Prioritize using R-Factor score (see `QUARTERLY_INNOVATION_ROADMAP.md`)
  4. Communicate decisions (build, backlog, decline) to sales team
- **Output:** Updated product roadmap (shared with sales team)

**Phase 3: Roadmap Communication (Product → Sales)**
- **Cadence:** Quarterly roadmap presentation (First Monday of quarter, 60 min)
- **Audience:** All AEs, Sales Leadership, CS Leadership
- **Agenda:**
  1. Last quarter recap (what we shipped, what worked, what didn't)
  2. This quarter roadmap (what we're building, why, when it launches)
  3. How to sell it (feature positioning, objections, ROI)
  4. Q&A

**Phase 4: Sales Enablement (Product → Sales)**
- **Trigger:** New feature launch
- **Deliverables:**
  - **Sales Battle Card:** Feature overview, benefits, objections, demo script
  - **Demo Recording:** 5-minute walkthrough (hosted on YouTube/Loom)
  - **ROI Calculator:** Spreadsheet to show customer value
  - **Competitive Comparison:** How we compare to [Competitor] on this feature
- **Training:** Live training session (30 min) + recording + quiz (pass with 80%)

**Phase 5: Field Feedback Loop (Sales → Product)**
- **Trigger:** After AE sells new feature 3-5 times
- **Format:** Quick feedback note in Slack #sales-feedback
- **Template:** "Sold [Feature] to [Customer]. They loved [X], but [Y] was confusing. Suggestion: [Z]"
- **PM Action:** Review feedback, iterate on positioning, update battle card

**Handoff Rituals:**
- **Weekly:** Sales call review (Friday 2 PM, 30 min) — AE shares prospect feedback
- **Monthly:** Feedback synthesis + roadmap update (Last Friday, 60 min)
- **Quarterly:** Roadmap presentation + sales enablement (First Monday, 60 min)

---

### Workflow 4: Product ↔ Customer Success (Retention Insights)

**Purpose:** Build features that drive retention, not just acquisition

**Phase 1: Churn Analysis (CS → Product)**
- **Trigger:** Customer churns (cancels subscription)
- **Churn Review Ticket:** CSM creates ticket in Zendesk/Linear
- **Churn Analysis Template:**
  ```
  Customer: [Company]
  ARR at Risk: [$XX,XXX]
  Churn Date: [Date]
  Churn Reason: [Price, Product, Fit, Competition, Out of Business]
  Primary Pain Point: [What went wrong?]
  Could We Have Prevented This? [Yes/No — How?]
  Feature Requests: [What could have saved this customer?]
  ```

**Phase 2: Monthly Retention Review (CS + Product)**
- **Cadence:** First Monday of month, 60 min
- **Attendees:** PM, CS Leadership, CSMs (rotating)
- **Agenda:**
  1. Retention metrics review (churn rate, NRR, logo churn)
  2. Churn analysis (top 5 churn reasons, what could have prevented churn)
  3. At-risk accounts (customers likely to churn, intervention plan)
  4. Feature requests (from churned customers + at-risk customers)
- **Output:** Product insights (features to build, features to kill, gaps to address)

**Phase 3: Customer Advisory Board (CS + Product + Customers)**
- **Cadence:** Quarterly (Last Wednesday of quarter, 2 hours)
- **Attendees:** 10-15 customer representatives (mix of Team + Enterprise tiers)
- **Agenda:**
  1. PsychSync roadmap preview (what we're planning)
  2. Customer feedback (what they love, hate, want)
  3. Co-creation (workshop on 1-2 features in development)
  4. Networking (customers learn from each other)
- **Output:** Product validation (we're building the right things) + customer advocates

**Phase 4: Beta Testing (Product → CS → Customers)**
- **Trigger:** New feature ready for beta
- **Selection:** CS identifies 10-20 beta customers (high engagement, positive relationship)
- **Process:**
  1. CS invites customers to beta (email/Slack)
  2. Product provides beta build + instructions
  3. CS onboard beta customers (15-min call)
  4. Product gathers feedback (Slack #beta-feedback, surveys)
  5. Product iterates based on feedback
- **Timeline:** 2-4 weeks before GA launch

**Handoff Rituals:**
- **Monthly:** Retention review (First Monday, 60 min)
- **Quarterly:** Customer advisory board (Last Wednesday, 2 hours)
- **Quarterly:** Beta customer selection + onboarding (ongoing)

---

### Workflow 5: Data Science ↔ Engineering (ML to Production)

**Purpose:** Turn ML models into production features that are fast, reliable, and scalable

**Phase 1: Model Development (Data Science → Data Science)**
- **Output:** Trained model + model card (documenting performance, biases, limitations)
- **Model Card Template:**
  ```
  Model Name: [e.g., Conflict Prediction Model v2.1]
  Model Type: [Classification / Regression / Clustering]
  Training Data: [Dataset size, time period, sources]
  Performance: [Accuracy, Precision, Recall, F1, AUC]
  Biases: [Known biases, e.g., better for US vs. EU teams]
  Limitations: [When model fails, e.g., small teams <5 people]
  Ethical Considerations: [Potential harms, mitigation]
  ```

**Phase 2: Model Review (Data Science + Engineering + Product)**
- **Cadence:** Bi-weekly model review (Fridays 10 AM, 60 min)
- **Attendees:** Data scientists, ML engineers, PM, Tech Lead
- **Agenda:**
  1. Model presentation (data scientist explains model)
  2. Technical review (engineers assess feasibility, performance, scalability)
  3. Product review (PM assesses user value, UX implications)
  4. Go/No-Go decision (ship to production, iterate, or kill)

**Phase 3: Productionization (Engineering → Data Science)**
- **Output:** Model deployed to production (API endpoint, batch job, or real-time inference)
- **Technical Requirements:**
  - **Performance:** p95 latency <500ms (for real-time models)
  - **Scalability:** Handle 10x current load
  - **Monitoring:** Model accuracy, drift, latency, error rate
  - **Rollback:** Ability to revert to previous model version if degraded
- **Timeline:** 2-3 sprints (4-6 weeks) from model approval to production

**Phase 4: Monitoring & Retraining (Data Science + Engineering)**
- **Cadence:** Weekly model performance review (Fridays 11 AM, 30 min)
- **Metrics Tracked:**
  - **Accuracy:** Is model performance degrading?
  - **Drift:** Is data distribution changing?
  - **Latency:** Is inference slowing down?
  - **Error Rate:** Are predictions failing?
- **Retraining Trigger:** If accuracy drops >5% or drift detected → Retrain model

**Phase 5: A/B Testing (Data Science + Product + Engineering)**
- **Trigger:** New model version ready
- **Process:**
  1. Deploy model B to 10% of users (feature flag)
  2. Run for 2-4 weeks
  3. Compare metrics (accuracy, user engagement, business impact)
  4. If model B wins → Roll out to 100%
  5. If model B loses → Roll back to model A, investigate why
- **Owner:** Data scientist (runs experiment), PM (approves rollout)

**Handoff Rituals:**
- **Bi-weekly:** Model review (Friday 10 AM, 60 min)
- **Weekly:** Model monitoring (Friday 11 AM, 30 min)
- **Quarterly:** Model retraining (as needed, based on drift)

---

### Workflow 6: Marketing ↔ Product (Launch Alignment)

**Purpose:** Launch features in a way that drives acquisition, adoption, and retention

**Phase 1: Launch Planning (Product → Marketing)**
- **Trigger:** Feature is 3 weeks from launch
- **Output:** Launch brief (document for marketing team)
- **Launch Brief Template:**
  ```
  Feature Name: [e.g., Conflict Early-Warning]
  Launch Date: [Date]
  Launch Tier: [Tier 1 / Tier 2 / Tier 3] — See PRODUCT_ANNOUNCEMENT_PLAYBOOK.md

  Value Proposition: [Why should customers care?]
  Target Audience: [Who is this for? Team Leads, HRBPs, C-Suite?]
  Key Benefits: [Top 3 benefits]
  Use Cases: [3-5 specific use cases]

  Customer Stories: [Any early adopters we can quote?]
  ROI Metrics: [What's the quantifiable value?]

  Competitive Differentiation: [How is this better than [Competitor]?]
  Launch Goals: [Adoption, engagement, revenue targets]
  ```

**Phase 2: Asset Creation (Marketing → Product)**
- **Deliverables (Tier 1 Launch):**
  - Blog post (1,500-2,000 words)
  - Announcement email (subject lines, body)
  - Social posts (LinkedIn, Twitter/X)
  - Press release (if media-worthy)
  - Graphics (screenshots, GIFs, diagrams)
  - Demo video (2-3 minutes, voice-over)
- **Review Cycle:** Product reviews all assets for accuracy (3-5 days)

**Phase 3: Launch Execution (Marketing + Product)**
- **Day-of-Launch:** See `PRODUCT_ANNOUNCEMENT_PLAYBOOK.md`
- **Roles:**
  - **Marketing:** Publish blog, send email, post social, manage press
  - **Product:** Enable in-app notifications, verify feature is live, support QA
  - **Sales:** Announce to prospects (personal outreach)
  - **CS:** Announce to customers (personal outreach)

**Phase 4: Post-Launch Analysis (Marketing + Product)**
- **Timing:** 7 days after launch
- **Metrics Review:**
  - **Acquisition:** Email open rate, CTR, blog views, social engagement
  - **Adoption:** Feature sign-ups, active users, teams activated
  - **Engagement:** Feature usage, session frequency, retention
  - **Business Impact:** PQLs, demos booked, deals influenced, revenue
- **Retrospective:** What worked? What didn't? Learnings for next launch

**Handoff Rituals:**
- **Monthly:** Launch calendar review (Last Monday, 30 min) — Plan upcoming launches
- **Per Launch:** Launch brief delivery (3 weeks before launch)
- **Per Launch:** Asset review (1 week before launch)
- **Post-Launch:** Launch review (7 days after launch, 30 min)

---

### Workflow 7: Executive ↔ Company (Strategy Alignment)

**Purpose:** Ensure entire company is aligned on vision, strategy, and execution

**Phase 1: Quarterly Strategy Planning (Executive)**
- **Cadence:** Quarterly planning (2 weeks before quarter start)
- **Attendees:** CEO, CPO, CTO, VP Sales, VP CS, Head of Data Science
- **Output:** Quarterly OKRs (Objectives and Key Results)
- **OKR Template:**
  ```
  Objective: [Qualitative goal — e.g., "Reduce churn to 12%"]
  Key Results:
    - KR1: 90-day retention → 85% (from 60%)
    - KR2: Team Personality Map adoption → 80%
    - KR3: Slack Integration adoption → 60%
    - KR4: DAU/MAU ratio → 50%
  ```

**Phase 2: Company All-Hands (Executive → Company)**
- **Cadence:** Monthly (First Friday, 60 min)
- **Agenda:**
  1. Vision & Strategy (10 min) — CEO: Where we're going, why it matters
  2. Product Updates (15 min) — CPO: What we shipped, what's next
  3. Customer Stories (10 min) — CS/Sales: Customer wins, testimonials
  4. Company Metrics (10 min) — CEO: ARR, teams, retention, NPS
  5. Recognition (10 min) — Celebrate wins, shout outs to team members
  6. Q&A (5 min) — Ask me anything (AMA)

**Phase 3: Team Syncs (Executive → Teams)**
- **Cadence:** Bi-weekly (Every other Monday, 30 min per team)
- **Format:** 1:1s with direct reports (CEO with VPs, VPs with managers)
- **Agenda:**
  1. What's going well? (Wins, progress)
  2. What's blocking you? (Friction, needs)
  3. How can I help? (Support, resources)
  4. Feedback for me (Leadership improvement)

**Phase 4: Weekly Executive Team Meeting (Executive)**
- **Cadence:** Weekly (Wednesdays 2-3 PM, 60 min)
- **Attendees:** CEO, CPO, CTO, VP Sales, VP CS, Head of Data Science
- **Agenda:**
  1. Metrics review (10 min) — Quick pulse on ARR, teams, retention
  2. OKR progress (20 min) — Each exec: green/yellow/red on OKRs
  3. Blockers (15 min) — What's blocking execution? How to unblock?
  4. Decisions (10 min) — Make decisions (don't defer)
  5. Updates (5 min) — Quick company announcements

**Phase 5: Quarterly Board Meeting (Executive → Board)**
- **Cadence:** Quarterly (End of quarter, 90 min)
- **Attendees:** CEO, CPO, CTO, VP Sales, Board Members
- **Agenda:** See `BOARD_PRESENTATION_DECK.md`
- **Output:** Board approval (strategy, budget, next quarter plan)

**Handoff Rituals:**
- **Quarterly:** Strategy planning (2 weeks before quarter)
- **Monthly:** Company all-hands (First Friday, 60 min)
- **Bi-weekly:** 1:1 syncs (Ongoing)
- **Weekly:** Exec team meeting (Wednesday 2-3 PM, 60 min)
- **Quarterly:** Board meeting (End of quarter, 90 min)

---

## 📅 Cross-Functional Rituals (Company-Wide)

### Daily Rituals
- **Async Standups:** All teams post updates by 10 AM (Slack #standups)
- **Bug triage:** Engineering + QA review new bugs (2 PM, 15 min)

### Weekly Rituals
- **Monday:**
  - Sprint planning (Product + Engineering, 9-11 AM)
  - Sales-CS sync (4 PM, 30 min)
- **Tuesday:**
  - Model review (Data Science + Engineering, 10 AM)
- **Wednesday:**
  - Exec team meeting (2-3 PM, 60 min)
- **Thursday:**
  - Model monitoring (11 AM, 30 min)
- **Friday:**
  - Sprint review (Product + Engineering, 3 PM, 60 min)
  - Weekly risk review (All execs, 3 PM, 30 min)
  - Sales call review (2 PM, 30 min)

### Monthly Rituals
- **First Week:**
  - Company all-hands (First Friday, 60 min)
  - Retention review (First Monday, 60 min)
- **Last Week:**
  - Feedback synthesis (Last Friday, 60 min)
  - Launch calendar review (Last Monday, 30 min)
- **Monthly:** Executive product reports (see `MONTHLY_EXECUTIVE_PRODUCT_REPORTS.md`)

### Quarterly Rituals
- **Quarter Start:**
  - Quarterly strategy planning (2 weeks before quarter)
  - Roadmap presentation (First Monday, 60 min)
  - OKR kickoff (First week, all teams)
- **Quarter End:**
  - Board meeting (Last week, 90 min)
  - Quarterly retrospective (Last week, 60 min)
  - Customer advisory board (Last Wednesday, 2 hours)
  - Performance reviews (Last 2 weeks)

---

## 🛠️ Collaboration Tools & Stack

### Communication
- **Slack:** Primary communication tool
  - #general (company-wide announcements)
  - #standups (daily standup updates)
  - #sprint-updates (product + engineering)
  - #sales-feedback (feature requests from sales)
  - #cs-feedback (customer feedback)
  - #random (watercooler, social)
- **Email:** External communication only (customers, partners)
- **Zoom:** Video meetings (recorded, stored in Loom library)

### Project Management
- **Linear:** Engineering tasks, bugs, sprints
- **Aha! (or Notion):** Product roadmap, PRDs, strategy docs
- **Salesforce:** Sales pipeline, customer accounts, handoffs
- **Zendesk:** Customer support, tickets, churn analysis

### Documentation
- **Google Docs:** Collaborative documents (PRDs, meeting notes)
- **Notion:** Knowledge base, playbooks, templates
- **GitHub/GitLab:** Code, PRDs, technical docs
- **Loom:** Video recordings (demos, training, tutorials)

### Design
- **Figma:** UI/UX design, prototypes, design system
- **Miro:** Collaborative whiteboarding (brainstorming, retrospectives)

### Analytics
- **Mixpanel:** Product analytics (funnels, cohorts, retention)
- **Tableau (or Looker):** Business intelligence dashboards
- **Amplitude:** User behavior analytics (optional, alternatives to Mixpanel)

---

## 🎯 Decision-Making Framework

### Decision Types (RAPI Framework)

**R - Reversible Decisions (Make Fast)**
- **Examples:** Feature name, button color, email copy
- **Process:** Individual owner decides, no consensus needed
- **Timeline:** Decide in <1 hour, execute immediately
- **Reversal:** If wrong, change it next iteration

**A - App reversible Decisions (Consult + Decide)**
- **Examples:** Sprint scope, feature prioritization, hiring
- **Process:** Owner consults stakeholders, then decides
- **Timeline:** Decide in <1 day, execute next sprint
- **Reversal:** If wrong, can be undone with some effort

**P - Painful Decisions (Consensus + Decide)**
- **Examples:** Pricing changes, platform architecture, layoffs
- **Process:** Discuss with all stakeholders, build consensus, owner decides
- **Timeline:** Decide in <1 week, execute next quarter
- **Reversal:** If wrong, very painful to undo (but possible)

**I - Irreversible Decisions (Study + Decide Slowly)**
- **Examples:** Fundraising (sell equity), rebranding, shut down product line
- **Process:** Extensive research, multiple discussions, CEO decides
- **Timeline:** Decide in <1 month, execute next year
- **Reversal:** If wrong, cannot undo (or extremely painful)

**Decision Rights:**
- **Product Features:** CPO decides (consults Engineering, Sales, CS)
- **Technical Architecture:** CTO decides (consults Engineering, Data Science)
- **Pricing:** CEO decides (consults CPO, VP Sales, VP Marketing)
- **Hiring:** Hiring manager decides (consults team, HR)
- **Firing:** CEO decides (consults Legal, HR)
- **Strategy:** CEO decides (consults exec team, then board)

---

## ⚠️ Conflict Resolution

### When Teams Disagree

**Scenario 1: Product vs. Engineering (Scope vs. Timeline)**
- **Conflict:** PM wants 5 features, Engineering says only 3 fit in sprint
- **Resolution:**
  1. Engineering provides effort estimates (story points) for all 5 features
  2. PM prioritizes top 3 features (using R-Factor score)
  3. PM moves 2 lowest-priority features to next sprint
  4. Document decision in sprint retrospective (learn for next time)

**Scenario 2: Sales vs. CS (Handoff Friction)**
- **Conflict:** CS says Sales oversold features, Sales says CS is failing customers
- **Resolution:**
  1. Review 5 recent deals (what was promised vs. delivered)
  2. Identify root cause (sales overpromising? CS under-delivering?)
  3. Create handoff checklist (what must be documented before handoff)
  4. Train AEs on handoff process (role-play in sales meeting)
  5. Review handoff quality weekly (sales-CS sync)

**Scenario 3: Product vs. Sales (Feature Requests)**
- **Conflict:** Sales wants Feature X now, Product says it's not on roadmap
- **Resolution:**
  1. Sales documents customer request (using feedback template)
  2. Product reviews request (R-Factor scoring, impact vs. effort)
  3. Product communicates decision (build, backlog, decline) with rationale
  4. If decline → Sales arms AE with "how to handle objection" talking points
  5. If build → Product communicates timeline (when it will ship)

**Scenario 4: Engineering vs. Data Science (ML Productionization)**
- **Conflict:** Data Science wants Model B, Engineering says it's not production-ready
- **Resolution:**
  1. Model review meeting (bi-weekly ritual)
  2. Engineers document technical concerns (latency, scalability, monitoring)
  3. Data scientists iterate on model (address concerns)
  4. Re-review at next model review meeting
  5. If still blocked → Escalate to CTO (decides: ship now, iterate more, or kill)

**Escalation Path:**
1. **Peer-to-peer:** Try to resolve directly (1:1 conversation)
2. **Manager involvement:** Escalate to team leads/managers
3. **Exec involvement:** Escalate to CPO/CTO/VP Sales/etc.
4. **CEO decision:** If still unresolved, CEO decides (final say)

---

`★ Insight ─────────────────────────────────────`

**Rituals Are Culture:** The rituals we define (daily standups, weekly reviews, quarterly planning) aren't just processes — they're our culture. If we respect the rituals, we build a culture of accountability, transparency, and collaboration. If we skip them, we build a culture of chaos and fire-fighting.

**Async First, Sync Second:** We've explicitly designed workflows to be async-first (Slack updates, documentation, recordings). This respects deep work time and scales across time zones. Meetings are for debate, relationship-building, and decisions — not for status updates (those should be async).

**Handoffs Are Where Balls Drop:** The highest-risk moments in any organization are handoffs (sales→CS, product→engineering, engineering→marketing). We've documented handoff templates, rituals, and checklists to prevent balls from dropping. A 10-minute handoff call saves 10 hours of firefighting later.

`─────────────────────────────────────────────────`

---

*Last Updated: January 12, 2025*
*Next Workflow Review: April 12, 2025 (Quarterly Process Optimization)*
*All Templates Available in: `/docs/templates/` (create if not exists)*
