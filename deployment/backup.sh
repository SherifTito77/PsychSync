#!/bin/bash

# PsychSync Production Backup Script
# This script performs automated backups of database and uploads to S3

set -euo pipefail

# Source environment variables
if [ -f /.env.production ]; then
    source /.env.production
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="${BACKUP_DIR}/psychsync_db_${DATE}.sql"
COMPRESSED_BACKUP_FILE="${BACKUP_DIR}/psychsync_db_${DATE}.sql.gz"
S3_BUCKET="${BACKUP_S3_BUCKET}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Cleanup function
cleanup() {
    if [ -f "${DB_BACKUP_FILE}" ]; then
        rm -f "${DB_BACKUP_FILE}"
    fi
    if [ -f "${COMPRESSED_BACKUP_FILE}" ]; then
        rm -f "${COMPRESSED_BACKUP_FILE}"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

log "Starting backup process..."

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Extract database connection details from DATABASE_URL
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    log "ERROR: Unable to parse DATABASE_URL"
    exit 1
fi

# Export PGPASSWORD for pg_dump
export PGPASSWORD="${DB_PASSWORD}"

# Create database backup
log "Creating database backup..."
if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --no-password \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="${DB_BACKUP_FILE}"; then
    log "Database backup created successfully: ${DB_BACKUP_FILE}"
else
    log "ERROR: Database backup failed"
    exit 1
fi

# Compress backup
log "Compressing backup..."
gzip "${DB_BACKUP_FILE}"

# Get file size for logging
BACKUP_SIZE=$(du -h "${COMPRESSED_BACKUP_FILE}" | cut -f1)
log "Backup compressed: ${BACKUP_SIZE}"

# Upload to S3 if configured
if [ -n "${S3_BUCKET}" ] && [ -n "${AWS_ACCESS_KEY_ID}" ]; then
    log "Uploading backup to S3: s3://${S3_BUCKET}/database/"

    S3_KEY="database/psychsync_db_${DATE}.sql.gz"

    if aws s3 cp "${COMPRESSED_BACKUP_FILE}" "s3://${S3_BUCKET}/${S3_KEY}" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256; then
        log "Backup uploaded to S3 successfully: ${S3_KEY}"

        # Verify upload
        if aws s3 ls "s3://${S3_BUCKET}/${S3_KEY}" > /dev/null 2>&1; then
            log "S3 upload verified"
        else
            log "WARNING: S3 upload verification failed"
        fi
    else
        log "ERROR: S3 upload failed"
        exit 1
    fi
else
    log "WARNING: S3 not configured, skipping upload"
fi

# Clean up old local backups
log "Cleaning up local backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "psychsync_db_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

# Clean up old S3 backups if configured
if [ -n "${S3_BUCKET}" ]; then
    log "Cleaning up S3 backups older than ${RETENTION_DAYS} days..."

    # Calculate cutoff date
    CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%Y%m%d)

    # List and delete old backups
    aws s3 ls "s3://${S3_BUCKET}/database/" | while read -r line; do
        # Extract date from filename (format: psychsync_db_YYYYMMDD_HHMMSS.sql.gz)
        if [[ $line =~ psychsync_db_([0-9]{8})_[0-9]{6}\.sql\.gz ]]; then
            BACKUP_DATE="${BASH_REMATCH[1]}"
            if [ "${BACKUP_DATE}" -lt "${CUTOFF_DATE}" ]; then
                S3_KEY=$(echo "$line" | awk '{print $4}')
                log "Deleting old S3 backup: ${S3_KEY}"
                aws s3 rm "s3://${S3_BUCKET}/database/${S3_KEY}"
            fi
        fi
    done
fi

log "Backup process completed successfully"

# Send notification if configured
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ PsychSync backup completed successfully\\nSize: ${BACKUP_SIZE}\\nDate: $(date)\"}" \
        "${SLACK_WEBHOOK_URL}" || true
fi
