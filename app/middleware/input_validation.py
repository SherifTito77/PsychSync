"""
Input Validation Middleware for NoSQL Injection Prevention
"""

import re
import json
from typing import Any, Dict, List, Optional

class InputValidationMiddleware:
    """Middleware to validate and sanitize input data"""

    def __init__(self):
        self.dangerous_patterns = [
            r'\$where',
            r'\$ne',
            r'\$gt',
            r'\$lt',
            r'\$gte',
            r'\$lte',
            r'\$in',
            r'\$nin',
            r'\$regex',
            r'\$expr',
            r'\$or',
            r'\$and',
            r'\$not',
            r'\$nor',
            r'function\(',
            r'return\s+',
            r'sleep\(',
            r'document\.',
            r'collection\.',
            r'db\.',
        ]

        self.sql_injection_patterns = [
            r'''['"]|;|--|\/\*|\*\/|xp_|sp_|execute''',
            r"union\s+select",
            r"select\s+.*\s+from",
            r"insert\s+into",
            r"update\s+.*\s+set",
            r"delete\s+from",
            r"drop\s+table",
        ]

    def validate_input(self, data: Any) -> Dict[str, Any]:
        """Validate input data for injection attempts"""
        result = {
            "valid": True,
            "sanitized": data,
            "threats_detected": [],
            "risk_level": "LOW"
        }

        if isinstance(data, str):
            return self._validate_string(data, result)
        elif isinstance(data, dict):
            return self._validate_dict(data, result)
        elif isinstance(data, list):
            return self._validate_list(data, result)
        elif isinstance(data, (int, float, bool)):
            return result
        else:
            result["valid"] = False
            result["threats_detected"].append("Unsupported data type")
            return result

    def _validate_string(self, value: str, result: Dict) -> Dict:
        """Validate string input"""
        original_value = value.lower()

        # Check for NoSQL injection patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, original_value, re.IGNORECASE):
                result["valid"] = False
                result["threats_detected"].append(f"NoSQL injection pattern: {pattern}")
                result["risk_level"] = "HIGH"

        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, original_value, re.IGNORECASE):
                result["valid"] = False
                result["threats_detected"].append(f"SQL injection pattern: {pattern}")
                result["risk_level"] = "HIGH"

        # Sanitize the input if valid
        if result["valid"]:
            result["sanitized"] = self._sanitize_string(value)

        return result

    def _validate_dict(self, data: Dict, result: Dict) -> Dict:
        """Validate dictionary input"""
        for key, value in data.items():
            validation_result = self.validate_input(value)
            if not validation_result["valid"]:
                result["valid"] = False
                result["threats_detected"].extend(validation_result["threats_detected"])
                result["risk_level"] = "HIGH"

            result["sanitized"][key] = validation_result["sanitized"]

        return result

    def _validate_list(self, data: List, result: Dict) -> Dict:
        """Validate list input"""
        for i, item in enumerate(data):
            validation_result = self.validate_input(item)
            if not validation_result["valid"]:
                result["valid"] = False
                result["threats_detected"].extend(validation_result["threats_detected"])
                result["risk_level"] = "HIGH"

            result["sanitized"][i] = validation_result["sanitized"]

        return result

    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        # Remove dangerous characters
        sanitized = re.sub(r'[{}$;\'"<>]', '', value)
        # Limit length
        sanitized = sanitized[:1000]
        return sanitized.strip()

# Global validation instance
input_validator = InputValidationMiddleware()

def validate_request_input(data: Any) -> Dict[str, Any]:
    """Validate request input data"""
    return input_validator.validate_input(data)
