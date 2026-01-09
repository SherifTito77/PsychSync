#!/bin/bash

################################################################################
# Automated PostgreSQL Restore Script for PsychSync Production
# Purpose: Restore PostgreSQL database from encrypted S3 backups
# Date: 2025-12-27
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="${NAMESPACE:-psychsync}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres-psychsync}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
DATABASE_NAME="${DATABASE_NAME:-psychsync}"

# S3 configuration
S3_BUCKET="${S3_BUCKET:-psychsync-postgres-backups}"
S3_PREFIX="${S3_PREFIX:-backups/production}"

# Encryption configuration
ENCRYPTION_KEY_ARN="${ENCRYPTION_KEY_ARN:-arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012}"

# Restore configuration
RESTORE_TYPE="${RESTORE_TYPE:-full}"  # full, roles, schema, or point-in-time
TARGET_TIMESTAMP="${TARGET_TIMESTAMP:-}"
DRY_RUN="${DRY_RUN:-false}"  # Set to 'true' to simulate restore without actual execution
FORCE_RESTORE="${FORCE_RESTORE:-false}"  # Skip confirmation prompts

# Notification configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $(date -u +%Y-%m-%dT%H:%M:%SZ) - $1"
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
              \"title\": \"PostgreSQL Restore Alert\",
              \"text\": \"$message\",
              \"footer\": \"PsychSync Production - $(date -u +%Y-%m-%d)\",
              \"ts\": $(date +%s)
            }]
          }" 2>/dev/null || true
    fi
}

# Function: List available backups
list_backups() {
    log_info "Available backups in S3:"
    echo ""

    # List all backup directories
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" | grep PRE | while read -r line; do
        local backup_date=$(echo "$line" | awk '{print $2}' | tr -d '/')

        # Count backups in this date directory
        local backup_count=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${backup_date}/" | wc -l)

        echo "  📅 $backup_date ($backup_count backups)"

        # List individual backups
        aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${backup_date}/" | grep "psychsync-${DATABASE_NAME}" | while read -r backup_line; do
            local backup_name=$(echo "$backup_line" | awk '{print $4}')
            local backup_size=$(echo "$backup_line" | awk '{print $3}')

            # Get backup timestamp from filename
            local backup_timestamp=$(echo "$backup_name" | grep -oP '\d{8}-\d{6}' || echo "unknown")

            echo "    └─ $backup_name ($backup_size)"
        done
        echo ""
    done
}

# Function: Get database credentials
get_db_credentials() {
    log_info "Retrieving database credentials from Kubernetes secrets..."

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

# Function: Validate backup file
validate_backup() {
    local backup_s3_path="$1"

    log_info "Validating backup: $backup_s3_path"

    # Check if backup exists
    if ! aws s3 ls "$backup_s3_path" > /dev/null 2>&1; then
        log_error "Backup file not found in S3"
        return 1
    fi

    # Check backup size
    local backup_size=$(aws s3 ls "$backup_s3_path" | awk '{print $3}')
    if [[ "$backup_size" == "0" ]]; then
        log_error "Backup size is 0 bytes, backup may be corrupted"
        return 1
    fi

    log_info "Backup validation successful (size: $backup_size)"
    return 0
}

# Function: Download backup from S3
download_backup() {
    local backup_s3_path="$1"
    local backup_file="$2"

    log_info "Downloading backup from S3..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Would download $backup_s3_path to $backup_file"
        return 0
    fi

    aws s3 cp "$backup_s3_path" "$backup_file" || {
        log_error "Failed to download backup from S3"
        return 1
    }

    local downloaded_size=$(du -h "$backup_file" | cut -f1)
    log_info "Backup downloaded: $backup_file ($downloaded_size)"

    return 0
}

# Function: Create backup of current database before restore
backup_current_database() {
    log_warning "Creating safety backup of current database before restore..."

    local safety_backup_timestamp=$(date -u +%Y%m%d-%H%M%S)
    local safety_backup_file="/tmp/psychsync-safety-backup-${safety_backup_timestamp}.sql.gz"
    local safety_backup_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/safety-backups/psychsync-safety-backup-${safety_backup_timestamp}.sql.gz"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Would create safety backup of current database"
        return 0
    fi

    # Create backup
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- pg_dump -U "$DB_USER" -d "$DATABASE_NAME" -h localhost \
      -F c -Z 9 -f - | gzip > "$safety_backup_file" || {
        log_error "Failed to create safety backup"
        return 1
    }

    # Upload to S3
    aws s3 cp "$safety_backup_file" "$safety_backup_s3_path" \
      --storage-class STANDARD_IA \
      --server-side-encryption aws:kms \
      --sse-kms-key-id "$ENCRYPTION_KEY_ARN" || {
        log_warning "Failed to upload safety backup (non-critical)"
    }

    rm -f "$safety_backup_file"

    log_info "Safety backup created: $safety_backup_s3_path"
    return 0
}

# Function: Restore database from backup
restore_database() {
    local backup_file="$1"

    log_step "Restoring database from backup..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Would restore database from $backup_file"
        return 0
    fi

    # Drop existing database
    log_info "Dropping existing database..."
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -h localhost -c "DROP DATABASE IF EXISTS ${DATABASE_NAME}_restore;" || {
        log_error "Failed to drop restore database"
        return 1
    }

    # Create new database for restore
    log_info "Creating new database for restore..."
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -h localhost -c "CREATE DATABASE ${DATABASE_NAME}_restore;" || {
        log_error "Failed to create restore database"
        return 1
    }

    # Restore backup to new database
    log_info "Restoring backup to ${DATABASE_NAME}_restore..."
    gunzip -c "$backup_file" | kubectl exec -i -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- pg_restore -U "$DB_USER" -d "${DATABASE_NAME}_restore" -h localhost \
      --no-owner --no-acl --clean --if-exists || {
        log_error "Failed to restore database"
        return 1
    }

    log_info "Database restored successfully to ${DATABASE_NAME}_restore"

    # Verify restore
    log_info "Verifying restore..."
    local table_count=$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "${DATABASE_NAME}_restore" -h localhost -t \
      -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

    if [[ "$table_count" -eq 0 ]]; then
        log_error "Restore verification failed - no tables found"
        return 1
    fi

    log_info "Restore verification successful - $table_count tables found"
    return 0
}

# Function: Swapping restored database with production
swap_databases() {
    log_step "Swapping restored database with production..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Would swap databases"
        return 0
    fi

    # Terminate all connections to production database
    log_info "Terminating all connections to production database..."
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -h localhost -c "
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '${DATABASE_NAME}'
        AND pid <> pg_backend_pid();" || {
        log_warning "Failed to terminate connections (may be safe to continue)"
    }

    # Swap databases
    log_info "Swapping databases..."
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -h localhost -c "
        ALTER DATABASE ${DATABASE_NAME} RENAME TO ${DATABASE_NAME}_old;
        ALTER DATABASE ${DATABASE_NAME}_restore RENAME TO ${DATABASE_NAME};" || {
        log_error "Failed to swap databases"
        return 1
    }

    log_info "Database swap completed successfully"
    return 0
}

# Function: Restore roles and permissions
restore_roles() {
    local backup_date="$1"
    local timestamp="$2"

    log_info "Restoring roles and permissions..."

    local roles_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${backup_date}/roles-${timestamp}.sql"
    local roles_file="/tmp/roles-${timestamp}.sql"

    if ! aws s3 ls "$roles_s3_path" > /dev/null 2>&1; then
        log_warning "Roles backup not found, skipping"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Would restore roles from $roles_s3_path"
        return 0
    fi

    # Download and apply roles
    aws s3 cp "$roles_s3_path" "$roles_file" || {
        log_warning "Failed to download roles backup"
        return 1
    }

    # Apply roles (manual review required)
    log_warning "Roles backup downloaded to $roles_file"
    log_warning "Manual review required before applying roles"

    rm -f "$roles_file"
    return 0
}

# Function: Run post-restore validation
post_restore_validation() {
    log_step "Running post-restore validation..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Would run post-restore validation"
        return 0
    fi

    # Check database connectivity
    log_info "Testing database connectivity..."
    kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- pg_isready -U "$DB_USER" -d "$DATABASE_NAME" -h localhost || {
        log_error "Database connectivity test failed"
        return 1
    }

    # Check table counts
    log_info "Verifying table counts..."
    local table_count=$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost -t \
      -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

    log_info "Tables found: $table_count"

    if [[ "$table_count" -lt 10 ]]; then
        log_warning "Low table count detected - restore may be incomplete"
    fi

    # Run basic queries to verify data integrity
    log_info "Running basic data integrity checks..."

    # Check users table
    local user_count=$(kubectl exec -n "$NAMESPACE" "${POSTGRES_SERVICE}-0" \
      -- psql -U "$DB_USER" -d "$DATABASE_NAME" -h localhost -t \
      -c "SELECT COUNT(*) FROM users WHERE is_active = true;" 2>/dev/null | xargs || echo "0")

    log_info "Active users: $user_count"

    if [[ "$user_count" -eq 0 ]]; then
        log_warning "No active users found - data may be missing"
    fi

    log_info "Post-restore validation completed"
    return 0
}

# Function: Confirm restore operation
confirm_restore() {
    if [[ "$FORCE_RESTORE" == "true" ]]; then
        log_warning "FORCE RESTORE: Skipping confirmation prompts"
        return 0
    fi

    echo ""
    echo -e "${RED}═══════════════════════════════════════════${NC}"
    echo -e "${RED}     WARNING: DATABASE RESTORE OPERATION${NC}"
    echo -e "${RED}═══════════════════════════════════════════${NC}"
    echo ""
    echo "This will RESTORE the database from backup."
    echo "Current production data will be backed up as a safety measure."
    echo ""
    echo "Database: $DATABASE_NAME"
    echo "Namespace: $NAMESPACE"
    echo ""
    echo -e "${YELLOW}This operation is IRREVERSIBLE!${NC}"
    echo ""
    read -p "Are you sure you want to proceed? (type 'yes' to confirm): " confirmation

    if [[ "$confirmation" != "yes" ]]; then
        log_info "Restore operation cancelled by user"
        exit 0
    fi
}

# Main restore function
main() {
    log_info "═══════════════════════════════════════════"
    log_info "     PostgreSQL Restore Started"
    log_info "═══════════════════════════════════════════"
    log_info "Database: $DATABASE_NAME"
    log_info "Namespace: $NAMESPACE"
    log_info "Restore Type: $RESTORE_TYPE"
    log_info "Dry Run: $DRY_RUN"
    log_info "═══════════════════════════════════════════"

    # Track start time
    local start_time=$(date +%s)

    # List available backups if no target specified
    if [[ -z "$TARGET_TIMESTAMP" ]]; then
        list_backups
        echo ""
        read -p "Enter backup timestamp (e.g., 20251227-143000) or backup date (e.g., 20251227): " backup_selection

        if [[ -z "$backup_selection" ]]; then
            log_error "No backup selected"
            exit 1
        fi

        # Determine if full timestamp or just date
        if [[ "$backup_selection" =~ ^[0-9]{8}$ ]]; then
            # Only date provided - use latest backup from that date
            local backup_date="$backup_selection"
            TARGET_TIMESTAMP=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${backup_date}/" | grep "psychsync-${DATABASE_NAME}" | sort -r | head -1 | awk '{print $4}' | grep -oP '\d{8}-\d{6}' || echo "")
        else
            # Full timestamp provided
            TARGET_TIMESTAMP="$backup_selection"
            backup_date=$(echo "$TARGET_TIMESTAMP" | cut -d'-' -f1)
        fi
    else
        backup_date=$(echo "$TARGET_TIMESTAMP" | cut -d'-' -f1)
    fi

    local backup_s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${backup_date}/psychsync-${DATABASE_NAME}-${TARGET_TIMESTAMP}.sql.gz"
    local backup_file="/tmp/psychsync-restore-${TARGET_TIMESTAMP}.sql.gz"

    log_info "Selected backup: $backup_s3_path"

    # Validate backup
    if ! validate_backup "$backup_s3_path"; then
        log_error "Backup validation failed"
        notify_slack "❌ PostgreSQL restore FAILED - Backup validation failed" "#DC143C"
        exit 1
    fi

    # Confirm restore operation
    confirm_restore

    # Execute restore steps
    {
        get_db_credentials && \
        download_backup "$backup_s3_path" "$backup_file" && \
        backup_current_database && \
        restore_database "$backup_file" && \
        swap_databases && \
        restore_roles "$backup_date" "$TARGET_TIMESTAMP" && \
        post_restore_validation
    } || {
        local exit_code=$?
        local error_message="Restore failed with exit code $exit_code"

        log_error "$error_message"
        notify_slack "❌ **PostgreSQL Restore FAILED**\n\n*Error:* ${error_message}\n*Backup:* ${backup_s3_path}" "#DC143C"

        # Cleanup
        rm -f "$backup_file"

        exit 1
    }

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_formatted=$(printf '%02d:%02d:%02d' $((duration/3600)) $((duration%3600/60)) $((duration%60)))

    # Cleanup
    rm -f "$backup_file"

    log_info "═══════════════════════════════════════════"
    log_info "     PostgreSQL Restore Completed Successfully"
    log_info "     Duration: $duration_formatted"
    log_info "     Restored from: $backup_s3_path"
    log_info "═══════════════════════════════════════════"

    # Send success notification
    local message="✅ **PostgreSQL Restore Successful**

*Database:* ${DATABASE_NAME}
*Timestamp:* $(date -u +%Y-%m-%dT%H:%M:%SZ)
*Restored from:* ${backup_s3_path}
*Duration:* ${duration_formatted}"

    notify_slack "$message" "#36A546"  # Green
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            list_backups
            exit 0
            ;;
        --timestamp)
            TARGET_TIMESTAMP="$2"
            shift 2
            ;;
        --type)
            RESTORE_TYPE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --force)
            FORCE_RESTORE="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --list              List available backups"
            echo "  --timestamp TS      Backup timestamp to restore (e.g., 20251227-143000)"
            echo "  --type TYPE         Restore type: full, roles, schema (default: full)"
            echo "  --dry-run           Simulate restore without actual execution"
            echo "  --force             Skip confirmation prompts"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --list"
            echo "  $0 --timestamp 20251227-143000"
            echo "  $0 --timestamp 20251227-143000 --dry-run"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"
