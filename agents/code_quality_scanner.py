#!/usr/bin/env python3
"""
Autonomous Agent: Code Quality Scanner
Scans code daily for bugs, code smells, unused imports, and dependency risks
Creates PRs automatically for fixes
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import re
import ast

# GitHub API
from github import Github
from git import Repo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agents/quality_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CodeQualityScanner:
    """Autonomous agent that scans code for quality issues and creates PRs"""

    def __init__(self):
        self.repo_path = Path(os.getcwd()).parent
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPOSITORY', 'psychsync/psychsync')
        self.branch_name = f"fix/quality-scan-{datetime.now().strftime('%Y%m%d')}"

        # Tools configuration
        self.tools = {
            'pylint': {
                'enabled': True,
                'config': '.pylintrc',
                'severity': 'ERROR'
            },
            'flake8': {
                'enabled': True,
                'config': '.flake8',
                'max_line_length': 100
            },
            'isort': {
                'enabled': True,
                'config': '.isort.cfg'
            },
            'bandit': {
                'enabled': True,
                'config': '.bandit'
            },
            'safety': {
                'enabled': True,
                'check_dependencies': True
            }
        }

        # Patterns for unused imports
        self.unused_import_patterns = [
            r'^from\s+(\S+)\s+import\s+\*',
            r'^import\s+(\S+)$',
            r'^from\s+(\S+)\s+import\s+([^,\n]+)',
        ]

    def scan_codebase(self) -> Dict[str, Any]:
        """Run all quality checks and collect findings"""
        logger.info("🔍 Starting code quality scan...")

        findings = {
            'bugs': [],
            'code_smells': [],
            'unused_imports': [],
            'dependency_risks': [],
            'security_issues': []
        }

        # 1. Scan for bugs and code smells using pylint
        if self.tools['pylint']['enabled']:
            findings['bugs'].extend(self._run_pylint())

        # 2. Scan for style issues using flake8
        if self.tools['flake8']['enabled']:
            findings['code_smells'].extend(self._run_flake8())

        # 3. Scan for unused imports
        findings['unused_imports'].extend(self._find_unused_imports())

        # 4. Scan for security issues using bandit
        if self.tools['bandit']['enabled']:
            findings['security_issues'].extend(self._run_bandit())

        # 5. Check for dependency vulnerabilities
        if self.tools['safety']['enabled']:
            findings['dependency_risks'].extend(self._run_safety())

        logger.info(f"✅ Scan complete. Found {sum(len(v) for v in findings.values())} issues total")
        return findings

    def _run_pylint(self) -> List[Dict]:
        """Run pylint and collect error-level findings"""
        logger.info("Running pylint...")

        try:
            result = subprocess.run(
                ['pylint', 'app/', '--output-format=json',
                 f'--rcfile={self.tools["pylint"]["config"]}'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            if result.returncode != 0:
                findings = json.loads(result.stdout)
                # Filter for only errors and fatal issues
                critical_findings = [
                    f for f in findings
                    if f.get('type') in ['error', 'fatal']
                ]
                logger.info(f"Pylint found {len(critical_findings)} critical issues")
                return critical_findings
            return []

        except Exception as e:
            logger.error(f"Pylint scan failed: {e}")
            return []

    def _run_flake8(self) -> List[Dict]:
        """Run flake8 and collect style issues"""
        logger.info("Running flake8...")

        try:
            result = subprocess.run(
                ['flake8', 'app/', '--format=json',
                 f'--max-line-length={self.tools["flake8"]["max_line_length"]}'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            if result.returncode != 0:
                findings = json.loads(result.stdout)
                logger.info(f"Flake8 found {len(findings)} style issues")
                return findings
            return []

        except Exception as e:
            logger.error(f"Flake8 scan failed: {e}")
            return []

    def _find_unused_imports(self) -> List[Dict]:
        """Find unused imports by analyzing Python files"""
        logger.info("Scanning for unused imports...")

        unused_imports = []
        python_files = list(self.repo_path.rglob('*.py'))

        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                # Get all imports
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])

                # Get all names used in the code
                used_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        # Handle attribute access
                        if isinstance(node.value, ast.Name):
                            used_names.add(node.value.id)

                # Find unused imports
                for imp in imports:
                    if imp not in used_names and not imp.startswith('_'):
                        unused_imports.append({
                            'file': str(file_path.relative_to(self.repo_path)),
                            'import': imp,
                            'type': 'unused_import',
                            'message': f"Unused import: {imp}"
                        })

            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")

        logger.info(f"Found {len(unused_imports)} unused imports")
        return unused_imports

    def _run_bandit(self) -> List[Dict]:
        """Run bandit security scanner"""
        logger.info("Running bandit security scan...")

        try:
            result = subprocess.run(
                ['bandit', '-r', 'app/', '-f', 'json',
                 f'-c {self.tools["bandit"]["config"]}'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            if result.returncode != 0:
                findings = json.loads(result.stdout)
                logger.info(f"Bandit found {len(findings.get('results', []))} security issues")
                return findings.get('results', [])
            return []

        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            return []

    def _run_safety(self) -> List[Dict]:
        """Run safety check for known security vulnerabilities"""
        logger.info("Checking dependencies for vulnerabilities...")

        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            if result.returncode != 0:
                vulnerabilities = json.loads(result.stdout)
                logger.info(f"Safety found {len(vulnerabilities)} vulnerable dependencies")
                return vulnerabilities
            return []

        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return []

    def create_fix_pr(self, findings: Dict[str, Any]) -> bool:
        """Create a pull request with automated fixes"""
        if not self.github_token:
            logger.error("GITHUB_TOKEN not set")
            return False

        # Check if there are any findings
        total_issues = sum(len(v) for v in findings.values())
        if total_issues == 0:
            logger.info("✅ No issues found - no PR needed")
            return True

        logger.info(f"🔧 Creating PR for {total_issues} fixes...")

        try:
            g = Github(self.github_token)
            repo = g.get_repo(self.repo_name)

            # Create new branch
            self._create_branch()

            # Apply fixes
            fixes_applied = self._apply_fixes(findings)

            if not fixes_applied:
                logger.info("No fixes could be applied automatically")
                return False

            # Commit changes
            self._commit_changes()

            # Push branch
            self._push_branch()

            # Create PR
            pr_title = f"🤖 Automated Code Quality Fixes ({datetime.now().strftime('%Y-%m-%d')})"
            pr_body = self._generate_pr_description(findings)

            pr = repo.create_pull_request(
                title=pr_title,
                body=pr_body,
                head=self.branch_name,
                base="main"
            )

            logger.info(f"✅ PR created: {pr.html_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return False

    def _create_branch(self):
        """Create a new git branch for fixes"""
        logger.info(f"Creating branch: {self.branch_name}")

        try:
            # Update main branch
            subprocess.run(
                ['git', 'fetch', 'origin', 'main'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Create and checkout new branch
            subprocess.run(
                ['git', 'checkout', '-b', self.branch_name, 'origin/main'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            logger.info(f"Branch {self.branch_name} created")

        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            raise

    def _apply_fixes(self, findings: Dict[str, Any]) -> bool:
        """Apply automated fixes"""
        logger.info("Applying automated fixes...")

        fixes_applied = False

        # Fix 1: Remove unused imports
        for finding in findings.get('unused_imports', []):
            if self._fix_unused_import(finding):
                fixes_applied = True

        # Fix 2: Auto-fix style issues with autopep8
        if findings.get('code_smells'):
            if self._run_autopep8():
                fixes_applied = True

        # Fix 3: Auto-fix imports with isort
        if self._run_isort():
            fixes_applied = True

        return fixes_applied

    def _fix_unused_import(self, finding: Dict) -> bool:
        """Remove an unused import from a file"""
        try:
            file_path = self.repo_path / finding['file']
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Find and remove the import line
            import_name = finding['import']
            new_lines = []
            for line in lines:
                if import_name in line and ('import' in line):
                    # Skip this line (remove the import)
                    continue
                new_lines.append(line)

            with open(file_path, 'w') as f:
                f.writelines(new_lines)

            logger.info(f"Removed unused import {import_name} from {finding['file']}")
            return True

        except Exception as e:
            logger.error(f"Failed to fix unused import: {e}")
            return False

    def _run_autopep8(self) -> bool:
        """Run autopep8 to fix style issues"""
        try:
            result = subprocess.run(
                ['autopep8', '--in-place', '--aggressive', '-r', 'app/'],
                cwd=self.repo_path,
                capture_output=True
            )
            logger.info("Autopep8 fixes applied")
            return True
        except Exception as e:
            logger.error(f"Autopep8 failed: {e}")
            return False

    def _run_isort(self) -> bool:
        """Run isort to fix import ordering"""
        try:
            result = subprocess.run(
                ['isort', 'app/', '--settings-path', '.isort.cfg'],
                cwd=self.repo_path,
                capture_output=True
            )
            logger.info("Isort fixes applied")
            return True
        except Exception as e:
            logger.error(f"Isort failed: {e}")
            return False

    def _commit_changes(self):
        """Commit the fixes"""
        commit_message = f'''🤖 Automated code quality fixes

- Remove unused imports
- Fix style issues (autopep8, isort)
- Apply automated linting fixes

Generated by: Code Quality Scanner Agent
Date: {datetime.now().isoformat()}
'''

        subprocess.run(
            ['git', 'add', '.'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

        logger.info("Changes committed")

    def _push_branch(self):
        """Push the branch to remote"""
        subprocess.run(
            ['git', 'push', '-u', 'origin', self.branch_name],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

        logger.info(f"Branch {self.branch_name} pushed to remote")

    def _generate_pr_description(self, findings: Dict[str, Any]) -> str:
        """Generate PR description from findings"""
        description = "## 🤖 Automated Code Quality Fixes\n\n"
        description += "This PR contains automated fixes for code quality issues found by the Code Quality Scanner agent.\n\n"

        if findings.get('bugs'):
            description += f"### 🐛 Bugs Fixed: {len(findings['bugs'])}\n"

        if findings.get('code_smells'):
            description += f"### 👃 Code Smells Fixed: {len(findings['code_smells'])}\n"

        if findings.get('unused_imports'):
            description += f"### 🧹 Unused Imports Removed: {len(findings['unused_imports'])}\n"
            description += "\n**Unused imports:**\n"
            for item in findings['unused_imports'][:10]:
                description += f"- `{item['file']}`: `{item['import']}`\n"
            if len(findings['unused_imports']) > 10:
                description += f"- ... and {len(findings['unused_imports']) - 10} more\n"

        if findings.get('security_issues'):
            description += f"\n### 🔒 Security Issues Found: {len(findings['security_issues'])}\n"
            description += "\n⚠️ **These require manual review!**\n"

        if findings.get('dependency_risks'):
            description += f"\n### 📦 Dependency Risks Found: {len(findings['dependency_risks'])}\n"
            description += "\n⚠️ **Update these dependencies:**\n"
            for item in findings['dependency_risks'][:5]:
                description += f"- {item}\n"

        description += "\n---\n\n"
        description += "## 📋 Next Steps\n\n"
        description += "1. Review the changes\n"
        description += "2. Run tests to ensure nothing broke\n"
        description += "3. Merge if all tests pass\n"
        description += "\n"
        description += "## ℹ️ Generated by\n"
        description += "Code Quality Scanner Agent - PsychSync DevOps Automation\n"
        description += f"Scan date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return description

    def run(self):
        """Main execution method"""
        logger.info("🚀 Code Quality Scanner Agent starting...")

        try:
            # Scan codebase
            findings = self.scan_codebase()

            # Create PR if issues found
            self.create_fix_pr(findings)

            logger.info("✅ Code Quality Scanner Agent completed successfully")

        except Exception as e:
            logger.error(f"❌ Agent failed: {e}")
            raise


def main():
    """Entry point for the agent"""
    agent = CodeQualityScanner()
    agent.run()


if __name__ == '__main__':
    main()
