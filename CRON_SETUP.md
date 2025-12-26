# Database Maintenance Cron Setup

This document explains how to set up automated database maintenance using cron jobs for the PsychSync application.

## Cron Schedule Configuration

Add the following entries to your crontab using `crontab -e`:

```bash
# PsychSync Database Maintenance
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
# │ │ │ │ │
# │ │ │ │ │
# * * * * *  /path/to/command

# Hourly maintenance (at minute 0)
0 * * * * /Users/sheriftito/Downloads/psychsync/scripts/cron_maintenance.sh hourly

# Daily maintenance (at 2:00 AM)
0 2 * * * /Users/sheriftito/Downloads/psychsync/scripts/cron_maintenance.sh daily

# Weekly maintenance (Sunday at 3:00 AM)
0 3 * * 0 /Users/sheriftito/Downloads/psychsync/scripts/cron_maintenance.sh weekly

# Monthly maintenance (1st of month at 4:00 AM)
0 4 1 * * /Users/sheriftito/Downloads/psychsync/scripts/cron_maintenance.sh monthly
```

## Environment Setup

### 1. Set Environment Variables

Create a `.env` file or set environment variables for the maintenance scripts:

```bash
# Database connection
export DATABASE_URL="postgresql://postgres:password@localhost:5432/psychsync"

# Alert configuration (optional)
export ALERT_EMAIL="admin@psychsync.com"

# Python path
export PYTHONPATH="/Users/sheriftito/Downloads/psychsync"
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/psychsync
sudo chown $USER:$USER /var/log/psychsync
chmod 755 /var/log/psychsync
```

### 3. Install Required Python Packages

```bash
pip3 install asyncpg psycopg2-binary
```

## Maintenance Tasks by Frequency

### Hourly Maintenance (Every Hour)
- Database connectivity check
- Statistics update for high-traffic tables
- Basic health monitoring

### Daily Maintenance (2:00 AM)
- Full VACUUM ANALYZE operation
- Index usage monitoring
- Materialized views refresh
- Performance metrics collection

### Weekly Maintenance (Sunday 3:00 AM)
- All daily maintenance tasks
- Long-running query monitoring
- Database size monitoring
- Storage usage analysis
- Partition management

### Monthly Maintenance (1st of Month 4:00 AM)
- All weekly maintenance tasks
- Deep table bloat analysis
- Comprehensive statistics update
- Monthly maintenance report generation
- Aggressive VACUUM operations if needed

## Monitoring and Alerts

### Log Files
Maintenance logs are stored in `/var/log/psychsync/`:
- `maintenance_YYYYMMDD.log` - Daily maintenance logs

### Alert Configuration
To receive email alerts for maintenance failures:

```bash
export ALERT_EMAIL="admin@psychsync.com"
```

The system will send alerts for:
- Maintenance task failures
- Database connectivity issues
- Critical storage problems
- High bloat levels

### Manual Execution

You can run maintenance manually:

```bash
# Run daily maintenance
./scripts/cron_maintenance.sh daily

# Run weekly maintenance
./scripts/cron_maintenance.sh weekly

# Run monthly maintenance
./scripts/cron_maintenance.sh monthly

# Show help
./scripts/cron_maintenance.sh help
```

## Security Considerations

1. **Database Credentials**: Store database credentials securely and limit access to maintenance scripts
2. **File Permissions**: Ensure only authorized users can execute maintenance scripts
3. **Log Rotation**: Set up log rotation to prevent unlimited log file growth

### Log Rotation Setup

Add to `/etc/logrotate.d/psychsync`:

```
/var/log/psychsync/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        # Optional: reload any services that might need to reopen log files
    endscript
}
```

## Performance Impact

### Maintenance Timing
- Scheduled during low-traffic periods (early morning)
- Uses `CONCURRENTLY` options to minimize blocking
- Progressive approach from light to heavy tasks

### Resource Usage
- Hourly: Minimal impact (< 1 minute)
- Daily: Moderate impact (5-15 minutes)
- Weekly: Higher impact (30-60 minutes)
- Monthly: Highest impact (1-3 hours)

### Monitoring Performance
Monitor database performance during maintenance:
- Connection count
- Query execution time
- System resource usage

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x scripts/cron_maintenance.sh
   chmod +x scripts/database_maintenance.py
   ```

2. **Python Module Not Found**
   ```bash
   pip3 install asyncpg psycopg2-binary
   ```

3. **Database Connection Failed**
   - Verify DATABASE_URL is correct
   - Check database is running
   - Verify network connectivity

4. **Log Directory Not Writable**
   ```bash
   sudo mkdir -p /var/log/psychsync
   sudo chown $USER:$USER /var/log/psychsync
   ```

### Debug Mode

To run maintenance with verbose output:

```bash
DEBUG=1 ./scripts/cron_maintenance.sh daily
```

### Testing Cron Jobs

Test cron job execution before deploying:

```bash
# Test with dry run
* * * * * /path/to/cron_maintenance.sh daily 2>&1 | logger -t test-maintenance
```

Check the logs to verify execution:

```bash
tail -f /var/log/syslog | grep test-maintenance
```

## Database Maintenance Best Practices

1. **Regular Monitoring**: Check maintenance logs regularly
2. **Performance Baseline**: Establish baseline performance metrics
3. **Backup Strategy**: Ensure backups before heavy maintenance
4. **Rollback Plan**: Have a plan to undo changes if needed
5. **Documentation**: Keep maintenance procedures updated
6. **Testing**: Test maintenance procedures in staging environment
7. **Monitoring**: Set up alerts for maintenance failures
8. **Scheduling**: Choose maintenance windows wisely
9. **Resource Planning**: Monitor system resources during maintenance
10. **Validation**: Verify maintenance completed successfully

## Emergency Procedures

If maintenance causes issues:

1. **Stop Maintenance**: Cancel running maintenance processes
2. **Check Logs**: Review recent maintenance logs for errors
3. **Rollback**: Apply database backups if necessary
4. **Notify**: Alert stakeholders of issues
5. **Investigate**: Analyze root cause of failures
6. **Document**: Record incidents and resolutions

## Integration with Monitoring Systems

### Prometheus Metrics

The maintenance script can expose metrics for Prometheus:

```python
# Add to database_maintenance.py
from prometheus_client import Counter, Histogram, Gauge

maintenance_counter = Counter('psychsync_maintenance_runs', 'Maintenance runs', ['task_type'])
maintenance_duration = Histogram('psychsync_maintenance_duration_seconds', 'Maintenance duration')
database_size = Gauge('psychsync_database_size_bytes', 'Database size')
```

### Grafana Dashboard

Create a Grafana dashboard to monitor:
- Database size over time
- Maintenance execution status
- Performance metrics
- Error rates

### Slack Integration

Send maintenance notifications to Slack:

```python
import requests

def send_slack_notification(message):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={'text': message})
```