#!/usr/bin/env python3
"""
PsychSync Database Backup System
Simple backup script for PostgreSQL database
"""

import subprocess
import os
import sys
import time
from datetime import datetime
from pathlib import Path

class DatabaseBackup:
    def __init__(self):
        self.backup_dir = Path("/tmp/psychsync_backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, db_name="psychsync_db"):
        """Create a database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{db_name}_backup_{timestamp}.sql"

        print(f"🗄️ Creating database backup for {db_name}...")

        try:
            # Use pg_dump to create backup
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "psychsync_user",
                "-d", db_name,
                "--verbose",
                "--no-password",
                "--format=custom",
                "--file", str(backup_file)
            ]

            # Set password in environment for pg_dump
            env = os.environ.copy()
            db_password = os.getenv('DB_PASSWORD', 'C8Vsywo9yXRQSOaGwxjVVQ-Secure9')
            if not os.getenv('DB_PASSWORD'):
                print("WARNING: DB_PASSWORD environment variable not set. Using default for development only.")
            env["PGPASSWORD"] = db_password

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode == 0:
                backup_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                print(f"✅ Backup created successfully: {backup_file}")
                print(f"📁 Backup size: {backup_size:.2f} MB")
                return backup_file
            else:
                print(f"❌ Backup failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"❌ Backup error: {e}")
            return None

    def restore_backup(self, backup_file, db_name="psychsync_db"):
        """Restore database from backup"""
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False

        print(f"🔄 Restoring database from {backup_file}...")

        try:
            cmd = [
                "pg_restore",
                "-h", "localhost",
                "-U", "psychsync_user",
                "-d", db_name,
                "--verbose",
                "--clean",
                "--if-exists",
                backup_file
            ]

            env = os.environ.copy()
            db_password = os.getenv('DB_PASSWORD', 'C8Vsywo9yXRQSOaGwxjVVQ-Secure9')
            if not os.getenv('DB_PASSWORD'):
                print("WARNING: DB_PASSWORD environment variable not set. Using default for development only.")
            env["PGPASSWORD"] = db_password

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode == 0:
                print(f"✅ Database restored successfully from {backup_file}")
                return True
            else:
                print(f"❌ Restore failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Restore error: {e}")
            return False

    def list_backups(self):
        """List all available backups"""
        print("📋 Available backups:")
        backup_files = sorted(self.backup_dir.glob("*.sql"))

        if not backup_files:
            print("  No backups found")
            return []

        for i, backup_file in enumerate(backup_files, 1):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            print(f"  {i}. {backup_file.name}")
            print(f"     Created: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Size: {file_size:.2f} MB")

        return backup_files

    def cleanup_old_backups(self, keep_days=30):
        """Remove backups older than specified days"""
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)

        print(f"🧹 Cleaning up backups older than {keep_days} days...")

        removed_count = 0
        for backup_file in self.backup_dir.glob("*.sql"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                removed_count += 1
                print(f"  🗑️ Removed: {backup_file.name}")

        if removed_count == 0:
            print("  No old backups to remove")
        else:
            print(f"  ✅ Removed {removed_count} old backup(s)")

def main():
    """Main backup function"""
    if len(sys.argv) < 2:
        print("Usage: python database_backup.py [create|restore|list|cleanup]")
        return

    action = sys.argv[1].lower()
    backup_system = DatabaseBackup()

    if action == "create":
        backup_file = backup_system.create_backup()
        if backup_file:
            print(f"🎉 Backup completed: {backup_file}")
        else:
            print("💥 Backup failed!")

    elif action == "restore":
        if len(sys.argv) < 3:
            print("Usage: python database_backup.py restore <backup_file>")
            return

        backup_file = sys.argv[2]
        success = backup_system.restore_backup(backup_file)
        if success:
            print("🎉 Restore completed!")
        else:
            print("💥 Restore failed!")

    elif action == "list":
        backup_system.list_backups()

    elif action == "cleanup":
        keep_days = 30
        if len(sys.argv) > 2:
            keep_days = int(sys.argv[2])
        backup_system.cleanup_old_backups(keep_days)

    else:
        print("Unknown action. Use: create, restore, list, or cleanup")

if __name__ == "__main__":
    main()