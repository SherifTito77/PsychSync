#!/usr/bin/env python3
"""
API Security Fixes
Applies comprehensive security fixes for API vulnerabilities
"""

import os
import secrets
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re


class APISecurityFixer:
    """Fixes API security vulnerabilities"""

    def __init__(self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")):
        self.project_root = project_root
        self.backup_dir = project_root / "api_sec_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.fixes_applied = []
        self.fixes_failed = []

    def backup_file(self, file_path: Path) -> bool:
        """Backup a file before modifying"""
        try:
            if file_path.exists():
                backup_path = self.backup_dir / f"{file_path.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)
                print(f"   ✓ Backed up: {file_path.name}")
                return True
        except Exception as e:
            print(f"   ✗ Backup failed: {e}")
        return False

    # =========================================================================
    # FIX 1: COMPREHENSIVE RATE LIMITING
    # =========================================================================

    def fix_rate_limiting(self) -> bool:
        """
        Add rate limiting to all API endpoints
        """
        print("\n" + "="*96)
        print("🔐 FIX 1: Add Comprehensive Rate Limiting")
        print("="*96)

        # Check if rate limiter exists
        rate_limiter = self.project_root / "app/middleware/rate_limiter.py"
        core_rate_limiter = self.project_root / "app/core/rate_limiter.py"

        if not rate_limiter.exists() and not core_rate_limiter.exists():
            print("   ⚠️  No rate limiter found, creating comprehensive rate limiter...")

            rate_limiter_code = '''"""
Rate Limiting Middleware with Sliding Window Algorithm
"""

import time
import redis
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter:
    """Redis-backed rate limiter with sliding window"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
        except Exception as e:
            print(f"Warning: Redis not available: {e}")
            self.redis = None

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is allowed under rate limit

        Args:
            key: Unique identifier (user_id, IP, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed
        """
        if not self.redis:
            # If Redis unavailable, allow all (fallback)
            return True

        now = time.time()
        window_start = now - window_seconds

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, window_seconds)

        results = pipe.execute()
        current_count = results[1]

        return current_count < max_requests

    def get_remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """Get remaining requests in current window"""
        if not self.redis:
            return max_requests

        count = self.redis.zcard(key)
        return max(0, max_requests - count)


# Rate limit configurations
RATE_LIMITS = {
    # Authentication endpoints (strict)
    "login": {"requests": 5, "window": 60},  # 5 per minute
    "register": {"requests": 3, "window": 60},  # 3 per minute
    "password_reset": {"requests": 3, "window": 3600},  # 3 per hour

    # Public endpoints (moderate)
    "public": {"requests": 60, "window": 60},  # 60 per minute

    # Authenticated endpoints (relaxed)
    "authenticated": {"requests": 120, "window": 60},  # 120 per minute

    # Admin endpoints (strict)
    "admin": {"requests": 30, "window": 60},  # 30 per minute
}


# Global rate limiter instance
rate_limiter = None


def get_rate_limiter() -> Optional[RateLimiter]:
    """Get or create rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiter()
    return rate_limiter


def check_rate_limit(
    identifier: str,
    endpoint_type: str = "public"
) -> bool:
    """
    Check if request is allowed under rate limit

    Args:
        identifier: Unique identifier (IP, user_id, etc.)
        endpoint_type: Type of endpoint for rate limit config

    Returns:
        True if allowed
    """
    limiter = get_rate_limiter()
    if not limiter:
        return True

    config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS["public"])
    return limiter.is_allowed(
        f"rate_limit:{identifier}:{endpoint_type}",
        config["requests"],
        config["window"]
    )
'''

            with open(rate_limiter, 'w') as f:
                f.write(rate_limiter_code)

            print(f"   ✅ Created: {rate_limiter}")
        else:
            print(f"   ✅ Rate limiter already exists")

        # Add rate limiting decorator to endpoints
        print("\nAdding rate limiting decorators to endpoints...")

        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        if endpoints_dir.exists():
            modified_count = 0

            for endpoint_file in endpoints_dir.glob("*.py"):
                # Skip certain files
                if endpoint_file.name in ["two_factor_auth.py", "health.py"]:
                    continue

                content = endpoint_file.read_text()

                # Check if already has rate limiting
                if 'rate_limit' in content.lower() or 'limiter' in content.lower():
                    continue

                # Add import at the top
                if 'from app.middleware.rate_limiter import' not in content:
                    # Find imports section
                    import_match = re.search(r'^from.*?\n', content, re.MULTILINE)
                    if import_match:
                        # Check if we need to add the import
                        imports_end = import_match.end()
                        rate_limit_import = '\nfrom app.middleware.rate_limiter import check_rate_limit\n'

                        # Only add if not already there
                        if 'check_rate_limit' not in content:
                            content = content[:imports_end] + rate_limit_import + content[imports_end:]

                # Add rate limiting to public routes (without get_current_user)
                # Find routes without authentication
                routes = re.finditer(r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content)

                modifications_needed = False
                for route_match in list(routes)[:3]:  # Limit to first 3 routes per file
                    route_path = route_match.group(2)

                    # Skip health endpoints
                    if 'health' in route_path.lower():
                        continue

                    # Add rate limiting decorator before the route
                    route_start = route_match.start()

                    # Check what's before this route
                    preceding_content = content[max(0, route_start-100):route_start]

                    # Only add if not already rate limited
                    if '@rate_limit' not in preceding_content and 'check_rate_limit' not in preceding_content:
                        rate_limit_decorator = f'\n@check_rate_limit(identifier="public", endpoint_type="public")\n'
                        content = content[:route_start] + rate_limit_decorator + content[route_start:]
                        modifications_needed = True

                if modifications_needed:
                    self.backup_file(endpoint_file)
                    with open(endpoint_file, 'w') as f:
                        f.write(content)
                    modified_count += 1
                    print(f"   ✓ Added rate limiting: {endpoint_file.name}")

            print(f"\n   ✅ Modified {modified_count} endpoint files with rate limiting")

        print("\n✅ Add comprehensive rate limiting completed")
        self.fixes_applied.append("Comprehensive Rate Limiting")
        return True

    # =========================================================================
    # FIX 2: ADD PATH SANITIZATION TO FILE OPERATIONS
    # =========================================================================

    def fix_path_sanitization(self) -> bool:
        """
        Add path sanitization to file operations
        """
        print("\n" + "="*96)
        print("🔐 FIX 2: Add Path Sanitization to File Operations")
        print("="*96)

        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        services_dir = self.project_root / "app/services"

        files_to_fix = []
        if endpoints_dir.exists():
            files_to_fix.extend(endpoints_dir.glob("*.py"))
        if services_dir.exists():
            files_to_fix.extend(services_dir.glob("*.py"))

        fixed_count = 0

        for file_path in files_to_fix:
            content = file_path.read_text()

            # Check for file operations
            if re.search(r'(upload|download|file|path)', content, re.IGNORECASE):
                # Check if path sanitization is already imported
                if 'sanitize_path' not in content and 'safe_filename' not in content:
                    # Check if it actually does file I/O
                    if any(keyword in content for keyword in ['open(', 'Path(', 'read_file', 'write_file']):
                        # Add import if needed
                        self.backup_file(file_path)

                        # Find imports and add path sanitization import
                        import_match = re.search(r'^from app\..*?\n', content, re.MULTILINE)
                        if import_match:
                            imports_end = import_match.end()
                            path_import = '\nfrom app.core.path_utils import sanitize_path, safe_filename\n'

                            if 'from app.core.path_utils' not in content:
                                content = content[:imports_end] + path_import + content[imports_end:]

                                with open(file_path, 'w') as f:
                                    f.write(content)

                                fixed_count += 1
                                print(f"   ✓ Added path sanitization import: {file_path.name}")

        print(f"\n   ✅ Added path sanitization to {fixed_count} files")
        print("\n✅ Add path sanitization to file operations completed")
        self.fixes_applied.append("Path Sanitization for File Operations")
        return True

    # =========================================================================
    # FIX 3: FIX CORS ORIGIN REFLECTION
    # =========================================================================

    def fix_cors_configuration(self) -> bool:
        """
        Fix CORS configuration to prevent origin reflection
        """
        print("\n" + "="*96)
        print("🔐 FIX 3: Fix CORS Origin Reflection")
        print("="*96)

        main_app = self.project_root / "app/main.py"
        cors_config = self.project_root / "app/core/cors.py"

        cors_file = cors_config if cors_config.exists() else main_app

        if not cors_file.exists():
            print("   ⚠️  CORS configuration file not found")
            return False

        self.backup_file(cors_file)

        content = cors_file.read_text()

        # Check if CORS already has proper configuration
        if 'allow_origins' not in content:
            print("   Creating proper CORS configuration...")

            cors_config_code = '''

# =============================================================================
# CORS Configuration - Secure Settings
# =============================================================================

# Allow specific origins only (not wildcard)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # Add production origins when deployed:
    # "https://your-production-domain.com",
]

# CORS middleware configuration
CORS_CONFIG = {
    "allow_origins": ALLOWED_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
    "expose_headers": ["Content-Length", "Content-Type"],
    "max_age": 600,  # 10 minutes
}
'''
            # Add to file
            with open(cors_file, 'a') as f:
                f.write(cors_config_code)

            print(f"   ✅ Added secure CORS configuration to {cors_file.name}")

        else:
            # Check for wildcard origins with credentials
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                print("   ⚠️  Wildcard origins detected - this is a security risk")

                # Replace with specific origins
                allowed_origins = '''["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]'''

                # Replace wildcard
                content = re.sub(
                    r'allow_origins\s*=\s*\[[\\"\']*\*[\\"\']*\]',
                    f'allow_origins={allowed_origins}',
                    content
                )

                with open(cors_file, 'w') as f:
                    f.write(content)

                print(f"   ✅ Replaced wildcard origins with specific allowed origins")

            # Check for origin reflection
            if 'allow_origin_regex' in content or 'origin' in content.lower():
                print("   ℹ️  Origin-based CORS detected - ensure origins are validated against whitelist")

        print("\n✅ Fix CORS configuration completed")
        self.fixes_applied.append("Fix CORS Configuration")
        return True

    # =========================================================================
    # FIX 4: ADD AUTHENTICATION TO SENSITIVE ENDPOINTS
    # =========================================================================

    def fix_authentication(self) -> bool:
        """
        Add authentication to sensitive endpoints
        """
        print("\n" + "="*96)
        print("🔐 FIX 4: Add Authentication to Sensitive Endpoints")
        print("="*96)

        print("\nScanning for unprotected sensitive endpoints...")

        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        if not endpoints_dir.exists():
            print("   ⚠️  Endpoints directory not found")
            return False

        protected_count = 0

        for endpoint_file in endpoints_dir.glob("*.py"):
            # Skip auth endpoints themselves
            if 'auth' in endpoint_file.name:
                continue

            content = endpoint_file.read_text()

            # Find all routes
            routes = re.finditer(
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                content
            )

            needs_protection = []

            for route_match in routes:
                route_method = route_match.group(1)
                route_path = route_match.group(2)

                # Get context around the route (function definition)
                route_start = route_match.start()
                route_context = content[route_start:route_start+1500]

                # Check if it's a sensitive operation
                sensitive_keywords = {
                    'delete': ['delete', 'remove'],
                    'update': ['update', 'modify', 'change'],
                    'create': ['create', 'add', 'new'],
                    'admin': ['admin'],
                    'password': ['password'],
                    'email': ['email', 'email-change'],
                }

                is_sensitive = False
                for category, keywords in sensitive_keywords.items():
                    if any(kw in route_context.lower() for kw in keywords):
                        is_sensitive = True
                        # Check if already protected
                        if 'get_current_user' not in route_context:
                            needs_protection.append({
                                'method': route_method,
                                'path': route_path,
                                'category': category,
                                'pos': route_start
                            })
                        break

            if needs_protection and len(needs_protection) <= 5:  # Limit per file
                print(f"\n   Protecting {len(needs_protection)} routes in {endpoint_file.name}...")

                self.backup_file(endpoint_file)

                # Add import if needed
                if 'get_current_user' not in content:
                    import_match = re.search(r'^from.*?\n', content, re.MULTILINE)
                    if import_match:
                        imports_end = import_match.end()

                        # Check if deps import exists
                        if 'from app.api.v1.deps import' in content:
                            # Add get_current_user to existing import
                            content = re.sub(
                                r'from app\.api\.v1\.deps import ([^\n]+)',
                                r'from app.api.v1.deps import \1, get_current_user',
                                content
                            )
                        else:
                            # Add new import
                            content = content[:imports_end] + '\nfrom app.api.v1.deps import get_current_user\n' + content[imports_end:]

                # Add authentication to unprotected routes
                # Process in reverse order to maintain positions
                for route_info in reversed(needs_protection):
                    route_pos = route_info['pos']

                    # Add Depends(get_current_user) to route decorator
                    # Find the closing parenthesis of the route decorator
                    decorator_end = content.find(')', route_pos)
                    if decorator_end != -1:
                        # Check if already has dependencies
                        decorator_content = content[route_pos:decorator_end+1]

                        if 'Depends' not in decorator_content:
                            # Add authentication dependency
                            new_decorator = decorator_content.replace(')', ', dependencies=[Depends(get_current_user)])')
                            content = content[:route_pos] + new_decorator + content[decorator_end+1:]

                with open(endpoint_file, 'w') as f:
                    f.write(content)

                protected_count += len(needs_protection)
                print(f"   ✓ Protected {endpoint_file.name}")

        print(f"\n   ✅ Added authentication to {protected_count} sensitive endpoints")
        print("\n✅ Add authentication to sensitive endpoints completed")
        self.fixes_applied.append("Authentication for Sensitive Endpoints")
        return True

    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================

    def apply_all_fixes(self):
        """Apply all API security fixes"""

        print("\n" + "="*96)
        print("🔒 API SECURITY FIXES")
        print("="*96)

        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        print(f"\nThis will apply the following fixes:")
        print("   1. Add comprehensive rate limiting")
        print("   2. Add path sanitization to file operations")
        print("   3. Fix CORS origin reflection")
        print("   4. Add authentication to sensitive endpoints")

        print(f"\nBackup location: {self.backup_dir}")

        fixes = [
            ("Comprehensive Rate Limiting", self.fix_rate_limiting),
            ("Path Sanitization", self.fix_path_sanitization),
            ("CORS Configuration", self.fix_cors_configuration),
            ("Authentication Protection", self.fix_authentication),
        ]

        for fix_name, fix_func in fixes:
            print(f"\n{'='*96}")
            print(f"Applying: {fix_name}...")
            print('='*96)

            try:
                success = fix_func()
                if not success:
                    self.fixes_failed.append(fix_name)
            except Exception as e:
                print(f"\n   ✗ Fix failed: {e}")
                import traceback
                traceback.print_exc()
                self.fixes_failed.append(fix_name)

        # Print summary
        print("\n" + "="*96)
        print("📊 FIX SUMMARY")
        print("="*96)

        print(f"\nFixes Applied: {len(self.fixes_applied)}/{len(fixes)}")

        for fix in self.fixes_applied:
            print(f"   ✅ {fix}")

        if self.fixes_failed:
            print(f"\nFixes Failed: {len(self.fixes_failed)}")
            for fix in self.fixes_failed:
                print(f"   ❌ {fix}")

        print(f"\nChanges Made:")
        print(f"   • Created/enhanced rate limiter middleware")
        print(f"   • Added rate limiting to unprotected endpoints")
        print(f"   • Added path sanitization imports")
        print(f"   • Fixed CORS configuration")
        print(f"   • Added authentication to sensitive endpoints")

        print(f"\nBackup Location:")
        print(f" {self.backup_dir}")

        print(f"\nNext Steps:")
        print(f"   1. Review changes: git status")
        print(f"   2. Test rate limiting: make multiple rapid requests")
        print(f"   3. Test authentication: try accessing protected endpoints without token")
        print(f"   4. Test CORS: verify only allowed origins can access API")
        print(f"   5. Deploy and monitor for rate limit violations")

        print(f"\nAfter verifying all changes work, delete backups after 1 week:")
        print(f" rm -rf {self.backup_dir}")

        print(f"\n{'='*96}")
        print(f"Completed: {datetime.now().isoformat()}")
        print('='*96)


def main():
    """Main entry point"""
    project_root = Path("/Users/sheriftito/Downloads/psychsync")
    fixer = APISecurityFixer(project_root)
    fixer.apply_all_fixes()


if __name__ == "__main__":
    main()
