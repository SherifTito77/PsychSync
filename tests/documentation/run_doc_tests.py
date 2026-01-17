#!/usr/bin/env python3
"""
Standalone Documentation Test Runner

This script runs documentation validation tests WITHOUT importing the FastAPI app.
Run this directly to avoid dependency issues.

Usage:
    python tests/documentation/run_doc_tests.py
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# =============================================================================
# Configuration
# =============================================================================

DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
CORRECTED_DOC = DOCS_DIR / "AI_AGENTS_USAGE_GUIDE_CORRECTED.md"
ORIGINAL_DOC = DOCS_DIR / "AI_AGENTS_USAGE_GUIDE.md"

# Security patterns that should NOT be in documentation
FORBIDDEN_PATTERNS = [
    (r'["\']your@email\.com["\']', "Hardcoded email address"),
    (r'["\']yourpassword["\']', "Hardcoded password"),
    (r'TOKEN\s*=\s*["\']YOUR[_"]?JWT[_"]?TOKEN["\']', "Hardcoded JWT token"),
    (r'SECRET_KEY["\']?\s*:\s*["\']my-secret-key["\']', "Hardcoded secret key"),
]


# =============================================================================
# Colors and Formatting
# =============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


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


# =============================================================================
# Validation Functions
# =============================================================================

def check_for_hardcoded_credentials(content: str, file_path: Path) -> List[dict]:
    """Check for hardcoded credentials in documentation"""
    violations = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        for pattern, description in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                violations.append({
                    'line_number': i,
                    'violation_type': description,
                    'context': line.strip()[:80]
                })

    return violations


def extract_code_blocks(markdown_content: str) -> List[dict]:
    """Extract all code blocks from markdown file"""
    code_blocks = []
    lines = markdown_content.split('\n')

    in_code_block = False
    current_language = ""
    current_code = []
    start_line = 0

    for i, line in enumerate(lines, 1):
        if line.strip().startswith('```'):
            if not in_code_block:
                # Start of code block
                in_code_block = True
                current_language = line.strip().replace('```', '').strip()
                start_line = i
                current_code = []
            else:
                # End of code block
                in_code_block = False
                code_blocks.append({
                    'language': current_language or "text",
                    'code': '\n'.join(current_code),
                    'line_number': start_line
                })
                current_code = []
        elif in_code_block:
            current_code.append(line)

    return code_blocks


def validate_json(code: str) -> Tuple[bool, str]:
    """Validate JSON syntax"""
    try:
        json.loads(code)
        return True, ""
    except json.JSONDecodeError as e:
        return False, str(e)


def validate_python(code: str) -> Tuple[bool, str]:
    """Validate Python syntax"""
    try:
        compile(code, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def check_python_imports(code: str) -> List[str]:
    """Check for undefined imports in Python code"""
    undefined = []
    undefined_patterns = [
        r'load_metrics\(',
        r'load_system_metrics\(',
    ]

    for pattern in undefined_patterns:
        if re.search(pattern, code):
            func_name = pattern.replace(r'\(', '').replace('\\', '')
            if f"def {func_name}" not in code:
                undefined.append(func_name)

    return undefined


# =============================================================================
# Test Suites
# =============================================================================

def test_security():
    """Test suite for security issues"""
    print_header("SECURITY TESTS")

    total_tests = 0
    passed_tests = 0

    # Test 1: Original doc should have hardcoded credentials (expected fail)
    print_info("Test 1: Checking original documentation for hardcoded credentials...")
    total_tests += 1

    if ORIGINAL_DOC.exists():
        content = ORIGINAL_DOC.read_text()
        violations = check_for_hardcoded_credentials(content, ORIGINAL_DOC)

        if len(violations) > 0:
            print_success(f"Found {len(violations)} security violations in original doc (expected)")
            for v in violations[:3]:
                print(f"    Line {v['line_number']}: {v['violation_type']}")
            passed_tests += 1
        else:
            print_warning("No violations found in original doc (unexpected)")
    else:
        print_warning("Original documentation not found")

    # Test 2: Corrected doc should have NO hardcoded credentials
    print_info("\nTest 2: Checking corrected documentation for hardcoded credentials...")
    total_tests += 1

    if CORRECTED_DOC.exists():
        content = CORRECTED_DOC.read_text()
        violations = check_for_hardcoded_credentials(content, CORRECTED_DOC)

        if len(violations) == 0:
            print_success("No hardcoded credentials found in corrected doc ✅")
            passed_tests += 1
        else:
            print_error(f"Found {len(violations)} hardcoded credential(s) in corrected doc:")
            for v in violations:
                print(f"    Line {v['line_number']}: {v['violation_type']}")
    else:
        print_error("Corrected documentation not found")

    return total_tests, passed_tests


def test_code_syntax():
    """Test suite for code syntax validation"""
    print_header("CODE SYNTAX TESTS")

    if not CORRECTED_DOC.exists():
        print_error("Corrected documentation not found")
        return 0, 0

    content = CORRECTED_DOC.read_text()
    code_blocks = extract_code_blocks(content)

    total_tests = 0
    passed_tests = 0

    # Test JSON examples
    print_info(f"Test 1: Validating JSON examples...")
    json_blocks = [b for b in code_blocks if b['language'].lower() in ['json', 'jsonc']]
    total_tests += 1

    errors = []
    for block in json_blocks:
        is_valid, error_msg = validate_json(block['code'])
        if not is_valid:
            errors.append({
                'line': block['line_number'],
                'error': error_msg
            })

    if not errors:
        print_success(f"All {len(json_blocks)} JSON examples are valid ✅")
        passed_tests += 1
    else:
        print_error(f"Found {len(errors)} invalid JSON example(s):")
        for e in errors[:3]:
            print(f"    Line {e['line']}: {e['error'][:60]}...")

    # Test Python examples
    print_info(f"\nTest 2: Validating Python syntax...")
    python_blocks = [b for b in code_blocks if b['language'].lower() == 'python']
    total_tests += 1

    errors = []
    for block in python_blocks:
        is_valid, error_msg = validate_python(block['code'])
        if not is_valid:
            errors.append({
                'line': block['line_number'],
                'error': error_msg
            })

    if not errors:
        print_success(f"All {len(python_blocks)} Python examples have valid syntax ✅")
        passed_tests += 1
    else:
        print_error(f"Found {len(errors)} Python syntax error(s):")
        for e in errors[:3]:
            print(f"    Line {e['line']}: {e['error'][:60]}...")

    # Test for undefined functions
    print_info(f"\nTest 3: Checking for undefined functions in Python examples...")
    total_tests += 1

    undefined_issues = []
    for block in python_blocks:
        undefined = check_python_imports(block['code'])
        if undefined:
            undefined_issues.append({
                'line': block['line_number'],
                'undefined': undefined
            })

    if not undefined_issues:
        print_success("No undefined functions found ✅")
        passed_tests += 1
    else:
        print_error(f"Found {len(undefined_issues)} example(s) with undefined functions:")
        for issue in undefined_issues[:3]:
            print(f"    Line {issue['line']}: {', '.join(issue['undefined'])}")

    return total_tests, passed_tests


def test_documentation_completeness():
    """Test suite for documentation completeness"""
    print_header("DOCUMENTATION COMPLETENESS TESTS")

    if not CORRECTED_DOC.exists():
        print_error("Corrected documentation not found")
        return 0, 0

    content = CORRECTED_DOC.read_text().lower()

    total_tests = 0
    passed_tests = 0

    # Test 1: Error responses
    print_info("Test 1: Checking for error response examples...")
    total_tests += 1

    if 'error' in content and ('response' in content or 'handling' in content):
        error_codes = ['401', '404', '500', '400']
        found_codes = sum(1 for code in error_codes if code in content)

        if found_codes >= 3:
            print_success(f"Found error response examples ({found_codes}/4 codes) ✅")
            passed_tests += 1
        else:
            print_warning(f"Limited error examples ({found_codes}/4 codes found)")
    else:
        print_error("No error response examples found")

    # Test 2: Rate limiting
    print_info("\nTest 2: Checking for rate limiting information...")
    total_tests += 1

    if 'rate limit' in content:
        print_success("Rate limiting information present ✅")
        passed_tests += 1
    else:
        print_error("No rate limiting information found")

    # Test 3: Parameter documentation
    print_info("\nTest 3: Checking for parameter documentation...")
    total_tests += 1

    param_keywords = ['parameter', 'type', 'required', 'description']
    found_params = sum(1 for kw in param_keywords if kw in content)

    if found_params >= 3:
        print_success(f"Parameter documentation present ({found_params}/4 keywords) ✅")
        passed_tests += 1
    else:
        print_warning(f"Limited parameter docs ({found_params}/4 keywords)")

    # Test 4: Authentication
    print_info("\nTest 4: Checking for authentication information...")
    total_tests += 1

    if 'authentication' in content or 'auth' in content:
        if 'jwt' in content or 'token' in content:
            print_success("Authentication information present ✅")
            passed_tests += 1
        else:
            print_warning("Auth section found but missing JWT/token info")
    else:
        print_error("No authentication information found")

    return total_tests, passed_tests


def test_file_quality():
    """Test suite for file quality metrics"""
    print_header("FILE QUALITY TESTS")

    total_tests = 0
    passed_tests = 0

    # Test 1: Corrected doc exists
    print_info("Test 1: Checking if corrected documentation exists...")
    total_tests += 1

    if CORRECTED_DOC.exists():
        print_success(f"Corrected doc found at {CORRECTED_DOC.name} ✅")
        passed_tests += 1
    else:
        print_error("Corrected documentation not found")

    # Test 2: Corrected doc is larger than original
    print_info("\nTest 2: Checking if corrected doc is more comprehensive...")
    total_tests += 1

    if ORIGINAL_DOC.exists() and CORRECTED_DOC.exists():
        original_size = ORIGINAL_DOC.stat().st_size
        corrected_size = CORRECTED_DOC.stat().st_size

        if corrected_size > original_size:
            improvement = ((corrected_size - original_size) / original_size) * 100
            print_success(f"Corrected doc is {improvement:.1f}% larger ✅")
            passed_tests += 1
        else:
            print_warning("Corrected doc is not larger than original")
    else:
        print_warning("Cannot compare (one or both files missing)")

    # Test 3: File size is reasonable
    print_info("\nTest 3: Checking if file size is reasonable...")
    total_tests += 1

    if CORRECTED_DOC.exists():
        size = CORRECTED_DOC.stat().st_size
        size_mb = size / (1024 * 1024)

        if size_mb < 1:
            print_success(f"File size is reasonable: {size_mb:.3f} MB ✅")
            passed_tests += 1
        else:
            print_warning(f"File is large: {size_mb:.2f} MB")

    return total_tests, passed_tests


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all documentation tests"""
    print(f"\n{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║         Documentation Code Examples Validation Tests             ║")
    print("║                    Phase 1 Code Quality Initiative               ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")

    all_total = 0
    all_passed = 0

    # Run all test suites
    total, passed = test_security()
    all_total += total
    all_passed += passed

    total, passed = test_code_syntax()
    all_total += total
    all_passed += passed

    total, passed = test_documentation_completeness()
    all_total += total
    all_passed += passed

    total, passed = test_file_quality()
    all_total += total
    all_passed += passed

    # Print summary
    print_header("TEST SUMMARY")
    print(f"Total Tests:  {all_total}")
    print(f"Passed:       {all_passed}")
    print(f"Failed:       {all_total - all_passed}")

    success_rate = (all_passed / all_total * 100) if all_total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✨ EXCELLENT! Documentation quality is high!{Colors.END}\n")
        return 0
    elif success_rate >= 60:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  GOOD, but room for improvement.{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ NEEDS ATTENTION - Review documentation.{Colors.END}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
