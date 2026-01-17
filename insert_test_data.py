#!/usr/bin/env python3
"""
Insert test data that matches existing schema
"""

import subprocess

def run_command(cmd, description):
    """Run a database command"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False
    return True

def main():
    """Insert test data matching existing schema"""

    commands = [
        ('psql -d psychsync_db -c "INSERT INTO organizations (id, name) VALUES (\'550e8400-e29b-41d4-a716-446655440001\', \'Test Organization\'), (\'550e8400-e29b-41d4-a716-446655440002\', \'Demo Organization\') ON CONFLICT (id) DO NOTHING;"', "Insert test organizations"),
        ('psql -d psychsync_db -c "INSERT INTO users (id, email, password_hash, full_name, is_active) VALUES (\'550e8400-e29b-41d4-a716-446655440003\', \'admin@example.com\', \'hashed_password\', \'Admin User\', true), (\'550e8400-e29b-41d4-a716-446655440004\', \'test@example.com\', \'hashed_password\', \'Test User\', true) ON CONFLICT (email) DO NOTHING;"', "Insert test users"),
    ]

    print("🚀 Inserting test data...")

    success = True
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            success = False

    if success:
        print("\n🎉 Test data insertion completed!")
        print("\n🔍 Verification:")
        run_command("psql -d psychsync_db -c \"SELECT COUNT(*) as users_count FROM users;\"", "Verify users count")
        run_command("psql -d psychsync_db -c \"SELECT COUNT(*) as orgs_count FROM organizations;\"", "Verify organizations count")
        run_command("psql -d psychsync_db -c \"SELECT COUNT(*) as teams_count FROM teams;\"", "Verify teams count")
    else:
        print("\n💥 Test data insertion failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
