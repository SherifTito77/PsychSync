# Project Management Tools Setup Guide
**Linear & Jira Configuration for Q1 Engineering Roadmap**

**Date:** January 12, 2025
**Purpose:** Setup project management tools to track Q1 2025 sprints

---

## 🎯 Objective

Configure Linear (preferred) or Jira to manage the Q1 Engineering Roadmap, enabling:
- Sprint planning and tracking
- Task assignment and ownership
- Progress monitoring
- Bug tracking
- Collaboration across engineering team

---

## 📊 Q1 2025 Engineering Roadmap Overview

**6 Sprints, 12 Weeks:**
- Sprint 1 (Weeks 1-2): Team Personality Map MVP
- Sprint 2 (Weeks 3-4): Slack Integration MVP
- Sprint 3 (Weeks 5-6): Conflict Prediction Alpha
- Sprint 4 (Weeks 7-8): Manager Playbooks v1
- Sprint 5 (Weeks 9-10): Integration & Polish
- Sprint 6 (Weeks 11-12): Launch & Measurement

**Goal:** 85% 90-day retention (up from 60%)

---

## 🔧 Linear Setup (Recommended)

### Step 1: Account Creation
1. Go to https://linear.app
2. Sign up with email (use work email: [name]@psychsync.io)
3. Create workspace: "PsychSync Engineering"
4. Invite team members (see `Q1_ENGINEERING_ROADMAP.md` for hiring plan)

### Step 2: Workspace Configuration

**Settings → Workspace:**
- **Workspace Name:** PsychSync Engineering
- **Workspace URL:** psychsync.linear.app
- **Time Zone:** Pacific Time (PT)
- **Date Format:** MM/DD/YYYY

**Settings → Teams:**
Create teams:
- **Team:** Engineering (all engineers)
- **Sub-teams:** Backend, Frontend, Data Science, ML
- **Labels:** Add team labels to issues

**Settings → Labels:**
Create issue labels:
- `priority-critical` - 🔴 P0 (blocking, fix immediately)
- `priority-high` - 🟠 P1 (high priority, fix this sprint)
- `priority-medium` - 🟡 P2 (medium priority, fix next sprint)
- `priority-low` - 🟢 P3 (low priority, backlog)
- `feature` - New feature development
- `bug` - Bug fix
- `enhancement` - Performance/UX improvement
- `tech-debt` - Technical debt payoff
- `documentation` - Documentation update

**Settings → Statuses:**
Create custom statuses:
- `Backlog` - Not started
- `Todo` - Planned, not assigned
- `In Progress` - Actively working on
- `In Review` - Code review pending
- `Done` - Complete and deployed
- `Blocked` - Waiting on something/someone
- `Canceled` - No longer pursuing

### Step 3: Create Projects

**Project 1: Q1 2025 Engineering Roadmap**
- **Type:** Roadmap
- **Description:** Q1 2025 features to reduce churn from 20% to 12%
- **Target:** Complete all 6 sprints by end of Q1

**Project 2: Sprint 1 (Weeks 1-2)**
- **Type:** Iteration
- **Description:** Team Personality Map MVP
- **Start Date:** Week 1 Monday
- **End Date:** Week 2 Friday
- **Target:** Team aggregation API, AI-generated insights, frontend visualization

**Project 3: Sprint 2 (Weeks 3-4)**
- **Type:** Iteration
- **Description:** Slack Integration MVP
- **Start Date:** Week 3 Monday
- **End Date:** Week 4 Friday
- **Target:** OAuth integration, notifications, smart routing

**Projects 4-9:** Create remaining sprints (see pattern above)

### Step 4: Import Sprint Tasks

**For Sprint 1 (Team Personality Map MVP):**

Create issues from `Q1_ENGINEERING_ROADMAP.md` Sprint 1 tasks:

**Backend:**
- BE-101: Design team aggregation API endpoint
- BE-102: Implement team personality calculation service
- BE-103: Create database schema for team_personality_maps table
- BE-104: Write migration scripts
- BE-105: Implement AI-generated insights service (GPT-4 integration)
- BE-106: Create Pydantic schemas for API responses
- BE-107: Write unit tests for aggregation service

**Frontend:**
- FE-101: Design Team Personality Map visualization component
- FE-102: Build team radar chart (spider chart)
- FE-103: Create team comparison view component
- FE-104: Implement insights display component
- FE-105: Add loading states and error handling
- FE-106: Integrate with backend API
- FE-107: Write component tests (React Testing Library)

**Data Science:**
- DS-101: Validate team aggregation algorithm
- DS-102: Create rule-based insights fallback
- DS-103: Test GPT-4 prompt engineering
- DS-104: Benchmark insights quality
- DS-105: Document methodology

**Each Issue Should Have:**
- **Title:** [CODE-###] [Description]
- **Description:** Acceptance criteria, technical notes, dependencies
- **Assignee:** [Engineer name]
- **Labels:** `[backend/frontend/data-science]`, `[feature]`, `priority-[high/medium/low]`
- **Status:** `Todo` → `In Progress` → `In Review` → `Done`
- **Estimate:** Story points (3, 5, 8, 13)
- **Due Date:** Sprint end date
- **Project:** Sprint 1

**Example Issue:**
```
Title: BE-102: Implement team personality calculation service

Description:
Create service to aggregate individual personality assessments into team-level insights.

Requirements:
- Query all assessments for a team
- Aggregate by Big Five dimensions (OCEAN)
- Calculate: avg, min, max, std_dev, distribution
- Generate strengths and gaps
- Calculate compatibility and diversity scores
- Cache results in team_personality_maps table

Acceptance Criteria:
- [ ] Service returns TeamPersonalityMap object
- [ ] Handles teams with 0 assessments (returns None)
- [ ] Handles teams with 1 assessment (graceful degradation)
- [ ] Calculates accurate statistics (validated with test data)
- [ ] Updates cache after calculation
- [ ] Unit tests cover 80%+ of code paths

Dependencies:
- BE-103: Database schema must be created first

Estimate: 5 story points
Assignee: [Senior Backend Engineer]
Labels: backend, feature, priority-high
Project: Sprint 1
Due Date: [Sprint end date]
```

### Step 5: Configure Views

**View 1: Sprint Board**
- **Type:** Board view
- **Group by:** Status
- **Filter:** Project = Sprint 1
- **Columns:** Backlog, Todo, In Progress, In Review, Done, Blocked

**View 2: My Issues**
- **Type:** List view
- **Filter:** Assignee = [Your name]
- **Sort:** Due date ascending

**View 3: Bug Triage**
- **Type:** Board view
- **Filter:** Labels = `bug`, `priority-critical` or `priority-high`
- **Group by:** Priority

**View 4: Sprint Progress**
- **Type:** Roadmap view
- **Filter:** Project = Sprint 1
- **Group by:** Status

### Step 6: Set Up Automations

**Automation 1: Auto-assign to Sprint**
- **Trigger:** Issue created with label `feature` or `bug`
- **Action:** Add to active sprint project
- **Condition:** If issue is not assigned

**Automation 2: Sprint Review Reminder**
- **Trigger:** Issue status = `In Review`
- **Action:** Notify #engaging channel
- **Message:** "Pull request ready for review: [Issue title]"

**Automation 3: Blocked Issues Escalation**
- **Trigger:** Issue status = `Blocked` for >2 days
- **Action:** Notify CTO + assignee
- **Message:** "Issue still blocked: [Issue title]. Please unblock or reassign."

---

## 🔧 Jira Setup (Alternative)

### Step 1: Account Creation
1. Go to https://jira.atlassian.com
2. Sign up for Jira Software (free for up to 10 users)
3. Create site: "PsychSync Engineering"
4. Invite team members

### Step 2: Project Configuration

**Create Project:**
- **Project Type:** Scrum software development
- **Project Name:** PsychSync Q1 2025
- **Key:** PSYCH-Q1

**Configure Scrum:**
- **Sprint Duration:** 2 weeks
- **Sprint Start Day:** Monday
- **Velocity:** Measure in story points

### Step 3: Create Components

Create components (teams):
- `Backend` - Backend engineering
- `Frontend` - Frontend engineering
- `Data Science` - ML and data science
- `DevOps` - Infrastructure and DevOps

### Step 4: Import Sprint Tasks

Follow the same issue structure as Linear (see above)

**Create Issues:**
- Go to Board → Create
- Fill in: Summary, Description, Issue Type (Story/Task/Bug), Priority, Component
- Assign to: [Engineer]
- Estimate: Story points
- Sprint: Add to active sprint

### Step 5: Configure Boards

**Sprint Board:**
- **Columns:** To Do, In Progress, In Review, Done
- **Swimlanes:** Backend, Frontend, Data Science
- **Quick Filters:** Assignee = [Your name]

**Backlog:**
- **Group by:** Component
- **Sort by:** Priority

### Step 6: Sprint Retrospective Template

**After Each Sprint:**
1. Go to Reports → Sprint Report
2. Generate sprint report (PDF)
3. Share in `#engineering` channel
4. Discuss in sprint retro meeting (Friday 3 PM, 1 hour)

---

## ✅ Setup Checklist

### Week 1 Setup
- [ ] Account created (Linear or Jira)
- [ ] Workspace configured (teams, labels, statuses)
- [ ] Projects created (Q1 roadmap + 6 sprints)
- [ ] Sprint 1 tasks imported (all BE/FE/DS tasks)
- [ ] Team members invited
- [ ] Views configured (Sprint board, My issues, Bug triage)
- [ ] Automations configured (if using Linear)

### Week 1 Execution
- [ ] Sprint 1 kickoff meeting (Monday 9 AM, 2 hours)
- [ ] Tasks assigned to engineers
- [ ] Sprint board active
- [ ] Daily standup updates (async in #engineering)
- [ ] Sprint review meeting (Friday 3 PM, 1 hour)
- [ ] Sprint retrospective (Friday 4 PM, 30 minutes)

### Ongoing Operations
- [ ] Sprint planning (Every 2 weeks, Monday 9 AM)
- [ ] Sprint review (Every 2 weeks, Friday 3 PM)
- [ ] Sprint retro (Every 2 weeks, Friday 4 PM)
- [ ] Backlog refinement (Weekly, Wednesday 10 AM)
- [ ] Bug triage (Weekly, Thursday 3 PM)

---

## 📊 Sprint Planning Template

**Use this template for each sprint planning meeting:**

```
# Sprint [X] Planning Meeting - [Date]

## Attendees
- [ ] CPO (Product)
- [ ] CTO (Engineering)
- [ ] Backend Engineers
- [ ] Frontend Engineers
- [ ] Data Scientists

## Agenda (2 hours)

1. Sprint Review (30 min)
   - Review previous sprint results
   - Demo completed features
   - Discuss what worked/what didn't

2. Sprint Goal (15 min)
   - Define sprint goal: "As a [user], I want [feature], so that [benefit]"
   - Target: [Metric] - [Current] → [Target]

3. Task Breakdown (45 min)
   - Break down features into tasks
   - Estimate story points
   - Identify dependencies

4. Task Assignment (15 min)
   - Self-assign tasks
   - Confirm capacity (engineers should not be over-allocated)
   - Identify risks

5. Definition of Done (15 min)
   - Code reviews completed
   - Tests written (80%+ coverage)
   - QA sign-off
   - Documentation updated

## Sprint Goal
[One sentence goal]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Tasks
| Task | Owner | Estimate | Status |
|------|-------|----------|--------|
| [Task 1] | [Name] | [SP] | [ ] |
| [Task 2] | [Name] | [SP] | [ ] |
| [Task 3] | [Name] | [SP] | [ ] |

## Risks
- [Risk 1] - Mitigation: [Plan]
- [Risk 2] - Mitigation: [Plan]

## Action Items
- [ ] [Action 1] - Owner: [Name] - Due: [Date]
```

---

## 📞 Support

**Linear Documentation:** https://linear.app/docs
**Jira Documentation:** https://support.atlassian.com/jira-software
**Tool Questions:** [CTO] - [Email]
**Process Questions:** [CPO] - [Email]

---

*Last Updated: January 12, 2025*
*Next Review: End of Q1 2025 (assess and adjust for Q2)*
