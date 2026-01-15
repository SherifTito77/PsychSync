# Automated Churn Scoring - Cron Configuration

## Overview

The churn prediction scheduler should be run periodically to:
1. Calculate churn risk scores for all users
2. Execute intervention triggers for high-risk users
3. Update risk scores based on latest behavioral signals

## Recommended Scheduling

### Daily Incremental Scoring
Run every day to score recently active users and catch at-risk users early:

```cron
# Run daily at 2 AM UTC - score users active in last 7 days
0 2 * * * cd /path/to/psychsync && python -m app.services.churnScheduler --mode recent --days 7 >> /var/log/churn_scoring_daily.log 2>&1
```

### Weekly Full Scoring
Run once per week to ensure all users have up-to-date risk scores:

```cron
# Run every Sunday at 3 AM UTC - score all users
0 3 * * 0 cd /path/to/psychsync && python -m app.services.churnScheduler --mode all --batch-size 100 >> /var/log/churn_scoring_weekly.log 2>&1
```

### Hourly Critical Check (Optional)
For high-value customers, run more frequent checks for critical interventions:

```cron
# Run every 6 hours - score users active in last 24 hours
0 */6 * * * cd /path/to/psychsync && python -m app.services.churnScheduler --mode recent --days 1 --batch-size 50 >> /var/log/churn_scoring_hourly.log 2>&1
```

## Installation

### Linux/Mac (cron)

1. Open crontab:
```bash
crontab -e
```

2. Add the cron jobs from above

3. Verify:
```bash
crontab -l
```

### Systemd Timer (Alternative)

Create `/etc/systemd/system/churn-scoring.service`:
```ini
[Unit]
Description=PsychSync Churn Risk Scoring
After=network.target postgresql.service

[Service]
Type=oneshot
User=psychsync
WorkingDirectory=/path/to/psychsync
ExecStart=/path/to/psychsync/.venv/bin/python -m app.services.churnScheduler --mode recent --days 7
```

Create `/etc/systemd/system/churn-scoring.timer`:
```ini
[Unit]
Description=Run churn scoring daily
Requires=churn-scoring.service

[Timer]
OnCalendar=*-*-* 02:00:00
Unit=churn-scoring.service

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable churn-scoring.timer
sudo systemctl start churn-scoring.timer
sudo systemctl status churn-scoring.timer
```

### AWS Lambda (Cloud)

For serverless deployment, create a Lambda function:
- Runtime: Python 3.11
- Handler: `lambda_handler.lambda_handler`
- Trigger: EventBridge Schedule Expression (rate: 1 day)

```python
# lambda_handler.py
import asyncio
from app.services.churnScheduler import ChurnScoringScheduler

def lambda_handler(event, context):
    scheduler = ChurnScoringScheduler(batch_size=100)
    result = asyncio.run(scheduler.score_recent_users(days=7))
    return {
        'statusCode': 200,
        'body': f"Processed {result['users_processed']} users"
    }
```

### GitHub Actions (Free Alternative)

Create `.github/workflows/churn-scoring.yml`:
```yaml
name: Churn Risk Scoring

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run churn scoring
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          python -m app.services.churnScheduler --mode recent --days 7
```

## Monitoring

### Check Logs

```bash
# View recent logs
tail -f /var/log/churn_scoring_daily.log

# Search for errors
grep "ERROR" /var/log/churn_scoring_daily.log

# Check high-risk users
grep "User.*CRITICAL risk" /var/log/churn_scoring_daily.log | tail -20
```

### Manual Health Check

```bash
# Get risk summary
python -m app.services.churnScheduler --mode summary

# Score recent users manually
python -m app.services.churnScheduler --mode recent --days 1
```

## Performance

Expected performance on production database:
- **Small teams** (< 1,000 users): ~5 seconds
- **Mid-sized** (1,000-10,000 users): ~30-60 seconds
- **Large** (10,000+ users): ~2-5 minutes

Adjust `--batch-size` based on your database capacity:
- Lower batch size (50) for slower databases
- Higher batch size (200+) for fast databases with lots of memory

## Troubleshooting

### Issue: Scheduler runs but no users are scored

**Cause:** No users match the date criteria

**Solution:**
```bash
# Check if you have users in the database
psql -U psychsync_user -d psychsync_db -c "SELECT COUNT(*) FROM users;"

# Run in 'all' mode to score everyone
python -m app.services.churnScheduler --mode all
```

### Issue: High memory usage

**Cause:** Processing too many users at once

**Solution:** Reduce batch size:
```bash
python -m app.services.churnScheduler --mode all --batch-size 50
```

### Issue: Triggers not executing

**Cause:** Triggers may be on cooldown from previous runs

**Solution:** Check cooldown table:
```bash
psql -U psychsync_user -d psychsync_db -c "SELECT * FROM churn_trigger_cooldowns WHERE cooldown_until > NOW();"
```

## Alerts (Recommended)

Set up alerts for:
1. **Scheduler failures**: If cron job exits with non-zero status
2. **High-risk spike**: If > 10% of users are high-risk in a single run
3. **No users scored**: If scheduler runs but processes 0 users
4. **Long runtime**: If scoring takes > 10 minutes

Example alert (using a simple script):
```bash
# In cron job, add at the end:
python -m app.services.churnScheduler --mode recent --days 7
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Churn scoring failed with exit code $EXIT_CODE" | mail -s "Churn Scoring Alert" admin@example.com
fi
```
