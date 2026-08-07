#!/usr/bin/env python3
"""
CORRECTED SECURE RANDOM REPLACEMENT SCRIPT
Properly replaces insecure random usage with secrets module

This version correctly preserves numeric values in replacements.
"""

import re
from pathlib import Path

# Mapping of patterns to secure replacements
REPLACEMENTS = [
    # random.randint(a, b) -> secrets.randbelow(b - a) + a
    (
        r"random\.randint\((\d+),\s*(\d+)\)",
        lambda m: f"secrets.randbelow({int(m.group(2)) - int(m.group(1))}) + {m.group(1)}",
    ),
    # secrets.SystemRandom().random() -> secrets.SystemRandom().random()
    (r"random\.random\(\)", "secrets.SystemRandom().random()"),
    # secrets.choice(x) -> secrets.choice(x)
    (r"random\.choice\(([^)]+)\)", r"secrets.choice(\1)"),
    # secrets.SystemRandom().shuffle(x) -> secrets.SystemRandom().shuffle(x)
    (r"random\.shuffle\(([^)]+)\)", r"secrets.SystemRandom().shuffle(\1)"),
    # secrets.SystemRandom().sample(x, n) -> secrets.SystemRandom().sample(x, n)
    (r"random\.sample\(([^,]+),\s*([^)]+)\)", r"secrets.SystemRandom().sample(\1, \2)"),
]


def apply_fixes(file_path: Path) -> bool:
    """Apply fixes to a single file"""
    try:
        content = file_path.read_text()
        original_content = content

        # Apply each replacement pattern
        for pattern, replacement in REPLACEMENTS:
            if callable(replacement):
                # For callable replacements (like randint with math)
                def replacer(match, repl=replacement):
                    return repl(match)

                content = re.sub(pattern, replacer, content)
            else:
                # For string replacements with backreferences
                content = re.sub(pattern, replacement, content)

        if content != original_content:
            # Backup original
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            if not backup_path.exists():
                backup_path.write_text(original_content)

            # Write fixed content
            file_path.write_text(content)
            print(f"✅ Fixed: {file_path}")
            return True
        return False

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def main():
    """Main execution"""
    project_root = Path("/Users/sheriftito/Downloads/psychsync")

    print("🔧 Applying CORRECTED secure random fixes...")
    print("⚠️  Backups will be created as .backup files")
    print()

    fixed_count = 0
    py_files = list(project_root.rglob("*.py"))

    # Exclude test files and venv
    py_files = [
        f
        for f in py_files
        if "test" not in str(f) and "venv" not in str(f) and ".venv" not in str(f)
    ]

    for py_file in py_files:
        if apply_fixes(py_file):
            fixed_count += 1

    print()
    print(f"✅ Fixed {fixed_count} file(s)")
    print()
    print("💡 Next steps:")
    print("   1. Review changes in .backup files")
    print("   2. Run tests to verify fixes work correctly")
    print("   3. Remove .backup files when satisfied")


if __name__ == "__main__":
    main()
