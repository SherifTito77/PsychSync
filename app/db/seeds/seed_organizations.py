"""
Seed script to create default organization and assign to existing users
MINIMAL VERSION - works with basic schema

File path: app/db/seeds/seed_organizations.py
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_async_db
from app.db.models.user import User
from datetime import datetime
from uuid import uuid4


def seed_default_organization(db: Session):
    """
    Create a default organization if it doesn't exist
    Using raw SQL to avoid model issues
    """
    try:
        # Check what columns exist in organizations table
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'organizations'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result]
        print(f"📋 Organizations table columns: {', '.join(columns)}")
        
        # Check if default organization exists
        result = db.execute(text("SELECT id, name FROM organizations WHERE name = :name"), 
                          {"name": "Default Organization"})
        org = result.fetchone()
        
        if org:
            print(f"✅ Default organization already exists with ID: {org[0]}")
            return org[0]
        
        # Create organization with only the columns that exist
        org_id = uuid4()
        
        if 'description' in columns:
            db.execute(text("""
                INSERT INTO organizations (id, name, description, created_at, updated_at)
                VALUES (:id, :name, :description, NOW(), NOW())
            """), {
                "id": org_id,
                "name": "Default Organization",
                "description": "Default organization for initial users"
            })
        else:
            db.execute(text("""
                INSERT INTO organizations (id, name, created_at, updated_at)
                VALUES (:id, :name, NOW(), NOW())
            """), {
                "id": org_id,
                "name": "Default Organization"
            })
        
        db.commit()
        print(f"✅ Created default organization with ID: {org_id}")
        return org_id
        
    except Exception as e:
        print(f"❌ Error creating organization: {e}")
        db.rollback()
        raise


def assign_organization_to_users(db: Session, organization_id):
    """
    Assign the default organization to all users without an organization
    """
    try:
        # Check if users table has organization_id column
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'organization_id'
        """))
        
        if not result.fetchone():
            print("⚠️  Users table doesn't have organization_id column yet")
            print("   Adding organization_id column to users...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id)
            """))
            db.commit()
        
        # Count users without organization
        result = db.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE organization_id IS NULL 
            AND (deleted_at IS NULL OR deleted_at IS NOT NULL)
        """))
        count_before = result.scalar()
        
        if count_before == 0:
            print("ℹ️  All users already have an organization assigned")
            return
        
        # Update users
        result = db.execute(text("""
            UPDATE users 
            SET organization_id = :org_id, updated_at = NOW()
            WHERE organization_id IS NULL
        """), {"org_id": organization_id})
        
        db.commit()
        print(f"✅ Assigned organization to {count_before} users")
        
        # List updated users
        result = db.execute(text("""
            SELECT email FROM users 
            WHERE organization_id = :org_id 
            LIMIT 5
        """), {"org_id": organization_id})
        
        for row in result:
            print(f"  - {row[0]}")
            
    except Exception as e:
        print(f"❌ Error assigning organizations to users: {e}")
        db.rollback()
        raise


def assign_organization_to_teams(db: Session, organization_id):
    """
    Assign organization to teams based on creator's organization
    """
    try:
        # Check if teams table has organization_id column
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'teams' AND column_name = 'organization_id'
        """))
        
        if not result.fetchone():
            print("⚠️  Teams table doesn't have organization_id column yet")
            print("   Adding organization_id column to teams...")
            db.execute(text("""
                ALTER TABLE teams 
                ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id)
            """))
            db.commit()
        
        # Update teams
        result = db.execute(text("""
            UPDATE teams t
            SET organization_id = u.organization_id, updated_at = NOW()
            FROM users u
            WHERE t.created_by_id = u.id
            AND t.organization_id IS NULL
        """))
        
        db.commit()
        print(f"✅ Updated teams with organization_id")
        
    except Exception as e:
        print(f"⚠️  Could not update teams: {e}")
        # Don't fail if teams update fails
        db.rollback()


def verify_assignment(db: Session):
    """
    Verify that setup is complete
    """
    try:
        # Count organizations
        result = db.execute(text("SELECT COUNT(*) FROM organizations"))
        org_count = result.scalar()
        
        # Count users with org
        result = db.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE organization_id IS NOT NULL 
            AND (deleted_at IS NULL OR deleted_at IS NOT NULL)
        """))
        users_with_org = result.scalar()
        
        # Count total users
        result = db.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE deleted_at IS NULL OR deleted_at IS NOT NULL
        """))
        total_users = result.scalar()
        
        print(f"\n📊 Summary:")
        print(f"  Organizations: {org_count}")
        print(f"  Total users: {total_users}")
        print(f"  Users with organization: {users_with_org}")
        print(f"  Users without organization: {total_users - users_with_org}")
        
        if users_with_org == total_users:
            print("✅ All users have an organization!")
        else:
            print("⚠️  Some users still don't have an organization")
            
    except Exception as e:
        print(f"⚠️  Could not verify: {e}")


def run_seed():
    """
    Main function to run the seed script
    """
    db = SessionLocal()
    try:
        print("=" * 60)
        print("Starting organization seed...")
        print("=" * 60)
        
        # Create default organization
        org_id = seed_default_organization(db)
        
        # Assign organization to users
        assign_organization_to_users(db, org_id)
        
        # Try to assign to teams
        assign_organization_to_teams(db, org_id)
        
        # Verify the assignment
        verify_assignment(db)
        
        print("=" * 60)
        print("Organization seed completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()