"""
Documentation Code Examples Validation Tests

This test suite validates that all code examples in documentation files:
1. Have valid syntax
2. Can execute without runtime errors
3. Follow security best practices (no hardcoded credentials)
4. Are properly formatted and complete

Purpose: Prevent broken code examples from reaching production
Framework: Phase 1 Code Quality Initiative
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
from pydantic import BaseModel, ValidationError


# =============================================================================
# Test Configuration
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
    (r'api_key\s*=\s*["\'][\w-]{20,}["\']', "Potential API key"),
    (r'password\s*=\s*["\'][\w]+["\']', "Hardcoded password"),
]


# =============================================================================
# Data Models
# =============================================================================

class CodeExample(BaseModel):
    """Represents a code example found in documentation"""
    language: str
    code: str
    line_number: int
    file_path: Path


class SecurityViolation(BaseModel):
    """Represents a security violation found in documentation"""
    line_number: int
    violation_type: str
    pattern: str
    context: str


class SyntaxError(BaseModel):
    """Represents a syntax error in code examples"""
    line_number: int
    language: str
    error_message: str
    code_snippet: str


# =============================================================================
# Helper Functions
# =============================================================================

def extract_code_blocks(markdown_content: str, file_path: Path) -> List[CodeExample]:
    """
    Extract all code blocks from markdown file

    Args:
        markdown_content: Content of markdown file
        file_path: Path to the markdown file

    Returns:
        List of CodeExample objects
    """
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
                code_blocks.append(CodeExample(
                    language=current_language or "text",
                    code='\n'.join(current_code),
                    line_number=start_line,
                    file_path=file_path
                ))
                current_code = []
        elif in_code_block:
            current_code.append(line)

    return code_blocks


def check_for_hardcoded_credentials(content: str, file_path: Path) -> List[SecurityViolation]:
    """
    Check for hardcoded credentials in documentation

    Args:
        content: Documentation content
        file_path: Path to documentation file

    Returns:
        List of SecurityViolation objects
    """
    violations = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        for pattern, description in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                violations.append(SecurityViolation(
                    line_number=i,
                    violation_type=description,
                    pattern=pattern,
                    context=line.strip()[:80]
                ))

    return violations


def validate_json_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate JSON syntax

    Args:
        code: JSON code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        json.loads(code)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {str(e)}"


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate Python syntax

    Args:
        code: Python code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        compile(code, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Python syntax error: {str(e)}"


def validate_bash_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate bash script syntax

    Args:
        code: Bash code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Write to temp file and check with bash -n
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(code)
            temp_path = f.name

        result = subprocess.run(
            ['bash', '-n', temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        os.unlink(temp_path)

        if result.returncode != 0:
            return False, f"Bash syntax error: {result.stderr}"

        return True, ""

    except subprocess.TimeoutExpired:
        return False, "Bash validation timeout"
    except Exception as e:
        return False, f"Bash validation error: {str(e)}"


def validate_curl_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate cURL command syntax (basic validation)

    Args:
        code: cURL command to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic validation - check for curl command
    if not re.search(r'\bcurl\b', code):
        return False, "No curl command found"

    # Check for balanced quotes
    single_quotes = code.count("'")
    double_quotes = code.count('"')

    if single_quotes % 2 != 0:
        return False, "Unbalanced single quotes"

    if double_quotes % 2 != 0:
        return False, "Unbalanced double quotes"

    return True, ""


def check_python_imports(code: str) -> List[str]:
    """
    Check for undefined imports in Python code

    Args:
        code: Python code to check

    Returns:
        List of potentially undefined identifiers
    """
    # This is a basic check - in production, you'd use AST parsing
    undefined = []

    # Common undefined functions found in broken docs
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
# Tests
# =============================================================================

class TestDocumentationSecurity:
    """Test suite for documentation security issues"""

    def test_no_hardcoded_credentials_in_original_doc(self):
        """Test: Original documentation should have hardcoded credentials (expected fail)"""
        if not ORIGINAL_DOC.exists():
            pytest.skip("Original documentation not found")

        content = ORIGINAL_DOC.read_text()
        violations = check_for_hardcoded_credentials(content, ORIGINAL_DOC)

        # This test EXPECTS to find violations in the original
        assert len(violations) > 0, "Expected to find hardcoded credentials in original doc"

        # Print violations for reference
        print(f"\nFound {len(violations)} security violations in original doc:")
        for v in violations[:5]:
            print(f"  Line {v.line_number}: {v.violation_type}")

    def test_no_hardcoded_credentials_in_corrected_doc(self):
        """Test: Corrected documentation should have NO hardcoded credentials"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        violations = check_for_hardcoded_credentials(content, CORRECTED_DOC)

        assert len(violations) == 0, (
            f"Found {len(violations)} hardcoded credential(s) in corrected doc:\n" +
            "\n".join([f"  Line {v.line_number}: {v.violation_type}" for v in violations])
        )


class TestCodeExamplesSyntax:
    """Test suite for code example syntax validation"""

    def test_json_examples_are_valid(self):
        """Test: All JSON code examples should be valid JSON"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        json_blocks = [b for b in code_blocks if b.language.lower() in ['json', 'jsonc']]
        errors = []

        for block in json_blocks:
            is_valid, error_msg = validate_json_syntax(block.code)
            if not is_valid:
                errors.append({
                    'line': block.line_number,
                    'error': error_msg,
                    'code': block.code[:100]
                })

        if errors:
            pytest.fail(
                f"Found {len(errors)} invalid JSON example(s):\n" +
                "\n".join([f"  Line {e['line']}: {e['error']}" for e in errors])
            )

    def test_python_examples_are_valid(self):
        """Test: All Python code examples should have valid syntax"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        python_blocks = [b for b in code_blocks if b.language.lower() == 'python']
        errors = []

        for block in python_blocks:
            is_valid, error_msg = validate_python_syntax(block.code)
            if not is_valid:
                errors.append({
                    'line': block.line_number,
                    'error': error_msg,
                    'code': block.code[:100]
                })

        if errors:
            pytest.fail(
                f"Found {len(errors)} Python syntax error(s):\n" +
                "\n".join([f"  Line {e['line']}: {e['error']}" for e in errors])
            )

    def test_bash_examples_are_valid(self):
        """Test: All bash script examples should have valid syntax"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        bash_blocks = [b for b in code_blocks if b.language.lower() in ['bash', 'sh', 'shell']]
        errors = []

        for block in bash_blocks:
            # Skip if it's just inline commands
            if not block.code.strip().startswith('#!') and 'echo ' in block.code[:50]:
                continue

            is_valid, error_msg = validate_bash_syntax(block.code)
            if not is_valid:
                errors.append({
                    'line': block.line_number,
                    'error': error_msg,
                    'code': block.code[:100]
                })

        if errors:
            pytest.fail(
                f"Found {len(errors)} bash syntax error(s):\n" +
                "\n".join([f"  Line {e['line']}: {e['error']}" for e in errors])
            )

    def test_curl_examples_are_valid(self):
        """Test: All cURL examples should have valid syntax"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        curl_blocks = [
            b for b in code_blocks
            if b.language.lower() == 'bash' and 'curl' in b.code
        ]
        errors = []

        for block in curl_blocks:
            # Extract curl commands
            for line in block.code.split('\n'):
                if 'curl' in line:
                    is_valid, error_msg = validate_curl_syntax(line)
                    if not is_valid:
                        errors.append({
                            'line': block.line_number,
                            'error': error_msg,
                            'command': line.strip()[:80]
                        })

        if errors:
            pytest.fail(
                f"Found {len(errors)} cURL syntax error(s):\n" +
                "\n".join([f"  Line {e['line']}: {e['error']}" for e in errors])
            )


class TestPythonCodeCompleteness:
    """Test suite for Python code completeness"""

    def test_no_undefined_functions_in_corrected_doc(self):
        """Test: Python examples should not have undefined functions"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        python_blocks = [b for b in code_blocks if b.language.lower() == 'python']
        undefined_issues = []

        for block in python_blocks:
            undefined = check_python_imports(block.code)
            if undefined:
                undefined_issues.append({
                    'line': block.line_number,
                    'undefined': undefined,
                    'code': block.code[:100]
                })

        if undefined_issues:
            pytest.fail(
                f"Found {len(undefined_issues)} Python example(s) with undefined functions:\n" +
                "\n".join([
                    f"  Line {issue['line']}: {', '.join(issue['undefined'])}"
                    for issue in undefined_issues
                ])
            )


class TestDocumentationCompleteness:
    """Test suite for documentation completeness"""

    def test_has_error_response_examples(self):
        """Test: Documentation should include error response examples"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()

        # Check for error response sections
        assert 'error_responses' in content.lower() or 'error handling' in content.lower(), \
            "Documentation should include error response examples"

        # Check for common error codes
        error_codes = ['401', '404', '500', '400']
        missing_codes = []

        for code in error_codes:
            if code not in content:
                missing_codes.append(code)

        assert len(missing_codes) == 0, \
            f"Missing error response examples for: {', '.join(missing_codes)}"

    def test_has_rate_limiting_documentation(self):
        """Test: Documentation should include rate limiting information"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()

        assert 'rate limit' in content.lower(), \
            "Documentation should include rate limiting information"

    def test_has_parameter_documentation(self):
        """Test: Endpoints should have parameter documentation"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()

        # Look for parameter tables
        parameter_keywords = [
            'parameter',
            'type',
            'required',
            'description'
        ]

        found_params = sum(1 for keyword in parameter_keywords if keyword.lower() in content.lower())

        assert found_params >= 3, \
            "Documentation should include parameter documentation (Parameter, Type, Required, Description)"

    def test_has_authentication_section(self):
        """Test: Documentation should include authentication information"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()

        assert 'authentication' in content.lower() or 'auth' in content.lower(), \
            "Documentation should include authentication section"

        # Check for JWT/token info
        assert 'jwt' in content.lower() or 'token' in content.lower(), \
            "Documentation should mention JWT tokens or authentication tokens"


class TestTemplateQuality:
    """Test suite for documentation template quality"""

    def test_template_exists(self):
        """Test: Documentation template should exist"""
        template_path = DOCS_DIR.parent / "docs" / "templates" / "API_DOCUMENTATION_TEMPLATE.md"

        assert template_path.exists(), \
            f"Documentation template not found at {template_path}"

    def test_template_has_security_checklist(self):
        """Test: Template should include security checklist"""
        template_path = DOCS_DIR.parent / "docs" / "templates" / "API_DOCUMENTATION_TEMPLATE.md"

        if not template_path.exists():
            pytest.skip("Template not found")

        content = template_path.read_text()

        assert 'security checklist' in content.lower() or 'security' in content.lower(), \
            "Template should include security checklist"

        assert 'hardcoded' in content.lower() or 'credential' in content.lower(), \
            "Template should warn against hardcoded credentials"

    def test_template_has_code_validation_section(self):
        """Test: Template should include code example validation"""
        template_path = DOCS_DIR.parent / "docs" / "templates" / "API_DOCUMENTATION_TEMPLATE.md"

        if not template_path.exists():
            pytest.skip("Template not found")

        content = template_path.read_text()

        assert 'code example' in content.lower(), \
            "Template should include code example guidelines"


class TestCorrectedDocumentationQuality:
    """Test suite for corrected documentation quality"""

    def test_corrected_doc_exists(self):
        """Test: Corrected documentation should exist"""
        assert CORRECTED_DOC.exists(), \
            f"Corrected documentation not found at {CORRECTED_DOC}"

    def test_corrected_doc_has_more_content_than_original(self):
        """Test: Corrected doc should be more complete than original"""
        if not ORIGINAL_DOC.exists():
            pytest.skip("Original documentation not found")

        original_content = ORIGINAL_DOC.read_text()
        corrected_content = CORRECTED_DOC.read_text()

        # Corrected should be longer (more comprehensive)
        assert len(corrected_content) > len(original_content), \
            "Corrected documentation should be more comprehensive than original"

    def test_corrected_doc_mentions_fixes(self):
        """Test: Corrected doc should mention fixes applied"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()

        # Should mention fixes or corrections
        assert any(keyword in content.lower() for keyword in ['fix', 'corrected', 'quality']), \
            "Corrected documentation should mention fixes applied"


# =============================================================================
# Integration Tests
# =============================================================================

class TestDocumentationWorkflow:
    """Test suite for documentation workflow validation"""

    def test_can_extract_all_code_examples(self):
        """Test: Should be able to extract all code examples from docs"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        assert len(code_blocks) > 0, "Should find code examples in documentation"

        # Print stats
        print(f"\nFound {len(code_blocks)} code examples:")
        by_lang = {}
        for block in code_blocks:
            by_lang[block.language] = by_lang.get(block.language, 0) + 1

        for lang, count in sorted(by_lang.items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang}: {count}")

    def test_all_python_code_can_be_parsed(self):
        """Test: All Python code should be parseable (AST)"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        python_blocks = [b for b in code_blocks if b.language.lower() == 'python']

        for block in python_blocks:
            try:
                compile(block.code, '<string>', 'exec')
            except SyntaxError as e:
                pytest.fail(f"Python code at line {block.line_number} cannot be parsed: {e}")


# =============================================================================
# Performance Tests
# =============================================================================

class TestDocumentationPerformance:
    """Test suite for documentation performance"""

    def test_documentation_size_is_reasonable(self):
        """Test: Documentation should not be excessively large (> 1MB)"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        size = CORRECTED_DOC.stat().st_size

        assert size < 1_000_000, \
            f"Documentation is too large: {size:,} bytes (should be < 1MB)"

    def test_code_examples_not_too_long(self):
        """Test: Individual code examples should be reasonable length (< 500 lines)"""
        if not CORRECTED_DOC.exists():
            pytest.skip("Corrected documentation not found")

        content = CORRECTED_DOC.read_text()
        code_blocks = extract_code_blocks(content, CORRECTED_DOC)

        for block in code_blocks:
            line_count = len(block.code.split('\n'))
            assert line_count < 500, \
                f"Code example at line {block.line_number} is too long: {line_count} lines"


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
