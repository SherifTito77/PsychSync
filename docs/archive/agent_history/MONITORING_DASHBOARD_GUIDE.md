# Query Optimization Monitoring Dashboard Guide

**Monitoring Period:** 2025-01-18 to 2025-02-01 (2 weeks)
**Status:** Active
**Dashboard:** Local monitoring with automated reports

---

## Quick Start

### Run Daily Monitoring Check
```bash
bash scripts/daily_monitoring_check.sh
```

### Generate Weekly Report
```bash
python scripts/generate_weekly_report.py --week 1
```

### Validate Deployment
```bash
python scripts/validate_query_optimization.py
```

---

## Monitoring Components

### 1. Daily Monitoring Script

**Location:** `scripts/daily_monitoring_check.sh`
**Schedule:** 8:00 AM daily (automated via cron)
**Duration:** ~2 minutes
**Output:** `monitoring_reports/daily_report_YYYY-MM-DD.md`

**What It Checks:**
1. ✅ Validation status (indexes, pagination)
2. 📊 Index usage statistics
3. ⚡ Query performance metrics
4. 📈 Database load metrics
5. ❌ Error log analysis
6. 📝 Daily summary report

**To Run Manually:**
```bash
bash scripts/daily_monitoring_check.sh
```

**To View Latest Report:**
```bash
cat monitoring_reports/daily_report_$(date +%Y-%m-%d).md
```

### 2. Weekly Performance Report

**Location:** `scripts/generate_weekly_report.py`
**Schedule:** 5:00 PM Friday (automated via cron)
**Duration:** ~1 minute
**Output:** `monitoring_reports/weekly_report_week_N_YYYY-MM-DD.md`

**What It Includes:**
1. 📊 Executive summary
2. 📈 Index usage trends
3. ⚡ Query performance analysis
4. 💾 Database load metrics
5. ⚠️ Issues and incidents
6. 🎯 Production readiness assessment
7. 📋 Comparison to baseline

**To Run Manually:**
```bash
python scripts/generate_weekly_report.py --week 1
```

**To View Latest Report:**
```bash
ls -lt monitoring_reports/weekly_report_*.md | head -1
```

### 3. Validation Script

**Location:** `scripts/validate_query_optimization.py`
**Purpose:** Quick health check
**Duration:** ~30 seconds

**What It Validates:**
- ✅ All 6 indexes present
- ✅ Pagination limits acceptable
- ✅ Query patterns using indexes
- ✅ No regressions

**To Run:**
```bash
python scripts/validate_query_optimization.py
```

---

## Monitoring Dashboard

### Local Monitoring Commands

Create an alias for quick monitoring:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias psych-monitor='bash scripts/daily_monitoring_check.sh'
alias psych-validate='cd /Users/sheriftito/Downloads/psychsync && python scripts/validate_query_optimization.py'
alias psych-report='cd /Users/sheriftito/Downloads/psychsync && python scripts/generate_weekly_report.py'
```

Then use:
```bash
psych-monitor    # Run daily check
psych-validate   # Quick validation
psych-report     # Generate weekly report
```

### Key Metrics Dashboard

**Index Usage:**
```bash
python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT indexrelname, idx_scan
        FROM pg_stat_user_indexes
        WHERE indexrelname LIKE 'idx_%'
        ORDER BY idx_scan DESC
        LIMIT 10
    '''))
    for row in result.fetchall():
        print(f'{row[0]}: {row[1]} scans')
"
```

**Query Performance:**
```bash
python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('''
        EXPLAIN ANALYZE
        SELECT COUNT(*) FROM team_members
        WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
    '''))
    plan = '\n'.join(row[0] for row in result.fetchall())
    if 'Execution Time:' in plan:
        print(f'Team Count Query: {plan.split(\"Execution Time:\")[-1].strip().split()[0]} ms')
"
```

**Database Load:**
```bash
python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT
            count(*) as total,
            count(*) FILTER (WHERE state = 'active') as active
        FROM pg_stat_activity
        WHERE datname = current_database()
    '''))
    row = result.fetchone()
    print(f'Total: {row[0]}, Active: {row[1]}')
"
```

---

## Setting Up Automated Monitoring

### Install Cron Jobs

Run the setup script to install automated monitoring:

```bash
bash scripts/setup_monitoring_cron.sh
```

This will:
- Install daily monitoring check (8:00 AM)
- Install weekly report generator (Friday 5:00 PM)
- Create log directory structure
- Test the monitoring scripts

### View Scheduled Jobs

```bash
# View all cron jobs
crontab -l

# View monitoring jobs only
crontab -l | grep -E "daily_monitoring|generate_weekly_report"
```

### Remove Monitoring Jobs

```bash
# CAUTION: This removes ALL cron jobs
crontab -r

# To remove only monitoring jobs, edit crontab:
crontab -e
# Delete lines containing daily_monitoring_check or generate_weekly_report
```

---

## Monitoring Reports

### Report Locations

**Daily Reports:** `monitoring_reports/daily_report_YYYY-MM-DD.md`
**Weekly Reports:** `monitoring_reports/weekly_report_week_N_YYYY-MM-DD.md`
**Logs:** `monitoring_logs/`

### View Latest Reports

```bash
# Latest daily report
cat monitoring_reports/daily_report_$(date +%Y-%m-%d).md

# Latest weekly report
ls -lt monitoring_reports/weekly_report_*.md | head -1 | awk '{print $NF}' | xargs cat

# All reports
ls -lh monitoring_reports/
```

---

## Monitoring Schedule

### Week 1 (Days 1-7)

**Daily Tasks:**
- [ ] Run validation script
- [ ] Check index usage
- [ ] Review error logs
- [ ] Document observations

**Friday (Day 7):**
- [ ] Generate weekly report
- [ ] Compare to baseline
- [ ] Assess production readiness

### Week 2 (Days 8-14)

**Daily Tasks:**
- [ ] Continue daily monitoring
- [ ] Track performance trends
- [ ] Watch for anomalies

**Monday (Day 8):**
- [ ] Review weekend data
- [ ] Check for issues

**Friday (Day 14):**
- [ ] Final performance report
- [ ] Production deployment decision
- [ ] Create deployment plan

---

## Alert Thresholds

### Critical Alerts (Immediate Action Required)

- Query time > 2x baseline (1000ms)
- Error rate > 1% for 1 hour
- Memory usage > 2x baseline (90MB)
- Database CPU > 80%
- Indexes not being used after 7 days

### Warning Alerts (Monitor Closely)

- Query time > 1.5x baseline (750ms)
- Error rate > 0.5% for 2 hours
- Cache hit rate < 70%
- Database connections > 90
- New indexes unused after 3 days

### Info Alerts (Normal)

- Index usage increasing
- Query times improving
- Memory usage decreasing
- Database load decreasing

---

## Troubleshooting

### Issue: Monitoring Script Fails

**Diagnosis:**
```bash
# Test script manually
bash scripts/daily_monitoring_check.sh

# Check error logs
cat monitoring_logs/daily_*.log | tail -50
```

**Solution:**
- Verify Python dependencies installed
- Check database connection
- Ensure scripts have execute permissions

### Issue: Index Usage Not Increasing

**Diagnosis:**
```bash
# Check if indexes exist
python scripts/validate_query_optimization.py

# Check query plans
EXPLAIN ANALYZE <your query>
```

**Solution:**
- Normal for low-traffic environments
- Run ANALYZE to update statistics
- Verify queries can use indexes
- Check for schema changes

### Issue: Query Performance Degraded

**Diagnosis:**
```bash
# Compare to baseline
python scripts/generate_weekly_report.py

# Check query plans
EXPLAIN ANALYZE <slow query>
```

**Solution:**
- Check index statistics
- Verify indexes are being used
- Look for table bloat
- Consider additional indexes

---

## Quick Reference

### Essential Commands

```bash
# Validate deployment
python scripts/validate_query_optimization.py

# Run daily monitoring
bash scripts/daily_monitoring_check.sh

# Generate weekly report
python scripts/generate_weekly_report.py --week 1

# Check index usage
python -c "from sqlalchemy import create_engine, text; from app.core.config import settings; engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', '')); conn = engine.connect(); result = conn.execute(text('SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE indexrelname LIKE \"idx_%\" ORDER BY idx_scan DESC')); [print(f'{r[0]}: {r[1]} scans') for r in result.fetchall()]"

# View latest daily report
cat monitoring_reports/daily_report_$(date +%Y-%m-%d).md

# Setup automated monitoring
bash scripts/setup_monitoring_cron.sh

# View cron jobs
crontab -l
```

### File Locations

- **Daily Monitoring:** `scripts/daily_monitoring_check.sh`
- **Weekly Report:** `scripts/generate_weekly_report.py`
- **Validation:** `scripts/validate_query_optimization.py`
- **Cron Setup:** `scripts/setup_monitoring_cron.sh`
- **Reports:** `monitoring_reports/`
- **Logs:** `monitoring_logs/`

---

## Support

**Documentation:**
- Quick Reference: `QUICK_REFERENCE_DEPLOYMENT.md`
- Deployment Status: `QUERY_OPTIMIZATION_DEPLOYMENT_STATUS.md`
- Complete: `DEPLOYMENT_COMPLETE_STAGING.md`
- Monitoring: `MONITORING_BASELINE_20250118.md`

**Issues:**
- Check logs: `monitoring_logs/`
- Run validation: `python scripts/validate_query_optimization.py`
- Review reports: `monitoring_reports/`
- Create GitHub issue for bugs

---

**Monitoring Started:** 2025-01-18
**Monitoring Ends:** 2025-02-01
**Production Target:** 2025-02-01
**Next Review:** 2025-01-20 (48 hours)
