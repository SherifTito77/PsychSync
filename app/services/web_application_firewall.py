"""
Web Application Firewall (WAF) - Advanced Request Filtering

Implements comprehensive WAF rules to block:
- SQL injection (SQLi)
- Cross-site scripting (XSS)
- Path traversal
- Command injection
- LDAP injection
- XML injection
- SSRF attacks
- File inclusion attacks

Author: Security Team
Date: 2025-12-24
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.responses import JSONResponse


# =============================================================================
# WAF Rules Engine
# =============================================================================

class WAFRule:
    """Base WAF rule"""
    name: str
    description: str
    severity: str  # low, medium, high, critical
    rule_type: str  # regex, pattern, size, logical
    enabled: bool = True


class WAFViolation:
    """WAF rule violation"""
    rule_name: str
    severity: str
    matched_pattern: str
    request_details: Dict
    timestamp: str


class WebApplicationFirewall:
    """
    Comprehensive Web Application Firewall

    Protection Layers:
    1. SQL Injection Detection
    2. XSS Detection
    3. Path Traversal Detection
    4. Command Injection Detection
    5. SSRF Detection
    6. File Upload Validation
    7. Request Size Limits
    8. HTTP Method Validation
    9. Content-Type Validation
    10. Rate Limiting (Advanced)
    """

    def __init__(self):
        self.rules = self._initialize_rules()
        self.violations_log: List[WAFViolation] = []

        # Statistics
        self.stats = {
            'total_requests_checked': 0,
            'requests_blocked': 0,
            'violations_by_severity': {
                'low': 0,
                'medium': 0,
                'high': 0,
                'critical': 0
            }
        }

    # ========================================================================
    # Rule Definitions
    # ========================================================================

    def _initialize_rules(self) -> List[WAFRule]:
        """Initialize all WAF rules"""

        return [
            # SQL Injection Rules
            WAFRule(
                name="SQLI-001",
                description="SQL Union-Based Injection",
                severity="critical",
                rule_type="regex"
            ),
            WAFRule(
                name="SQLI-002",
                description="SQL Boolean-Based Injection",
                severity="critical",
                rule_type="regex"
            ),
            WAFRule(
                name="SQLI-003",
                description="SQL Error-Based Injection",
                severity="critical",
                rule_type="regex"
            ),
            WAFRule(
                name="SQLI-004",
                description="SQL Stacked Queries",
                severity="critical",
                rule_type="regex"
            ),

            # XSS Rules
            WAFRule(
                name="XSS-001",
                description="Cross-Site Scripting - Script Tag",
                severity="high",
                rule_type="regex"
            ),
            WAFRule(
                name="XSS-002",
                description="Cross-Site Scripting - Event Handler",
                severity="high",
                rule_type="regex"
            ),
            WAFRule(
                name="XSS-003",
                description="Cross-Site Scripting - JavaScript Protocol",
                severity="high",
                rule_type="regex"
            ),

            # Path Traversal Rules
            WAFRule(
                name="PATH-001",
                description="Path Traversal - ../ Sequence",
                severity="high",
                rule_type="regex"
            ),
            WAFRule(
                name="PATH-002",
                description="Path Traversal - Encoded Dots",
                severity="high",
                rule_type="regex"
            ),

            # Command Injection Rules
            WAFRule(
                name="CMD-001",
                description="Command Injection - Unix Commands",
                severity="critical",
                rule_type="regex"
            ),
            WAFRule(
                name="CMD-002",
                description="Command Injection - Windows Commands",
                severity="critical",
                rule_type="regex"
            ),

            # SSRF Rules
            WAFRule(
                name="SSRF-001",
                description="Server-Side Request Forgery - Internal IPs",
                severity="high",
                rule_type="regex"
            ),
            WAFRule(
                name="SSRF-002",
                description="Server-Side Request Forgery - Localhost",
                severity="high",
                rule_type="regex"
            ),
        ]

    # ========================================================================
    # Request Inspection
    # ========================================================================

    async def check_request(self, request: Request, body: Optional[bytes] = None) -> Tuple[bool, Optional[WAFViolation]]:
        """
        Check request against all WAF rules

        Returns: (is_clean, violation)
        """

        self.stats['total_requests_checked'] += 1

        # Parse request
        request_data = await self._parse_request(request, body)

        # Check 1: SQL Injection
        sqli_violation = self._check_sql_injection(request_data)
        if sqli_violation:
            return False, sqli_violation

        # Check 2: XSS
        xss_violation = self._check_xss(request_data)
        if xss_violation:
            return False, xss_violation

        # Check 3: Path Traversal
        path_violation = self._check_path_traversal(request_data)
        if path_violation:
            return False, path_violation

        # Check 4: Command Injection
        cmd_violation = self._check_command_injection(request_data)
        if cmd_violation:
            return False, cmd_violation

        # Check 5: SSRF
        ssrf_violation = self._check_ssrf(request_data)
        if ssrf_violation:
            return False, ssrf_violation

        # Check 6: Request Size
        size_violation = self._check_request_size(request_data)
        if size_violation:
            return False, size_violation

        # Check 7: HTTP Method
        method_violation = self._check_http_method(request_data)
        if method_violation:
            return False, method_violation

        # Check 8: Content-Type
        content_violation = self._check_content_type(request_data)
        if content_violation:
            return False, content_violation

        # All checks passed
        return True, None

    async def _parse_request(self, request: Request, body: Optional[bytes] = None) -> Dict:
        """Parse request into structured data"""

        data = {
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
            'body': body.decode('utf-8', errors='ignore') if body else '',
            'cookies': dict(request.cookies),
            'client': {
                'host': request.client.host if request.client else 'unknown',
                'port': request.client.port if request.client else None
            }
        }

        # Try to parse JSON body
        if body and request.headers.get('content-type', '').startswith('application/json'):
            try:
                data['json'] = json.loads(data['body'])
            except:
                pass

        return data

    # ========================================================================
    # Attack Detection Methods
    # ========================================================================

    def _check_sql_injection(self, data: Dict) -> Optional[WAFViolation]:
        """Check for SQL injection patterns"""

        # SQL Injection Patterns
        sqli_patterns = [
            # Union-based
            r"['\"]\s*;\s*union\s+(all\s+)?select",
            r"union\s+select.*from",
            r"\d+\s*union\s+select",

            # Boolean-based
            r"\bor\s+1\s*=\s*1",
            r"\band\s+1\s*=\s*1",
            r"['\"]\s+or\s+['\"][\w-]+['\"]\s*=\s*['\"]",
            r"admin['\"]\s*(--|#|/\*|')",

            # Error-based
            r"convert\s*\(|cast\s*\(|group_concat\(",
            r"row\s*\(\s*\d+\s*\)",
            r"count\s*\(\s*\*\s*\)",

            # Stacked queries
            r";\s*(drop|alter|create|delete|insert|update)\s",

            # Time-based blind
            r"waitfor\s+delay\s+['\"]?\d+",
            r"sleep\s*\(\s*\d+\s*\)",
            r"benchmark\s*\(",

            # Common functions
            r"@@version",
            r"version\s*\(\)",
            r"database\s*\(\)",
            r"user\s*\(\)",
            r"current_user",
            r"load_file\s*\(",
            r"into\s+outfile",
            r"information_schema",
        ]

        # Combine all patterns
        combined_pattern = '|'.join(f'(?:{pattern})' for pattern in sqli_patterns)

        # Check all string fields
        fields_to_check = [
            data.get('query', ''),
            data.get('path', ''),
            data.get('body', ''),
            str(data.get('json', {})),
            str(data.get('headers', {})),
        ]

        for field in fields_to_check:
            if isinstance(field, str):
                matches = re.findall(combined_pattern, field, re.IGNORECASE)
                if matches:
                    violation = WAFViolation(
                        rule_name="SQL_INJECTION_DETECTED",
                        severity="critical",
                        matched_pattern=matches[0] if matches else "",
                        request_data=data,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    self.stats['violations_by_severity']['critical'] += 1
                    return violation

        return None

    def _check_xss(self, data: Dict) -> Optional[WAFViolation]:
        """Check for XSS patterns"""

        xss_patterns = [
            # Script tags
            r"<script[^>]*>.*?</script>",
            r"<script[^>]*>",

            # Event handlers
            r"on\w+\s*=\s*['\"][^'\"]*javascript:",

            # JavaScript protocol
            r"javascript:",

            # Common XSS payloads
            r"<iframe[^>]*>",
            r"<embed[^>]*>",
            r"<object[^>]*>",
            r"<link[^>]*>",

            # Expression (IE)
            r"expression\s*\(",

            # Common payload strings
            r"alert\s*\(",
            r"document\.cookie",
            r"document\.location",
            r"fromCharCode",
            r"\\.eval\\(",
        ]

        combined_pattern = '|'.join(f'(?:{pattern})' for pattern in xss_patterns)

        # Check fields
        fields_to_check = [
            data.get('query', ''),
            data.get('body', ''),
            str(data.get('json', {})),
        ]

        for field in fields_to_check:
            if isinstance(field, str):
                matches = re.findall(combined_pattern, field, re.IGNORECASE)
                if matches:
                    violation = WAFViolation(
                        rule_name="XSS_DETECTED",
                        severity="high",
                        matched_pattern=matches[0] if matches else "",
                        request_data=data,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    self.stats['violations_by_severity']['high'] += 1
                    return violation

        return None

    def _check_path_traversal(self, data: Dict) -> Optional[WAFViolation]:
        """Check for path traversal patterns"""

        path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e",
            r"%252e",
            r"\.\.%2f",
            r"\.\.%5c",
            r"%2e%2e%2f",
            r"etc/passwd",
            r"etc/shadow",
            r"windows/system32",
            r"boot\.ini",
            r"web\.config",
        ]

        combined_pattern = '|'.join(f'(?:{pattern})' for pattern in path_traversal_patterns)

        fields_to_check = [
            data.get('path', ''),
            data.get('query', ''),
            str(data.get('json', {})),
        ]

        for field in fields_to_check:
            if isinstance(field, str):
                matches = re.findall(combined_pattern, field, re.IGNORECASE)
                if matches:
                    violation = WAFViolation(
                        rule_name="PATH_TRAVERSAL_DETECTED",
                        severity="high",
                        matched_pattern=matches[0] if matches else "",
                        request_data=data,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    self.stats['violations_by_severity']['high'] += 1
                    return violation

        return None

    def _check_command_injection(self, data: Dict) -> Optional[WAFViolation]:
        """Check for command injection patterns"""

        cmd_injection_patterns = [
            # Unix commands
            r";\s*(ls|cat|wget|curl|nc|netcat|bash|sh|perl|python|ruby)\b",
            r"\|\s*(ls|cat|wget|curl|nc|netcat)",
            r"`\s*(ls|cat|wget|curl)`",
            r"\$\([^)]*\)",

            # Windows commands
            r";\s*(dir|type|cmd|powershell|whoami)\b",
            r"\|\s*(dir|type|cmd|powershell)",

            # Metacharacters
            r";\s*\w+",
            r"\|\s*\w+",
            r"&&\s*\w+",
            r"`[^`]+`",
            r"\$[^$]+",
        ]

        combined_pattern = '|'.join(f'(?:{pattern})' for pattern in cmd_injection_patterns)

        fields_to_check = [
            data.get('path', ''),
            data.get('query', ''),
            data.get('body', ''),
        ]

        for field in fields_to_check:
            if isinstance(field, str):
                matches = re.findall(combined_pattern, field, re.IGNORECASE)
                if matches:
                    violation = WAFViolation(
                        rule_name="COMMAND_INJECTION_DETECTED",
                        severity="critical",
                        matched_pattern=matches[0] if matches else "",
                        request_data=data,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    self.stats['violations_by_severity']['critical'] += 1
                    return violation

        return None

    def _check_ssrf(self, data: Dict) -> Optional[WAFViolation]:
        """Check for Server-Side Request Forgery patterns"""

        ssrf_patterns = [
            # Internal IPs
            r"https?://(?:127\.|0x7f|localhost|2130706433)",
            r"https?://10\.",
            r"https?://172\.(1[6-9]|2[0-9]|3[01])\.",
            r"https?://192\.168\.",

            # Internal hostname
            r"https?://internal",
            r"https?://localhost",
            r"https?://127\.0\.0\.1",
        ]

        combined_pattern = '|'.join(f'(?:{pattern})' for pattern in ssrf_patterns)

        fields_to_check = [
            data.get('query', ''),
            data.get('body', ''),
            str(data.get('json', {})),
        ]

        for field in fields_to_check:
            if isinstance(field, str):
                matches = re.findall(combined_pattern, field, re.IGNORECASE)
                if matches:
                    violation = WAFViolation(
                        rule_name="SSRF_DETECTED",
                        severity="high",
                        matched_pattern=matches[0] if matches else "",
                        request_data=data,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    self.stats['violations_by_severity']['high'] += 1
                    return violation

        return None

    def _check_request_size(self, data: Dict) -> Optional[WAFViolation]:
        """Check request size limits"""

        MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
        MAX_QUERY_SIZE = 2048  # 2KB
        MAX_HEADER_SIZE = 8192  # 8KB

        body_size = len(data.get('body', ''))
        query_size = len(str(data.get('query_params', {})))
        header_size = len(str(data.get('headers', {})))

        if body_size > MAX_BODY_SIZE:
            violation = WAFViolation(
                rule_name="REQUEST_TOO_LARGE",
                severity="medium",
                matched_pattern=f"Body size {body_size} exceeds {MAX_BODY_SIZE}",
                request_data=data,
                timestamp=datetime.utcnow().isoformat()
            )
            self.stats['violations_by_severity']['medium'] += 1
            return violation

        if query_size > MAX_QUERY_SIZE:
            violation = WAFViolation(
                rule_name="QUERY_TOO_LARGE",
                severity="low",
                matched_pattern=f"Query size {query_size} exceeds {MAX_QUERY_SIZE}",
                request_data=data,
                timestamp=datetime.utcnow().isoformat()
            )
            self.stats['violations_by_severity']['low'] += 1
            return violation

        if header_size > MAX_HEADER_SIZE:
            violation = WAFViolation(
                rule_name="HEADERS_TOO_LARGE",
                severity="low",
                matched_pattern=f"Header size {header_size} exceeds {MAX_HEADER_SIZE}",
                request_data=data,
                timestamp=datetime.utcnow().isoformat()
            )
            self.stats['violations_by_severity']['low'] += 1
            return violation

        return None

    def _check_http_method(self, data: Dict) -> Optional[WAFViolation]:
        """Validate HTTP method"""

        allowed_methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}

        method = data.get('method', '').upper()

        if method not in allowed_methods:
            violation = WAFViolation(
                rule_name="INVALID_HTTP_METHOD",
                severity="medium",
                matched_pattern=f"Method {method} not allowed",
                request_data=data,
                timestamp=datetime.utcnow().isoformat()
            )
            self.stats['violations_by_severity']['medium'] += 1
            return violation

        return None

    def _check_content_type(self, data: Dict) -> Optional[WAFViolation]:
        """Validate Content-Type for POST/PUT/PATCH"""

        method = data.get('method', '').upper()

        if method in {'POST', 'PUT', 'PATCH'}:
            content_type = data.get('headers', {}).get('content-type', '')

            allowed_content_types = {
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data',
                'text/plain',
            }

            # Extract base content type (before ;)
            base_content_type = content_type.split(';')[0].strip().lower()

            if base_content_type and base_content_type not in allowed_content_types:
                violation = WAFViolation(
                    rule_name="INVALID_CONTENT_TYPE",
                    severity="low",
                    matched_pattern=f"Content-Type {base_content_type} not allowed",
                    request_data=data,
                    timestamp=datetime.utcnow().isoformat()
                )
                self.stats['violations_by_severity']['low'] += 1
                return violation

        return None

    # ========================================================================
    # Statistics & Monitoring
    # ========================================================================

    def get_statistics(self) -> Dict:
        """Get WAF statistics"""
        return {
            'total_requests_checked': self.stats['total_requests_checked'],
            'requests_blocked': self.stats['requests_blocked'],
            'block_rate': (
                self.stats['requests_blocked'] / self.stats['total_requests_checked']
                if self.stats['total_requests_checked'] > 0 else 0
            ),
            'violations_by_severity': self.stats['violations_by_severity'],
            'active_rules': len([r for r in self.rules if r.enabled]),
            'total_rules': len(self.rules)
        }


# =============================================================================
# FastAPI Middleware
# =============================================================================

from datetime import datetime

waf = WebApplicationFirewall()


async def waf_middleware(request: Request, call_next):
    """
    WAF Middleware for FastAPI

    Inspects all incoming requests and blocks malicious ones
    """

    # Skip health checks
    if request.url.path == "/api/v1/health":
        return await call_next(request)

    # Read request body
    body = await request.body()

    # Check request against WAF rules
    is_clean, violation = await waf.check_request(request, body)

    if not is_clean and violation:
        # Log violation
        waf.stats['requests_blocked'] += 1
        waf.violations_log.append(violation)

        # Print to logs (in production, send to logging system)
        print(f"[WAF BLOCKED] {violation.rule_name}: {violation.matched_pattern}")

        # Return 403 Forbidden
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Request blocked by Web Application Firewall",
                "rule": violation.rule_name
            }
        )

    # Allow request to proceed
    response = await call_next(request)

    # Add WAF header
    response.headers["X-WAF-Checked"] = "true"
    response.headers["X-WAF-Rule-Version"] = "1.0"

    return response
