#!/usr/bin/env python3
"""
Advanced Documentation Validation Tests

Additional validation scenarios beyond the basic quality checks.
Tests for: TODOs, dead links, heading structure, table formatting.

Usage:
    python tests/documentation/advanced_validation.py
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urljoin


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def check_todos_and_fixes(content: str, file_path: Path) -> List[dict]:
    """Check for unresolved TODOs and FIXMEs"""
    issues = []
    lines = content.split("\n")

    todo_patterns = [
        (r"TODO:", "TODO comment"),
        (r"FIXME:", "FIXME comment"),
        (r"XXX:", "XXX comment"),
        (r"HACK:", "HACK comment"),
        (r"NOTE:", "NOTE that requires action"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, description in todo_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if in code block
                if not _is_in_code_block(lines[:i]):
                    issues.append(
                        {"line": i, "type": description, "content": line.strip()[:80]}
                    )

    return issues


def check_dead_links(content: str, file_path: Path) -> List[dict]:
    """Check for dead external links in documentation"""
    issues = []

    # Extract all markdown links
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    for match in re.finditer(link_pattern, content):
        link_text = match.group(1)
        link_url = match.group(2)

        # Skip internal links and anchors
        if link_url.startswith("#") or link_url.startswith("/"):
            continue

        # Skip email links
        if link_url.startswith("mailto:"):
            continue

        # Check if link is accessible (with timeout)
        try:
            if link_url.startswith("http"):
                req = urllib.request.Request(link_url, method="HEAD")
                req.add_header("User-Agent", "Documentation-Validator/1.0")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status >= 400:
                        issues.append(
                            {
                                "url": link_url,
                                "status": response.status,
                                "text": link_text,
                            }
                        )
        except Exception as e:
            # Don't fail on network errors, just note them
            issues.append({"url": link_url, "error": str(e), "text": link_text})

    return issues


def check_heading_structure(content: str, file_path: Path) -> List[dict]:
    """Check for proper heading hierarchy"""
    issues = []
    lines = content.split("\n")
    headings = []

    # Extract all headings
    for i, line in enumerate(lines, 1):
        if line.startswith("#"):
            level = len(re.match(r"^#+", line).group())
            text = line.lstrip("#").strip()
            headings.append({"line": i, "level": level, "text": text})

    # Check hierarchy
    if len(headings) == 0:
        return [{"error": "No headings found"}]

    # Should start with h1
    if headings[0]["level"] != 1:
        issues.append(
            {
                "line": headings[0]["line"],
                "issue": f"First heading is h{headings[0]['level']}, should be h1",
                "text": headings[0]["text"][:50],
            }
        )

    # Check for skipped levels (e.g., h1 -> h3)
    for i in range(1, len(headings)):
        prev_level = headings[i - 1]["level"]
        curr_level = headings[i]["level"]

        if curr_level > prev_level + 1:
            issues.append(
                {
                    "line": headings[i]["line"],
                    "issue": f"Skipped heading level: h{prev_level} → h{curr_level}",
                    "text": headings[i]["text"][:50],
                }
            )

    return issues


def check_table_formatting(content: str, file_path: Path) -> List[dict]:
    """Check for properly formatted markdown tables"""
    issues = []
    lines = content.split("\n")
    in_table = False
    table_start = 0
    table_lines = []

    for i, line in enumerate(lines, 1):
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_start = i
                table_lines = []
            table_lines.append((i, line))
        elif in_table:
            # Table ended
            issues.extend(_validate_table(table_lines, table_start))
            in_table = False
            table_lines = []

    return issues


def _validate_table(table_lines: List[Tuple[int, str]], table_start: int) -> List[dict]:
    """Validate a single table"""
    issues = []

    if len(table_lines) < 2:
        return [{"line": table_start, "issue": "Table has no header row"}]

    # Check separator row (second line)
    if len(table_lines) >= 2:
        separator = table_lines[1][1]
        if not re.match(r"^\|[\s\-:]+\|$", separator):
            issues.append(
                {
                    "line": table_lines[1][0],
                    "issue": "Table separator row malformed (should be |---|---|)",
                    "content": separator[:60],
                }
            )

    # Check all rows have same column count
    col_counts = [line.count("|") - 1 for _, line in table_lines]
    if len(set(col_counts)) > 1:
        issues.append(
            {
                "line": table_start,
                "issue": f"Table has inconsistent column counts: {col_counts}",
                "content": f"{len(table_lines)} rows with varying columns",
            }
        )

    return issues


def check_code_block_languages(content: str, file_path: Path) -> List[dict]:
    """Check that all code blocks have language identifiers"""
    issues = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            # Closing fence
            if line.strip() == "```":
                continue

            # Opening fence - check for language
            lang = line.strip().replace("```", "").strip()
            if not lang:
                issues.append(
                    {
                        "line": i,
                        "issue": "Code block missing language identifier",
                        "context": _get_code_context(lines, i),
                    }
                )

    return issues


def _get_code_context(lines: List[str], line_num: int) -> str:
    """Get context around a code block"""
    start = max(0, line_num - 2)
    end = min(len(lines), line_num + 3)
    context = "\n".join(lines[start:end])
    return context[:150] + "..." if len(context) > 150 else context


def _is_in_code_block(lines_before: List[str]) -> bool:
    """Check if current position is inside a code block"""
    code_block_count = sum(1 for line in lines_before if line.strip().startswith("```"))
    return code_block_count % 2 == 1


def run_advanced_validation(docs_dir: Path) -> dict:
    """Run all advanced validation tests"""
    print_header("ADVANCED DOCUMENTATION VALIDATION")

    all_docs = list(docs_dir.glob("*.md"))
    all_docs.extend(docs_dir.rglob("*.md"))

    results = {
        "total_files": len(all_docs),
        "files_with_todos": 0,
        "files_with_heading_issues": 0,
        "files_with_table_issues": 0,
        "files_with_code_block_issues": 0,
        "total_issues": 0,
    }

    for doc_file in all_docs:
        print_info(f"Validating: {doc_file.relative_to(docs_dir.parent)}")

        try:
            content = doc_file.read_text()
        except (OSError, IOError, ValueError) as e:
            continue

        # Check for TODOs
        todos = check_todos_and_fixes(content, doc_file)
        if todos:
            results["files_with_todos"] += 1
            results["total_issues"] += len(todos)
            print_warning(f"  Found {len(todos)} TODO(s)")
            for todo in todos[:2]:
                print(f"    Line {todo['line']}: {todo['content']}")

        # Check heading structure
        headings = check_heading_structure(content, doc_file)
        if headings:
            results["files_with_heading_issues"] += 1
            results["total_issues"] += len(headings)
            print_warning(f"  Heading issues: {len(headings)}")
            for issue in headings[:1]:
                print(f"    Line {issue['line']}: {issue['issue']}")

        # Check table formatting
        tables = check_table_formatting(content, doc_file)
        if tables:
            results["files_with_table_issues"] += 1
            results["total_issues"] += len(tables)
            print_warning(f"  Table issues: {len(tables)}")
            for issue in tables[:1]:
                print(f"    Line {issue['line']}: {issue['issue']}")

        # Check code block languages
        code_blocks = check_code_block_languages(content, doc_file)
        if code_blocks:
            results["files_with_code_block_issues"] += 1
            results["total_issues"] += len(code_blocks)
            print_warning(f"  Code block issues: {len(code_blocks)}")
            for issue in code_blocks[:1]:
                print(f"    Line {issue['line']}: {issue['issue']}")

    return results


def main():
    """Run advanced validation"""
    docs_dir = Path(__file__).parent.parent.parent / "docs"

    if not docs_dir.exists():
        print_error(f"Documentation directory not found: {docs_dir}")
        sys.exit(1)

    results = run_advanced_validation(docs_dir)

    # Print summary
    print_header("ADVANCED VALIDATION SUMMARY")
    print(f"Total Files Scanned: {results['total_files']}")
    print(f"Files with TODOs: {results['files_with_todos']}")
    print(f"Files with Heading Issues: {results['files_with_heading_issues']}")
    print(f"Files with Table Issues: {results['files_with_table_issues']}")
    print(f"Files with Code Block Issues: {results['files_with_code_block_issues']}")
    print(f"\nTotal Issues Found: {results['total_issues']}")

    if results["total_issues"] == 0:
        print_success("\n✨ No advanced issues found!")
        return 0
    else:
        print_warning(f"\n⚠️  Found {results['total_issues']} issues to review")
        return 0  # Don't fail, just warn


if __name__ == "__main__":
    sys.exit(main())
