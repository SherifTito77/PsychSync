#!/bin/bash

################################################################################
# Automated PostgreSQL Backup Script for PsychSync Production
# Purpose: Create encrypted backups every 6 hours with automated rotation
# Schedule: Kubernetes CronJob (every 6 hours at 0, 6, 12, 18 UTC)
# Date: 2025-12-27
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
NAMESPACE="${NAMESPACE:-psychsync}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres-psychsync}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
DATABASE_NAME="${DATABASE_NAME:-psychsync}"

# Backup configuration
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"  # Keep 30 days of backups
BACKUP_TYPE="${BACKUP_TYPE:-full}"  # full or incremental

# S3 configuration
S3_BUCKET="${S3_BUCKET:-psychsync-postgres-backups}"
S3_PREFIX="backups/production"
S3_STORAGE_CLASS="${S3_STORAGE_CLASS:-STANDARD_IA}"  # Use infrequent access for cost savings

# Encryption configuration
ENCRYPTION_KEY_ARN="${ENCRYPTION_KEY_ARN:-arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012}"
ENCRYPTION_CONTEXT="psychsync-production-db-backup"

# Notification configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
PAGERDUTY_KEY="${PAGERDUTY_KEY:-}"

# Timestamp
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
DATE_ONLY=$(date -u +%Y%m%d)

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date -u +%Y-%m-%dT%H:%M:%SZ) - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date -u +%Y-%m-%dT%H:%M:%SZ) - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date -u +%Y-%m-%dT%H:%M:%SZ) - $1"
}

notify_slack() {
    local message="$1"
    local color="${2:-#36A5FF}"  # Blue by default

    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST "$SLACK_WEBHOOK" \
          -H 'Content-Type: application/json' \
          -d "{
            \"attachments\": [{
              \"color\": \"$color\",
              \"title\": \"PostgreSQL Backup Alert\",
              \"text\": \"$message\",
              \"footer\": \"PsychSync Production - $(date -u +%Y-%m-%d)\",
              \"ts\": $(date +%s)
            }]
          }" 2>/dev/null || true
    fi
}

# Function: Get database credentials from Kubernetes secrets
get_db_credentials() {
    log_info "Retrieving database credentials from Kubernetes secrets..."

    # Get credentials from Kubernetes secret
    DB_USER=$(kubectl get secret psychsync-database -n "$NAMESPACE" -o jsonpath='{.data.DATABASE_USER}' | base64 -d)
    DB_PASSWORD=$(kubectl get secret psychsync-database -n "$NAMESPACE" -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d)
    DB_HOST=$(kubectl get secret psychsync-database -n "$NAMESPACE" -o jsonpath='{.data.DATABASE_HOST}' | base64 -d)

    if [[ -z "$DB_USER" ]] || [[ -z "$DB_PASSWORD" ]] || [[ -z "$DB_HOST" ]]; then
        log_error "Failed to retrieve database credentials from Kubernetes"
        return 1
    fi

    log_info "Database credentials retrieved successfully"
    return 0
}

# Function: Test database connectivity
test_database_connection() {
    log_info "Testing database connectivity..."

    # Use kubectl exec to run pg_isready
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- pg_isready -U "$DB_USER" -d "$DATABASE_NAME" -h localhost || {
        log_error "Database connectivity test failed"
        return 1
    }

    log_info "Database connectivity test passed"
    return 0
}

# Function: Create backup using pg_dump
create_backup() {
    log_info "Creating PostgreSQL backup..."

    local backup_file="/tmp/psychsync-${DATABASE_NAME}-${TIMESTAMP}.sql.gz"
    local backup_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/psychsync-${DATABASE_NAME}-${TIMESTAMP}.sql.gz"

    # Create backup using pg_dump from the database pod
    log_info "Running pg_dump..."

    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- pg_dump \
        -U "$DB_USER" \
        -d "$DATABASE_NAME" \
        -h localhost \
        -p "$POSTGRES_PORT" \
        -F c \
        -Z 9 \
        -f - \
        --schema=public \
        --exclude-table-data='schema_migrations' \
        --exclude-table-data='alembic_version' | \
        gzip > "$backup_file" || {
        log_error "pg_dump failed"
        rm -f "$backup_file"
        return 1
    }

    local backup_size=$(du -h "$backup_file" | cut -f1)
    log_info "Backup created: $backup_file ($backup_size)"

    # Upload to S3 with encryption
    log_info "Uploading backup to S3..."

    aws s3 cp "$backup_file" "$backup_s3_path" \
      --storage-class "$S3_STORAGE_CLASS" \
      --server-side-encryption aws:kms \
      --sse-kms-key-id "$ENCRYPTION_KEY_ARN" \
      --metadata "timestamp=$TIMESTAMP,database=$DATABASE_NAME,type=full,encryption=aws:kms" \
      --tag "timestamp=$TIMESTAMP" \
      --tag "database=$DATABASE_NAME" \
      --tag "type=full" \
      --tag "environment=production" || {
        log_error "S3 upload failed"
        rm -f "$backup_file"
        return 1
    }

    log_info "Backup uploaded successfully to $backup_s3_path"

    # Generate backup manifest
    local manifest_file="/tmp/backup-manifest-${TIMESTAMP}.json"
    cat > "$manifest_file" <<EOF
{
  "backup_id": "${TIMESTAMP}",
  "database": "$DATABASE_NAME",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_file": "$backup_s3_path",
  "backup_size": "$backup_size",
  "backup_type": "$BACKUP_TYPE",
  "encryption": "aws:kms",
  "encryption_key_arn": "$ENCRYPTION_KEY_ARN",
  "s3_bucket": "$S3_BUCKET",
  "retention_days": "$BACKUP_RETENTION_DAYS",
  "server_version": "$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" -- psql -U "$DB_USER" -d "$DATABASE_NAME" -t -c 'SELECT version();' | xargs)",
  "postgresql_version": "$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" -- psql -U "$DB_USER" -d "$DATABASE_NAME" -t -c 'SELECT version();')"
}
EOF

    # Upload manifest to S3
    local manifest_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/manifest-${TIMESTAMP}.json"
    aws s3 cp "$manifest_file" "$manifest_s3_path" || {
        log_warning "Failed to upload backup manifest (non-critical)"
    }

    # Cleanup local files
    rm -f "$backup_file" "$manifest_file"

    # Verify backup
    if ! aws s3 ls "$backup_s3_path" > /dev/null 2>&1; then
        log_error "Backup verification failed - file not found in S3"
        return 1
    fi

    log_info "Backup verification successful"

    return 0
}

# Function: Backup database roles and permissions
backup_roles() {
    log_info "Backing up database roles and permissions..."

    local roles_file="/tmp/roles-${TIMESTAMP}.sql"
    local roles_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/roles-${TIMESTAMP}.sql"

    # Dump roles
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -c "\du" > "$roles_file" || {
        log_warning "Failed to backup roles"
        return 1
    }

    # Upload to S3
    aws s3 cp "$roles_file" "$roles_s3_path" \
      --storage-class "$S3_STORAGE_CLASS" \
      --server-side-encryption aws:kms \
      --sse-kms-key-id "$ENCRYPTION_KEY_ARN" || {
        log_warning "Failed to upload roles backup (non-critical)"
    }

    rm -f "$roles_file"

    log_info "Roles backup completed"
    return 0
}

# Function: Backup database schema only
backup_schema() {
    log_info "Backing up database schema..."

    local schema_file="/tmp/schema-${TIMESTAMP}.sql.gz"
    local schema_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/schema-${TIMESTAMP}.sql.gz"

    # Dump schema only
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- pg_dump -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -p "$POSTGRES_PORT" \
      -s \
      -f - | gzip > "$schema_file" || {
        log_warning "Failed to backup schema"
        return 1
    }

    # Upload to S3
    aws s3 cp "$schema_file" "$schema_s3_path" \
      --storage-class "$S3_STORAGE_CLASS" \
      --server-side-encryption aws:kms \
      --sse-kms-key-id "$ENCRYPTION_KEY_ARN" || {
        log_warning "Failed to upload schema backup (non-critical)"
    }

    rm -f "$schema_file"

    log_info "Schema backup completed"
    return 0
}

# Function: Create database checksum for verification
create_checksum() {
    log_info "Creating database checksum for verification..."

    local checksum_file="/tmp/checksum-${TIMESTAMP}.txt"
    local checksum_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/checksum-${TIMESTAMP}.txt"

    # Get row counts for all tables
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -c "
      SELECT
        schemaname,
        tablename,
        n_live_tup as row_count
      FROM pg_stats
      WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
      ORDER BY schemaname, tablename
      " > "$checksum_file"

    # Upload to S3
    aws s3 cp "$checksum_file" "$checksum_s3_path" \
      --storage-class "$S3_STORAGE_CLASS" \
      --server-side-encryption aws:kms \
      --sse-kms-key-id "$ENCRYPTION_KEY_ARN" || {
        log_warning "Failed to upload checksum (non-critical)"
    }

    rm -f "$checksum_file"

    log_info "Checksum created"
    return 0
}

# Function: Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."

    # List old backups
    local old_backups=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" | grep "PRE" | awk '{print $2}' | while read -r backup_path; do
        backup_date=$(echo "$backup_path" | cut -d'/' -f2)
        backup_timestamp=$(date -d "$backup_date" +%s 2>/dev/null || echo "0")
        current_timestamp=$(date +%s)
        age_seconds=$((current_timestamp - backup_timestamp))
        age_days=$((age_seconds / 86400))

        if [[ $age_days -gt $BACKUP_RETENTION_DAYS ]]; then
            log_info "Deleting old backup: $backup_path ($age_days days old)"
            aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}/$backup_path" --recursive
        fi
    done

    log_info "Old backups cleanup completed"
    return 0
}

# Function: Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."

    # List recent backups
    local latest_backup=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/" | grep "psychsync-${DATABASE_NAME}" | sort -r | head -1 | awk '{print $4}')

    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for verification"
        return 1
    fi

    log_info "Latest backup: $latest_backup"

    # Check backup size (should be > 0)
    backup_size=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/$latest_backup" | awk '{print $3}')
    if [[ "$backup_size" =~ ^0 && "0" -eq "$backup_size" ]]; then
        log_error "Backup size is 0 bytes, backup may be corrupted"
        return 1
    fi

    log_info "Backup size: $backup_size"

    # TODO: Implement restore test (see restore script)
    log_info "Backup verification completed"

    return 0
}

# Function: Create backup metadata document
create_backup_metadata() {
    log_info "Creating backup metadata document..."

    local metadata_file="/tmp/metadata-${TIMESTAMP}.json"
    local metadata_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/metadata-${TIMESTAMP}.json"

    # Get database size
    local db_size=$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -t -c "SELECT pg_size_pretty(pg_database_size('$DATABASE_NAME'));" | xargs)

    # Get number of tables
    local num_tables=$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

    # Get PostgreSQL version
    local pg_version=$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -t -c "SELECT version();" | xargs)

    cat > "$metadata_file" <<EOF
{
  "backup_id": "${TIMESTAMP}",
  "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "database_name": "$DATABASE_NAME",
  "database_size": "$db_size",
  "num_tables": "$num_tables",
  "postgresql_version": "$pg_version",
  "backup_type": "$BACKUP_TYPE",
  "retention_days": "$BACKUP_RETENTION_DAYS",
  "s3_bucket": "$S3_BUCKET",
  "s3_prefix": "$S3_PREFIX",
  "encryption": {
    "type": "aws:kms",
    "key_arn": "$ENCRYPTION_KEY_ARN",
    "context": "$ENCRYPTION_CONTEXT"
  },
  "backup_files": [
    "${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/psychsync-${DATABASE_NAME}-${TIMESTAMP}.sql.gz",
    "${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/roles-${TIMESTAMP}.sql",
    "${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/schema-${TIMESTAMP}.sql.gz",
    "${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/checksum-${TIMESTAMP}.txt",
    "${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/manifest-${TIMESTAMP}.json"
  ],
  "cluster": "psychsync-production",
  "namespace": "$NAMESPACE",
  "backup_script_version": "1.0.0"
}
EOF

    # Upload to S3
    aws s3 cp "$metadata_file" "$metadata_s3_path" \
      --storage-class "$S3_STORAGE_CLASS" \
      --server-side-encryption aws:kms \
      --sse-kms-key-id "$ENCRYPTION_KEY_ARN" || {
        log_warning "Failed to upload metadata (non-critical)"
    }

    rm -f "$metadata_file"

    log_info "Backup metadata created"
    return 0
}

# Function: Send success notification
notify_success() {
    local message="✅ **PostgreSQL Backup Successful**

*Backup ID:* ${TIMESTAMP}
*Database:* ${DATABASE_NAME}
*Timestamp:* $(date -u +%Y-%m-%dT%H:%M:%SZ)
*S3 Location:* s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/
*Retention:* ${BACKUP_RETENTION_DAYS} days
*Encryption:* AWS KMS (${ENCRYPTION_KEY_ARN})"

    notify_slack "$message" "#36A546"  # Green
}

# Function: Send failure notification
notify_failure() {
    local error_message="$1"

    local message="❌ **PostgreSQL Backup FAILED**

*Database:* ${DATABASE_NAME}
*Timestamp:* $(date -u +%Y-%m-%dT%H:%M:%SZ)
*Error:* ${error_message}

Immediate action required!"
    notify_slack "$message" "#DC143C"  # Red

    # Trigger PagerDuty
    if [[ -n "$PAGERDUTY_KEY" ]]; then
        curl -X POST "https://events.pagerduty.com/v2/enqueue/${PAGERDUTY_KEY}" \
          -H 'Content-Type: application/json' \
          -H 'Accept: application/json' \
          -d "{
            \"payload\": {
              \"summary\": \"PostgreSQL backup failed\",
              \"severity\": \"error\",
              \"source\": \"postgres-backup\",
              \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
              \"custom_details\": {
                \"database\": \"${DATABASE_NAME}\",
                \"error\": \"${error_message}\",
                \"cluster\": \"psychsync-production\"
              }
            },
            \"routing_key\": \"${PAGERDUTY_KEY}\"
          }" 2>/dev/null || true
    fi
}

# Main backup function
main() {
    log_info "═══════════════════════════════════════════"
    log_info "     PostgreSQL Backup Started"
    log_info "═══════════════════════════════════════════"
    log_info "Database: $DATABASE_NAME"
    log_info "Backup ID: $TIMESTAMP"
    log_info "Retention: $BACKUP_RETENTION_DAYS days"
    log_info "Encryption: AWS KMS (${ENCRYPTION_KEY_ARN})"
    log_info "═══════════════════════════════════════════"

    # Track start time
    local start_time=$(date +%s)

    # Execute backup steps
    {
        get_db_credentials && \
        test_database_connection && \
        create_backup && \
        backup_roles && \
        backup_schema && \
        create_checksum && \
        create_backup_metadata && \
        verify_backup && \
        cleanup_old_backups && \
        notify_success
    } || {
        local exit_code=$?
        local error_message="Backup failed with exit code $exit_code"

        log_error "$error_message"
        notify_failure "$error_message"
        exit 1
    }

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_formatted=$(printf '%02d:%02d:%02d' $((duration/3600)) $((duration%3600/60)) $((duration%60)))

    log_info "═══════════════════════════════════════════"
    log_info "     PostgreSQL Backup Completed Successfully"
    log_info "     Duration: $duration_formatted"
    log_info "     Backup ID: $TIMESTAMP"
    log_info "═══════════════════════════════════════════"
}

# Execute main function
main "$@"
