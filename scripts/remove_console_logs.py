#!/usr/bin/env python3
"""
Console.log Removal Script

This script finds and replaces console.log statements with proper logging
using environment-aware logging utilities.

Usage:
    # Dry run (see what would be changed)
    python scripts/remove_console_logs.py --dry-run

    # Apply changes with backup
    python scripts/remove_console_logs.py --apply --backup

    # Apply to specific directory
    python scripts/remove_console_logs.py --apply --path frontend/src/components
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Console.log patterns to find
CONSOLE_PATTERNS = [
    r"console\.log\(",  # console.log(
    r"console\.debug\(",  # console.debug(
    r"console\.info\(",  # console.info(
    r"console\.warn\(",  # console.warn(
    r"console\.error\(",  # console.error(
    r"console\.trace\(",  # console.trace(
]


class ConsoleLogRemover:
    """Finds and replaces console.log statements with proper logging."""

    def __init__(self, root_path: str, dry_run: bool = False, backup: bool = False):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.backup = backup
        self.stats = {
            "files_scanned": 0,
            "files_modified": 0,
            "console_logs_removed": 0,
            "errors": 0,
        }

    def find_typescript_files(self) -> List[Path]:
        """Find all TypeScript files in the project."""
        patterns = ["**/*.ts", "**/*.tsx"]
        files = []

        for pattern in patterns:
            files.extend(self.root_path.rglob(pattern))

        # Filter out node_modules and other ignored directories
        ignored_dirs = {
            "node_modules",
            ".git",
            "dist",
            "build",
            ".next",
            "coverage",
            ".cache",
        }

        return [
            f
            for f in files
            if not any(ignored_dir in f.parts for ignored_dir in ignored_dirs)
        ]

    def has_logger_import(self, content: str) -> bool:
        """Check if file already has logger import."""
        # Check for both default and named imports
        return bool(
            re.search(r"import\s+logger.*from.*['\"@/utils/logger'\"]", content)
        )

    def add_logger_import(self, content: str, file_path: Path) -> Tuple[str, bool]:
        """Add logger import to file if needed."""
        if self.has_logger_import(content):
            return content, False

        # Find the last import statement
        import_pattern = r"^import\s+.*from\s+['\"].*['\"]\s*;?\s*$"
        imports = list(re.finditer(import_pattern, content, re.MULTILINE))

        if not imports:
            # No imports found, add at the beginning
            import_statement = "import logger from '@/utils/logger';\n"
            return import_statement + "\n" + content, True

        # Add after the last import
        last_import = imports[-1]
        insert_pos = last_import.end()

        import_statement = "\nimport logger from '@/utils/logger';"
        new_content = content[:insert_pos] + import_statement + content[insert_pos:]

        return new_content, True

    def create_comment(self, content: str, line_num: int, original: str) -> str:
        """Create a comment showing the original console.log for manual review."""
        return (
            f"// TODO(human): Review and convert to appropriate logger method\n"
            f"// Original: {original}\n"
        )

    def should_auto_convert(self, console_call: str, log_level: str) -> bool:
        """Determine if a console call can be auto-converted."""
        # Auto-convert simple cases
        simple_patterns = [
            r"console\.log\(['\"]\w+['\"]\)",  # console.log('simple')
            r"console\.error\(['\"]\w+['\"]\)",  # console.error('error')
        ]

        for pattern in simple_patterns:
            if re.match(pattern, console_call.strip()):
                return True

        return False

    def replace_simple_console(self, content: str, matches) -> Tuple[str, int]:
        """Replace simple console statements that can be auto-converted."""
        new_content = content
        conversions = 0

        # Simple replacements for console.error -> logger.error
        new_content = re.sub(
            r"console\.error\(['\"]([^'\"]+)['\"]\);?",
            r"logger.error('\1');",
            new_content,
        )

        # Simple replacements for console.warn -> logger.warn
        new_content = re.sub(
            r"console\.warn\(['\"]([^'\"]+)['\"]\);?",
            r"logger.warn('\1');",
            new_content,
        )

        # Count how many were converted
        conversions = (
            content.count("console.error")
            + content.count("console.warn")
            - new_content.count("console.error")
            - new_content.count("console.warn")
        )

        return new_content, conversions

    def process_file(self, file_path: Path) -> Dict:
        """Process a single file and replace console statements."""
        result = {
            "path": str(file_path),
            "modified": False,
            "logs_removed": 0,
            "backup_path": None,
            "changes": [],
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            content = original_content
            logs_removed = 0

            # Count console statements before
            before_count = sum(content.count(pattern) for pattern in CONSOLE_PATTERNS)

            # Check and add logger import if needed
            content, import_added = self.add_logger_import(content, file_path)
            if import_added:
                result["changes"].append("Added logger import")

            # Auto-convert simple console.error and console.warn statements
            content, conversions = self.replace_simple_console(content, None)
            logs_removed += conversions

            # Count remaining console statements
            after_count = sum(content.count(pattern) for pattern in CONSOLE_PATTERNS)

            # Track remaining console statements that need manual review
            if after_count > 0:
                result["needs_manual_review"] = True
                result["remaining_consoles"] = after_count

                # Find line numbers for remaining console statements
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if any(pattern in line for pattern in CONSOLE_PATTERNS):
                        result["changes"].append(f"Line {i}: {line.strip()[:80]}")

            result["logs_removed"] = before_count - after_count
            result["modified"] = content != original_content

            if result["modified"] and not self.dry_run:
                # Create backup
                if self.backup:
                    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
                    backup_path.write_text(original_content)
                    result["backup_path"] = str(backup_path)

                # Write changes
                file_path.write_text(content)

        except Exception as e:
            result["error"] = str(e)
            self.stats["errors"] += 1

        return result

    def run(self) -> List[Dict]:
        """Run the console log removal process."""
        files = self.find_typescript_files()
        results = []

        print(f"🔍 Scanning {len(files)} TypeScript files...\n")

        for file_path in files:
            self.stats["files_scanned"] += 1
            result = self.process_file(file_path)
            results.append(result)

            # Show files that were modified or need review
            if result["modified"] or result.get("needs_manual_review"):
                if result["modified"]:
                    self.stats["files_modified"] += 1
                    self.stats["console_logs_removed"] += result["logs_removed"]
                    status = "✅ Would modify" if self.dry_run else "✅ Modified"
                else:
                    status = "⚠️  Needs review"

                print(f"{status}: {file_path.relative_to(self.root_path)}")
                if result.get("logs_removed"):
                    print(
                        f"   ├─ Auto-converted: {result['logs_removed']} console statements"
                    )
                if result.get("remaining_consoles"):
                    print(
                        f"   ├─ Needs manual review: {result['remaining_consoles']} statements"
                    )
                    if result.get("changes"):
                        for change in result["changes"][:2]:  # Show first 2
                            print(f"   │  ├─ {change}")
                        if len(result["changes"]) > 2:
                            print(f"   │  └─ ... and {len(result['changes']) - 2} more")
                if result.get("backup_path"):
                    print(f"   └─ Backup: {Path(result['backup_path']).name}")
                print()

        return results

    def print_summary(self):
        """Print summary of changes."""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Files scanned:       {self.stats['files_scanned']}")
        print(f"Files modified:      {self.stats['files_modified']}")
        print(f"Console logs removed: {self.stats['console_logs_removed']}")
        print(f"Errors:              {self.stats['errors']}")

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No files were modified")
            print("   Run with --apply --backup to make changes with backups")

        # Count files needing manual review
        needs_review = sum(
            1 for r in self.__dict__.get("_results", []) if r.get("needs_manual_review")
        )
        if needs_review > 0:
            print(
                f"\n⚠️  {needs_review} files need manual review for complex console statements"
            )
            print(
                "   These files have console statements that couldn't be auto-converted"
            )
            print("   Please review and convert them manually using:")
            print("   - logger.error() for errors")
            print("   - logger.warn() for warnings")
            print("   - logger.debug() for development-only output")
            print("   - logger.info() for general information")
            print("   - logger.logSecurityEvent() for security-relevant events")

        if self.stats["console_logs_removed"] > 0 or needs_review > 0:
            print("\n📚 Documentation:")
            print("   Logger API: frontend/src/utils/logger.ts")
            print("   Fix guide: QUICK_FIX_GUIDE.md")


def main():
    parser = argparse.ArgumentParser(
        description="Remove console.log statements and replace with proper logging"
    )
    parser.add_argument(
        "--path", default="frontend/src", help="Path to scan (default: frontend/src)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes to files")
    parser.add_argument(
        "--backup", action="store_true", help="Create backup files before modifying"
    )

    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True  # Default to dry run for safety

    remover = ConsoleLogRemover(
        root_path=args.path, dry_run=args.dry_run, backup=args.backup
    )

    remover.run()
    remover.print_summary()


if __name__ == "__main__":
    main()
