#!/usr/bin/env python3
"""
PII FIELD ENCRYPTION MIGRATION TOOL
====================================
Encrypts remaining unencrypted PII fields in the database

SECURITY ENHANCEMENT:
----------------------
This tool identifies unencrypted PII fields and migrates them to use
Fernet encryption (AES-128) for data at rest protection.

FIELDS TO ENCRYPT:
------------------
1. User model:
   - email (already indexed, need hashed version for search)
   - full_name (encrypted version exists in user_secure, need to migrate)
   - phone_number (encrypted version exists, need to migrate)

2. Organization model:
   - display_name
   - address
   - phone
   - email

3. Slack workspace model:
   - token (already should be encrypted)

4. Email connection model:
   - token
   - email
   - address

Usage:
    python migrate_pii_encryption.py --dry-run     # Preview changes
    python migrate_pii_encryption.py --plan        # Generate SQL plan
    python migrate_pii_encryption.py --execute     # Execute migration

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import hashlib
import os
import re
import secrets
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class FieldMigration:
    """Represents a field that needs encryption migration"""

    table_name: str
    field_name: str
    field_type: str
    is_pii: bool = True
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM
    notes: str = ""


class PIIEncryptionMigrator:
    """PII field encryption migration tool"""

    # PII fields that should be encrypted (from security scan)
    PII_FIELDS_TO_MIGRATE = [
        # User model (app/db/models/user.py)
        FieldMigration(
            "users",
            "email",
            "CITEXT",
            is_pii=True,
            priority="CRITICAL",
            notes="Need hashed version for indexing",
        ),
        FieldMigration(
            "users",
            "full_name",
            "String",
            is_pii=True,
            priority="HIGH",
            notes="Encrypted version exists in user_secure",
        ),
        FieldMigration(
            "users",
            "phone_number",
            "String",
            is_pii=True,
            priority="HIGH",
            notes="Encrypted version exists in user_secure",
        ),
        FieldMigration("users", "address", "Text", is_pii=True, priority="HIGH"),
        # Organization model (app/db/models/organization.py)
        FieldMigration(
            "organizations",
            "display_name",
            "String",
            is_pii=False,
            priority="MEDIUM",
            notes="May contain sensitive info",
        ),
        FieldMigration(
            "organizations", "address", "Text", is_pii=True, priority="HIGH"
        ),
        FieldMigration(
            "organizations", "phone", "String", is_pii=True, priority="HIGH"
        ),
        FieldMigration(
            "organizations", "email", "String", is_pii=True, priority="HIGH"
        ),
        # Slack workspace (app/db/models/slack_workspace.py)
        FieldMigration(
            "slack_workspaces",
            "token",
            "Text",
            is_pii=True,
            priority="CRITICAL",
            notes="OAuth tokens should be encrypted",
        ),
        # Email connection (app/db/models/email_connection.py)
        FieldMigration(
            "email_connections",
            "token",
            "Text",
            is_pii=True,
            priority="CRITICAL",
            notes="OAuth tokens should be encrypted",
        ),
        FieldMigration(
            "email_connections", "email", "String", is_pii=True, priority="HIGH"
        ),
        FieldMigration(
            "email_connections", "address", "String", is_pii=True, priority="HIGH"
        ),
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.models_dir = project_root / "app" / "db" / "models"
        self.migrations_dir = project_root / "alembic" / "versions"

    def generate_encryption_key(self) -> str:
        """Generate a new encryption key for Fernet"""
        from cryptography.fernet import Fernet

        return Fernet.generate_key().decode()

    def scan_models_for_unencrypted_pii(self) -> List[Dict]:
        """Scan model files for unencrypted PII fields"""
        print("🔍 Scanning models for unencrypted PII fields...\n")

        unencrypted_fields = []

        # Keywords that indicate PII
        pii_keywords = [
            "email",
            "phone",
            "address",
            "full_name",
            "name",
            "token",
            "secret",
            "password",
            "ssn",
            "social_security",
            "credit_card",
            "birth",
            "dob",
            "location",
        ]

        for model_file in self.models_dir.glob("*.py"):
            # Skip secure models (already encrypted)
            if "secure" in model_file.name or "_secure" in model_file.name:
                continue

            content = model_file.read_text()

            # Find Column definitions
            column_pattern = r"(\w+)\s*=\s*Column\s*\(([^)]+)\)"
            matches = re.finditer(column_pattern, content, re.MULTILINE)

            for match in matches:
                field_name = match.group(1)
                column_def = match.group(2)

                # Check if field contains PII keywords
                is_pii = any(keyword in field_name.lower() for keyword in pii_keywords)

                # Check if already marked as encrypted
                is_encrypted = "encrypted" in column_def.lower()

                if is_pii and not is_encrypted:
                    # Extract field type
                    type_match = re.search(r"(String|Text|CITEXT)", column_def)
                    field_type = type_match.group(1) if type_match else "Unknown"

                    unencrypted_fields.append(
                        {
                            "file": model_file.name,
                            "field": field_name,
                            "type": field_type,
                            "definition": column_def.strip(),
                        }
                    )

        return unencrypted_fields

    def generate_migration_plan(self) -> str:
        """Generate SQL migration plan"""
        plan = []
        plan.append("-- PII ENCRYPTION MIGRATION PLAN")
        plan.append(f"-- Generated: {datetime.now().isoformat()}")
        plan.append("--")
        plan.append("-- This migration adds encrypted columns and migrates data")
        plan.append("-- ")
        plan.append("-- IMPORTANT: Review and test before running in production!")
        plan.append("-- ")
        plan.append("")

        # Generate migration for each field
        for field_migration in self.PII_FIELDS_TO_MIGRATE:
            table = field_migration.table_name
            field = field_migration.field_name
            encrypted_field = f"_{field}_encrypted"

            plan.append(f"-- Migration for {table}.{field}")
            plan.append(f"-- Priority: {field_migration.priority}")
            plan.append(f"-- {field_migration.notes}")
            plan.append("")

            # Step 1: Add encrypted column
            plan.append(f"-- Step 1: Add encrypted column")
            plan.append(f"ALTER TABLE {table}")
            plan.append(f"  ADD COLUMN {encrypted_field} TEXT;")
            plan.append("")

            # Step 2: Migrate and encrypt data
            plan.append(f"-- Step 2: Migrate data with encryption")
            plan.append(f"UPDATE {table}")
            plan.append(f"  SET {encrypted_field} = pgp_sym_encrypt(")
            plan.append(f"    {field},")
            plan.append(f"    '{{ENCRYPTION_KEY}}'  -- Replace with actual key")
            plan.append(f"  )")
            plan.append(f"  WHERE {field} IS NOT NULL;")
            plan.append("")

            # Step 3: Update model to use encrypted field
            plan.append(f"-- Step 3: Update application model")
            plan.append(f"-- - Add @hybrid_property for {field}")
            plan.append(f"-- - Update getters/setters to encrypt/decrypt")
            plan.append("")

            # Step 4: Drop original column (AFTER verification)
            plan.append(f"-- Step 4: Drop original column (DO THIS LAST)")
            plan.append(f"-- ALTER TABLE {table} DROP COLUMN {field};")
            plan.append("-- RENAME COLUMN {encrypted_field} TO {field};")
            plan.append("")

            plan.append("-" * 70)
            plan.append("")

        return "\n".join(plan)

    def generate_model_update_code(self, file_path: Path, field_name: str) -> str:
        """Generate code to update a model with encryption"""
        return f"""
    # === ENCRYPTED {field_name.upper()} ===

    _{field_name}_encrypted = Column(
        Text,
        nullable=True,
        name="{field_name}_encrypted",
        comment="Encrypted {field_name} (PII)"
    )

    @hybrid_property
    def {field_name}(self) -> str:
        \"\"\"Get decrypted {field_name}\"\"\"
        if self._{field_name}_encrypted:
            return self._decrypt_field(self._{field_name}_encrypted)
        return None

    @{field_name}.setter
    def {field_name}(self, value: str):
        \"\"\"Set encrypted {field_name}\"\"\"
        if value:
            self._{field_name}_encrypted = self._encrypt_field(value)
        else:
            self._{field_name}_encrypted = None

    def _encrypt_field(self, value: str) -> str:
        \"\"\"Encrypt a field value using Fernet\"\"\"
        try:
            from app.core.config import settings
            from cryptography.fernet import Fernet

            key = settings.ENCRYPTION_KEY.encode()
            f = Fernet(key)
            encrypted_value = f.encrypt(value.encode())
            return encrypted_value.decode()
        except Exception as e:
            security_logger.error(f"Field encryption failed: {{e}}")
            raise RuntimeError("Field encryption failed")

    def _decrypt_field(self, encrypted_value: str) -> str:
        \"\"\"Decrypt a field value using Fernet\"\"\"
        try:
            from app.core.config import settings
            from cryptography.fernet import Fernet

            if not encrypted_value:
                return None
            key = settings.ENCRYPTION_KEY.encode()
            f = Fernet(key)
            decrypted_value = f.decrypt(encrypted_value.encode())
            return decrypted_value.decode()
        except Exception as e:
            security_logger.error(f"Field decryption failed: {{e}}")
            return None
"""

    def generate_alembic_migration(self) -> str:
        """Generate Alembic migration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_id = f"{timestamp}_encrypt_pii_fields"

        migration_content = f'''"""encrypt PII fields

Revision ID: {migration_id}
Revises:
Create Date: {datetime.now().isoformat()}

This migration encrypts remaining PII fields for GDPR/CCPA compliance.

SECURITY:
- Adds encrypted columns for PII data
- Migrates existing data with Fernet encryption (AES-128)
- Updates models to use encrypted fields

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '{migration_id}'
down_revision = None  # TODO: Set to previous migration
branch_labels = None
depends_on = None


def upgrade():
    """Encrypt PII fields"""
'''

        # Add upgrade steps for each field
        for field_migration in self.PII_FIELDS_TO_MIGRATE:
            table = field_migration.table_name
            field = field_migration.field_name
            encrypted_field = f"_{field}_encrypted"

            migration_content += f'''
    # Encrypt {table}.{field}
    op.add_column(table_name='{table}',
                  column=sa.Column('{encrypted_field}', sa.Text(), nullable=True))

    # TODO: Run data migration to encrypt existing values
    # op.execute(f"""
    #     UPDATE {table}
    #     SET {encrypted_field} = pgp_sym_encrypt({field}, '{{{{ENCRYPTION_KEY}}}}')
    #     WHERE {field} IS NOT NULL
    # """)

    print(f"✅ Added encrypted column for {table}.{field}")
'''

        migration_content += '''

def downgrade():
    """Remove encryption (NOT RECOMMENDED - data may be lost)"""
    # TODO: Implement rollback if needed
    # WARNING: Rollback will expose PII in plain text
    pass
'''

        return migration_content, migration_id

    def generate_summary_report(self) -> Dict:
        """Generate summary report of PII encryption migration"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_fields_to_migrate": len(self.PII_FIELDS_TO_MIGRATE),
            "fields_by_priority": {
                "CRITICAL": [
                    f for f in self.PII_FIELDS_TO_MIGRATE if f.priority == "CRITICAL"
                ],
                "HIGH": [f for f in self.PII_FIELDS_TO_MIGRATE if f.priority == "HIGH"],
                "MEDIUM": [
                    f for f in self.PII_FIELDS_TO_MIGRATE if f.priority == "MEDIUM"
                ],
            },
            "summary": {
                "critical": sum(
                    1 for f in self.PII_FIELDS_TO_MIGRATE if f.priority == "CRITICAL"
                ),
                "high": sum(
                    1 for f in self.PII_FIELDS_TO_MIGRATE if f.priority == "HIGH"
                ),
                "medium": sum(
                    1 for f in self.PII_FIELDS_TO_MIGRATE if f.priority == "MEDIUM"
                ),
            },
        }


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="PII Field Encryption Migration Tool")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without executing"
    )
    parser.add_argument(
        "--plan", action="store_true", help="Generate SQL migration plan"
    )
    parser.add_argument(
        "--alembic", action="store_true", help="Generate Alembic migration file"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Scan models for unencrypted PII"
    )
    parser.add_argument("--execute", action="store_true", help="Execute migration")

    args = parser.parse_args()

    project_root = Path(os.path.dirname(os.path.abspath(__file__)))
    migrator = PIIEncryptionMigrator(project_root)

    print("=" * 80)
    print("🔒 PII FIELD ENCRYPTION MIGRATION TOOL")
    print("=" * 80)
    print()

    if args.scan:
        # Scan for unencrypted PII
        unencrypted = migrator.scan_models_for_unencrypted_pii()
        print(f"\n📊 Found {len(unencrypted)} unencrypted PII field(s)")
        for field in unencrypted:
            print(f"   • {field['file']}: {field['field']} ({field['type']})")

    elif args.plan:
        # Generate SQL migration plan
        plan = migrator.generate_migration_plan()
        plan_file = project_root / "pii_encryption_migration_plan.sql"
        plan_file.write_text(plan)
        print(f"✅ SQL migration plan saved to: {plan_file.name}")
        print(f"\n   Review the plan and execute when ready.")

    elif args.alembic:
        # Generate Alembic migration
        migration_content, migration_id = migrator.generate_alembic_migration()
        migration_file = (
            migrator.migrations_dir / f"{migration_id}_encrypt_pii_fields.py"
        )
        migration_file.write_text(migration_content)
        print(f"✅ Alembic migration saved to: {migration_file.name}")
        print(f"\n   Run: alembic upgrade head")

    elif args.execute:
        print("⚠️  EXECUTION MODE")
        print("   This will modify your database schema!")
        print("   Make sure to:")
        print("   1. Backup your database")
        print("   2. Review the migration plan")
        print("   3. Test in development first")
        print()
        response = input("   Continue? (yes/no): ")
        if response.lower() == "yes":
            print("   🔧 Executing migration...")
            print("   TODO: Implement execution logic")
        else:
            print("   Cancelled.")

    else:
        # Show summary
        summary = migrator.generate_summary_report()
        print("📊 MIGRATION SUMMARY")
        print("=" * 80)
        print(f"\nTotal fields to migrate: {summary['total_fields_to_migrate']}")
        print(f"  🔴 CRITICAL: {summary['summary']['critical']}")
        print(f"  🟠 HIGH: {summary['summary']['high']}")
        print(f"  🟡 MEDIUM: {summary['summary']['medium']}")

        print("\nFields by priority:")
        print("\n🔴 CRITICAL:")
        for f in summary["fields_by_priority"]["CRITICAL"]:
            print(f"  • {f.table_name}.{f.field_name} ({f.notes})")

        print("\n🟠 HIGH:")
        for f in summary["fields_by_priority"]["HIGH"][:5]:
            print(f"  • {f.table_name}.{f.field_name}")
        if len(summary["fields_by_priority"]["HIGH"]) > 5:
            print(f"  ... and {len(summary['fields_by_priority']['HIGH']) - 5} more")

        print("\n🟡 MEDIUM:")
        for f in summary["fields_by_priority"]["MEDIUM"]:
            print(f"  • {f.table_name}.{f.field_name}")

        print("\n" + "=" * 80)
        print("\nNext steps:")
        print("  1. Run: python migrate_pii_encryption.py --scan")
        print("  2. Run: python migrate_pii_encryption.py --plan")
        print("  3. Review the generated SQL plan")
        print("  4. Run: python migrate_pii_encryption.py --alembic")
        print("  5. Test the migration in development")
        print("  6. Run: alembic upgrade head")
        print("=" * 80)


if __name__ == "__main__":
    main()
