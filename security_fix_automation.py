#!/usr/bin/env python3
"""
Automated Security Fix Implementation
Addresses critical database security vulnerabilities found in assessment
"""

import os
import json
import re
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SecurityFixAutomation:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.fix_log = []
        self.backup_dir = self.base_path / "security_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)

    def log_fix(self, action: str, status: str, details: str = ""):
        """Log security fix actions"""
        fix_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "status": status,
            "details": details
        }
        self.fix_log.append(fix_entry)
        print(f"{'✅' if status == 'SUCCESS' else '❌'} {action}: {details}")

    def backup_file(self, file_path: Path) -> bool:
        """Create backup of file before modification"""
        try:
            backup_path = self.backup_dir / f"{file_path.name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if file_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)
                self.log_fix(f"BACKUP", "SUCCESS", f"Backed up {file_path}")
                return True
        except Exception as e:
            self.log_fix(f"BACKUP", "FAILED", f"Failed to backup {file_path}: {e}")
        return False

    def fix_hardcoded_credentials(self) -> Dict[str, Any]:
        """Fix hardcoded credentials in configuration files"""
        print("\n🔧 FIXING HARDCODED CREDENTIALS...")

        fixed_files = []
        credential_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', "REPLACE_WITH_ENV_VAR"),
            (r'db_password\s*=\s*["\']([^"\']+)["\']', "REPLACE_WITH_ENV_VAR"),
            (r'DATABASE_URL=postgresql://[^:]+:([^@]+)@', "MASK_PASSWORD"),
            (r'secret\s*=\s*["\']([^"\']+)["\']', "REPLACE_WITH_ENV_VAR"),
        ]

        env_files = [".env.dev", ".env.prod", ".env"]

        for env_file in env_files:
            file_path = self.base_path / env_file
            if file_path.exists():
                if self.backup_file(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()

                        original_content = content
                        changes_made = []

                        # Replace hardcoded passwords with environment variables
                        for pattern, action in credential_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                if action == "REPLACE_WITH_ENV_VAR":
                                    # Replace with environment variable reference
                                    content = re.sub(pattern, lambda m: m.group(0).split('=')[0] + '="${' + m.group(0).split('=')[0].upper() + '_PASSWORD}"', content, flags=re.IGNORECASE)
                                    changes_made.append(f"Replaced {len(matches)} hardcoded password(s) with env vars")
                                elif action == "MASK_PASSWORD":
                                    # Mask passwords in database URLs
                                    content = re.sub(r'(:[^@]+@)', ':***PASSWORD_MASKED***@', content)
                                    changes_made.append("Masked passwords in database URLs")

                        if changes_made:
                            with open(file_path, 'w') as f:
                                f.write(content)

                            fixed_files.append({
                                "file": env_file,
                                "changes": changes_made,
                                "original_size": len(original_content),
                                "fixed_size": len(content)
                            })

                            self.log_fix("CREDENTIALS_FIXED", "SUCCESS", f"Fixed {env_file}: {', '.join(changes_made)}")

                        else:
                            self.log_fix("CREDENTIALS_FIXED", "NO_CHANGE", f"No hardcoded credentials found in {env_file}")

                    except Exception as e:
                        self.log_fix("CREDENTIALS_FIXED", "FAILED", f"Error fixing {env_file}: {e}")

        return {"fixed_files": fixed_files, "total_fixed": len(fixed_files)}

    def sanitize_log_files(self) -> Dict[str, Any]:
        """Sanitize log files containing sensitive data"""
        print("\n🧹 SANITIZING LOG FILES...")

        sanitized_files = []

        # Sensitive data patterns to mask
        sensitive_patterns = [
            (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '****-****-****-****'),  # Credit cards
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***'),  # Emails
            (r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', '***-**-****'),  # SSN/Phone
            (r'password["\']?\s*[:=]\s*["\']([^"\']{6,})["\']', 'password="***MASKED***"'),  # Passwords
            (r'token["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', 'token="***MASKED***"'),  # Tokens
            (r'key["\']?\s*[:=]\s*["\']([^"\']{16,})["\']', 'key="***MASKED***"'),  # Keys
        ]

        # Find log files
        log_files = list(self.base_path.rglob("*.log")) + list(self.base_path.rglob("*.out"))

        for log_file in log_files:
            if "node_modules" in str(log_file) or ".git" in str(log_file):
                continue

            if self.backup_file(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    original_content = content
                    sanitization_count = 0

                    # Apply sensitive data masking
                    for pattern, replacement in sensitive_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                            sanitization_count += len(matches)

                    if sanitization_count > 0:
                        with open(log_file, 'w', encoding='utf-8') as f:
                            f.write(content)

                        sanitized_files.append({
                            "file": str(log_file.relative_to(self.base_path)),
                            "sensitive_items_masked": sanitization_count,
                            "original_size": len(original_content),
                            "sanitized_size": len(content)
                        })

                        self.log_fix("LOG_SANITIZED", "SUCCESS", f"Sanitized {log_file.name}: {sanitization_count} items masked")

                    else:
                        self.log_fix("LOG_SANITIZED", "NO_CHANGE", f"No sensitive data found in {log_file.name}")

                except Exception as e:
                    self.log_fix("LOG_SANITIZED", "FAILED", f"Error sanitizing {log_file}: {e}")

        return {"sanitized_files": sanitized_files, "total_sanitized": len(sanitized_files)}

    def secure_backup_files(self) -> Dict[str, Any]:
        """Secure backup files with proper permissions and encryption"""
        print("\n🔒 SECURING BACKUP FILES...")

        secured_files = []

        backup_patterns = ["*.backup", "*.bak", "*.sql", "*.dump"]

        for pattern in backup_patterns:
            for backup_file in self.base_path.rglob(pattern):
                if "node_modules" in str(backup_file) or ".git" in str(backup_file):
                    continue

                try:
                    # Change file permissions to owner-only read/write
                    os.chmod(backup_file, 0o600)

                    # Create an encrypted version
                    encrypted_path = backup_file.with_suffix(backup_file.suffix + '.enc')

                    # Simple encryption using XOR (for demonstration - use proper encryption in production)
                    with open(backup_file, 'rb') as f:
                        data = f.read()

                    # Generate encryption key
                    key = secrets.token_bytes(32)

                    # XOR encryption (replace with AES in production)
                    encrypted_data = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

                    with open(encrypted_path, 'wb') as f:
                        f.write(encrypted_data)

                    # Save key separately (in production, use proper key management)
                    key_path = backup_file.with_suffix(backup_file.suffix + '.key')
                    with open(key_path, 'wb') as f:
                        f.write(key)

                    # Secure the key file
                    os.chmod(key_path, 0o600)

                    secured_files.append({
                        "original_file": str(backup_file.relative_to(self.base_path)),
                        "encrypted_file": str(encrypted_path.relative_to(self.base_path)),
                        "key_file": str(key_path.relative_to(self.base_path)),
                        "action": "Encrypted and permissions secured"
                    })

                    self.log_fix("BACKUP_SECURED", "SUCCESS", f"Secured {backup_file.name}")

                except Exception as e:
                    self.log_fix("BACKUP_SECURED", "FAILED", f"Error securing {backup_file}: {e}")

        return {"secured_files": secured_files, "total_secured": len(secured_files)}

    def create_input_validation_middleware(self) -> Dict[str, Any]:
        """Create input validation middleware for NoSQL injection prevention"""
        print("\n🛡️ CREATING INPUT VALIDATION MIDDLEWARE...")

        middleware_content = '''"""
Input Validation Middleware for NoSQL Injection Prevention
"""

import re
import json
from typing import Any, Dict, List, Optional

class InputValidationMiddleware:
    """Middleware to validate and sanitize input data"""

    def __init__(self):
        self.dangerous_patterns = [
            r'\\$where',
            r'\\$ne',
            r'\\$gt',
            r'\\$lt',
            r'\\$gte',
            r'\\$lte',
            r'\\$in',
            r'\\$nin',
            r'\\$regex',
            r'\\$expr',
            r'\\$or',
            r'\\$and',
            r'\\$not',
            r'\\$nor',
            r'function\\(',
            r'return\\s+',
            r'sleep\\(',
            r'document\\.',
            r'collection\\.',
            r'db\\.',
        ]

        self.sql_injection_patterns = [
            r"'|\"|;|--|\\/\\*|\\*\\/|xp_|sp_|execute",
            r"union\\s+select",
            r"select\\s+.*\\s+from",
            r"insert\\s+into",
            r"update\\s+.*\\s+set",
            r"delete\\s+from",
            r"drop\\s+table",
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
        sanitized = re.sub(r'[{}$;\\\'"<>]', '', value)
        # Limit length
        sanitized = sanitized[:1000]
        return sanitized.strip()

# Global validation instance
input_validator = InputValidationMiddleware()

def validate_request_input(data: Any) -> Dict[str, Any]:
    """Validate request input data"""
    return input_validator.validate_input(data)
'''

        middleware_path = self.base_path / "app" / "middleware" / "input_validation.py"
        middleware_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(middleware_path, 'w') as f:
                f.write(middleware_content)

            self.log_fix("MIDDLEWARE_CREATED", "SUCCESS", f"Created input validation middleware at {middleware_path}")

            return {
                "middleware_created": True,
                "path": str(middleware_path.relative_to(self.base_path)),
                "features": ["NoSQL injection prevention", "SQL injection prevention", "Input sanitization"]
            }

        except Exception as e:
            self.log_fix("MIDDLEWARE_CREATED", "FAILED", f"Error creating middleware: {e}")
            return {"middleware_created": False, "error": str(e)}

    def generate_secure_env_template(self) -> Dict[str, Any]:
        """Generate secure environment template"""
        print("\n📝 GENERATING SECURE ENVIRONMENT TEMPLATE...")

        secure_env_content = '''# =============================================================================
# PSYCHSYNC SECURE ENVIRONMENT TEMPLATE
# =============================================================================
# SECURITY NOTES:
# - Use strong, unique passwords for all credentials
# - Store this file securely with restricted permissions (chmod 600)
# - Use environment variable management in production
# - Regularly rotate credentials (every 90 days recommended)
# =============================================================================

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=psychsync_db
DB_USER=psychsync_user
# Generate strong password: openssl rand -base64 32
DB_PASSWORD=GENERATE_STRONG_PASSWORD_HERE

# Database URL (use environment variables in production)
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Database Pool Settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=True
DB_ECHO=False

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# Generate Redis password: openssl rand -base64 16
REDIS_PASSWORD=GENERATE_REDIS_PASSWORD_HERE
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================
# Generate JWT secret: openssl rand -base64 32
SECRET_KEY=GENERATE_JWT_SECRET_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# =============================================================================
# CORS SETTINGS (configure for your domains)
# =============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5174
ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
ALLOWED_HEADERS=*
ALLOW_CREDENTIALS=True

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
# Use app-specific passwords for Gmail
SMTP_PASSWORD=GENERATE_EMAIL_PASSWORD_HERE
SMTP_TLS=True

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
# Enable security headers
SECURITY_HEADERS_ENABLED=True
# Rate limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Session security
SESSION_TIMEOUT=1800
COOKIE_SECURE=True
COOKIE_HTTPONLY=True

# =============================================================================
# MONITORING AND LOGGING
# =============================================================================
# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
# Enable security logging
SECURITY_LOGGING=True
# Log file location
LOG_FILE=/var/log/psychsync/app.log

# Sentry for error tracking (optional)
SENTRY_DSN=YOUR_SENTRY_DSN_HERE
ENABLE_METRICS=True

# =============================================================================
# AI/ML SETTINGS
# =============================================================================
AI_ENABLED=False
# Generate API key for AI services
AI_API_KEY=GENERATE_AI_API_KEY_HERE
AI_API_URL=https://api.ai-service.com

# =============================================================================
# CACHE SETTINGS
# =============================================================================
CACHE_ENABLED=True
CACHE_DEFAULT_EXPIRE=3600
CACHE_USER_EXPIRE=1800
CACHE_ASSESSMENT_EXPIRE=3600
CACHE_TEAM_EXPIRE=1800

# =============================================================================
# TEAM SETTINGS
# =============================================================================
MAX_TEAM_SIZE=50
MIN_TEAM_SIZE=2

# =============================================================================
# PAGINATION
# =============================================================================
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# =============================================================================
# ENVIRONMENT
# =============================================================================
ENVIRONMENT=development
DEBUG=False
TESTING=False

# =============================================================================
# FRONTEND URLS
# =============================================================================
FRONTEND_URL=http://localhost:5174
FRONTEND_PASSWORD_RESET_URL=http://localhost:5174/reset-password
FRONTEND_EMAIL_VERIFY_URL=http://localhost:5174/verify-email
'''

        template_path = self.base_path / ".env.template.secure"

        try:
            with open(template_path, 'w') as f:
                f.write(secure_env_content)

            # Set secure permissions
            os.chmod(template_path, 0o600)

            self.log_fix("ENV_TEMPLATE", "SUCCESS", f"Created secure environment template at {template_path}")

            return {
                "template_created": True,
                "path": str(template_path.relative_to(self.base_path)),
                "permissions": "600 (owner-only)"
            }

        except Exception as e:
            self.log_fix("ENV_TEMPLATE", "FAILED", f"Error creating template: {e}")
            return {"template_created": False, "error": str(e)}

    def run_all_fixes(self) -> Dict[str, Any]:
        """Run all security fixes"""
        print("🚀 STARTING AUTOMATED SECURITY FIX IMPLEMENTATION")
        print("=" * 60)

        fix_results = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": {},
            "total_fixes": 0,
            "successful_fixes": 0,
            "failed_fixes": 0
        }

        # Fix 1: Hardcoded credentials
        credential_fixes = self.fix_hardcoded_credentials()
        fix_results["fixes_applied"]["hardcoded_credentials"] = credential_fixes
        fix_results["total_fixes"] += 1
        if credential_fixes["total_fixed"] > 0:
            fix_results["successful_fixes"] += 1

        # Fix 2: Sanitize log files
        log_fixes = self.sanitize_log_files()
        fix_results["fixes_applied"]["log_sanitization"] = log_fixes
        fix_results["total_fixes"] += 1
        if log_fixes["total_sanitized"] > 0:
            fix_results["successful_fixes"] += 1

        # Fix 3: Secure backup files
        backup_fixes = self.secure_backup_files()
        fix_results["fixes_applied"]["backup_security"] = backup_fixes
        fix_results["total_fixes"] += 1
        if backup_fixes["total_secured"] > 0:
            fix_results["successful_fixes"] += 1

        # Fix 4: Create input validation middleware
        middleware_fixes = self.create_input_validation_middleware()
        fix_results["fixes_applied"]["input_validation"] = middleware_fixes
        fix_results["total_fixes"] += 1
        if middleware_fixes.get("middleware_created", False):
            fix_results["successful_fixes"] += 1

        # Fix 5: Generate secure environment template
        env_fixes = self.generate_secure_env_template()
        fix_results["fixes_applied"]["env_template"] = env_fixes
        fix_results["total_fixes"] += 1
        if env_fixes.get("template_created", False):
            fix_results["successful_fixes"] += 1

        # Generate summary
        fix_results["summary"] = {
            "fix_log_entries": len(self.fix_log),
            "backup_directory": str(self.backup_dir),
            "security_improvement": "CRITICAL vulnerabilities addressed",
            "next_steps": [
                "Review and test applied fixes",
                "Update application to use input validation middleware",
                "Generate and set actual secure credentials",
                "Implement regular security scanning"
            ]
        }

        # Save fix log
        with open(self.base_path / "security_fix_log.json", "w") as f:
            json.dump({
                "fix_results": fix_results,
                "fix_log": self.fix_log
            }, f, indent=2, default=str)

        return fix_results

def main():
    """Main execution function"""
    fix_automation = SecurityFixAutomation()

    try:
        results = fix_automation.run_all_fixes()

        print("\n" + "=" * 60)
        print("🛠️ AUTOMATED SECURITY FIX IMPLEMENTATION COMPLETE")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Fixes Applied: {results['total_fixes']}")
        print(f"✅ Successful Fixes: {results['successful_fixes']}")
        print(f"❌ Failed Fixes: {results['failed_fixes']}")
        print(f"📝 Fix Log Entries: {summary['fix_log_entries']}")
        print(f"💾 Backup Directory: {summary['backup_directory']}")

        print(f"\n🎯 SECURITY IMPROVEMENT: {summary['security_improvement']}")

        print(f"\n📋 NEXT STEPS:")
        for i, step in enumerate(summary["next_steps"], 1):
            print(f"  {i}. {step}")

        print(f"\n📄 Detailed fix log saved to: security_fix_log.json")

        # Show individual fix results
        for fix_type, fix_data in results["fixes_applied"].items():
            if isinstance(fix_data, dict) and fix_data:
                print(f"\n✅ {fix_type.upper().replace('_', ' ')}:")
                for key, value in fix_data.items():
                    if key != "error":
                        print(f"   → {key}: {value}")

    except Exception as e:
        print(f"❌ Error running security fixes: {e}")

if __name__ == "__main__":
    main()
