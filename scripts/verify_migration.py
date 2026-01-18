"""
Migration Verification Script
==============================

Verifies that the migration from app.core.security to app.services.security
was successful and no regressions were introduced.

Usage:
    python scripts/verify_migration.py

Author: Development Team
Version: 1.0 (Phase 2 - Service Layer Refactoring)
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# =============================================================================
# Configuration
# =============================================================================


# Patterns to search for remaining old imports
OLD_IMPORT_PATTERNS = [
    r"from app\.core\.security import",
]

# Files and directories to exclude from verification
EXCLUDE_PATTERNS = [
    "*.backup*",
    "*.pyc",
    "__pycache__",
    "venv/",
    ".venv/",
    "node_modules/",
    ".git/",
    "dist/",
    "build/",
]

# Explicit excludes (files that are allowed to have old imports)
EXPLICIT_EXCLUDES = [
    "scripts/migrate_security_imports.py",
    "scripts/verify_migration.py",
    "PHASE2_IMPLEMENTATION_PLAN.md",
    "SOLID_REMEDIATION_IMPLEMENTATION.md",
]


# =============================================================================
# Verification Functions
# =============================================================================


def check_old_imports(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Check for remaining old imports in the codebase.

    Args:
        project_root: Root directory of project

    Returns:
        (has_old_imports, list_of_files_with_old_imports)
    """
    print("🔍 Checking for remaining old imports...")
    print("-" * 70)

    files_with_old_imports = []

    # Use grep to search for old imports
    for pattern in OLD_IMPORT_PATTERNS:
        try:
            result = subprocess.run(
                ["grep", "-r", pattern, "--include=*.py", str(project_root)],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                # Parse results
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue

                    # Extract file path
                    file_path = line.split(":")[0]
                    file_path_obj = Path(file_path)

                    # Check if should be excluded
                    relative_path = file_path_obj.relative_to(project_root)

                    # Skip explicit excludes
                    if any(str(relative_path) == exc for exc in EXPLICIT_EXCLUDES):
                        continue

                    # Skip exclude patterns
                    if any(pattern in str(relative_path) for pattern in EXCLUDE_PATTERNS):
                        continue

                    if str(relative_path) not in files_with_old_imports:
                        files_with_old_imports.append(str(relative_path))

        except FileNotFoundError:
            print("⚠️  grep command not found, using Python fallback...")
            # Fallback: use Python to search
            for py_file in project_root.rglob("*.py"):
                relative_path = py_file.relative_to(project_root)

                # Skip explicit excludes
                if any(str(relative_path) == exc for exc in EXPLICIT_EXCLUDES):
                    continue

                # Skip exclude patterns
                if any(pattern in str(relative_path) for pattern in EXCLUDE_PATTERNS):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    if re.search(pattern, content):
                        files_with_old_imports.append(str(relative_path))

                except Exception:
                    pass

    print()
    if files_with_old_imports:
        print(f"⚠️  Found {len(files_with_old_imports)} files with old imports:")
        for file_path in files_with_old_imports:
            print(f"   ❌ {file_path}")
        return False, files_with_old_imports
    else:
        print("✅ No old imports found!")
        return True, []


def check_new_imports(project_root: Path) -> Tuple[bool, int]:
    """
    Check for new imports to confirm migration occurred.

    Args:
        project_root: Root directory of project

    Returns:
        (has_new_imports, count_of_files_with_new_imports)
    """
    print("\n🔍 Checking for new imports...")
    print("-" * 70)

    pattern = r"from app\.services\.security import"
    files_with_new_imports = []

    for py_file in project_root.rglob("*.py"):
        relative_path = py_file.relative_to(project_root)

        # Skip exclude patterns
        if any(pattern in str(relative_path) for pattern in EXCLUDE_PATTERNS):
            continue

        # Skip explicit excludes
        if any(str(relative_path) == exc for exc in EXPLICIT_EXCLUDES):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            if re.search(pattern, content):
                files_with_new_imports.append(str(relative_path))

        except Exception:
            pass

    if files_with_new_imports:
        print(f"✅ Found {len(files_with_new_imports)} files with new imports")
        return True, len(files_with_new_imports)
    else:
        print("⚠️  No files found with new imports!")
        print("   This might indicate migration didn't work correctly")
        return False, 0


def check_python_syntax(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Check Python syntax of all files.

    Args:
        project_root: Root directory of project

    Returns:
        (all_files_valid, list_of_invalid_files)
    """
    print("\n🔍 Checking Python syntax...")
    print("-" * 70)

    import py_compile

    invalid_files = []
    checked_count = 0

    for py_file in project_root.rglob("*.py"):
        relative_path = py_file.relative_to(project_root)

        # Skip exclude patterns
        if any(pattern in str(relative_path) for pattern in EXCLUDE_PATTERNS):
            continue

        # Skip explicit excludes
        if any(str(relative_path) == exc for exc in EXPLICIT_EXCLUDES):
            continue

        try:
            py_compile.compile(str(py_file), doraise=True)
            checked_count += 1
        except py_compile.PyCompileError as e:
            invalid_files.append(str(relative_path))

    print(f"📝 Checked {checked_count} files")

    if invalid_files:
        print(f"⚠️  Found {len(invalid_files)} files with syntax errors:")
        for file_path in invalid_files:
            print(f"   ❌ {file_path}")
        return False, invalid_files
    else:
        print("✅ All files have valid syntax!")
        return True, []


def check_imports_work(project_root: Path) -> bool:
    """
    Check if new imports actually work.

    Args:
        project_root: Root directory of project

    Returns:
        True if imports work, False otherwise
    """
    print("\n🔍 Checking if new imports work...")
    print("-" * 70)

    test_imports = [
        "from app.services.security import get_password_hash",
        "from app.services.security import verify_password",
        "from app.services.security import validate_password",
        "from app.services.security import create_access_token",
        "from app.services.security import verify_token",
        "from app.services.security import get_current_user",
        "from app.services.security import has_role",
        "from app.services.security import is_owner",
        "from app.services.security import sanitize_input",
        "from app.services.security import escape_html",
    ]

    all_passed = True

    for import_statement in test_imports:
        try:
            result = subprocess.run(
                [sys.executable, "-c", import_statement],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=10,
            )

            if result.returncode == 0:
                print(f"   ✅ {import_statement}")
            else:
                print(f"   ❌ {import_statement}")
                print(f"      Error: {result.stderr}")
                all_passed = False

        except subprocess.TimeoutExpired:
            print(f"   ⏱️  {import_statement} (timeout)")
            all_passed = False
        except Exception as e:
            print(f"   ❌ {import_statement}")
            print(f"      Error: {e}")
            all_passed = False

    if all_passed:
        print("\n✅ All imports work correctly!")
    else:
        print("\n⚠️  Some imports failed!")

    return all_passed


def check_git_status(project_root: Path) -> Tuple[bool, int]:
    """
    Check git status to see what changed.

    Args:
        project_root: Root directory of project

    Returns:
        (is_git_repo, number_of_changed_files)
    """
    print("\n🔍 Checking git status...")
    print("-" * 70)

    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        if result.returncode != 0:
            print("⚠️  Not in a git repository")
            return False, 0

        # Get number of changed files
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            changed_files = [f for f in result.stdout.strip().split("\n") if f]

            if changed_files:
                print(f"📝 Found {len(changed_files)} changed files:")
                for file_path in changed_files[:10]:  # Show first 10
                    print(f"   → {file_path}")

                if len(changed_files) > 10:
                    print(f"   ... and {len(changed_files) - 10} more")

                return True, len(changed_files)
            else:
                print("ℹ️  No changes detected (files may already be committed)")
                return True, 0

    except FileNotFoundError:
        print("⚠️  git command not found")
        return False, 0

    return False, 0


def print_summary(
    old_imports_ok: bool,
    new_imports_ok: bool,
    syntax_ok: bool,
    imports_work: bool,
    files_with_old_imports: List[str],
    files_with_new_imports: int,
):
    """Print verification summary."""
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)

    checks = [
        ("Old imports removed", old_imports_ok, "⚠️  Some old imports remain"),
        ("New imports present", new_imports_ok, "No new imports found"),
        ("Python syntax valid", syntax_ok, "Some files have syntax errors"),
        ("Imports work", imports_work, "Some imports don't work"),
    ]

    all_passed = True

    for check_name, passed, fail_message in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")

        if not passed:
            print(f"   → {fail_message}")
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✅ VERIFICATION PASSED!")
        print("\n🚀 Migration successful! You can now:")
        print("   1. Commit your changes")
        print("   2. Run the test suite")
        print("   3. Push to remote")
        print("\n" + "=" * 70 + "\n")
        return 0
    else:
        print("\n❌ VERIFICATION FAILED!")
        print("\n🔧 Please fix the issues above:")
        print("   1. Check files with old imports")
        print("   2. Fix syntax errors")
        print("   3. Re-run this script")
        print("\n" + "=" * 70 + "\n")
        return 1


# =============================================================================
# Main
# =============================================================================


def main():
    """Main verification function."""
    project_root = Path.cwd()

    print("=" * 70)
    print("🔍 MIGRATION VERIFICATION SCRIPT")
    print("=" * 70)
    print(f"📁 Project root: {project_root}\n")

    # Run all checks
    old_imports_ok, files_with_old_imports = check_old_imports(project_root)
    new_imports_ok, files_with_new_imports = check_new_imports(project_root)
    syntax_ok, invalid_files = check_python_syntax(project_root)
    imports_work = check_imports_work(project_root)

    # Check git status (optional, doesn't affect pass/fail)
    is_git_repo, changed_files = check_git_status(project_root)

    # Print summary and exit
    exit_code = print_summary(
        old_imports_ok=old_imports_ok,
        new_imports_ok=new_imports_ok,
        syntax_ok=syntax_ok,
        imports_work=imports_work,
        files_with_old_imports=files_with_old_imports,
        files_with_new_imports=files_with_new_imports,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
