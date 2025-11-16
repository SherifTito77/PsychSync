#!/bin/bash

# PsychSync Database Management Script
# Provides common database operations for local development

set -e

DB_NAME="psychsync_db"
DB_USER="psychsync_user"
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🗄️  PsychSync Database Management${NC}"
    echo "===================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check database connection
check_connection() {
    if psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to reset database
reset_database() {
    print_warning "This will delete all data in $DB_NAME. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  Dropping database..."
        dropdb -U "$DB_USER" -h "$DB_HOST" "$DB_NAME" 2>/dev/null || true

        echo "📦 Creating database..."
        createdb -U "$DB_USER" -h "$DB_HOST" "$DB_NAME"

        echo "🔄 Running migrations..."
        cd "$(dirname "$0")/.."
        source .venv/bin/activate
        alembic upgrade head

        print_success "Database reset completed"
    else
        echo "Operation cancelled"
    fi
}

# Function to create backup
create_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backups/psychsync_backup_${timestamp}.sql"

    mkdir -p backups

    echo "📦 Creating backup: $backup_file"
    pg_dump -U "$DB_USER" -h "$DB_HOST" "$DB_NAME" > "$backup_file"

    if [ $? -eq 0 ]; then
        print_success "Backup created: $backup_file"
        echo "📊 File size: $(du -h "$backup_file" | cut -f1)"
    else
        print_error "Backup failed"
    fi
}

# Function to restore backup
restore_backup() {
    echo "📂 Available backups:"
    ls -la backups/*.sql 2>/dev/null || echo "No backups found"

    echo "Enter backup filename to restore:"
    read -r backup_file

    if [ -f "backups/$backup_file" ]; then
        print_warning "This will replace current database data. Continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "🔄 Restoring from backup: $backup_file"
            psql -U "$DB_USER" -h "$DB_HOST" "$DB_NAME" < "backups/$backup_file"
            print_success "Database restored from backup"
        else
            echo "Operation cancelled"
        fi
    else
        print_error "Backup file not found: backups/$backup_file"
    fi
}

# Function to connect to database
connect_database() {
    echo "🔗 Connecting to database..."
    psql -U "$DB_USER" -h "$DB_HOST" "$DB_NAME"
}

# Function to show database info
show_info() {
    echo "📊 Database Information:"
    echo "========================"

    if check_connection; then
        echo "🔗 Connection: ✅ Connected"
        echo "📦 Database: $DB_NAME"
        echo "👤 User: $DB_USER"
        echo "🌐 Host: $DB_HOST:$DB_PORT"
        echo ""
        echo "📈 Database size:"
        psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME')) as database_size;" -t

        echo ""
        echo "📋 Tables:"
        psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -c "SELECT schemaname,tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;" -t
    else
        print_error "Cannot connect to database"
        echo "Please check that PostgreSQL is running and the database exists"
    fi
}

# Function to run migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    cd "$(dirname "$0")/.."
    source .venv/bin/activate
    alembic upgrade head
    print_success "Migrations completed"
}

# Function to create new migration
create_migration() {
    echo "📝 Creating new migration..."
    echo "Enter migration description:"
    read -r description

    cd "$(dirname "$0")/.."
    source .venv/bin/activate
    alembic revision --autogenerate -m "$description"
    print_success "Migration created: $description"
}

# Main menu
case "${1:-}" in
    "reset")
        print_header
        reset_database
        ;;
    "backup")
        print_header
        create_backup
        ;;
    "restore")
        print_header
        restore_backup
        ;;
    "connect")
        print_header
        connect_database
        ;;
    "info")
        print_header
        show_info
        ;;
    "migrate")
        print_header
        run_migrations
        ;;
    "migration")
        print_header
        create_migration
        ;;
    *)
        print_header
        echo "Usage: $0 {reset|backup|restore|connect|info|migrate|migration}"
        echo ""
        echo "Commands:"
        echo "  reset     - Reset database (delete all data and run migrations)"
        echo "  backup    - Create database backup"
        echo "  restore   - Restore database from backup"
        echo "  connect   - Connect to database with psql"
        echo "  info      - Show database information"
        echo "  migrate   - Run pending migrations"
        echo "  migration - Create new migration"
        ;;
esac