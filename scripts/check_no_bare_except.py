#!/usr/bin/env python3
"""
Pre-commit hook to check for bare exception handlers.

This script scans Python files for bare 'except:' clauses and rejects commits
that contain them, enforcing better error handling practices.
"""

import ast
import sys
from pathlib import Path


class BareExceptChecker(ast.NodeVisitor):
    """AST visitor to find bare except clauses."""

    def __init__(self, filename: str):
        self.filename = filename
        self.errors = []

    def check(self) -> bool:
        """Check file for bare except clauses. Returns True if found."""

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception:
            return False  # Can't read file

        try:
            tree = ast.parse(source, filename=self.filename)
        except SyntaxError:
            return False  # Will be caught by other hooks

        self.visit(tree)
        return len(self.errors) > 0

    def visit_Try(self, node: ast.Try):
        """Visit try statements and check for bare except."""

        for handler in node.handlers:
            if handler.type is None:  # Bare except
                self.errors.append(
                    {
                        "line": handler.lineno,
                        "col": handler.col_offset,
                    }
                )

        self.generic_visit(node)


def main():
    """Main entry point."""

    if len(sys.argv) < 2:
        print("Usage: check_no_bare_except.py <file1.py> [file2.py] ...")
        sys.exit(1)

    files = sys.argv[1:]
    has_errors = False

    for file_path in files:
        path = Path(file_path)

        if not path.exists():
            continue

        if not path.suffix == ".py":
            continue

        checker = BareExceptChecker(str(path))

        if checker.check():
            has_errors = True

            for error in checker.errors:
                print(f"❌ {path}:{error['line']}: Bare 'except:' clause found")
                print(
                    f"   Use 'except Exception as e:' or specific exception types instead"
                )

    if has_errors:
        print("\n💡 Bare exception handlers are dangerous because they:")
        print("   • Catch KeyboardInterrupt (prevents Ctrl+C)")
        print("   • Catch SystemExit (prevents program termination)")
        print("   • Hide errors without logging")
        print("   • Make debugging impossible")
        print("\n✅ Fix: Replace 'except:' with 'except Exception as e:'")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
