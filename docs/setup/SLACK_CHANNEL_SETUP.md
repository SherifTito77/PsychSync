# Slack Channel Setup Guide
**Collaboration Workflows Configuration**

**Date:** January 12, 2025
**Purpose:** Configure Slack channels for cross-team collaboration workflows

---

## 🎯 Objective

Implement the Slack channel structure defined in `CROSS_TEAM_COLLABORATION_WORKFLOWS.md`, enabling:
- Async communication (respect deep work time)
- Cross-functional collaboration
- Rapid decision-making
- Knowledge sharing

---

## 📋 Required Channels (All Teams)

### Company-Wide Channels
| Channel | Purpose | Members | Posting Guidelines |
|---------|---------|---------|-------------------|
| #general | Company-wide announcements | Everyone | CEO announcements, company wins |
| #standups | Daily standup updates | Everyone | Async standups (by 10 AM PT) |
| #random | Watercooler, social | Everyone | Non-work chat, memes, pets |
| #shoutouts | Appreciation and recognition | Everyone | Celebrate wins, thank teammates |

### Team Channels
| Channel | Purpose | Members |
|---------|---------|---------|
| #engineering | Engineering discussions | Engineers + CTO |
| #product | Product discussions | PM + Design + CPO |
| #sales | Sales discussions | AEs + VP Sales |
| #customer-success | CS discussions | CSMs + VP CS |
| #marketing | Marketing discussions | Marketing team |
| #datascience | Data science + ML | Data scientists + ML engineers |
| #leadership | Executive discussions | C-level + VPs |

### Cross-Functional Channels
| Channel | Purpose | Members |
|---------|---------|---------|
| #sprint-updates | Sprint progress updates | Engineering + Product + Design |
| #sales-feedback | Customer feedback from sales calls | Sales + Product + CS |
| #cs-feedback | Customer feedback from support | CS + Product + Engineering |
| #risk-management | Risk tracking (weekly reviews) | All execs + risk owners |
| #announcements | Feature launches | Everyone (auto-post from bot) |

### Project Channels (Create as Needed)
| Channel | Purpose | Duration |
|---------|---------|----------|
| #sprint-1-team-map | Sprint 1: Team Personality Map | Weeks 1-2 |
| #sprint-2-slack | Sprint 2: Slack Integration | Weeks 3-4 |
| #sprint-3-conflict | Sprint 3: Conflict Prediction | Weeks 5-6 |
| #launch-team-map | Launch coordination: Team Map | 1 week around launch |
| #launch-slack | Launch coordination: Slack | 1 week around launch |

---

## 🔧 Setup Instructions

### Step 1: Create Channels

**In Slack:**
1. Click `+` next to `Channels` in sidebar
2. Select `Create a channel`
3. Follow table above to create all channels

**For Large Teams (50+ members), use Slack CLI:**
```bash
# Create all channels at once
slack channels create #general
slack channels create #standups
slack channels create #random
# ... etc
```

### Step 2: Set Channel Purposes

**For each channel, set purpose:**
1. Click channel name → `Channel Details`
2. Click `Edit` next to purpose
3. Add purpose (see table above)
4. Add topic if needed

**Example for #standups:**
- **Purpose:** Daily async standup updates. Post by 10 AM PT: yesterday/today/blockers.
- **Topic:** See CROSS_TEAM_COLLABORATION_WORKFLOWS.md for async standup template.

### Step 3: Configure Channel Permissions

**Channel Types:**
- **Public:** `#general`, `#standups`, `#random`, `#shoutouts`
- **Private:** `#leadership`, `#risk-management`
- **Team-Private:** `#sales`, `#customer-success` (if sensitive discussions)

**To Make Channel Private:**
1. Click channel name → `Channel Details`
2. Click `Settings` → `Change to a private channel`
3. Confirm

### Step 4: Set Up Channel Guidelines

**Post this message in each channel (adjust as needed):**

**For #standups:**
```
Welcome to #standups! 🎯

This is our daily async standup channel. Post updates by 10 AM PT.

**Format:**
• Yesterday: [What you did]
• Today: [What you'll do]
• Blockers: [What's blocking you]

**Guidelines:**
• Keep it brief (3-5 bullets max)
• No need to tag anyone (this is your update)
• Read others' updates asynchronously (no need to react to every post)
• If you're blocked, tag the person who can help

Let's respect everyone's deep work time! 🙌
```

**For #sprint-updates:**
```
Welcome to #sprint-updates! 🚀

This channel tracks progress for Sprint [X]: [Sprint name].

**Posting Guidelines:**
• Engineers: Post when you start/finish a task
• Tag @cso when ready for QA review
• Tag @pso when ready for product review
• Blockers: Post immediately, don't wait

**Daily Updates (Friday 3 PM):**
• Sprint progress review (30 min)
• Demo completed features (all engineers)
• QA sign-off
• Plan next sprint

See Q1_ENGINEERING_ROADMAP.md for full sprint details.
```

**For #sales-feedback:**
```
Welcome to #sales-feedback! 💬

This channel is for AEs to share feedback from sales calls with Product and CS.

**What to Post:**
• Feature requests from prospects
• Objections heard (what's blocking deals?)
• Competitive intelligence (who are we losing to?)
• Customer wins (why did they buy?)

**Format:**
**Customer:** [Company Name]
**Pain Point:** [What problem are they trying to solve?]
**Requested Feature:** [What did they ask for?]
**Value:** [How much would they pay? Deal impact?]
**Objections:** [What concerns did they raise?]

**How Product & CS Will Use This:**
• Product: Prioritize features based on demand
• CS: Identify churn risks early
• Both: Improve our positioning

Thanks for sharing! 🙏
```

**For #cs-feedback:**
```
Welcome to #cs-feedback! 🎧

This channel is for CSMs to share customer feedback with Product and Engineering.

**What to Post:**
• Churn reasons (why are they leaving?)
• Feature requests (what do they want?)
• Bugs reported (what's broken?)
• Success stories (what do they love?)

**How Engineering Will Use This:**
• Prioritize bug fixes
• Improve UX based on real usage
• Fix friction points in onboarding

**How Product Will Use This:**
• Identify retention risks
• Prioritize feature development
• Improve customer experience

Together we can reduce churn! 📉
```

**For #risk-management:**
```
Welcome to #risk-management! 🚨

This channel tracks our 4 critical risks with weekly reviews.

**The 4 Critical Risks:**
1. Scientific Validity (Owner: @head-of-ds)
2. Data Breach (Owner: @cto)
3. ML Accuracy (Owner: @head-of-ml)
4. Regulatory Compliance (Owner: @gc)

**Weekly Review:**
• Fridays 3 PM PT (30 minutes)
• See RISK_TRACKING_SETUP.md for details
• Come prepared with Week X progress

**Risk Tracker:** [Link to Airtable/Linear/Notion]

Let's stay ahead of these risks! 🎯
```

### Step 5: Set Up Bots & Integrations

**Bot 1: Standup Reminder Bot**
- **Tool:** Slack Workflow Builder (free)
- **Trigger:** Weekdays at 9:30 AM PT
- **Channel:** #standups
- **Message:** "Good morning! 🌅 Remember to post your standup update by 10 AM PT."

**Bot 2: Sprint Review Reminder**
- **Tool:** Slack Workflow Builder
- **Trigger:** Fridays at 2 PM PT
- **Channel:** #sprint-updates
- **Message:** "Sprint review in 1 hour! 🚀 Get your demos ready. See you at 3 PM."

**Bot 3: Weekly Risk Review Reminder**
- **Tool:** Slack Workflow Builder
- **Trigger:** Fridays at 2 PM PT
- **Channel:** #risk-management
- **Message:** "Weekly risk review in 1 hour! 🚨 See risk tracker: [link]. Come prepared with Week X progress."

**Bot 4: GitHub Integration**
- **Tool:** Slack GitHub App
- **Configuration:**
  - Post PRs to: #sprint-updates
  - Post deployments to: #announcements
  - Post security alerts to: #engineering (urgently)

**Bot 5: PagerDuty Integration (Optional)**
- **Tool:** Slack PagerDuty App
- **Configuration:**
  - On-call rotations: #engineering
  - Escalation path: On-call → CTO → CEO
  - Incident alerts: #engineering-incident

### Step 6: Create Channel Directory

**Post in #general:**
```
📖 PsychSync Channel Directory

**Company-Wide:**
#general - Company announcements
#standups - Daily async updates (post by 10 AM PT)
#random - Watercooler, social, fun
#shoutouts - Appreciation and recognition

**Teams:**
#engineering - Engineering discussions
#product - Product + Design discussions
#sales - Sales team discussions
#customer-success - CS team discussions
#marketing - Marketing discussions
#datascience - Data science + ML
#leadership - Executive team

**Cross-Functional:**
#sprint-updates - Sprint progress
#sales-feedback - Customer feedback from sales calls
#cs-feedback - Customer feedback from support
#risk-management - Risk tracking (Fridays 3 PM PT)
#announcements - Feature launches (auto-post)

**Workflows:**
• Daily standups: Post in #standups by 10 AM PT
• Sprint reviews: Fridays 3 PM PT in #sprint-updates
• Risk reviews: Fridays 3 PM PT in #risk-management
• Sales call debriefs: Post in #sales-feedback after calls
• CS feedback: Post in #cs-feedback as issues arise

See CROSS_TEAM_COLLABORATION_WORKFLOWS.md for full details.
```

---

## 🎯 Collaboration Rituals (Slack-Based)

### Daily Rituals
- **Async Standups (Daily 9:30 AM):** Post in `#standups` by 10 AM
- **Bug Triage (Daily 2 PM):** Post critical bugs to `#engineering`

### Weekly Rituals
- **Sprint Planning (Every 2 weeks, Monday 9 AM):** Announce in `#sprint-updates`
- **Sprint Review (Every 2 weeks, Friday 3 PM):** Demo in `#sprint-updates`
- **Weekly Risk Review (Every Friday 3 PM):** Discuss in `#risk-management`
- **Sales Call Review (Every Friday 2 PM):** Share in `#sales-feedback`

### Monthly Rituals
- **Executive Review (First Monday, 2 hours):** See EXECUTIVE_TEAM_REVIEW_AGENDA.md
- **All-Hands (First Friday, 30 min):** CEO announcement in `#general`

---

## ✅ Setup Checklist

### Week 1 Setup
- [ ] All 25+ channels created
- [ ] Channel purposes set
- [ ] Channel guidelines posted
- [ ] Bots configured (4 reminders)
- [ ] GitHub integration connected
- [ ] Channel directory posted in #general

### Week 1 Execution
- [ ] Daily standups happening (async in #standups)
- [ ] Weekly sprint reviews happening (Fridays 3 PM)
- [ ] Weekly risk reviews happening (Fridays 3 PM)
- [ ] Sales feedback being shared (ongoing)
- [ ] CS feedback being shared (ongoing)

### Ongoing Operations
- [ ] New project channels created for each sprint
- [ ] Launch channels created 1 week before feature launch
- [ ] Channel cleanup (archive old sprint channels)
- [ ] Onboarding: New hires added to all channels
- [ ] Offboarding: Departed employees removed from channels

---

## 🔐 Security & Privacy

### Private Channels
- **#leadership:** Sensitive company discussions (financials, M&A, personnel)
- **#risk-management:** Risk scores, mitigation strategies (until declassified)
- **#salary-review:** Compensation discussions (HR + Finance only)

### Sensitive Information
- **Do NOT post in public channels:**
  - Customer names (use pseudonyms)
  - Financial data (unannounced)
  - Personnel issues (use HR channels)
  - Security vulnerabilities (use #engineering-incident, not #engineering)

### Data Retention
- **Public channels:** Retain indefinitely (company knowledge base)
- **Private channels:** Retain 7 years (legal requirement)
- **DMs:** Retain 1 year (then auto-delete)

---

## 📊 Channel Metrics

Track channel health quarterly:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Active users | >80% of company | Slack analytics |
| Daily active channels | >5 | Slack analytics |
| Async standup compliance | >90% | Count posts by 10 AM |
| Response time | <4 hours | Time from @mention to reply |

---

## 📞 Support

**Slack Admin Questions:** [Operations Lead] - [Email]
**Channel Questions:** [CTO] - [Email]
**Process Questions:** CEO - ceo@psychsync.io

---

*Last Updated: January 12, 2025*
*Next Review: Quarterly (assess channel structure and adjust)*
