# PsychSync User Personas & Roles Matrix

**Comprehensive user segmentation, role definitions, and permission structures**

---

## 📋 Executive Summary

PsychSync serves multiple user types across different organizational levels. This document defines our core personas, their needs, permissions, and how they interact with the platform.

**Key Personas**: 5 primary roles identified
**Permission Levels**: 4-tier access control system
**Organizational Hierarchy**: 3 levels (User → Team → Organization)

---

## 👥 Primary User Personas

### 1. **Individual Professional** (Free Tier User)

**Profile**: Individual seeking personal development insights

| Attribute | Details |
|-----------|---------|
| **Demographics** | Age 25-45, knowledge workers, individual contributors |
| **Goals** | Self-awareness, career growth, communication improvement |
| **Pain Points** | Limited budget, needs quick insights, privacy concerns |
| **Technical Comfort** | Moderate - familiar with SaaS tools |
| **Decision Maker** | Self-directed |

**Key Jobs-to-be-Done**:
- Complete psychological assessments (Big Five, MBTI, Enneagram)
- Understand personal strengths and growth areas
- Receive AI-powered coaching recommendations
- Track personal development over time

**Platform Features Used**:
- Assessment dashboard
- Personal results and insights
- Basic analytics (self-view)
- Onboarding tutorials

**Success Metrics**:
- Assessment completion rate
- Time to first insight
- Return usage frequency

---

### 2. **Team Lead / Manager** (Professional Tier)

**Profile**: People managers leading 5-50 person teams

| Attribute | Details |
|-----------|---------|
| **Demographics** | Age 28-55, first-line to mid-level managers |
| **Goals** | Build cohesive teams, improve communication, identify leaders |
| **Pain Points** | Team conflict, low engagement, limited time for 1:1s |
| **Technical Comfort** | Moderate to High |
| **Decision Maker** | Team budget influencer |

**Key Jobs-to-be-Done**:
- Invite team members to assessments
- View team analytics and insights
- Identify team strengths and blind spots
- Get recommendations for team building
- Track team morale and engagement trends

**Platform Features Used**:
- Team management dashboard
- Team analytics and composition
- Conflict detection alerts
- Performance insights
- 1:1 coaching guides

**Success Metrics**:
- Team assessment completion rate
- Weekly dashboard logins
- Team retention impact
- Feature adoption (analytics, reports)

---

### 3. **HR Business Partner** (Professional Tier)

**Profile**: HR professionals supporting multiple teams

| Attribute | Details |
|-----------|---------|
| **Demographics** | Age 30-55, HR generalists and specialists |
| **Goals** | Talent development, succession planning, culture health |
| **Pain Points** | Limited visibility, manual data aggregation, compliance needs |
| **Technical Comfort** | Moderate to High |
| **Decision Maker** | HR budget owner |

**Key Jobs-to-be-Done**:
- Manage organization-wide assessments
- Identify high-potential employees
- Track engagement and satisfaction
- Generate reports for leadership
- Support succession planning

**Platform Features Used**:
- Multi-team management
- Organization analytics
- Succession planning tools
- Export and reporting features
- Compliance and audit logs

**Success Metrics**:
- Organization coverage (% employees assessed)
- Report generation frequency
- Time saved vs. manual processes
- Leadership satisfaction with insights

---

### 4. **Executive Leader** (Enterprise Tier)

**Profile**: C-level, VPs, Directors with P&L responsibility

| Attribute | Details |
|-----------|---------|
| **Demographics** | Age 40-65, senior leaders |
| **Goals** | Organizational alignment, culture transformation, business outcomes |
| **Pain Points** | Limited actionable insights, disconnected initiatives, ROI proof |
| **Technical Comfort** | Varied - want executive summaries |
| **Decision Maker** | Enterprise budget approval |

**Key Jobs-to-be-Done**:
- View organization-wide dashboards
- Understand culture health and risks
- Make data-driven talent decisions
- Track initiative ROI
- Communicate insights to board/investors

**Platform Features Used**:
- Executive dashboards
- Organizational health scores
- Trend analysis and forecasting
- Board presentation materials
- Custom reporting

**Success Metrics**:
- Monthly dashboard views
- Action taken on insights
- Culture KPI improvement
- ROI on initiatives

---

### 5. **Consultant / Coach** (Enterprise Tier - External)

**Profile**: External consultants and coaches supporting client organizations

| Attribute | Details |
|-----------|---------|
| **Demographics** | Age 30-65, independent and boutique firm consultants |
| **Goals** | Deliver client value, scale services, differentiate offerings |
| **Pain Points** | Limited tools, manual analysis, white-label needs |
| **Technical Comfort** | High |
| **Decision Maker** | Tool selection for practice |

**Key Jobs-to-be-Done**:
- White-label assessments for clients
- Analyze client team dynamics
- Generate professional reports
- Track client progress over engagements
- Integrate insights into consulting methodology

**Platform Features Used**:
- White-label branding
- Client management (multi-tenant)
- Advanced analytics and export
- Custom assessment creation
- API access for integrations

**Success Metrics**:
- Client retention
- Assessments delivered per client
- Time savings per engagement
- Practice differentiation

---

## 🎭 Secondary Personas

### **IT / Security Administrator** (Enterprise)
- **Primary Concern**: Data security, SSO, compliance
- **Interaction**: Initial setup, ongoing configuration
- **Features Used**: SSO setup, audit logs, data export, compliance reports

### **Finance / Procurement** (Enterprise)
- **Primary Concern**: Cost justification, billing management
- **Interaction**: Purchase, renewal, invoice review
- **Features Used**: Usage reports, billing dashboard, cost-per-employee analytics

### **Employee / Team Member** (All Tiers)
- **Primary Concern**: Privacy, time investment, value received
- **Interaction**: Complete assessments, view personal results
- **Features Used**: Assessment interface, personal dashboard, insights

---

## 🔐 Permission & Roles Matrix

### Role-Based Access Control (RBAC)

| Role | Dashboard | Assessments | Team Analytics | Org Analytics | Admin | Billing | API Access |
|------|-----------|-------------|----------------|---------------|-------|---------|------------|
| **Individual** | ✅ Personal | ✅ Create | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Team Lead** | ✅ Team | ✅ Create/Assign | ✅ Own Team | ❌ | ❌ | ❌ | ❌ |
| **HRBP** | ✅ Multi-Team | ✅ Create/Assign | ✅ Assigned Teams | ✅ Assigned | ❌ | ❌ | ❌ |
| **Executive** | ✅ Executive | ✅ View | ✅ All Teams | ✅ All Orgs | ❌ | ❌ | ❌ |
| **Consultant** | ✅ Client | ✅ Create/Assign | ✅ Client Teams | ✅ Client Orgs | ⚠️ Client | ⚠️ Client | ✅ |
| **Admin** | ✅ All | ✅ All | ✅ All | ✅ All | ✅ Full | ✅ Full | ✅ |
| **IT Admin** | ⚠️ Limited | ❌ | ❌ | ❌ | ✅ Security | ⚠️ View | ⚠️ Readonly |

**Legend**:
- ✅ = Full Access
- ⚠️ = Limited/Scoped Access
- ❌ = No Access

---

### Granular Permission Definitions

#### **Assessment Permissions**
| Permission | Description | Roles |
|------------|-------------|-------|
| `view_own_assessments` | See own assessment results | All Users |
| `create_assessments` | Create new assessments | Individual, Team Lead, HRBP, Consultant |
| `assign_assessments` | Assign to team members | Team Lead, HRBP, Consultant |
| `view_team_assessments` | View team-level results | Team Lead, HRBP, Executive, Consultant |
| `view_org_assessments` | View org-level results | HRBP, Executive, Consultant, Admin |
| `delete_assessments` | Remove assessments | Admin, IT Admin (GDPR) |

#### **Analytics Permissions**
| Permission | Description | Roles |
|------------|-------------|-------|
| `view_personal_analytics` | Own personal insights | All Users |
| `view_team_analytics` | Team-level dashboards | Team Lead, HRBP, Executive, Consultant |
| `view_org_analytics` | Organization-wide insights | HRBP, Executive, Consultant, Admin |
| `export_analytics` | Export data and reports | HRBP, Consultant, Admin |
| `view_advanced_analytics` | AI/ML insights, predictions | Professional, Enterprise |

#### **Admin Permissions**
| Permission | Description | Roles |
|------------|-------------|-------|
| `manage_users` | Add/remove users, change roles | Admin, IT Admin |
| `manage_teams` | Create/delete teams, modify structure | Admin, HRBP |
| `manage_org_settings` | Organization configuration | Admin, Executive |
| `view_audit_logs` | Security and compliance logs | Admin, IT Admin |
| `manage_billing` | Billing and subscription management | Admin |
| `manage_integrations` | API, SSO, third-party connections | Admin, IT Admin |
| `view_all_data` | Full data access (GDPR requests) | Admin |

---

## 🏢 Organizational Hierarchy

```
Organization (Enterprise)
├── Executive (Full org visibility)
├── HRBP (Multi-team visibility)
├── IT Admin (System configuration)
└── Teams
    ├── Team A
    │   ├── Team Lead (Team A visibility)
    │   ├── Member 1 (Personal visibility only)
    │   └── Member 2 (Personal visibility only)
    ├── Team B
    │   ├── Team Lead (Team B visibility)
    │   └── Members
    └── Team C
        └── ...
```

### Visibility Rules

| Role | Personal | Team | Organization | Cross-Org |
|------|----------|------|--------------|-----------|
| Individual | ✅ Own | ❌ | ❌ | ❌ |
| Team Lead | ✅ Own | ✅ Own Team | ❌ | ❌ |
| HRBP | ✅ Own | ✅ Assigned | ✅ Assigned | ❌ |
| Executive | ✅ Own | ✅ All | ✅ All | ❌ |
| Consultant | ✅ Own | ✅ Client | ✅ Client | ✅ Multi-Client |
| Admin | ✅ All | ✅ All | ✅ All | ✅ All |

---

## 🎯 Persona-Based Feature Prioritization

### High Impact Features by Persona

| Feature | Individual | Team Lead | HRBP | Executive | Consultant |
|---------|------------|-----------|------|-----------|------------|
| Personal Assessments | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ |
| Team Analytics | - | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| AI Insights | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ |
| Executive Dashboards | - | - | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| White Labeling | - | - | - | - | ⭐⭐⭐ |
| API Access | - | - | ⭐ | ⭐ | ⭐⭐⭐ |
| Advanced Reports | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Succession Planning | - | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Mobile App | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ |

**Legend**: ⭐⭐⭐ = Critical | ⭐⭐ = Important | ⭐ = Nice-to-have

---

## 📊 Persona Adoption Metrics

### Activation Milestones by Persona

| Persona | Activation Definition | Time to Activate |
|----------|----------------------|------------------|
| Individual | Complete first assessment | < 15 minutes |
| Team Lead | Invite first team member | < 1 hour |
| HRBP | Create team, assign assessments | < 1 day |
| Executive | View executive dashboard | < 1 week |
| Consultant | White-label setup, first client | < 1 day |

### Retention Signals by Persona

| Persona | Key Retention Driver | Churn Risk Signal |
|----------|---------------------|-------------------|
| Individual | Personal insights value | No assessment in 30 days |
| Team Lead | Team adoption (>50%) | < 25% team completed |
| HRBP | Organization coverage | < 10% monthly growth |
| Executive | Dashboard usage | No login in 14 days |
| Consultant | Client satisfaction | Client cancellation |

---

## 🎨 Persona-Specific UX Considerations

### Individual Professional
- **Mobile-first**: Quick assessments on phone
- **Privacy emphasis**: Clear data usage messaging
- **Instant gratification**: Immediate insights after assessment
- **Low friction**: Minimal setup, social login options

### Team Lead / Manager
- **Team-centric view**: Team health front and center
- **Actionable insights**: Clear recommendations, not just data
- **Time-efficient**: 5-minute check-ins sufficient
- **Celebration**: Highlight team wins and improvements

### HRBP
- **Multi-tasking**: Save progress, bulk operations
- **Compliance ready**: Audit logs, data export
- **Report automation**: Scheduled reports, executive summaries
- **Benchmarking**: Industry comparisons available

### Executive
- **High-level summaries**: Drill-down available but not required
- **Trend visualization**: Time-series, forecasting
- **Red flag alerts**: Critical issues surfaced immediately
- **Board-ready**: Export to presentation formats

### Consultant
- **White-label flexibility**: Full branding control
- **Client separation**: Clear client boundaries
- **Data portability**: Clean exports for client handoff
- **Methodology integration**: Custom framework support

---

## 🔄 Persona Evolution Paths

### Individual → Team Lead
**Trigger**: Becomes people manager
**Action**: In-app upgrade prompt, team setup tutorial
**Time**: Send when job title change detected or team invitation requested

### Team Lead → HRBP
**Trigger**: Managing multiple teams or HR role change
**Action**: Multi-team dashboard introduction, HRBP features tour
**Time**: Proactive outreach at 3+ teams

### Professional → Enterprise
**Trigger**: Organization growth to 50+ users
**Action**: Enterprise features preview, SSO/security overview
**Time**: Sales outreach at organization threshold

### Consultant Signup
**Trigger**: Account creation with consultant intent
**Action**: White-label setup wizard, API docs introduction
**Time**: Immediate onboarding focus

---

## 📚 Supporting Documentation

- [User Journey Map](./user-journey-map.md) - End-to-end flows for each persona
- [Feature Briefs](./features/feature-briefs.md) - Detailed feature specifications
- [Pricing Strategy](./pricing/pricing-strategy.md) - Persona-based tier alignment
- [Activation Milestones](./metrics/activation-milestones.md) - Success metrics per persona

---

**🧠 PsychSync AI - Personas & Roles**

*Version: 1.0*
*Last Updated: January 2025*
*Owner: Product Team*
*Next Review: April 2025*
