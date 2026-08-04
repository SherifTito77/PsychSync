#!/usr/bin/env python3
"""
Comprehensive Exception Handling Fixer Script

Automatically applies standardized exception handling to all API endpoints.
This script fixes the most common unsafe patterns:
1. Raw exception details in HTTPException
2. Inconsistent error response formats
3. Missing exception logging
4. Unsafe error messages

Usage:
    python scripts/fix_exception_handling_comprehensive.py
"""

import re
from pathlib import Path
from typing import List, Tuple


class ExceptionHandlingFixer:
    """Automated exception handling pattern fixer"""

    def __init__(self, base_path: str = "/Users/sheriftito/Downloads/psychsync"):
        self.base_path = Path(base_path)
        self.endpoints_dir = self.base_path / "app/api/v1/endpoints"

        # Patterns to fix
        self.patterns = {
            # Pattern 1: Raw exception in HTTPException detail
            "raw_exception": re.compile(
                r'raise HTTPException\(\s*status_code=status\.HTTP_\d+_\w+,\s*detail=f?"?[^"]*\{e![sr}]\}[^"]*\"?\s*(?:from e)?\s*\)',
                re.MULTILINE,
            ),
            # Pattern 2: Generic except Exception as e without logging
            "generic_except": re.compile(
                r"except\s+Exception\s+as\s+e:\s*\n\s*(?:logger\.\w+)?\s*(?:raise|return)",
                re.MULTILINE,
            ),
            # Pattern 3: HTTPException with raw detail string
            "unsafe_detail": re.compile(
                r'raise HTTPException\(\s*status_code=(\d+|status\.HTTP_\w+),\s*detail=("[^"]*"|\'[^\']*\')\s*\)',
                re.MULTILINE,
            ),
        }

    def find_files_to_fix(self) -> List[Path]:
        """Find all Python files in endpoints directory"""
        return list(self.endpoints_dir.glob("*.py"))

    def fix_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Fix exception handling in a single file

        Returns:
            (was_modified, fix_count)
        """
        content = file_path.read_text()
        original_content = content
        fix_count = 0

        # Check if already uses @handle_exceptions
        if (
            "@handle_exceptions" in content
            or "from app.core.exception_handling import" in content
        ):
            return False, 0

        # Add import if needed
        if "from app.core.exception_handling import" not in content:
            # Find the imports section
            import_match = re.search(r"(from app\.api\.v1\.deps import.*?\n)", content)
            if import_match:
                # Add our import after the deps import
                insert_pos = import_match.end()
                new_import = (
                    "from app.core.exception_handling import handle_exceptions\n"
                )
                content = content[:insert_pos] + new_import + content[insert_pos:]
                fix_count += 1

        # Fix Pattern 1: Raw exception in HTTPException
        matches = self.patterns["raw_exception"].finditer(content)
        for match in matches:
            # Extract the status code
            status_match = re.search(
                r"status_code=(status\.HTTP_\d+_\w+)", match.group(0)
            )
            if status_match:
                status_code = status_match.group(1)
                # Replace with safe message
                safe_replacement = f"""raise HTTPException(
                    status_code={status_code},
                    detail={{
                        "message": "An error occurred while processing your request",
                        "error_code": "SYS_6000"
                    }}
                )"""
                content = (
                    content[: match.start()] + safe_replacement + content[match.end() :]
                )
                fix_count += 1

        # Fix Pattern 2: Generic except without proper handling
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for unsafe exception handling patterns
            if "except Exception as e:" in line:
                # Check if next line has logging
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if (
                        "logger" not in next_line
                        and "raise HTTPException" not in next_line
                    ):
                        # Add proper logging
                        indent = len(line) - len(line.lstrip())
                        logger_line = (
                            " " * indent
                            + 'logger.error(f"Unexpected error: {e!s}", exc_info=True)'
                        )
                        lines.insert(i + 1, logger_line)
                        fix_count += 1

            i += 1

        content = "\n".join(lines)

        # Only write if changes were made
        if content != original_content:
            file_path.write_text(content)
            return True, fix_count

        return False, 0

    def fix_all_files(self) -> dict:
        """Fix all endpoint files"""
        files = self.find_files_to_fix()
        results = {
            "total": len(files),
            "modified": 0,
            "skipped": 0,
            "total_fixes": 0,
            "files": [],
        }

        print(f"🔍 Found {len(files)} endpoint files to analyze...")

        for file_path in files:
            if file_path.name.startswith("_") or file_path.suffix != ".py":
                continue

            try:
                was_modified, fix_count = self.fix_file(file_path)

                if was_modified:
                    results["modified"] += 1
                    results["total_fixes"] += fix_count
                    results["files"].append(
                        {
                            "path": str(file_path.relative_to(self.base_path)),
                            "fixes": fix_count,
                        }
                    )
                    print(f"  ✅ Fixed {file_path.name} ({fix_count} fixes)")
                else:
                    results["skipped"] += 1

            except Exception as e:
                print(f"  ❌ Error fixing {file_path.name}: {e}")

        return results


def main():
    """Main execution"""
    print("=" * 80)
    print("🔒 COMPREHENSIVE EXCEPTION HANDLING FIXER")
    print("=" * 80)
    print()

    fixer = ExceptionHandlingFixer()
    results = fixer.fix_all_files()

    print()
    print("=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print(f"Total files analyzed: {results['total']}")
    print(f"Files modified: {results['modified']}")
    print(f"Files skipped: {results['skipped']}")
    print(f"Total fixes applied: {results['total_fixes']}")
    print()

    if results["files"]:
        print("Modified files:")
        for file_info in results["files"]:
            print(f"  - {file_info['path']}: {file_info['fixes']} fixes")

    print()
    print("=" * 80)
    print("✅ EXCEPTION HANDLING FIX COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
