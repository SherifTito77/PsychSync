#!/bin/bash

# PsychSync Database Initialization Script
# Sets up the database with initial data for development

set -e

DB_NAME="psychsync_db"
DB_USER="psychsync_user"
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🗄️  PsychSync Database Initialization${NC}"
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

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d ".venv" ]; then
        print_error "Virtual environment not found. Please run ./start-dev.sh first."
        exit 1
    fi
}

# Function to activate virtual environment
activate_venv() {
    source .venv/bin/activate
}

# Function to run database migrations
run_migrations() {
    print_success "Running database migrations..."
    alembic upgrade head
}

# Function to create initial user
create_initial_user() {
    print_success "Creating initial development user..."

    # Check if create_user.py exists
    if [ -f "create_user.py" ]; then
        python create_user.py --email "dev@psychsync.com" --password "dev123456" --name "Development User" --is-superuser || {
            print_warning "Initial user may already exist or creation failed"
        }
    else
        print_warning "create_user.py not found. Skipping initial user creation."
    fi
}

# Function to seed templates
seed_templates() {
    print_success "Seeding assessment templates..."

    if [ -f "seed_templates.py" ]; then
        python seed_templates.py || {
            print_warning "Template seeding may have failed or templates already exist"
        }
    else
        print_warning "seed_templates.py not found. Skipping template seeding."
    fi
}

# Function to create test organization and team
create_test_org() {
    print_success "Creating test organization and team..."

    python3 << EOF
import asyncio
import sys
sys.path.append('.')

from app.core.database import get_async_session
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.db.models.org_member import OrgMember
from app.db.models.user import User
from sqlalchemy import select

async def create_test_data():
    async for session in get_async_session():
        try:
            # Check if test org already exists
            result = await session.execute(
                select(Organization).where(Organization.name == "PsychSync Test Org")
            )
            existing_org = result.scalar_one_or_none()

            if existing_org:
                print("Test organization already exists")
                return

            # Find the development user
            result = await session.execute(
                select(User).where(User.email == "dev@psychsync.com")
            )
            dev_user = result.scalar_one_or_none()

            if not dev_user:
                print("Development user not found. Please run initial user creation first.")
                return

            # Create test organization
            test_org = Organization(
                name="PsychSync Test Org",
                description="Test organization for development",
                is_active=True
            )
            session.add(test_org)
            await session.flush()

            # Create test team
            test_team = Team(
                name="Development Team",
                description="Development team for testing",
                organization_id=test_org.id,
                is_active=True
            )
            session.add(test_team)
            await session.flush()

            # Add user to organization as admin
            org_member = OrgMember(
                user_id=dev_user.id,
                organization_id=test_org.id,
                role="admin",
                is_active=True
            )
            session.add(org_member)

            await session.commit()
            print("Test organization and team created successfully")

        except Exception as e:
            print(f"Error creating test data: {e}")
            await session.rollback()
        finally:
            await session.close()

asyncio.run(create_test_data())
EOF
}

# Function to verify database setup
verify_setup() {
    print_success "Verifying database setup..."

    python3 << EOF
import asyncio
import sys
sys.path.append('.')

from app.core.database import get_async_session
from sqlalchemy import text

async def verify():
    async for session in get_async_session():
        try:
            # Check if tables exist
            result = await session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")

            # Check user count
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"Users: {user_count}")

            # Check organization count
            result = await session.execute(text("SELECT COUNT(*) FROM organizations"))
            org_count = result.scalar()
            print(f"Organizations: {org_count}")

        except Exception as e:
            print(f"Error verifying setup: {e}")
        finally:
            await session.close()

asyncio.run(verify())
EOF
}

# Main execution
main() {
    print_header

    echo "🔍 Checking prerequisites..."
    check_venv
    activate_venv

    echo ""
    echo "🔄 Initializing database..."

    # Run migrations
    run_migrations

    # Create initial user
    create_initial_user

    # Seed templates
    seed_templates

    # Create test organization
    create_test_org

    # Verify setup
    verify_setup

    echo ""
    print_success "Database initialization completed!"
    echo "======================================"
    echo ""
    echo "📝 Development Credentials:"
    echo "   Email: dev@psychsync.com"
    echo "   Password: dev123456"
    echo ""
    echo "🌐 You can now:"
    echo "   1. Start the backend: uvicorn app.main:app --reload"
    echo "   2. Start the frontend: cd frontend && npm run dev"
    echo "   3. Login with the development credentials"
    echo ""
}

# Run main function
main "$@"