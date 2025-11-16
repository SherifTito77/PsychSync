#!/usr/bin/env python3
"""
PsychSync Email Analysis - Quick Start Script
This script helps set up and run the email analysis system quickly.
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path

def print_header():
    """Print colorful header"""
    print("\n" + "="*60)
    print("🧠 PSYCHSYNC EMAIL ANALYSIS - QUICK START")
    print("="*60)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    required_packages = ['python', 'pip', 'psql']
    missing = []

    for package in required_packages:
        try:
            subprocess.run([package, '--version'],
                         capture_output=True, check=True)
            print(f"  ✅ {package}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(package)
            print(f"  ❌ {package} - NOT FOUND")

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Please install them before continuing.")
        return False

    print("✅ All dependencies found!")
    return True

def create_venv():
    """Create Python virtual environment"""
    venv_path = Path("venv")

    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created!")
    else:
        print("📦 Virtual environment already exists!")

def install_dependencies():
    """Install Python dependencies"""
    print("📚 Installing Python dependencies...")

    # Activate venv and install requirements
    if os.name == 'nt':  # Windows
        pip_cmd = ["venv\\Scripts\\pip"]
    else:  # Unix/Mac
        pip_cmd = ["./venv/bin/pip"]

    try:
        subprocess.run([*pip_cmd, "install", "-r", "requirements.txt"],
                       check=True)
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

    return True

def generate_encryption_key():
    """Generate encryption key for email tokens"""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    print(f"🔐 Generated encryption key: {key}")
    print("💾 Add this to your .env file as EMAIL_ENCRYPTION_KEY")

    return key

def setup_env_file():
    """Set up environment file"""
    env_file = Path(".env")

    if not env_file.exists():
        print("📝 Creating .env file from template...")

        # Generate encryption key
        encryption_key = generate_encryption_key()

        env_content = f"""# Database Configuration
DATABASE_URL=postgresql://psychsync_user:password@localhost:5432/psychsync_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Application Configuration
SECRET_KEY={secrets.token_urlsafe(32)}
ENVIRONMENT=development
DEBUG=true

# Email Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret

# Email Encryption
EMAIL_ENCRYPTION_KEY={encryption_key}

# Feature Flags
ENABLE_EMAIL_ANALYSIS=true
ENABLE_CULTURE_METRICS=true
ENABLE_AI_COACHING=true

# Frontend URL (for OAuth callbacks)
FRONTEND_URL=http://localhost:3000

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
"""

        with open(env_file, 'w') as f:
            f.write(env_content)

        print("✅ .env file created!")
        print("⚠️  Please update GOOGLE_CLIENT_* and MICROSOFT_CLIENT_* with your OAuth credentials")
    else:
        print("📝 .env file already exists!")

def check_database():
    """Check if database is accessible"""
    print("🗄️  Checking database connection...")

    try:
        import psycopg2
        from urllib.parse import urlparse

        # Try to get database URL from .env
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip()
                        break
                else:
                    db_url = "postgresql://psychsync_user:password@localhost:5432/psychsync_db"

        parsed = urlparse(db_url)

        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading /
            user=parsed.username,
            password=parsed.password
        )

        conn.close()
        print("✅ Database connection successful!")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure PostgreSQL is running and accessible")
        return False

def create_sample_data():
    """Create sample test data for development"""
    print("📊 Creating sample data...")

    try:
        from app.db.session import SessionLocal
        from app.db.models.user import User
        from app.db.models.organization import Organization
        from app.core.security import get_password_hash

        db = SessionLocal()

        # Create test organization
        org = Organization(
            name="Test Organization",
            description="Sample organization for email analysis testing"
        )
        db.add(org)
        db.flush()

        # Create test user
        user = User(
            email="test@psychsync.ai",
            hashed_password=get_password_hash("test123"),
            first_name="Test",
            last_name="User",
            is_active=True,
            org_id=org.id
        )
        db.add(user)
        db.commit()

        print("✅ Sample data created!")
        print("📧 Email: test@psychsync.ai")
        print("🔑 Password: test123")

        return True

    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def run_database_migrations():
    """Run Alembic database migrations"""
    print("🔄 Running database migrations...")

    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Database migrations completed!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Database migrations failed: {e}")
        print("Please check your database configuration")
        return False

def start_services():
    """Start application services"""
    print("🚀 Starting PsychSync services...")

    print("\n📊 Starting in development mode...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nTo start manually:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")

    print("2. Start database services (PostgreSQL, Redis)")
    print("3. Start API server:")
    print("   uvicorn app.main:app --reload")
    print("4. Start Celery worker:")
    print("   celery -A app.core.celery worker --loglevel=info")
    print("5. Start Celery beat scheduler:")
    print("   celery -A app.core.celery beat --loglevel=info")

    # Try to start services automatically
    try:
        print("\n🔄 Attempting to start services automatically...")

        # Start with uvicorn in background
        uvicorn_process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print("✅ API server started (http://localhost:8000)")
        print("📚 API Docs: http://localhost:8000/docs")
        print("⏹️  Press Ctrl+C to stop")

        # Keep the process running
        uvicorn_process.wait()

    except KeyboardInterrupt:
        print("\n👋 Services stopped by user")
    except Exception as e:
        print(f"❌ Failed to start services: {e}")
        print("Please start them manually using the commands above")

def main():
    """Main quick start function"""
    print_header()

    # Check if we're in the right directory
    if not Path("app").exists() or not Path("requirements.txt").exists():
        print("❌ Please run this script from the psychsync root directory")
        sys.exit(1)

    steps = [
        ("Dependencies", check_dependencies),
        ("Virtual Environment", create_venv),
        ("Python Dependencies", install_dependencies),
        ("Environment File", setup_env_file),
        ("Database Connection", check_database),
        ("Database Migrations", run_database_migrations),
        ("Sample Data", create_sample_data),
    ]

    failed_steps = []

    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except KeyboardInterrupt:
            print(f"\n⏹️  Setup interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            failed_steps.append(step_name)

    if failed_steps:
        print(f"\n❌ Setup completed with {len(failed_steps)} failed step(s):")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease resolve these issues and run the script again.")
        sys.exit(1)

    print("\n✅ Setup completed successfully!")

    # Ask if user wants to start services
    try:
        response = input("\n🚀 Do you want to start the services now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            start_services()
        else:
            print("\n💡 To start services later, run:")
            print("   uvicorn app.main:app --reload")
            print("   celery -A app.core.celery worker --loglevel=info")
            print("   celery -A app.core.celery beat --loglevel=info")
    except KeyboardInterrupt:
        print("\n👋 Setup completed. Run the script again to start services.")

if __name__ == "__main__":
    main()