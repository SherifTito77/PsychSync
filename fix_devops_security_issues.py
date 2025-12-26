#!/usr/bin/env python3
"""
DEVOPS SECURITY AUTOMATED FIX SCRIPT
Automatically fixes all critical and high-priority DevOps security issues

Fixes:
1. Adds non-root user to all Dockerfiles
2. Pins Docker image versions (removes :latest)
3. Fixes risky host directory mounts in Docker Compose files
4. Cleans up environment files with embedded secrets
5. Updates .gitignore with security patterns

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import os
import sys
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

project_root = Path(os.path.dirname(os.path.abspath(__file__)))


class DevOpsSecurityFixer:
    """Automated DevOps security fixes"""

    def __init__(self):
        self.project_root = project_root
        self.fixes_applied = []
        self.fixes_failed = []
        self.backup_dir = self.project_root / "security_fix_backups"

    def print_header(self, title: str):
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}{title}{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}")

    def backup_file(self, file_path: Path) -> bool:
        """Create backup of file before modifying"""
        try:
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{file_path.name}.backup.{timestamp}"
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"   ❌ Backup failed: {e}")
            return False

    # ========== FIX 1: Dockerfile Security ==========

    def fix_dockerfiles(self):
        """Fix #1: Add non-root user to all Dockerfiles"""
        self.print_header("🐳 FIX 1: Dockerfile Security - Adding Non-Root User")

        dockerfiles = list(self.project_root.rglob("Dockerfile*"))
        dockerfiles = [f for f in dockerfiles if f.is_file()]

        print(f"\nFound {len(dockerfiles)} Dockerfiles to fix...")

        fixed_count = 0
        for dockerfile in dockerfiles:
            print(f"\n   Processing: {dockerfile.relative_to(self.project_root)}")

            try:
                content = dockerfile.read_text()
                lines = content.split('\n')

                # Check if already has USER directive
                has_user = any("USER" in line.upper() and not line.strip().startswith("#") for line in lines)

                if has_user:
                    print(f"      ✅ Already has USER directive - skipping")
                    continue

                # Backup file
                if not self.backup_file(dockerfile):
                    continue

                # Find the best place to add USER directive
                # Strategy: Add after last RUN command, before COPY, or before CMD/ENTRYPOINT
                insert_index = -1
                last_run_index = -1
                first_copy_index = -1
                cmd_index = -1

                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("RUN ") and not stripped.startswith("#"):
                        last_run_index = i
                    elif stripped.startswith("COPY ") and not stripped.startswith("#") and first_copy_index == -1:
                        first_copy_index = i
                    elif (stripped.startswith("CMD ") or stripped.startswith("ENTRYPOINT ")) and not stripped.startswith("#") and cmd_index == -1:
                        cmd_index = i

                # Determine insertion point
                if last_run_index >= 0:
                    # Insert after last RUN command
                    insert_index = last_run_index + 1
                    # But insert before COPY if it comes right after
                    if first_copy_index == insert_index:
                        insert_index = first_copy_index
                elif first_copy_index >= 0:
                    # Insert before first COPY
                    insert_index = first_copy_index
                elif cmd_index >= 0:
                    # Insert before CMD
                    insert_index = cmd_index
                else:
                    # Insert at end, before last line if it's CMD/ENTRYPOINT
                    insert_index = len(lines) - 1

                # Determine base image for user selection
                base_image = "python"
                for line in lines:
                    if line.strip().startswith("FROM"):
                        from_match = re.search(r'FROM\s+([^\s:]+)', line, re.IGNORECASE)
                        if from_match:
                            base_image = from_match.group(1).lower()
                        break

                # Generate USER directives based on base image
                user_directives = self._get_user_directives(base_image)

                # Insert USER directives
                new_lines = lines[:insert_index] + [""] + user_directives + [""] + lines[insert_index:]
                new_content = '\n'.join(new_lines)

                # Write fixed content
                dockerfile.write_text(new_content)

                print(f"      ✅ Added non-root user directives")
                fixed_count += 1
                self.fixes_applied.append(f"Dockerfile: {dockerfile.name}")

            except Exception as e:
                print(f"      ❌ Error: {e}")
                self.fixes_failed.append(f"Dockerfile: {dockerfile.name} - {str(e)}")

        print(f"\n✅ Fixed {fixed_count}/{len(dockerfiles)} Dockerfiles")

    def _get_user_directives(self, base_image: str) -> List[str]:
        """Get USER directives for specific base image"""
        if "python" in base_image or "ubuntu" in base_image or "debian" in base_image:
            return [
                "# Create non-root user",
                "RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app",
                "USER appuser"
            ]
        elif "alpine" in base_image:
            return [
                "# Create non-root user",
                "RUN addgroup -g 1000 appgroup && adduser -D -u 1000 -G appgroup appuser",
                "USER appuser"
            ]
        elif "node" in base_image:
            return [
                "# Create non-root user",
                "RUN useradd -m -u 1000 nodeuser && chown -R nodeuser:nodeuser /app",
                "USER nodeuser"
            ]
        else:
            return [
                "# Create non-root user",
                "RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app",
                "USER appuser"
            ]

    # ========== FIX 2: Pin Docker Image Versions ==========

    def fix_docker_image_versions(self):
        """Fix #2: Pin Docker image versions (remove :latest)"""
        self.print_header("📌 FIX 2: Pinning Docker Image Versions")

        dockerfiles = list(self.project_root.rglob("Dockerfile*"))
        dockerfiles = [f for f in dockerfiles if f.is_file()]

        compose_files = list(self.project_root.rglob("docker-compose*.yml"))
        compose_files.extend(list(self.project_root.rglob("docker-compose*.yaml")))

        all_files = dockerfiles + compose_files

        print(f"\nScanning {len(all_files)} files for unpinned images...")

        fixed_count = 0
        for file_path in all_files:
            try:
                content = file_path.read_text()
                original_content = content
                modified = False

                # Fix :latest tags
                def pin_latest_tag(match):
                    image = match.group(1)
                    tag = match.group(2)

                    if tag == "latest" or tag == "":
                        # Suggest specific versions
                        if "python:" in image.lower():
                            return f"{image}:3.11.7-slim"
                        elif "node:" in image.lower():
                            return f"{image}:18-alpine"
                        elif "nginx:" in image.lower():
                            return f"{image}:1.25-alpine"
                        elif "postgres:" in image.lower():
                            return f"{image}:15-alpine"
                        elif "redis:" in image.lower():
                            return f"{image}:7-alpine"
                        else:
                            return f"{image}:latest"  # Keep if unknown
                    return match.group(0)

                # Find and replace unpinned images
                pattern = r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+):(\w*)'
                new_content = re.sub(pattern, pin_latest_tag, content)

                if new_content != original_content:
                    self.backup_file(file_path)
                    file_path.write_text(new_content)
                    print(f"   ✅ {file_path.name}")
                    fixed_count += 1
                    self.fixes_applied.append(f"Pinned versions in: {file_path.name}")
                    modified = True

            except Exception as e:
                print(f"   ❌ Error in {file_path.name}: {e}")

        if fixed_count == 0:
            print(f"\n   ℹ️  No unpinned images found (or all already pinned)")
        else:
            print(f"\n✅ Pinned versions in {fixed_count} files")

    # ========== FIX 3: Fix Docker Compose Host Mounts ==========

    def fix_docker_compose_mounts(self):
        """Fix #3: Add safety to Docker Compose host directory mounts"""
        self.print_header("🔒 FIX 3: Securing Docker Compose Host Mounts")

        compose_files = list(self.project_root.rglob("docker-compose*.yml"))
        compose_files.extend(list(self.project_root.rglob("docker-compose*.yaml")))

        print(f"\nScanning {len(compose_files)} Docker Compose files...")

        fixed_count = 0
        risky_mounts_found = 0

        for compose_file in compose_files:
            try:
                content = compose_file.read_text()
                original_content = content
                modified = False

                lines = content.split('\n')
                new_lines = []

                for i, line in enumerate(lines):
                    # Check for dangerous mounts
                    dangerous_patterns = [
                        (r'-\s*/:', 'Full root mount detected'),
                        (r'-\s*/var/run/docker\.sock', 'Docker socket mount'),
                        (r'-\s*:/host', 'Host filesystem mount'),
                    ]

                    line_modified = False
                    for pattern, description in dangerous_patterns:
                        if re.search(pattern, line) and not line.strip().startswith("#"):
                            risky_mounts_found += 1

                            # Add safety comment
                            indent = len(line) - len(line.lstrip())
                            indent_str = " " * indent

                            # Insert warning comment before the mount
                            new_lines.append(f"{indent_str}# ⚠️  SECURITY: {description}")
                            new_lines.append(f"{indent_str}# Consider: using read-only (:ro) or specific paths instead")

                            # Add read-only if not present
                            if ":ro" not in line and ":rw" not in line:
                                # Try to add read-only flag
                                line = line.rstrip()
                                if ':' in line and not line.endswith(':'):
                                    # It's a bind mount, add :ro
                                    line = line + ":ro"
                                elif line.startswith('- "') and '"' in line[3:]:
                                    # Quoted path format
                                    parts = line.split('"')
                                    if len(parts) >= 2:
                                        line = f'{parts[0]}"{parts[1]}":ro"{parts[2] if len(parts) > 2 else ""}'

                            line_modified = True
                            modified = True
                            break

                    new_lines.append(line)

                if modified:
                    self.backup_file(compose_file)
                    new_content = '\n'.join(new_lines)
                    compose_file.write_text(new_content)
                    print(f"   ✅ {compose_file.relative_to(self.project_root)}")
                    fixed_count += 1
                    self.fixes_applied.append(f"Secured mounts in: {compose_file.name}")

            except Exception as e:
                print(f"   ❌ Error in {compose_file.name}: {e}")

        if risky_mounts_found == 0:
            print(f"\n   ℹ️  No risky host mounts found")
        else:
            print(f"\n✅ Added safety comments to {risky_mounts_found} risky mounts in {fixed_count} files")

    # ========== FIX 4: Clean Environment Files ==========

    def clean_environment_files(self):
        """Fix #4: Clean up environment files with embedded secrets"""
        self.print_header("🔐 FIX 4: Cleaning Environment Files")

        # Files to remove or clean
        files_to_remove = []
        files_to_scrub = []

        # Check for backup env files
        backup_pattern = self.project_root / "security_fix_backups" / ".env.*.backup*"
        files_to_remove.extend(list(self.project_root.glob("security_fix_backups/.env.*.backup*")))

        # Check .env files for embedded secrets (flagged by scanner)
        env_files_with_secrets = [
            self.project_root / ".env.prod",
            self.project_root / ".env.staging",
            self.project_root / "security_fix_backups" / ".env.prod.backup.20251222_121946"
        ]

        # Remove known backup files with secrets
        print(f"\n🗑️  Removing backup .env files with embedded secrets...")
        removed_count = 0

        for file_path in files_to_remove:
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    print(f"   ✅ Removed: {file_path.name}")
                    removed_count += 1
                    self.fixes_applied.append(f"Removed: {file_path.name}")
                except Exception as e:
                    print(f"   ❌ Could not remove {file_path.name}: {e}")

        # Verify .gitignore has .env patterns
        gitignore = self.project_root / ".gitignore"
        print(f"\n📝 Updating .gitignore...")

        gitignore_patterns = [
            ".env",
            ".env.*",
            ".env.local",
            ".env.*.local",
            "*.key",
            "*.pem",
            "secrets.yaml",
            "secrets.yml",
            ".DS_Store",
        ]

        try:
            if gitignore.exists():
                gitignore_content = gitignore.read_text()
            else:
                gitignore_content = ""
                gitignore.touch()

            added_count = 0
            for pattern in gitignore_patterns:
                if pattern not in gitignore_content:
                    with open(gitignore, 'a') as f:
                        f.write(f"\n# Security: Exclude sensitive files\n{pattern}\n")
                    print(f"   ✅ Added: {pattern}")
                    added_count += 1
                    self.fixes_applied.append(f"Added to .gitignore: {pattern}")

            if added_count == 0:
                print(f"   ℹ️  All patterns already in .gitignore")

        except Exception as e:
            print(f"   ❌ Error updating .gitignore: {e}")

        # Remove .DS_Store files
        print(f"\n🗑️  Removing .DS_Store files...")
        ds_store_files = list(self.project_root.rglob(".DS_Store"))
        ds_store_removed = 0

        for ds_file in ds_store_files:
            try:
                ds_file.unlink()
                ds_store_removed += 1
            except Exception as e:
                pass

        if ds_store_removed > 0:
            print(f"   ✅ Removed {ds_store_removed} .DS_Store files")
            self.fixes_applied.append(f"Removed {ds_store_removed} .DS_Store files")

        print(f"\n✅ Removed {removed_count} backup .env files")

    # ========== FIX 5: Update .gitignore ==========

    def update_gitignore(self):
        """Fix #5: Comprehensive .gitignore update for security"""
        self.print_header("📝 FIX 5: Updating .gitignore for Security")

        gitignore = self.project_root / ".gitignore"

        security_patterns = [
            "\n# ========================",
            "# Security - Sensitive Files",
            "# ========================",
            "# Environment files",
            ".env",
            ".env.*",
            ".env.local",
            ".env.*.local",
            "# Private keys and certificates",
            "*.key",
            "*.pem",
            "*.p12",
            "*.pfx",
            "id_rsa",
            "id_rsa.*",
            "# Kubernetes secrets",
            "secrets.yaml",
            "secrets.yml",
            "*-secret.yaml",
            "*-secret.yml",
            "# Database backups",
            "*.sql",
            "*.sql.gz",
            "*.sql.enc",
            "# System files",
            ".DS_Store",
            "Thumbs.db",
            "# Backup files",
            "*.backup",
            "*.bak",
            "*~",
            "# Log files with sensitive data",
            "*.log",
            "logs/",
            "# SSL certificates",
            "*.crt",
            "*.csr",
            "# AWS/GCP credentials",
            ".aws/credentials",
            "gcloud-credentials.json",
            "# Service account keys",
            "*-service-account.json",
            "*-sa-key.json",
        ]

        try:
            if gitignore.exists():
                existing_content = gitignore.read_text()
            else:
                existing_content = ""
                gitignore.touch()

            # Check which patterns need to be added
            missing_patterns = []
            for pattern in security_patterns:
                # Extract actual pattern from comment lines
                if pattern.strip() and not pattern.strip().startswith("#"):
                    if pattern not in existing_content:
                        missing_patterns.append(pattern)

            if missing_patterns:
                # Add missing patterns
                with open(gitignore, 'a') as f:
                    f.write("\n" + "\n".join(security_patterns) + "\n")

                print(f"   ✅ Added {len(missing_patterns)} security patterns to .gitignore")
                self.fixes_applied.append("Updated .gitignore with security patterns")
            else:
                print(f"   ℹ️  All security patterns already in .gitignore")

        except Exception as e:
            print(f"   ❌ Error updating .gitignore: {e}")

    # ========== RUN ALL FIXES ==========

    def run_all_fixes(self):
        """Run all DevOps security fixes"""
        self.print_header("🔧 DEVOPS SECURITY AUTOMATED FIXES")
        print(f"Project Root: {self.project_root}")
        print(f"Backup Directory: {self.backup_dir}")
        print(f"Started at: {datetime.now().isoformat()}")

        # Run all fixes
        self.fix_dockerfiles()
        self.fix_docker_image_versions()
        self.fix_docker_compose_mounts()
        self.clean_environment_files()
        self.update_gitignore()

        # Generate summary
        self.print_summary()

    def print_summary(self):
        """Print summary of fixes applied"""
        self.print_header("📋 FIX SUMMARY")

        print(f"\n✅ Fixes Applied: {len(self.fixes_applied)}")

        if self.fixes_applied:
            print(f"\nApplied fixes:")
            for i, fix in enumerate(self.fixes_applied[:20], 1):
                print(f"   {i}. {fix}")
            if len(self.fixes_applied) > 20:
                print(f"   ... and {len(self.fixes_applied) - 20} more")

        if self.fixes_failed:
            print(f"\n❌ Fixes Failed: {len(self.fixes_failed)}")
            for fail in self.fixes_failed:
                print(f"   - {fail}")

        # Next steps
        self.print_header("📋 REQUIRED ACTIONS")

        print("""
1. Review Backup Files
   Check: security_fix_backups/
   - Review changes made to Dockerfiles
   - Review changes made to Docker Compose files
   - Restore if needed

2. Test Docker Containers
   docker-compose build
   docker-compose up -d
   - Verify containers start correctly
   - Check logs for errors

3. Verify Non-Root User
   docker-compose exec backend whoami
   - Should show: appuser (not root)

4. Clean Up Old Images
   docker system prune -a

5. Run Security Scan Again
   python comprehensive_devops_security_scanner.py
   - Verify improvements
   - Score should be significantly higher

6. Commit Changes
   git add .
   git commit -m "security: fix Docker and DevOps security issues"
   - Review changes before pushing
        """)

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print(f"{GREEN}{'=' * 80}{RESET}")


def main():
    """Main entry point"""
    fixer = DevOpsSecurityFixer()
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
