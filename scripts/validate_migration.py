#!/usr/bin/env python3
"""
Migration Validation Script

Run this script after each migration step to verify success.

Usage:
    python scripts/validate_migration.py --step 1
    python scripts/validate_migration.py --step 2
    python scripts/validate_migration.py --step 3
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

# Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "psychsync",
    "user": "postgres",
    "password": "",  # Set via environment or config
}


class MigrationValidator:
    """Validate migration steps"""

    def __init__(self, step: int):
        self.step = step
        self.passed = 0
        self.failed = 0
        self.warnings = []

    def run(self):
        """Run validation for the specified step"""
        print(f"\n{'='*60}")
        print(f"Validating Migration Step {self.step}")
        print(f"{'='*60}\n")

        try:
            with psycopg.connect(**DB_CONFIG) as conn:
                conn.row_factory = dict_row
                cursor = conn.cursor()

                if self.step == 1:
                    self.validate_step1(cursor)
                elif self.step == 2:
                    self.validate_step2(cursor)
                elif self.step == 3:
                    self.validate_step3(cursor)
                else:
                    print(f"❌ Invalid step: {self.step}")
                    sys.exit(1)

        except psycopg.Error as e:
            print(f"\n❌ Database error: {e}")
            sys.exit(1)

        # Print summary
        print(f"\n{'='*60}")
        print(f"Validation Summary")
        print(f"{'='*60}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")

        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print()

        if self.failed > 0:
            print("❌ VALIDATION FAILED")
            sys.exit(1)
        else:
            print("✅ VALIDATION PASSED")
            sys.exit(0)

    def validate_step1(self, cursor):
        """Validate Step 1: UUID columns added"""

        print("Checking that UUID columns exist...")

        # Check responses table
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'responses'
              AND column_name LIKE '%uuid%'
            ORDER BY column_name
        """
        )

        columns = cursor.fetchall()
        expected_columns = {
            "id_uuid": "uuid",
            "assessment_id_uuid": "uuid",
            "respondent_id_uuid": "uuid",
        }

        for col in expected_columns:
            found = any(c["column_name"] == col for c in columns)
            if found:
                self.passed += 1
                print(f"  ✅ {col} column exists")
            else:
                self.failed += 1
                print(f"  ❌ {col} column MISSING")

        # Check response_scores table
        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'response_scores'
              AND column_name LIKE '%uuid%'
            ORDER BY column_name
        """
        )

        columns = cursor.fetchall()
        expected_columns = {"id_uuid": "uuid", "response_id_uuid": "uuid"}

        for col in expected_columns:
            found = any(c["column_name"] == col for c in columns)
            if found:
                self.passed += 1
                print(f"  ✅ {col} column exists")
            else:
                self.failed += 1
                print(f"  ❌ {col} column MISSING")

        # Verify integer columns still exist
        print("\nChecking that integer columns still exist...")

        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'responses'
              AND column_name IN ('id', 'assessment_id', 'respondent_id')
              AND data_type = 'integer'
        """
        )

        int_columns = cursor.fetchall()
        if len(int_columns) >= 3:
            self.passed += 1
            print(f"  ✅ Integer columns still present")
        else:
            self.failed += 1
            print(f"  ❌ Integer columns missing or wrong type")

    def validate_step2(self, cursor):
        """Validate Step 2: Data migrated to UUID columns"""

        print("Checking that UUID columns are populated...")

        # Check responses table
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE id_uuid IS NULL) as null_count,
                COUNT(*) as total_count
            FROM responses
        """
        )

        result = cursor.fetchone()
        null_count = result["null_count"]
        total_count = result["total_count"]

        if null_count == 0:
            self.passed += 1
            print(f"  ✅ All {total_count} responses have UUIDs")
        else:
            self.failed += 1
            print(f"  ❌ {null_count} of {total_count} responses have NULL UUIDs")

        # Check response_scores table
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE id_uuid IS NULL) as null_count,
                COUNT(*) as total_count
            FROM response_scores
        """
        )

        result = cursor.fetchone()
        null_count = result["null_count"]
        total_count = result["total_count"]

        if null_count == 0:
            self.passed += 1
            print(f"  ✅ All {total_count} response_scores have UUIDs")
        else:
            self.failed += 1
            print(f"  ❌ {null_count} of {total_count} response_scores have NULL UUIDs")

        # Check foreign key relationships
        print("\nChecking foreign key relationships...")

        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE assessment_id_uuid IS NULL) as null_fk,
                COUNT(*) FILTER (WHERE assessment_id IS NOT NULL) as should_have_fk
            FROM responses
        """
        )

        result = cursor.fetchone()
        null_fk = result["null_fk"]
        should_have_fk = result["should_have_fk"]

        # Allow for responses without assessments (nullable FK)
        if null_fk == 0:
            self.passed += 1
            print(f"  ✅ All foreign key relationships migrated")
        else:
            self.failed += 1
            print(
                f"  ⚠️  {null_fk} responses without assessment UUID (expected if nullable)"
            )

    def validate_step3(self, cursor):
        """Validate Step 3: Integer columns replaced with UUID"""

        print("Checking that integer columns are removed...")

        # Check that integer columns are gone from responses
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'responses'
              AND column_name IN ('id', 'assessment_id', 'respondent_id')
        """
        )

        remaining_int_cols = cursor.fetchall()

        if len(remaining_int_cols) == 0:
            self.passed += 1
            print(f"  ✅ Integer columns removed from responses")
        else:
            self.failed += 1
            print(
                f"  ❌ Integer columns still exist: {[c['column_name'] for c in remaining_int_cols]}"
            )

        # Check that UUID columns are now primary keys
        print("\nChecking primary keys...")

        cursor.execute(
            """
            SELECT
                t.table_name,
                a.attname as column_name,
                typ.typname as data_type
            FROM pg_tables t
            JOIN pg_attribute a ON a.attrelid = t.tablename::regclass
            JOIN pg_type typ ON a.atttypid = typ.oid
            JOIN pg_index i ON i.indrelid = a.attrelid AND a.attnum = ANY(i.indkey)
            WHERE t.schemaname = 'public'
              AND i.indisprimary
              AND t.table_name = 'responses'
        """
        )

        result = cursor.fetchone()

        if result and result["data_type"] == "uuid":
            self.passed += 1
            print(f"  ✅ Responses table has UUID primary key")
        else:
            self.failed += 1
            print(f"  ❌ Responses table primary key issue")

        # Test foreign key constraints
        print("\nTesting foreign key constraints...")

        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM responses r
                JOIN assessments a ON r.assessment_id = a.id
            """
            )
            result = cursor.fetchone()
            self.passed += 1
            print(f"  ✅ Foreign key to assessments works")
        except psycopg.Error as e:
            self.failed += 1
            print(f"  ❌ Foreign key to assessments failed: {e}")

        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM response_scores rs
                JOIN responses r ON rs.response_id = r.id
            """
            )
            result = cursor.fetchone()
            self.passed += 1
            print(f"  ✅ Foreign key to responses works")
        except psycopg.Error as e:
            self.failed += 1
            print(f"  ❌ Foreign key to responses failed: {e}")

        # Check for NULL IDs
        print("\nChecking for NULL IDs...")

        cursor.execute(
            """
            SELECT
                'responses' as table_name,
                COUNT(*) FILTER (WHERE id IS NULL) as null_count
            FROM responses
            UNION ALL
            SELECT
                'response_scores',
                COUNT(*) FILTER (WHERE id IS NULL)
            FROM response_scores
        """
        )

        results = cursor.fetchall()

        all_zero = True
        for result in results:
            if result["null_count"] > 0:
                all_zero = False
                self.failed += 1
                print(
                    f"  ❌ {result['table_name']} has {result['null_count']} NULL IDs"
                )

        if all_zero:
            self.passed += 1
            print(f"  ✅ No NULL IDs found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate migration steps")
    parser.add_argument(
        "--step",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="Migration step to validate (1, 2, or 3)",
    )

    args = parser.parse_args()

    validator = MigrationValidator(args.step)
    validator.run()
