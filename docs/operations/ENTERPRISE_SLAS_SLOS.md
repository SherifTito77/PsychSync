# Enterprise Service Level Agreements (SLAs) & Service Level Objectives (SLOs)
## PsychSync Enterprise Commitments

---

## Executive Summary

This document defines PsychSync's service level commitments for enterprise customers, including guaranteed performance metrics, credit policies for missed targets, and operational responsibilities. These SLAs demonstrate our commitment to reliability and provide customers with predictable service quality.

**Document Version:** 2.0
**Effective Date:** Q2 2025 (April 1, 2025)
**Applies To:** Enterprise tier customers (200+ seats, $15,000+ ARR)

---

## Part 1: Service Level Objectives (SLOs)

### SLO Definition
**Service Level Objective (SLO):** A target level of service performance that we commit to achieving. SLOs are specific, measurable metrics with defined targets.

### Core SLOs

#### SLO 1: API Availability
**Metric:** Percentage of time API endpoints respond successfully
**Target:** 99.9% monthly uptime
**Measurement:** Automated monitoring (5-minute intervals)
**Exclusions:** Scheduled maintenance (maximum 4 hours/month, announced 7 days in advance)

```python
# Calculation
Availability = (Total Minutes - Downtime Minutes) / Total Minutes × 100

# Example: 43,200 minutes in a 30-day month
# Target: Allow maximum 43.2 minutes of downtime
# 99.9% = (43,200 - 43.2) / 43,200 × 100
```

#### SLO 2: API Response Time
**Metric:** Time to receive response from API (p95)
**Target:** <500ms for 95th percentile of requests
**Measurement:** Continuous monitoring of all API requests
**Scope:** Core API endpoints (assessments, users, teams, analytics)

**By Endpoint Type:**
| Endpoint Category | p50 Target | p95 Target | p99 Target |
|-------------------|------------|------------|------------|
| Authentication | <100ms | <200ms | <500ms |
| Read Operations | <50ms | <150ms | <300ms |
| Write Operations | <100ms | <300ms | <1,000ms |
| Analytics Queries | <200ms | <500ms | <2,000ms |
| Assessment Processing | <500ms | <1,500ms | <5,000ms |

#### SLO 3: Data Durability
**Metric:** Probability that data is not lost
**Target:** 99.999999999% (11 nines)
**Implementation:** Triple-redundant storage with automatic failover
**Scope:** All user data, assessment responses, team analytics

#### SLO 4: Backup Recovery
**Metric:** Time to restore from backup
**Target:** RPO <1 minute, RTO <2 hours
**Measurement:** Quarterly disaster recovery tests
**Scope:** Accidental deletion, data corruption, regional failure

- **RPO (Recovery Point Objective):** Maximum acceptable data loss (1 minute)
- **RTO (Recovery Time Objective):** Time to restore service (2 hours)

#### SLO 5: Support Response Time
**Metric:** Time to first response from support team
**Target:**
- **Critical (P1):** <1 hour (24/7)
- **High (P2):** <4 hours (business hours)
- **Medium (P3):** <1 business day
- **Low (P4):** <2 business days

**Priority Definitions:**
- **P1 - Critical:** Complete service outage, data loss, security breach
- **P2 - High:** Major feature unavailable, significant degradation
- **P3 - Medium:** Minor feature unavailable, workaround available
- **P4 - Low:** General questions, feature requests, documentation

#### SLO 6: Data Freshness (Analytics)
**Metric:** Time for data to appear in analytics dashboards
**Target:** <5 minutes for 95% of updates
**Scope:** Team dashboards, assessment results, user activity

#### SLO 7: Assessment Processing
**Metric:** Time to generate assessment results
**Target:** <3 seconds for 95% of assessments
**Scope:** MBTI, Big Five, Enneagram, custom assessments

#### SLO 8: Security Incident Response
**Metric:** Time to acknowledge and respond to security incidents
**Target:**
- Acknowledgment: <1 hour
- Initial assessment: <4 hours
- Resolution plan: <24 hours
- Complete remediation: <72 hours

---

## Part 2: Service Level Agreements (SLAs)

### SLA Definition
**Service Level Agreement (SLA):** A formal commitment with financial consequences if SLOs are not met.

### SLA Commitments

#### Commitment 1: Uptime Guarantee
**SLO:** 99.9% monthly uptime
**Credit Schedule:**
| Monthly Uptime | Credit |
|----------------|--------|
| <99.9% but ≥99.0% | 10% of monthly fee |
| <99.0% but ≥95.0% | 25% of monthly fee |
| <95.0% but ≥90.0% | 50% of monthly fee |
| <90.0% | 100% of monthly fee |

**Example Calculation:**
- Monthly fee: $2,000
- Actual uptime: 98.5% (below 99.9% target)
- Credit: 10% × $2,000 = $200

#### Commitment 2: Performance Guarantee
**SLO:** p95 response time <500ms
**Credit Schedule:**
- If p95 >500ms but <1s for >5% of month: 5% credit
- If p95 >1s for >1% of month: 10% credit
- If p95 >2s for >0.5% of month: 20% credit

#### Commitment 3: Support Response Guarantee
**SLO:** P1 tickets responded to within 1 hour
**Credit Schedule:**
- If P1 response time >1 hour in >10% of cases: 5% credit
- If P1 response time >4 hours in >5% of cases: 10% credit
- If P1 response time >8 hours in >1% of cases: 20% credit

#### Commitment 4: Data Durability Guarantee
**SLO:** 99.999999999% data durability
**Credit Schedule:**
- If customer data is permanently lost: 100% credit + $10,000 penalty

---

## Part 3: Maintenance Windows

### Scheduled Maintenance
**Frequency:** Maximum once per month
**Duration:** Maximum 4 hours
**Notification:** 7 days advance notice via email
**Timing:** Weekends, 2:00 AM - 6:00 AM ET (customer timezone)

**Maintenance Activities:**
- Database upgrades
- Security patches
- Infrastructure scaling
- Feature deployments (major releases only)

### Emergency Maintenance
**Definition:** Unplanned maintenance to address critical issues
**Notification:** 2 hours advance notice (if possible)
**Duration:** As long as necessary to resolve issue
**Exceptions:** No notice required for immediate security fixes

---

## Part 4: Exclusions & Exceptions

### Exclusions from SLA Calculation
1. **Force Majeure:** Natural disasters, war, government actions
2. **Customer Actions:** Issues caused by customer's systems/network
3. **Beta Features:** Pre-release features explicitly marked as "beta"
4. **Free Tier:** Non-paying customers
5. **Third-Party Services:** Outages beyond our control (e.g., AWS, Slack API)
6. **Scheduled Maintenance:** Pre-announced maintenance windows

### Customer Responsibilities
To receive SLA credits, customers must:
1. Report outages within 24 hours
2. Provide reasonable access to diagnose issues
3. Maintain compliant API integration (rate limits, authentication)
4. Not abuse service (DDoS, excessive API calls)
5. Keep contact information up to date

---

## Part 5: Monitoring & Reporting

### Monitoring Infrastructure
**Tools:** Prometheus, Grafana, PagerDuty, DataDog
**Coverage:** All services, databases, APIs
**Alerting:** Automatic paging for P1 incidents

### Reporting
**Monthly SLA Report:** Includes:
- Actual uptime vs. target
- Response time percentiles (p50, p95, p99)
- Support ticket response times
- Credits issued (if any)
- Incidents summary

**Delivery:** By 5th business day of following month
**Access:** Customer portal + email

### Real-Time Status Page
**URL:** status.psychsync.com
**Updates:** Every 5 minutes during incidents
**Historical Data:** 90-day incident history

---

## Part 6: Credit Request Process

### How to Request Credits
1. **Submit Request:** Within 30 days of affected month
2. **Provide Evidence:** Logs, timestamps, impact description
3. **Review Period:** 5 business days
4. **Credit Application:** Applied to next invoice (or refund if preferred)

### Credit Request Form
```yaml
Customer Information:
  Company: [Customer Name]
  Account ID: [Account ID]
  Contact: [Name, Email]

Incident Details:
  Date/Time: [Start and end of outage]
  Affected Service: [API, Analytics, etc.]
  Impact Description: [How it affected your operations]
  Evidence: [Screenshots, logs, support ticket numbers]

SLA Violation:
  SLO Affected: [e.g., Uptime, Response Time]
  Target Value: [e.g., 99.9%]
  Actual Value: [e.g., 98.5%]
  Expected Credit: [Calculate based on schedule]

Supporting Documentation:
  - [ ] Ticket numbers
  - [ ] Timestamps
  - [ ] Impact assessment
  - [ ] Business losses (if applicable)
```

---

## Part 7: Incident Management

### Incident Severity Levels

**SEV1 (Critical):**
- Complete service outage
- Data loss or corruption
- Security breach
- Impact: All customers
- Response: All hands on deck

**SEV2 (High):**
- Major feature unavailable
- Significant performance degradation
- Partial service outage
- Impact: Many customers
- Response: Primary on-call + backup

**SEV3 (Medium):**
- Minor feature unavailable
- Moderate performance degradation
- Workaround available
- Impact: Some customers
- Response: On-call engineer

**SEV4 (Low):**
- Cosmetic issues
- Documentation errors
- Feature requests
- Impact: Minimal
- Response: Normal business hours

### Incident Response Process

1. **Detection** (Automated monitoring or customer report)
2. **Triage** (Assess severity, assign owner)
3. **Investigation** (Identify root cause)
4. **Mitigation** (Implement workaround or fix)
5. **Resolution** (Verify service restored)
6. **Post-Mortem** (Document learnings, prevent recurrence)

**Target Resolution Times:**
- SEV1: <4 hours
- SEV2: <8 hours
- SEV3: <24 hours
- SEV4: <72 hours

---

## Part 8: Performance Baselines

### Current Performance (Q1 2025)
Based on last 90 days of production data:

**Availability:**
- Actual: 99.95%
- Target: 99.9%
- Status: ✅ Exceeding target

**Response Time (p95):**
- Actual: 320ms
- Target: 500ms
- Status: ✅ Exceeding target

**Support Response (P1):**
- Actual: 45 minutes average
- Target: <1 hour
- Status: ✅ Exceeding target

**Data Durability:**
- Actual: 100% (0 incidents)
- Target: 99.999999999%
- Status: ✅ Exceeding target

### Historical Trend
| Quarter | Availability | p95 Response | P1 Response | Credits Issued |
|---------|--------------|--------------|-------------|----------------|
| Q4 2024 | 99.92% | 380ms | 52 min | $0 |
| Q1 2025 | 99.95% | 320ms | 45 min | $0 |
| Q2 2025* | 99.9% (target) | 500ms (target) | 60 min (target) | TBD |

*Projected based on current capacity

---

## Part 9: Tier-Specific SLAs

### Starter Tier (1-19 seats)
- **No SLA** (best effort)
- Community support only
- 99% uptime target (internal)

### Business Tier (20-199 seats)
- **Uptime:** 99.5% (21.6 hours downtime/month)
- **Support:** P1 <4 hours, P2 <1 business day
- **Response Time:** p95 <1s
- **Credits:** Maximum 10% of monthly fee

### Enterprise Tier (200+ seats)
- **Uptime:** 99.9% (43.2 minutes downtime/month)
- **Support:** P1 <1 hour (24/7), P2 <4 hours
- **Response Time:** p95 <500ms
- **Credits:** Up to 100% of monthly fee
- **Additional:** Dedicated CSM, quarterly business reviews

### Enterprise Plus (500+ seats)
- **Uptime:** 99.95% (21.6 minutes downtime/month)
- **Support:** P1 <30 minutes (24/7), P2 <2 hours
- **Response Time:** p95 <300ms
- **Credits:** Up to 100% + penalty fees
- **Additional:** Dedicated engineer, custom integrations, on-premise option

---

## Part 10: Legal & Compliance

### SLA Contract Language

**Sample Clause (for enterprise contracts):**

```
Section X: Service Level Agreement

X.1 Service Commitment. Provider agrees to maintain the Services with the
service levels set forth in this Section X.

X.2 Service Credits. If Provider fails to meet the service levels, Customer
will be entitled to service credits as set forth in the Service Level Credit
Policy located at: https://psychsync.com/sla-credits

X.3 exclusions. Service credits will not be provided for any failure to meet
a service level resulting from: (a) Force Majeure; (b) Customer's systems or
network; (c) Beta Features; or (d) Third-Party Services.

X.4 Request for Credits. Customer must request service credits within thirty
(30) days of the end of the affected month. Provider will evaluate all
requests within five (5) business days.

X.5 Maximum Liability. Provider's total liability for service credits in any
twelve (12) month period shall not exceed the fees paid by Customer for such
period.
```

### Audit Rights
Enterprise customers may request an audit of SLA compliance once per year.
- **Notice:** 30 days advance notice
- **Scope:** SLA-related metrics only
- **Cost:** No charge if violation found; customer pays if compliant

---

## Part 11: Continuous Improvement

### Quarterly SLA Reviews
**Participants:** Engineering leadership, customer success, customer advisory board
**Agenda:**
1. Review SLA performance vs. targets
2. Identify gaps and root causes
3. Adjust targets (if appropriate)
4. Infrastructure investment plan
5. Customer feedback integration

**Target Adjustments:**
- May increase SLA targets with 90-day notice
- Will not decrease SLAs for existing customers (grandfathered)
- New customers get current SLA commitments

### Investment in Reliability
**Q2 2025 Initiatives:**
- Multi-region deployment (reduce single point of failure)
- Database read replicas (improve performance)
- Automated failover testing (weekly)
- Capacity planning (3x headroom)

**Target by Q4 2025:**
- Uptime: 99.95% (from 99.9%)
- Response time: p95 <300ms (from 500ms)
- Support: P1 <30 minutes (from 60 minutes)

---

## Conclusion

PsychSync's enterprise SLAs demonstrate our commitment to reliability and customer success. We stand behind our service with meaningful guarantees, transparent reporting, and fair credit policies.

**Key Takeaways:**
- ✅ 99.9% uptime guarantee (industry-leading)
- ✅ Performance commitments with financial backing
- ✅ 24/7 support for critical issues
- ✅ Transparent monitoring and reporting
- ✅ Continuous improvement path to 99.95%

**Next Steps:**
1. Review SLA terms with legal
2. Set up monitoring dashboards for customers
3. Create monthly SLA report templates
4. Train support team on SLA policies
5. Launch status.psychsync.com

**Reliability isn't a feature—it's a promise. We keep our promises. 🎯**
