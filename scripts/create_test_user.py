"""
File Path: scripts/create_test_user.py
Script to create test users for development and testing
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.db.models.user import User, UserRole
from app.db.models.organization import Organization
from app.db.models.team import Team, TeamMember, TeamRole
from app.core.security import get_password_hash
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_organization(db: Session, name: str) -> Organization:
    """Create test organization"""
    org = Organization(
        name=name,
        created_at=datetime.utcnow()
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    logger.info(f"✅ Created organization: {org.name} (ID: {org.id})")
    return org


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    organization_id: int,
    role: UserRole = UserRole.USER,
    is_verified: bool = True
) -> User:
    """Create test user"""
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        organization_id=organization_id,
        role=role,
        is_active=True,
        is_verified=is_verified,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"✅ Created user: {user.email} (Role: {role.value})")
    return user


def create_team(db: Session, name: str, organization_id: int, created_by_id: int) -> Team:
    """Create test team"""
    team = Team(
        name=name,
        organization_id=organization_id,
        created_by_id=created_by_id,
        created_at=datetime.utcnow()
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    logger.info(f"✅ Created team: {team.name} (ID: {team.id})")
    return team


def add_team_member(db: Session, team_id: int, user_id: int, role: TeamRole = TeamRole.MEMBER):
    """Add user to team"""
    member = TeamMember(
        team_id=team_id,
        user_id=user_id,
        role=role,
        joined_at=datetime.utcnow()
    )
    db.add(member)
    db.commit()
    logger.info(f"✅ Added user {user_id} to team {team_id} as {role.value}")


def create_complete_test_environment():
    """
    Create a complete test environment with:
    - 2 Organizations
    - Admin, Manager, and Regular users
    - Teams with members
    - Sample assessments (if models available)
    """
    logger.info("🚀 Starting test environment creation...")
    
    db = SessionLocal()
    
    try:
        # =============================================
        # ORGANIZATIONS
        # =============================================
        org1 = create_organization(db, "Acme Corporation")
        org2 = create_organization(db, "Tech Startup Inc")
        
        # =============================================
        # USERS - Organization 1
        # =============================================
        admin = create_user(
            db,
            email="admin@acme.com",
            password="Admin123!",
            full_name="Admin User",
            organization_id=org1.id,
            role=UserRole.ADMIN
        )
        
        manager = create_user(
            db,
            email="manager@acme.com",
            password="Manager123!",
            full_name="Manager Smith",
            organization_id=org1.id,
            role=UserRole.USER
        )
        
        users_org1 = []
        for i in range(1, 6):
            user = create_user(
                db,
                email=f"user{i}@acme.com",
                password="User123!",
                full_name=f"Employee {i}",
                organization_id=org1.id,
                role=UserRole.USER
            )
            users_org1.append(user)
        
        # =============================================
        # USERS - Organization 2
        # =============================================
        admin2 = create_user(
            db,
            email="admin@techstartup.com",
            password="Admin123!",
            full_name="Startup Admin",
            organization_id=org2.id,
            role=UserRole.ADMIN
        )
        
        users_org2 = []
        for i in range(1, 4):
            user = create_user(
                db,
                email=f"dev{i}@techstartup.com",
                password="Dev123!",
                full_name=f"Developer {i}",
                organization_id=org2.id,
                role=UserRole.USER
            )
            users_org2.append(user)
        
        # =============================================
        # TEAMS
        # =============================================
        dev_team = create_team(
            db,
            name="Development Team",
            organization_id=org1.id,
            created_by_id=admin.id
        )
        
        design_team = create_team(
            db,
            name="Design Team",
            organization_id=org1.id,
            created_by_id=admin.id
        )
        
        startup_team = create_team(
            db,
            name="Core Team",
            organization_id=org2.id,
            created_by_id=admin2.id
        )
        
        # =============================================
        # TEAM MEMBERS
        # =============================================
        # Development Team
        add_team_member(db, dev_team.id, manager.id, TeamRole.LEADER)
        add_team_member(db, dev_team.id, users_org1[0].id, TeamRole.MEMBER)
        add_team_member(db, dev_team.id, users_org1[1].id, TeamRole.MEMBER)
        add_team_member(db, dev_team.id, users_org1[2].id, TeamRole.MEMBER)
        
        # Design Team
        add_team_member(db, design_team.id, users_org1[3].id, TeamRole.LEADER)
        add_team_member(db, design_team.id, users_org1[4].id, TeamRole.MEMBER)
        
        # Startup Team
        add_team_member(db, startup_team.id, admin2.id, TeamRole.LEADER)
        for user in users_org2:
            add_team_member(db, startup_team.id, user.id, TeamRole.MEMBER)
        
        # =============================================
        # SUMMARY
        # =============================================
        logger.info("\n" + "="*60)
        logger.info("🎉 Test environment created successfully!")
        logger.info("="*60)
        logger.info("\n📊 Summary:")
        logger.info(f"  • Organizations: 2")
        logger.info(f"  • Users: {len(users_org1) + len(users_org2) + 4}")
        logger.info(f"  • Teams: 3")
        logger.info(f"  • Team memberships: {len(users_org1) + len(users_org2) + 2}")
        
        logger.info("\n🔑 Test Credentials:")
        logger.info("\n  Organization 1 (Acme Corporation):")
        logger.info("    Admin:   admin@acme.com / Admin123!")
        logger.info("    Manager: manager@acme.com / Manager123!")
        logger.info("    Users:   user1@acme.com - user5@acme.com / User123!")
        
        logger.info("\n  Organization 2 (Tech Startup Inc):")
        logger.info("    Admin:   admin@techstartup.com / Admin123!")
        logger.info("    Devs:    dev1@techstartup.com - dev3@techstartup.com / Dev123!")
        
        logger.info("\n💡 Quick Test Commands:")
        logger.info("  • Login: POST /api/v1/auth/login")
        logger.info("  • Teams: GET /api/v1/teams")
        logger.info("  • Users:  GET /api/v1/users")
        logger.info("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Error creating test environment: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def create_single_test_user(
    email: str = "test@example.com",
    password: str = "Test123!",
    full_name: str = "Test User",
    role: str = "user"
):
    """
    Create a single test user
    
    Usage:
        python scripts/create_test_user.py --email test@example.com --password Test123!
    """
    logger.info(f"🚀 Creating single test user: {email}")
    
    db = SessionLocal()
    
    try:
        # Check if organization exists
        org = db.query(Organization).first()
        if not org:
            org = create_organization(db, "Test Organization")
        
        # Convert role string to enum
        role_enum = UserRole.ADMIN if role.lower() == "admin" else UserRole.USER
        
        # Create user
        user = create_user(
            db,
            email=email,
            password=password,
            full_name=full_name,
            organization_id=org.id,
            role=role_enum
        )
        
        logger.info("\n✅ User created successfully!")
        logger.info(f"  Email: {user.email}")
        logger.info(f"  Password: {password}")
        logger.info(f"  Role: {role_enum.value}")
        logger.info(f"  Organization: {org.name}\n")
        
        return user
        
    except Exception as e:
        logger.error(f"❌ Error creating user: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def clean_test_data():
    """
    Clean all test data from database
    ⚠️  WARNING: This will delete ALL data!
    """
    logger.warning("⚠️  WARNING: This will delete ALL data from the database!")
    confirmation = input("Type 'DELETE ALL' to confirm: ")
    
    if confirmation != "DELETE ALL":
        logger.info("❌ Deletion cancelled")
        return
    
    db = SessionLocal()
    
    try:
        logger.info("🗑️  Deleting all data...")
        
        # Delete in correct order due to foreign keys
        from app.db.models.team import TeamMember
        from app.db.models.assessment import AssessmentResponse
        
        db.query(TeamMember).delete()
        db.query(Team).delete()
        
        try:
            db.query(AssessmentResponse).delete()
        except:
            pass  # Table might not exist
        
        db.query(User).delete()
        db.query(Organization).delete()
        
        db.commit()
        logger.info("✅ All test data deleted!")
        
    except Exception as e:
        logger.error(f"❌ Error deleting data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create test users for PsychSync")
    parser.add_argument("--mode", choices=["full", "single", "clean"], default="full",
                       help="Creation mode: full environment, single user, or clean data")
    parser.add_argument("--email", default="test@example.com", help="User email")
    parser.add_argument("--password", default="Test123!", help="User password")
    parser.add_argument("--name", default="Test User", help="User full name")
    parser.add_argument("--role", default="user", choices=["user", "admin"], help="User role")
    
    args = parser.parse_args()
    
    if args.mode == "full":
        create_complete_test_environment()
    elif args.mode == "single":
        create_single_test_user(
            email=args.email,
            password=args.password,
            full_name=args.name,
            role=args.role
        )
    elif args.mode == "clean":
        clean_test_data()