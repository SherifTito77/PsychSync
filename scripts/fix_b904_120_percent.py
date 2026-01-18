#!/usr/bin/env python3
"""
120% B904 Exception Chaining Fix - Comprehensive Improvement Strategy

This script not only fixes B904 errors but also:
- Tests syntax thoroughly
- Identifies related bugs
- Suggests improvements
- Validates changes

Goal: Go beyond 100% to 120% - complete B904 compliance + bug fixes + improvements
"""

import ast
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict


def check_syntax_detailed(file_path: str) -> Tuple[bool, List[str]]:
    """Check syntax and return detailed errors."""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        return True, []
    except SyntaxError as e:
        return False, [
            f"Line {e.lineno}: {e.msg}",
            f"  {e.text if e.text else ''}"
        ]


def fix_b904_manually(file_path: str) -> Dict[str, int]:
    """Manually fix B904 errors with careful review."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        original = content
        lines = content.split('\n')
        result = []
        fixes = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            result.append(line)

            # Track if we're in an except block
            for j in range(max(0, i-15), i):
                if re.match(r'^(\s*)except\s+\w+\s+as\s+(\w+):', lines[j]):
                    indent = re.match(r'^(\s*)except', lines[j]).group(1)
                    exc_var = re.search(r'as\s+(\w+):', lines[j]).group(1)

                    # Check if current line has a raise without 'from'
                    if re.search(r'raise\s+\w+', line) and ' from ' not in line:
                        # Find the end of the raise statement
                        if line.rstrip().endswith(')'):
                            # Single line raise
                            result[-1] = re.sub(r'\)\s*$', f') from {exc_var}', line)
                            fixes += 1
                        elif line.rstrip().endswith('('):
                            # Multi-line raise - find closing paren
                            k = i + 1
                            while k < len(lines) and not lines[k].strip().startswith(')'):
                                result.append(lines[k])
                                k += 1
                            if k < len(lines):
                                # Found closing line
                                result[-1] = re.sub(r'\)\s*$', f') from {exc_var}', result[-1])
                                fixes += 1
                                i = k
                    break
            i += 1

        if fixes > 0:
            with open(file_path, 'w') as f:
                f.write('\n'.join(result))

        return {'b904_fixes': fixes}

    except Exception as e:
        return {'error': str(e)}


def identify_improvements(file_path: str) -> List[str]:
    """Identify potential improvements beyond B904 fixes."""
    improvements = []

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check for common issues
        if 'print(' in content:
            improvements.append("Contains print() statements - consider logging")

        if 'TODO' in content or 'FIXME' in content:
            improvements.append("Contains TODO/FIXME comments")

        if content.count('try:') != content.count('except'):
            improvements.append("Unmatched try/except blocks")

        # Check for overly complex functions
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 50:
                    improvements.append(f"Function {node.name} is very long ({len(node.body)} statements)")

    except (ValueError, TypeError, json.JSONDecodeError) as e:
        pass

    return improvements


def validate_fix(file_path: str) -> Dict[str, any]:
    """Validate that fixes are correct."""
    validation = {
        'syntax_ok': False,
        'b904_count': 0,
        'improvements': [],
        'can_commit': False
    }

    # Check syntax
    syntax_ok, errors = check_syntax_detailed(file_path)
    validation['syntax_ok'] = syntax_ok

    if not syntax_ok:
        validation['syntax_errors'] = errors
        return validation

    # Check B904 count
    result = subprocess.run(
        ["ruff", "check", file_path, "--select", "B904"],
        capture_output=True,
        text=True
    )
    validation['b904_count'] = result.stdout.count('B904')

    # Check for improvements
    validation['improvements'] = identify_improvements(file_path)

    validation['can_commit'] = (
        validation['syntax_ok'] and
        validation['b904_count'] == 0
    )

    return validation


def process_file_comprehensive(file_path: str) -> Dict[str, any]:
    """Process a file with comprehensive review."""
    print(f"\n{'='*70}")
    print(f"PROCESSING: {file_path}")
    print('='*70)

    result = {
        'file': file_path,
        'original_b904': 0,
        'fixed': False,
        'syntax_errors': [],
        'improvements': [],
        'bugs_found': 0
    }

    # Get original B904 count
    check_result = subprocess.run(
        ["ruff", "check", file_path, "--select", "B904"],
        capture_output=True,
        text=True
    )
    result['original_b904'] = check_result.stdout.count('B904')
    print(f"Original B904 errors: {result['original_b904']}")

    # Check initial syntax
    syntax_ok, errors = check_syntax_detailed(file_path)
    if not syntax_ok:
        result['syntax_errors'] = errors
        print(f"❌ Syntax errors:")
        for error in errors:
            print(f"   {error}")
        return result

    print("✓ Syntax OK")

    # Apply B904 fixes
    fix_result = fix_b904_manually(file_path)
    if 'error' in fix_result:
        print(f"❌ Fix error: {fix_result['error']}")
        return result

    print(f"✓ Applied {fix_result.get('b904_fixes', 0)} B904 fixes")

    # Try ruff auto-fix
    ruff_result = subprocess.run(
        ["ruff", "check", file_path, "--select", "B904", "--fix"],
        capture_output=True,
        text=True
    )

    # Validate final state
    validation = validate_fix(file_path)
    print(f"Final B904 errors: {validation['b904_count']}")

    if validation['improvements']:
        print(f"\n🔍 Potential improvements found:")
        for imp in validation['improvements'][:5]:
            print(f"   • {imp}")
        result['improvements'] = validation['improvements']
        result['bugs_found'] = len(validation['improvements'])

    result['fixed'] = validation['b904_count'] == 0
    result['final_b904'] = validation['b904_count']

    if result['fixed']:
        print("\n✅ FULLY FIXED - B904 compliant!")
    elif validation['b904_count'] < result['original_b904']:
        print(f"\n⚠️  PARTIALLY FIXED - {result['original_b904'] - validation['b904_count']} errors resolved")
    else:
        print("\n❌ COULD NOT FIX - Requires expert review")

    return result


# Main execution
if __name__ == "__main__":
    import sys

    # Read file list from previous command
    files_to_fix = []
    with open('/tmp/b904_files.txt', 'r') as f:
        for line in f:
            if '-->' in line:
                file_path = line.split('-->')[1].strip()
                if file_path and file_path not in files_to_fix:
                    files_to_fix.append(file_path)

    print("="*80)
    print("120% B904 IMPROVEMENT - COMPREHENSIVE FIX")
    print("="*80)
    print(f"Files to process: {len(files_to_fix)}")

    if len(sys.argv) > 1:
        # Process specific file
        file_path = sys.argv[1]
        result = process_file_comprehensive(file_path)
        sys.exit(0 if result['fixed'] else 1)
    else:
        print("\nUsage: python3 scripts/fix_b904_120_percent.py <file_path>")
        print("\nTop 10 critical files to fix:")
        for i, file in enumerate(files_to_fix[:10], 1):
            print(f"  {i}. {file}")
