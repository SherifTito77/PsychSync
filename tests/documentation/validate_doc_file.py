#!/usr/bin/env python3
"""
Pre-commit hook for validating individual documentation files.

Usage:
    python tests/documentation/validate_doc_file.py path/to/doc.md

This script performs quick validation on a single documentation file:
- Checks for hardcoded credentials
- Validates JSON examples
- Validates Python code blocks
- Checks for common documentation issues

Exit codes:
    0: All checks passed
    1: Validation failed
"""

import sys
import re
import json
import ast
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_hardcoded_credentials(content: str, filepath: str) -> List[Tuple[int, str]]:
    """Check for hardcoded credentials in documentation."""
    issues = []
    lines = content.split('\n')

    # Patterns to detect hardcoded credentials
    patterns = [
        (r'(email|password|secret|token|api_key|apikey)\s*[:=]\s*["\'][^"\']+@[^"\']+["\']',
         'Hardcoded credential detected'),
        (r'(email|password)\s*[:=]\s*["\'][^"\']{8,}["\']',
         'Potential hardcoded credential'),
    ]

    # Exclude common placeholders and example values
    exclusion_patterns = [
        r'\byour_\w+\b',  # your_token, your_password, etc.
        r'\byour-\w+-\w+\b',  # your-production-secret-key
        r'\bexample\.(com|org|net)\b',
        r'\btest@\w+\.\w+\b',
        r'\bdemo@\w+\.\w+\b',
        r'\buser@\w+\.\w+\b',
        r'\badmin@\w+\.\w+\b',
        r'\bjohn@example\.com\b',
        r'\bjane@example\.com\b',
        r'\\$[A-Z_]+\b',  # Environment variables like $EMAIL, $PASSWORD
        r'\$\{[A-Z_]+\b',  # Environment variables like ${EMAIL}
        r'\$\{[A-Z_]+:',  # Environment variable defaults ${SECRET_KEY:-default}
        r'\bBearer\s+\$\w+\b',  # Bearer $TOKEN
        r'Bearer\s+eyJ',  # Example JWT tokens (start with eyJ)
        r'\.\.\.',  # Ellipsis in examples
        r'Error:',
        r'<API_TOKEN>',
        r'<EMAIL>',
        r'<PASSWORD>',
    ]

    for line_num, line in enumerate(lines, 1):
        # Skip lines with excluded patterns
        if any(re.search(pattern, line) for pattern in exclusion_patterns):
            continue

        for pattern, message in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append((line_num, f'{message} on line {line_num}'))

    return issues


def extract_json_blocks(content: str) -> List[Tuple[int, str, str]]:
    """Extract JSON code blocks from markdown."""
    json_blocks = []
    lines = content.split('\n')
    in_json_block = False
    block_start = 0
    block_content = []

    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith('```json'):
            in_json_block = True
            block_start = line_num
            block_content = []
        elif in_json_block and line.strip() == '```':
            in_json_block = False
            json_blocks.append((block_start, '\n'.join(block_content), line_num))
        elif in_json_block:
            block_content.append(line)

    return json_blocks


def validate_json_blocks(content: str, filepath: str) -> List[Tuple[int, str]]:
    """Validate all JSON examples in the documentation."""
    issues = []
    json_blocks = extract_json_blocks(content)

    for start_line, json_content, end_line in json_blocks:
        try:
            json.loads(json_content)
        except json.JSONDecodeError as e:
            issues.append((start_line,
                          f'JSON parse error at block starting at line {start_line}: {str(e)}'))

    return issues


def extract_python_blocks(content: str) -> List[Tuple[int, str, str]]:
    """Extract Python code blocks from markdown."""
    python_blocks = []
    lines = content.split('\n')
    in_python_block = False
    block_start = 0
    block_content = []

    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith('```python') or line.strip().startswith('```py'):
            in_python_block = True
            block_start = line_num
            block_content = []
        elif in_python_block and line.strip() == '```':
            in_python_block = False
            python_blocks.append((block_start, '\n'.join(block_content), line_num))
        elif in_python_block:
            block_content.append(line)

    return python_blocks


def validate_python_blocks(content: str, filepath: str) -> List[Tuple[int, str]]:
    """Validate all Python code blocks in the documentation."""
    issues = []
    python_blocks = extract_python_blocks(content)

    for start_line, python_content, end_line in python_blocks:
        try:
            ast.parse(python_content)
        except SyntaxError as e:
            issues.append((start_line,
                          f'Python syntax error at block starting at line {start_line}: {str(e)}'))

    return issues


def check_documentation_completeness(content: str, filepath: str) -> List[Tuple[int, str]]:
    """Check for common documentation completeness issues."""
    issues = []
    lines = content.split('\n')

    # Check if file has error response examples
    has_error_responses = any('error' in line.lower() and '```' in lines[max(0, i-5):i+5]
                             for i, line in enumerate(lines))

    # Check if file has authentication section
    has_auth_section = any('authentication' in line.lower() or 'auth' in line.lower()
                          for line in lines)

    # For API documentation (check by file path or content)
    if 'api' in filepath.lower() or '/api/' in content.lower():
        if not has_error_responses:
            issues.append((0, 'Missing error response examples'))

        if not has_auth_section:
            issues.append((0, 'Missing authentication section'))

    return issues


def validate_documentation_file(filepath: str) -> Tuple[bool, List[str]]:
    """Validate a single documentation file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f'Failed to read file: {str(e)}']

    all_issues = []

    # Run all validation checks
    all_issues.extend(check_hardcoded_credentials(content, filepath))
    all_issues.extend(validate_json_blocks(content, filepath))
    all_issues.extend(validate_python_blocks(content, filepath))
    all_issues.extend(check_documentation_completeness(content, filepath))

    # Convert issues to strings
    issue_strings = [issue[1] for issue in all_issues]

    return len(issue_strings) == 0, issue_strings


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print(f'{YELLOW}Usage: validate_doc_file.py <documentation_file.md>{RESET}')
        sys.exit(1)

    filepath = sys.argv[1]
    path = Path(filepath)

    if not path.exists():
        print(f'{RED}Error: File not found: {filepath}{RESET}')
        sys.exit(1)

    if not path.suffix == '.md':
        # Not a markdown file, skip
        sys.exit(0)

    print(f'{BLUE}Validating: {filepath}{RESET}')

    is_valid, issues = validate_documentation_file(filepath)

    if is_valid:
        print(f'{GREEN}✅ Documentation validation passed!{RESET}')
        sys.exit(0)
    else:
        print(f'{RED}❌ Documentation validation failed:{RESET}')
        for issue in issues:
            print(f'{RED}  - {issue}{RESET}')
        print()
        print(f'{YELLOW}Please fix the above issues before committing.{RESET}')
        sys.exit(1)


if __name__ == '__main__':
    main()
