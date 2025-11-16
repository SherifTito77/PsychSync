#/scripts/backup.sh
#!/bin/bash

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="psychsync_backup_$TIMESTAMP.sql.gz"

# Create backup
pg_dump -h localhost -U psychsync psychsync_db | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Keep only last 7 days
find $BACKUP_DIR -name "psychsync_backup_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
# aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" s3://your-bucket/backups/