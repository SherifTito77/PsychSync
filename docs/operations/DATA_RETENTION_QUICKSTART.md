# Data Retention & Archiving - Quick Start Guide

**Last Updated:** 2026-01-04
**Version:** 1.0

---

## Quick Setup (5 Minutes)

### 1. Initialize the System

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/psychsync"
export AWS_REGION="us-east-1"
export ARCHIVE_BUCKET="psychsync-data-archive"
export FROZEN_BUCKET="psychsync-frozen-archive"
export KMS_KEY_ALIAS="alias/psychsync-archive-key"

# Run initialization
python scripts/setup_data_retention.py --action init
```

### 2. Validate Configuration

```bash
python scripts/setup_data_retention.py --action validate
```

### 3. Test Archival (Dry Run)

```bash
# Preview what would be archived
python scripts/setup_data_retention.py --action archive --dry-run
```

### 4. Run First Archive

```bash
# Confirm and run
python scripts/setup_data_retention.py --action archive
```

---

## Daily Operations

### Check Archive Status

```bash
python scripts/setup_data_retention.py --action stats
```

Expected output:
```
Policies:
  assessment_responses_6months              | Active: True | Last run: 2026-01-04 02:00:00
  analytics_3months                         | Active: True | Last run: 2026-01-04 03:00:00

Archives:
  assessment_responses                      | Archives:   12 | Records:    150000 | Size:   2.50 GB
  analytics                                | Archives:    6 | Records:     50000 | Size:   0.80 GB

Database size: 298 GB
```

### Manual Archival

```bash
# For specific data type
python -c "
import asyncio
from scripts.setup_data_retention import RetentionService
from app.core.database import engine

async def manual_archive():
    service = RetentionService(engine)
    await service.process_retention(dry_run=False)

asyncio.run(manual_archive())
"
```

---

## Schedule Automated Jobs

### Option 1: Cron (Linux)

```bash
# Edit crontab
crontab -e

# Add these lines:
0 2 * * * cd /app && python scripts/setup_data_retention.py --action archive >> /var/log/archive.log 2>&1
0 6 * * * cd /app && python scripts/setup_data_retention.py --action stats >> /var/log/stats.log 2>&1
```

### Option 2: systemd Timer

Create `/etc/systemd/system/psychsync-archive.service`:

```ini
[Unit]
Description=PsychSync Data Archival Service
After=network.target postgresql.service

[Service]
Type=oneshot
User=psychsync
WorkingDirectory=/app
Environment="PATH=/app/venv/bin"
ExecStart=/app/venv/bin/python scripts/setup_data_retention.py --action archive

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/psychsync-archive.timer`:

```ini
[Unit]
Description=PsychSync Daily Archive Timer
Requires=psychsync-archive.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable psychsync-archive.timer
sudo systemctl start psychsync-archive.timer
```

### Option 3: Airflow DAG

```python
# dags/data_retention_dag.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'psychsync',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 4),
    'email': ['ops-team@psychsync.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'psychsync_data_retention',
    default_args=default_args,
    description='Daily data archival job',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['retention', 'archive', 'maintenance'],
)

archive_task = BashOperator(
    task_id='run_data_archival',
    bash_command='cd /app && python scripts/setup_data_retention.py --action archive',
    dag=dag,
)

stats_task = BashOperator(
    task_id='collect_stats',
    bash_command='cd /app && python scripts/setup_data_retention.py --action stats',
    dag=dag,
)

archive_task >> stats_task
```

---

## Monitor & Troubleshoot

### Check Logs

```bash
# View recent logs
tail -f data_retention_setup.log

# Check for errors
grep ERROR data_retention_setup.log | tail -20
```

### Health Check

```bash
# Via API (if implemented)
curl http://localhost:8000/api/v1/retention/health

# Expected response:
{
  "status": "healthy",
  "last_archive": "2026-01-04T02:00:00Z",
  "hours_since_last_archive": 4.5,
  "archive_queue_size": 0,
  "database_size_gb": 298,
  "archive_size_gb": 150.5
}
```

### Common Issues

**Issue: Archive job failing**
```bash
# Check error messages
grep "Failed to process policy" data_retention_setup.log

# Common fixes:
# - Check database connection
# - Verify S3 bucket exists
# - Check KMS key permissions
# - Ensure sufficient disk space
```

**Issue: Slow archival**
```bash
# Check database size
SELECT pg_size_pretty(pg_database_size('psychsync'));

# Optimize tables
VACUUM ANALYZE assessment_responses;

# Increase batch size if needed (edit script)
```

**Issue: Missing data after archival**
```bash
# Use restoration script
python scripts/restore_from_archive.py assessment_responses 2023-01-01 2023-12-31 --to-db
```

---

## Storage Estimation

Calculate expected savings:

```python
# Quick estimation script
import pandas as pd

# Current database size
current_db_size_gb = 500

# Growth rate (GB/month)
growth_rate_gb_per_month = 50

# Without archiving
size_12_months_no_archive = current_db_size_gb + (growth_rate_gb_per_month * 12)

# With archiving (65% reduction)
archived_percentage = 0.65
size_12_months_with_archive = (current_db_size_gb * (1 - archived_percentage)) + \
                              (growth_rate_gb_per_month * (1 - archived_percentage) * 12)

print(f"Without archiving: {size_12_months_no_archive:.0f} GB")
print(f"With archiving: {size_12_months_with_archive:.0f} GB")
print(f"Savings: {size_12_months_no_archive - size_12_months_with_archive:.0f} GB")

# Cost estimation (us-east-1)
cost_no_archive = size_12_months_no_archive * 0.25  # SSD
cost_with_archive = size_12_months_with_archive * 0.25  # Hot
print(f"\nMonthly cost without: ${cost_no_archive:.2f}")
print(f"Monthly cost with: ${cost_with_archive:.2f}")
print(f"Monthly savings: ${cost_no_archive - cost_with_archive:.2f}")
```

---

## Retention Policy Reference

Default policies configured by the system:

| Data Type | Keep For | Archive After | Storage | Auto-Delete |
|-----------|----------|---------------|---------|-------------|
| Assessment Responses | 2 years | 6 months | S3 | Yes (after 7 years) |
| Individual Responses | 2 years | 6 months | S3 | Yes |
| Analytics | 1 year | 3 months | S3 | Yes |
| Audit Logs | 7 years | 3 months | S3 | Yes |
| Report Cache | 7 days | Never | Delete | Yes |
| Report Views | 6 months | 90 days | S3 | Yes |
| Wellness Data | 7 years | 2 years | S3 | Yes |
| Team Dynamics | 2 years | 1 year | S3 | Yes |

---

## Modify Policies

### Update Retention Period

```sql
-- Connect to database
psql -d psychsync

-- Update policy
UPDATE retention_policies
SET retention_period_days = 365,  -- Change to 1 year
    archive_after_days = 90,       -- Archive after 3 months
    updated_at = NOW()
WHERE policy_name = 'assessment_responses_6months';

-- Add new policy
INSERT INTO retention_policies (
    policy_name, data_type, source_table,
    retention_period_days, archive_after_days,
    target_storage, is_active, schedule, next_run_at
) VALUES (
    'custom_data_30days',
    'custom_data',
    'custom_table',
    30,  -- Keep 30 days
    7,   -- Archive after 1 week
    's3',
    TRUE,
    '0 3 * * *',
    NOW() + INTERVAL '1 hour'
);
```

### Pause Policy

```sql
UPDATE retention_policies
SET is_active = FALSE
WHERE policy_name = 'analytics_3months';
```

---

## Backup & Restore

### Before Archival

```bash
# Take database backup
pg_dump -U postgres -d psychsync -F c -b -v -f \
    "backups/pre-archive-$(date +%Y%m%d).dump"

# Verify backup
pg_restore -l "backups/pre-archive-$(date +%Y%m%d).dump"
```

### Restore from Archive

```python
# Use the restoration script
import asyncio
from scripts.restore_from_archive import restore_data
from datetime import datetime

async def restore():
    # Restore to temporary location first
    await restore_data(
        data_type='assessment_responses',
        date_range=(datetime(2023, 1, 1), datetime(2023, 12, 31)),
        target_db=False  # Set to True to restore to database
    )

asyncio.run(restore())
```

---

## Security Checklist

- [ ] KMS encryption key created
- [ ] S3 bucket policies restrict access
- [ ] Database credentials secured
- [ ] Archive catalog access controlled
- [ ] Audit logging enabled
- [ ] Legal hold process tested
- [ ] Data anonymization verified
- [ ] Backup procedures tested
- [ ] Restoration drills conducted

---

## Contact & Support

**Documentation:** `docs/operations/DATA_RETENTION_ARCHIVING_STRATEGY.md`

**Scripts:**
- Setup: `scripts/setup_data_retention.py`
- SQL Templates: `scripts/archive_old_data.sql`
- Restore: `scripts/restore_from_archive.py`

**Support:**
- Operations Team: ops-team@psychsync.com
- Data Privacy Officer: dpo@psychsync.com
- Emergency Pager: [Configure in PagerDuty]

---

**Remember:**
1. Always test on staging first
2. Take backups before large operations
3. Monitor the first few archival cycles
4. Document any custom policies
5. Review retention periods quarterly

---

*For detailed information, see the full strategy document.*
