# PsychSync Enterprise SLAs & SLOs

**Service Level Agreements and Objectives for enterprise customers**

---

## 📋 Executive Summary

This document defines PsychSync's Service Level Agreements (SLAs) and Service Level Objectives (SLOs) for enterprise customers. These commitments ensure reliability, performance, and support quality that enterprise organizations require.

**SLA Philosophy**: Under-promise, over-deliver. Build trust through consistency.
**Commitment Levels**: Three tiers (Professional, Enterprise, Custom)
**Current Performance**: All SLOs being met (see Performance Dashboard)
**Credit Policy**: Service credits if SLAs not met

---

## 🎯 Service Level Tiers

### **Professional Tier (Standard SLOs)**

**Target Customers**: Teams and organizations with < 100 users
**Included**: Yes, no additional cost
**Support Response**: 24 hours

| SLO | Commitment | Measurement |
|-----|------------|-------------|
| **Uptime** | 99.5% monthly uptime | Monthly calculation |
| **API Response Time** | <500ms (p95) | 24-hour rolling average |
| **Data Recovery** | 24-hour RPO (Recovery Point Objective) | Backup verification |
| **Support Response** | 24 hours (business days) | Time to first response |

**Implied Downtime Budget**: Up to 3.65 hours of downtime per month

---

### **Enterprise Tier (Enhanced SLOs)**

**Target Customers**: Organizations with 100+ users, mission-critical usage
**Included**: Yes, included in Enterprise pricing
**Support Response**: 4 hours

| SLO | Commitment | Measurement |
|-----|------------|-------------|
| **Uptime** | 99.9% monthly uptime | Monthly calculation |
| **API Response Time** | <200ms (p95) | 24-hour rolling average |
| **Data Recovery** | 1-hour RPO | Real-time replication |
| **Support Response** | 4 hours (24/7) | Time to first response |
| **Scheduled Maintenance** | 7-day advance notice | Maintenance windows |

**Implied Downtime Budget**: Up to 43.2 minutes of downtime per month

---

### **Custom Tier (Premium SLOs)**

**Target Customers**: Fortune 500, regulated industries, mission-critical deployments
**Included**: Additional fee (typically +20-30% of contract)
**Support Response**: 1 hour

| SLO | Commitment | Measurement |
|-----|------------|-------------|
| **Uptime** | 99.95% monthly uptime | Monthly calculation |
| **API Response Time** | <100ms (p95) | 24-hour rolling average |
| **Data Recovery** | 15-minute RPO | Hot standby, multi-region |
| **Support Response** | 1 hour (24/7) | Time to first response |
| **Scheduled Maintenance** | 14-day advance notice | Maintenance windows |
| **Dedicated Infrastructure** | Isolated tenant | Available upon request |

**Implied Downtime Budget**: Up to 21.6 minutes of downtime per month

---

## 📊 Detailed SLO Definitions

### **Uptime SLO**

#### **Definition**
```
Uptime % = (Total Minutes in Month - Downtime Minutes) / Total Minutes in Month × 100
```

#### **What Counts as Downtime**
- System unavailable (5xx errors for >5 minutes)
- Unable to authenticate/login
- API endpoints returning errors for >5 minutes
- Scheduled maintenance (unless communicated in advance)

#### **What Does NOT Count as Downtime**
- Individual user issues (browser, internet, device)
- Third-party service outages (e.g., Slack integration down)
- Customer-specific issues (e.g., SSO misconfiguration)
- Performance degradation (covered under Response Time SLO)
- Maintenance windows communicated per SLA

#### **Current Performance**
| Month | Uptime | Status |
|-------|--------|--------|
| **Jan 2025** | 99.97% | ✅ Exceeds Enterprise target |
| **Dec 2024** | 99.95% | ✅ Meets Custom target |
| **Nov 2024** | 99.98% | ✅ Exceeds all targets |

#### **Trend**: 12-month average uptime: 99.96%

---

### **API Response Time SLO**

#### **Definition**
- **Measurement**: Time from API request receipt to first byte of response
- **Percentile**: 95th percentile (p95) - fastest 95% of requests
- **Rolling Window**: 24-hour rolling average
- **Endpoints**: All `/api/v1/*` endpoints

#### **Target by Tier**
| Tier | Target (p95) | Current Performance |
|------|--------------|---------------------|
| **Professional** | <500ms | 180ms ✅ |
| **Enterprise** | <200ms | 180ms ✅ |
| **Custom** | <100ms | [Dedicated infra] |

#### **Performance Dashboard**
- **Real-time Monitoring**: Datadog/Prometheus dashboard
- **Public Status Page**: status.psychsync.ai
- **Alerting**: On-call engineer paged if p95 > target for >5 min

---

### **Data Recovery SLO**

#### **Definition**
**RPO (Recovery Point Objective)**: Maximum acceptable data loss
**RTO (Recovery Time Objective)**: Maximum time to restore service

| Tier | RPO | RTO | Backup Frequency |
|------|-----|-----|------------------|
| **Professional** | 24 hours | 4 hours | Daily backups |
| **Enterprise** | 1 hour | 1 hour | Hourly backups |
| **Custom** | 15 minutes | 30 minutes | Continuous replication |

#### **Backup & Recovery Process**
1. **Database Backups**: Automated, encrypted, stored in multiple regions
2. **Verification**: Weekly restore tests to validate backups
3. **Disaster Recovery**: Annual full disaster recovery drill
4. **Data Retention**: 90-day retention (Professional), 1-year (Enterprise), 5-year (Custom)

---

### **Support Response Time SLO**

#### **Definition**
**Response Time**: Time from support ticket creation to first human response

| Tier | Target (Severity 1) | Target (Severity 2) | Target (Severity 3) |
|------|---------------------|---------------------|---------------------|
| **Professional** | 24 hours | 48 hours | 72 hours |
| **Enterprise** | 4 hours | 8 hours | 24 hours |
| **Custom** | 1 hour | 4 hours | 8 hours |

#### **Severity Levels**

| Severity | Definition | Examples |
|----------|------------|----------|
| **Sev 1 (Critical)** | Production down, complete work stoppage | Login failure, API returning 500 errors, data loss |
| **Sev 2 (High)** | Major feature broken, significant impact | Can't generate reports, assessments failing |
| **Sev 3 (Medium)** | Minor issue, workaround available | UI bug, non-critical feature broken |
| **Sev 4 (Low)** | Question, enhancement request | How-to question, feature request |

#### **Support Channels**
- **Professional**: Email support (support@psychsync.ai)
- **Enterprise**: Email + Private Slack channel + Phone (Sev 1)
- **Custom**: Email + Slack + Phone + Dedicated account manager

---

## 🔔 Scheduled Maintenance

### **Maintenance Windows**

| Tier | Window | Advance Notice | Frequency |
|------|--------|----------------|-----------|
| **Professional** | Sunday 2-4am ET | 7 days | Weekly (as needed) |
| **Enterprise** | Sunday 2-4am ET | 7 days | Weekly (as needed) |
| **Custom** | By agreement | 14 days | Quarterly (planned) |

### **Maintenance Communication**
1. **14 Days Before**: Schedule maintenance (email + in-app banner)
2. **7 Days Before**: Reminder with specific time and impact
3. **24 Hours Before**: Final reminder
4. **1 Hour Before**: Maintenance begins
5. **Complete**: "Maintenance complete" confirmation

### **Emergency Maintenance**
- **Definition**: Unplanned, critical fix (security vulnerability, data loss risk)
- **Notice**: Best effort, may be immediate
- **Credit**: If unplanned maintenance >1 hour during business hours

---

## 💳 Service Credit Policy

### **SLA Breach Credits**

If we fail to meet our SLO commitments, customers receive service credits:

| SLO | Breach Threshold | Credit | Max Monthly Credit |
|-----|------------------|--------|-------------------|
| **Uptime** | <99.5% (Professional) | 10% of monthly fee | 50% |
| **Uptime** | <99.9% (Enterprise) | 10% of monthly fee | 50% |
| **API Response Time** | >target for >10% of month | 5% of monthly fee | 25% |
| **Support Response** | Late response (Sev 1) | 5% of monthly fee per occurrence | 25% |

### **Credit Calculation Example**

**Scenario**: Enterprise customer ($1,000/month) experiences 99.85% uptime in January (below 99.9% target)

```
Uptime Achieved: 99.85%
Uptime Target: 99.90%
Breach: 0.05% below target

Credit: 10% of $1,000 = $100 credit applied to February invoice
```

### **How to Request Credits**
1. **Submit Support Ticket**: Within 30 days of SLA breach
2. **Provide Evidence**: Logs, timestamps demonstrating breach
3. **Review**: PsychSync reviews and responds within 5 business days
4. **Credit Applied**: If validated, credit applied to next invoice

### **Exclusions**
- Force majeure events (natural disasters, wars)
- Third-party outages beyond our control
- Customer-caused issues
- Beta features, preview releases
- Free tier (no SLA commitment)

---

## 📈 Performance Monitoring & Reporting

### **Real-Time Monitoring**

**Tools**: Datadog, Prometheus, Grafana
**Metrics Tracked**:
- Request rate, error rate, latency
- Database performance (query time, connections)
- Infrastructure health (CPU, memory, disk)
- Application logs (errors, warnings)

**Alerting**:
- **Sev 1**: On-call engineer paged within 5 minutes
- **Sev 2**: On-call engineer notified via Slack/email
- **Sev 3**: Issue created, triaged during business hours

### **Public Status Page**

**URL**: status.psychsync.ai
**Updates**:
- **All Systems**: Real-time status
- **Incidents**: Live updates during active incidents
- **Maintenance**: Scheduled maintenance calendar
- **History**: 90-day incident history

### **Monthly SLA Reports**

**Delivered To**: All Enterprise and Custom tier customers
**Includes**:
- Uptime percentage
- API response time (p50, p95, p99)
- Incident summary (number, severity, resolution time)
- Support metrics (response time, resolution time, customer satisfaction)
- Credits issued (if any)

**Delivery**: Email by 5th business day of each month

---

## 🔒 Security & Compliance SLAs

### **Security Incident Response**

| Tier | Detection Time | Response Time | Resolution Time |
|------|----------------|---------------|-----------------|
| **Professional** | Best effort | 24 hours | 72 hours |
| **Enterprise** | <1 hour | 4 hours | 48 hours |
| **Custom** | <15 minutes | 1 hour | 24 hours |

### **Compliance Commitments**

| Compliance | Standard | PsychSync Status |
|------------|----------|------------------|
| **SOC 2 Type II** | AICPA | In progress (target: Q3 2025) |
| **GDPR** | EU Regulation | Compliant |
| **CCPA** | California Law | Compliant |
| **HIPAA** | HHS | Available (BAA required) |
| **ISO 27001** | International | In progress (target: Q4 2025) |

---

## 📋 SLA Contract Terms

### **Enterprise Contract SLA Clause**

```markdown
## Service Level Agreement

PsychSync agrees to maintain the following service levels:

**Uptime**: PsychSync warrants 99.9% monthly uptime, excluding scheduled maintenance
and force majeure events. Uptime is calculated as (Total Minutes - Downtime) / Total Minutes.

**API Performance**: PsychSync API will respond in <200ms (p95) measured over a 24-hour
rolling average for all `/api/v1/*` endpoints.

**Support Response**: PsychSync will respond to Severity 1 issues within 4 hours (24/7),
Severity 2 within 8 hours, and Severity 3 within 24 hours.

**Credits**: If PsychSync fails to meet these commitments, Customer will receive a service
credit equal to 10% of the monthly fee for the affected month, up to a maximum of 50%
of monthly fees.

**Exclusions**: This SLA excludes free tier, beta features, third-party outages,
customer-caused issues, and force majeure events.

**Monitoring**: Performance is monitored 24/7 and reported monthly. Public status
available at status.psychsync.ai.
```

---

## 🎯 SLA Health Dashboard

### **Current Status (January 2025)**

| SLO | Target | Actual | Status | Trend |
|-----|--------|--------|--------|-------|
| **Uptime (Jan)** | 99.9% | 99.97% | ✅ Exceeding | 📈 Improving |
| **API Response (p95)** | <200ms | 180ms | ✅ Exceeding | ➡️ Stable |
| **Support Response (Sev 1)** | <4 hours | 2.5 hours | ✅ Exceeding | 📈 Improving |
| **Data Recovery RPO** | <1 hour | 15 minutes | ✅ Exceeding | ➡️ Stable |

**Overall SLA Health**: 🟢 All SLOs being met

---

## 🔄 SLA Review & Improvement

### **Quarterly Business Reviews (QBRs)**

**Participants**: Customer success, engineering leadership, product
**Frequency**: Quarterly for Enterprise and Custom customers
**Agenda**:
- SLA performance review
- Feature roadmap alignment
- Support quality feedback
- Expansion opportunities

### **Annual SLA Review**

**When**: Each year in Q4
**Purpose**:
- Review SLA targets (are they still appropriate?)
- Assess customer feedback and needs
- Benchmark against industry standards
- Update SLAs for next year (with 60-day notice)

### **Continuous Improvement**

**Initiatives**:
- **2025**: Achieve SOC 2 compliance
- **2025**: Implement multi-region deployment for Custom tier
- **2026**: Target 99.99% uptime (Custom tier)

---

## 📚 Supporting Documentation

- [Security Architecture](../../docs/SECURITY_ARCHITECTURE.md) - Security practices
- [Incident Response Playbook](../../docs/incidents/README.md) - Incident management
- [Monitoring Setup](../../docs/MONITORING_QUICK_START.md) - Technical monitoring
- [Enterprise Strategy](../go-to-market/enterprise-strategy.md) - Enterprise sales

---

**🧠 PsychSync AI - Enterprise SLAs & SLOs**

*Version: 1.0*
*Last Updated: January 2025*
*Owner: Product Team + Operations*
*SLA Compliance Review: Monthly*
*Next SLA Update: Q4 2025 (annual review)*
