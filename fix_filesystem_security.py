#!/usr/bin/env python3
"""
FILE SYSTEM SECURITY FIX SCRIPT
Fixes critical file system and storage security issues

Author: Security Team
Version: 1.0
Date: December 23, 2024

Fixes:
1. Remove .env files from git tracking
2. Update .gitignore with security patterns
3. Clean deployment artifacts
4. Remove backup files
5. Add path sanitization helpers
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

project_root = Path(os.path.dirname(os.path.abspath(__file__)))


class FilesystemSecurityFixer:
    """Fix file system security vulnerabilities"""

    def __init__(self):
        self.backup_dir = project_root / "fs_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.changes_made = []
        self.dry_run = False

    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}{title}{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}\n")

    def backup_file(self, file_path: Path) -> bool:
        """Backup a file before modifying"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{file_path.name}.backup.{timestamp}"

            if file_path.exists():
                shutil.copy2(file_path, backup_path)
                self.changes_made.append(f"Backed up: {file_path}")
                return True
        except Exception as e:
            print(f"{RED}Failed to backup {file_path}: {e}{RESET}")
        return False

    def fix_1_remove_env_from_git(self):
        """FIX 1: Remove .env files from git tracking"""
        self.print_header("🔒 FIX 1: Remove .env Files from Git")

        # Check if we're in a git repository
        if not (project_root / ".git").exists():
            print(f"{YELLOW}Not a git repository - skipping .env git removal{RESET}")
            return True

        # Check which .env files are tracked
        print(f"{BLUE}Checking for .env files tracked by git...{RESET}")

        try:
            result = subprocess.run(
                ['git', 'ls-files', '.env*'],
                cwd=project_root,
                capture_output=True,
                text=True
            )

            tracked_env_files = [f for f in result.stdout.strip().split('\n') if f]

            if not tracked_env_files:
                print(f"{GREEN}✅ No .env files tracked by git{RESET}")
                return True

            print(f"{YELLOW}Found {len(tracked_env_files)} .env files tracked by git:{RESET}")
            for env_file in tracked_env_files:
                print(f"   - {env_file}")

            # Remove from git tracking
            print(f"\n{BLUE}Removing from git tracking...{RESET}")

            if not self.dry_run:
                # Remove from git index
                result = subprocess.run(
                    ['git', 'rm', '--cached'] + tracked_env_files,
                    cwd=project_root,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(f"{GREEN}✅ Removed from git tracking{RESET}")

                    # Commit the removal
                    commit_result = subprocess.run(
                        ['git', 'commit', '-m',
                         'security: remove .env files from git tracking\n'
                         '\n'
                         'Removes environment files from version control to prevent\n'
                         'accidental exposure of sensitive credentials.'],
                        cwd=project_root,
                        capture_output=True,
                        text=True
                    )

                    if commit_result.returncode == 0:
                        print(f"{GREEN}✅ Committed removal{RESET}")
                        self.changes_made.append("Removed .env files from git")
                    else:
                        print(f"{YELLOW}⚠️  Could not commit (you may need to commit manually){RESET}")
                else:
                    print(f"{RED}❌ Failed to remove from git: {result.stderr}{RESET}")
                    return False
            else:
                print(f"{YELLOW}[DRY RUN] Would remove from git: {tracked_env_files}{RESET}")

        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            return False

        return True

    def fix_2_update_gitignore(self):
        """FIX 2: Update .gitignore with security patterns"""
        self.print_header("📝 FIX 2: Update .gitignore")

        gitignore = project_root / ".gitignore"

        if not gitignore.exists():
            print(f"{YELLOW}Creating .gitignore file...{RESET}")
            gitignore.touch()

        # Backup existing .gitignore
        self.backup_file(gitignore)

        # Read current content
        current_content = gitignore.read_text()

        # Required security patterns
        required_patterns = [
            "# Environment files",
            ".env",
            ".env.*",
            ".env.local",
            ".env.*.local",
            "",
            "# Database",
            "*.sql",
            "*.sql.backup",
            "*.db",
            "*.sqlite",
            "",
            "# Logs",
            "*.log",
            "logs/",
            "*.log.*",
            "",
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "wheels/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            "",
            "# Virtual environments",
            "venv/",
            "ENV/",
            "env/",
            ".venv/",
            "",
            "# Node",
            "node_modules/",
            "npm-debug.log",
            "yarn-error.log",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Backup files",
            "*.backup",
            "*.bak",
            "*.old",
            "*.orig",
            "",
            "# Security",
            "*.key",
            "*.pem",
            "*.crt",
            "secrets.yaml",
            "secrets/",
            "",
            "# Test coverage",
            ".coverage",
            "htmlcov/",
            "",
            "# Frontend build",
            "frontend/dist/",
            "frontend/build/",
            ".next/",
            ".nuxt/",
            "",
            "# Temporary files",
            "tmp/",
            "temp/",
            "uploads/tmp/",
        ]

        # Check which patterns are missing
        missing_patterns = []
        content_lines = current_content.split('\n')

        for pattern in required_patterns:
            # Check if pattern or similar already exists
            pattern_stripped = pattern.strip().lstrip('#')
            if pattern_stripped and not any(
                pattern_stripped in line or line.strip() == pattern_stripped
                for line in content_lines
            ):
                if not pattern.startswith('#'):  # Only add actual patterns, not comments
                    missing_patterns.append(pattern)

        if missing_patterns:
            print(f"{YELLOW}Adding {len(missing_patterns)} missing patterns to .gitignore:{RESET}")

            for pattern in missing_patterns[:10]:
                print(f"   + {pattern}")

            if len(missing_patterns) > 10:
                print(f"   ... and {len(missing_patterns) - 10} more")

            # Append missing patterns
            if not self.dry_run:
                with open(gitignore, 'a') as f:
                    f.write('\n\n# Added by security fix script\n')
                    for pattern in missing_patterns:
                        f.write(f'{pattern}\n')

                print(f"{GREEN}✅ .gitignore updated{RESET}")
                self.changes_made.append("Updated .gitignore")
            else:
                print(f"{YELLOW}[DRY RUN] Would update .gitignore{RESET}")
        else:
            print(f"{GREEN}✅ All required patterns already in .gitignore{RESET}")

        return True

    def fix_3_clean_artifacts(self):
        """FIX 3: Clean deployment artifacts"""
        self.print_header("🧹 FIX 3: Clean Deployment Artifacts")

        artifacts_to_remove = []

        # Python cache files
        print(f"{BLUE}Scanning for Python cache files...{RESET}")
        pycache_count = 0
        for pycache in project_root.rglob("__pycache__"):
            if pycache.is_dir():
                artifacts_to_remove.append(pycache)
                pycache_count += 1

        print(f"   Found {pycache_count} __pycache__ directories")

        # Backup files
        print(f"{BLUE}Scanning for backup files...{RESET}")
        backup_count = 0
        for pattern in ["*.backup", "*.bak", "*.old", "*~"]:
            for backup in project_root.rglob(pattern):
                if backup.is_file() and "backup" not in str(backup.parent):  # Skip our backup dir
                    artifacts_to_remove.append(backup)
                    backup_count += 1

        print(f"   Found {backup_count} backup files")

        # macOS metadata
        print(f"{BLUE}Scanning for macOS metadata files...{RESET}")
        ds_store_count = 0
        for ds_store in project_root.rglob(".DS_Store"):
            if ds_store.is_file():
                artifacts_to_remove.append(ds_store)
                ds_store_count += 1

        print(f"   Found {ds_store_count} .DS_Store files")

        # Log files in root
        print(f"{BLUE}Scanning for log files in root...{RESET}")
        log_count = 0
        for log_file in project_root.glob("*.log"):
            if log_file.is_file():
                artifacts_to_remove.append(log_file)
                log_count += 1

        print(f"   Found {log_count} log files in root")

        # Total
        total = len(artifacts_to_remove)
        print(f"\n{CYAN}Total artifacts to remove: {total}{RESET}")

        if total > 0:
            if not self.dry_run:
                print(f"\n{BLUE}Removing artifacts...{RESET}")

                removed = 0
                for artifact in artifacts_to_remove:
                    try:
                        if artifact.is_dir():
                            shutil.rmtree(artifact)
                        else:
                            artifact.unlink()
                        removed += 1

                        # Limit output
                        if removed <= 10:
                            print(f"   ✓ Removed: {artifact.relative_to(project_root)}")
                        elif removed == 11:
                            print(f"   ... and {total - 10} more")

                    except Exception as e:
                        print(f"   ✗ Failed to remove {artifact}: {e}")

                print(f"\n{GREEN}✅ Removed {removed}/{total} artifacts{RESET}")
                self.changes_made.append(f"Cleaned {removed} deployment artifacts")
            else:
                print(f"{YELLOW}[DRY RUN] Would remove {total} artifacts{RESET}")

                # Show some examples
                print(f"{BLUE}Examples:{RESET}")
                for artifact in artifacts_to_remove[:5]:
                    print(f"   - {artifact.relative_to(project_root)}")

        else:
            print(f"{GREEN}✅ No artifacts to clean{RESET}")

        return True

    def fix_4_add_path_sanitization(self):
        """FIX 4: Add path sanitization helper utilities"""
        self.print_header("🛡️  FIX 4: Add Path Sanitization Helpers")

        # Create security utilities file
        security_utils = project_root / "app/core/path_utils.py"

        if security_utils.exists():
            print(f"{YELLOW}File already exists: {security_utils.relative_to(project_root)}{RESET}")
            print(f"{YELLOW}Skipping path utils creation{RESET}")
            return True

        print(f"{BLUE}Creating path sanitization utilities...{RESET}")

        utils_content = '''"""
Path Sanitization Utilities for Secure File Operations
Provides safe path handling to prevent directory traversal attacks
"""

from pathlib import Path
from typing import Optional, List, Set
import re


class PathTraversalError(Exception):
    """Raised when path traversal is detected"""
    pass


class FileExtensionError(Exception):
    """Raised when file extension is not allowed"""
    pass


def sanitize_path(
    user_path: str,
    allowed_dir: Path,
    allowed_extensions: Optional[Set[str]] = None
) -> Path:
    """
    Sanitize and validate a user-provided path

    This function prevents directory traversal attacks by:
    1. Resolving the path to its absolute form
    2. Verifying it's within the allowed directory
    3. Checking file extension against whitelist

    Args:
        user_path: User-provided path (relative or absolute)
        allowed_dir: Directory that files are allowed from
        allowed_extensions: Set of allowed file extensions (e.g., {'.txt', '.pdf'})
                             If None, all extensions allowed

    Returns:
        Absolute, sanitized Path object

    Raises:
        PathTraversalError: If path attempts to escape allowed directory
        FileExtensionError: If file extension not in whitelist

    Example:
        >>> allowed_dir = Path("/var/www/uploads")
        >>> safe_path = sanitize_path("../../etc/passwd", allowed_dir)
        PathTraversalError: Path traversal detected

        >>> safe_path = sanitize_path("image.png", allowed_dir, {".png", ".jpg"})
        Path("/var/www/uploads/image.png")
    """
    # Join with allowed directory
    full_path = (allowed_dir / user_path).resolve()

    # Verify it's within allowed directory
    allowed_resolved = allowed_dir.resolve()

    try:
        full_path.relative_to(allowed_resolved)
    except ValueError:
        raise PathTraversalError(
            f"Path traversal detected: {user_path} attempts to access "
            f"{full_path} outside allowed directory {allowed_dir}"
        )

    # Check file extension if whitelist provided
    if allowed_extensions is not None and full_path.is_file():
        if full_path.suffix.lower() not in allowed_extensions:
            raise FileExtensionError(
                f"File extension {full_path.suffix} not allowed. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )

    return full_path


def safe_filename(filename: str) -> str:
    """
    Sanitize a user-provided filename

    Removes dangerous characters and ensures safe filename

    Args:
        filename: User-provided filename

    Returns:
        Sanitized filename safe for filesystem

    Example:
        >>> safe_filename("../../etc/passwd")
        "etc_passwd"

        >>> safe_filename("my document.txt")
        "my_document.txt"
    """
    # Remove path separators
    sanitized = filename.replace("/", "_").replace("\\", "_")

    # Remove dangerous characters
    sanitized = re.sub(r'[<>:"|?*]', '_', sanitized)

    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')

    return sanitized


def validate_file_type(
    file_path: Path,
    allowed_mime_types: Optional[Set[str]] = None,
    allowed_extensions: Optional[Set[str]] = None
) -> bool:
    """
    Validate file type by extension and/or MIME type

    Args:
        file_path: Path to file
        allowed_mime_types: Set of allowed MIME types
        allowed_extensions: Set of allowed extensions (with dot, e.g., '.jpg')

    Returns:
        True if file type is allowed

    Example:
        >>> validate_file_type(Path("image.jpg"), {".jpg", ".png"})
        True

        >>> validate_file_type(Path("script.php"), {".jpg", ".png"})
        False
    """
    if not file_path.exists():
        return False

    # Check extension
    if allowed_extensions is not None:
        if file_path.suffix.lower() not in allowed_extensions:
            return False

    # Check MIME type if requested
    if allowed_mime_types is not None:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type not in allowed_mime_types:
            return False

    return True


# Common allowed extensions for different file types
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm'}
ALLOWED_ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz', '.bz2'}
'''

        if not self.dry_run:
            security_utils.parent.mkdir(parents=True, exist_ok=True)
            security_utils.write_text(utils_content)
            print(f"{GREEN}✅ Created: {security_utils.relative_to(project_root)}{RESET}")
            self.changes_made.append("Created path sanitization utilities")
        else:
            print(f"{YELLOW}[DRY RUN] Would create: {security_utils.relative_to(project_root)}{RESET}")

        return True

    def fix_5_create_env_template(self):
        """FIX 5: Create secure .env.example template"""
        self.print_header("📄 FIX 5: Create Secure .env Template")

        env_example = project_root / ".env.example"

        # Check if already exists
        if env_example.exists():
            existing_content = env_example.read_text()

            # Check if it has a warning header
            if "DO NOT commit actual secrets" in existing_content or "TEMPLATE" in existing_content:
                print(f"{GREEN}✅ .env.example already has security warnings{RESET}")
                return True

        print(f"{BLUE}Creating secure .env.example template...{RESET}")

        template_content = """# ==============================================================================
# ENVIRONMENT CONFIGURATION TEMPLATE
# ==============================================================================
#
# ⚠️  SECURITY WARNING:
#
# 1. DO NOT commit actual secrets to version control
# 2. DO NOT share this file with actual values filled in
# 3. Use this only as a template for .env.local
# 4. Keep actual .env files in .gitignore
# 5. Rotate secrets immediately if accidentally exposed
#
# ==============================================================================

# Application Settings
APP_NAME=PsychSync
APP_ENV=development
DEBUG=true

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/psychsync_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=psychsync_db
DB_USER=psychsync_user
DB_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Security Settings
SECRET_KEY=generate_with_python_secrets_module()
ENCRYPTION_KEY=generate_with_python_secrets_module()
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_your_public_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAIL_FROM=noreply@psychsync.com

# S3/Storage Configuration (if applicable)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Monitoring & Logging
SENTRY_DSN=
LOG_LEVEL=INFO

# External APIs
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ==============================================================================
# INSTRUCTIONS
# ==============================================================================
#
# 1. Copy this file to .env.local:
#    cp .env.example .env.local
#
# 2. Fill in actual values in .env.local (NEVER this file)
#
# 3. Generate secure random values:
#    python -c "import secrets; print(secrets.token_urlsafe(32))"
#
# 4. Never commit .env.local or any .env file with real secrets
#
# ==============================================================================
"""

        if not self.dry_run:
            # Backup existing if it exists
            if env_example.exists():
                self.backup_file(env_example)

            env_example.write_text(template_content)
            print(f"{GREEN}✅ Created secure .env.example template{RESET}")
            self.changes_made.append("Created .env.example template")
        else:
            print(f"{YELLOW}[DRY RUN] Would create .env.example template{RESET}")

        return True

    def run_all_fixes(self):
        """Run all file system security fixes"""
        self.print_header("🔒 FILE SYSTEM SECURITY FIXES")

        print(f"{BLUE}Started: {datetime.now().isoformat()}{RESET}")
        print(f"{BLUE}Project: {project_root}{RESET}\n")

        print(f"{YELLOW}This will apply the following fixes:{RESET}")
        print(f"   1. Remove .env files from git tracking")
        print(f"   2. Update .gitignore with security patterns")
        print(f"   3. Clean deployment artifacts")
        print(f"   4. Add path sanitization helpers")
        print(f"   5. Create secure .env.example template")

        print(f"\n{YELLOW}Backup location: {self.backup_dir}{RESET}\n")

        fixes = [
            ("Remove .env from git", self.fix_1_remove_env_from_git),
            ("Update .gitignore", self.fix_2_update_gitignore),
            ("Clean artifacts", self.fix_3_clean_artifacts),
            ("Add path sanitization", self.fix_4_add_path_sanitization),
            ("Create .env template", self.fix_5_create_env_template),
        ]

        results = {}

        for name, fix_func in fixes:
            try:
                print(f"\n{MAGENTA}Applying: {name}...{RESET}")
                success = fix_func()
                results[name] = success

                if success:
                    print(f"{GREEN}✅ {name} completed{RESET}")
                else:
                    print(f"{RED}❌ {name} failed{RESET}")

            except Exception as e:
                print(f"{RED}❌ {name} error: {e}{RESET}")
                results[name] = False
                import traceback
                traceback.print_exc()

        # Print summary
        self.print_summary(results)

    def print_summary(self, results: dict):
        """Print fix summary"""
        self.print_header("📊 FIX SUMMARY")

        succeeded = sum(1 for v in results.values() if v)
        total = len(results)

        print(f"\n{CYAN}Fixes Applied: {succeeded}/{total}{RESET}\n")

        for name, success in results.items():
            status = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
            print(f"   {status} {name}")

        if self.changes_made:
            print(f"\n{YELLOW}Changes Made:{RESET}")
            for change in self.changes_made:
                print(f"   • {change}")

        print(f"\n{YELLOW}Backup Location:{RESET}")
        print(f"   {self.backup_dir}")

        print(f"\n{BLUE}Next Steps:{RESET}")
        print(f"   1. Review changes using: git status")
        print(f"   2. Stage .gitignore update: git add .gitignore")
        print(f"   3. Commit improvements: git commit -m 'security: filesystem fixes'")
        print(f"   4. Create your .env.local: cp .env.example .env.local")
        print(f"   5. Fill in actual values in .env.local (NEVER commit this)")
        print(f"   6. Use path sanitization in file upload endpoints:")
        print(f"      from app.core.path_utils import sanitize_path")
        print(f"      safe_path = sanitize_path(user_filename, UPLOAD_DIR)")

        print(f"\n{GREEN}After verifying all changes work, delete backups after 1 week:{RESET}")
        print(f"   rm -rf {self.backup_dir}")

        print(f"\n{CYAN}Completed: {datetime.now().isoformat()}{RESET}\n")


def main():
    """Main entry point"""
    fixer = FilesystemSecurityFixer()

    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser(description="Fix file system security issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    if args.dry_run:
        fixer.dry_run = True
        print(f"\n{YELLOW}DRY RUN MODE - No changes will be made{RESET}\n")

    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
