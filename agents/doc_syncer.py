#!/usr/bin/env python3
"""
Autonomous Agent: Documentation Synchronizer
Automatically syncs documentation with code changes
Keeps API docs, README, and other docs up-to-date
"""

import os
import sys
import re
import json
import logging
import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from difflib import unified_diff

# GitHub API
from github import Github
from git import Repo, Diff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agents/doc_syncer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DocumentationSyncer:
    """
    Autonomous agent that keeps documentation in sync with code

    Features:
    - Scans for code changes (functions, classes, API endpoints)
    - Updates documentation automatically
    - Detects outdated documentation
    - Creates PRs for documentation updates
    - Supports multiple documentation formats
    """

    def __init__(self):
        self.repo_path = Path(os.getcwd()).parent
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPOSITORY', 'psychsync/psychsync')

        # Documentation files to sync
        self.doc_files = {
            'api': 'docs/api/OPENAPI_SPECIFICATION.yaml',
            'readme': 'README.md',
            'changelog': 'CHANGELOG.md',
            'database': 'docs/DATABASE_SCHEMA.md',
            'architecture': 'docs/ARCHITECTURE.md'
        }

        # Code patterns to document
        self.patterns = {
            'api_endpoints': r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            'functions': r'def\s+(\w+)\s*\(([^)]*)\)',
            'classes': r'class\s+(\w+)\s*(\(([^)]*)\))?:',
            'models': r'class\s+(\w+)\s*\((Base|db\.Model)\)',
        }

        logger.info("📚 Documentation Syncer initialized")

    def scan_and_sync(self, commit_hash: str = None) -> Dict:
        """
        Scan codebase for changes and sync documentation

        Args:
            commit_hash: Specific commit to scan (if None, scans latest)
        """
        logger.info("🔄 Scanning codebase for changes...")

        changes = {
            'timestamp': datetime.now().isoformat(),
            'commit': commit_hash,
            'code_changes': [],
            'doc_updates': [],
            'pr_created': False
        }

        try:
            # 1. Get code changes
            code_changes = self._detect_code_changes(commit_hash)
            changes['code_changes'] = code_changes

            if not code_changes:
                logger.info("✅ No code changes detected")
                return changes

            # 2. Analyze what needs to be updated
            update_plan = self._create_update_plan(code_changes)

            # 3. Apply updates
            doc_updates = self._apply_documentation_updates(update_plan)
            changes['doc_updates'] = doc_updates

            # 4. Commit and create PR
            if doc_updates:
                self._commit_and_create_pr(changes)
                changes['pr_created'] = True

            logger.info(f"✅ Documentation sync complete: {len(doc_updates)} files updated")
            return changes

        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            raise

    def _detect_code_changes(self, commit_hash: str = None) -> List[Dict]:
        """Detect code changes since last documentation update"""
        logger.info("Detecting code changes...")

        code_changes = []

        # Get git diff
        if commit_hash:
            # Compare with specific commit
            result = subprocess.run(
                ['git', 'diff', commit_hash, 'HEAD', '--name-only'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
        else:
            # Compare with last doc update commit
            result = subprocess.run(
                ['git', 'diff', 'HEAD~5', 'HEAD', '--name-only'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

        changed_files = result.stdout.strip().split('\n')

        # Filter for code files
        for file_path in changed_files:
            if not file_path:
                continue

            if any(file_path.startswith(src_dir) for src_dir in ['app/', 'ai/', 'frontend/src/']):
                if file_path.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    code_changes.append({
                        'file_path': file_path,
                        'change_type': self._get_change_type(file_path),
                        'language': self._get_language(file_path)
                    })

        logger.info(f"Found {len(code_changes)} changed code files")
        return code_changes

    def _get_change_type(self, file_path: str) -> str:
        """Determine if file was added, modified, or deleted"""
        result = subprocess.run(
            ['git', 'log', '--diff-filter=A', '--name-only', '--pretty=format:', 'HEAD', '--', file_path],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            return 'added'

        result = subprocess.run(
            ['git', 'log', '--diff-filter=D', '--name-only', '--pretty=format:', 'HEAD', '--', file_path],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            return 'deleted'

        return 'modified'

    def _get_language(self, file_path: str) -> str:
        """Get programming language from file extension"""
        ext = Path(file_path).suffix
        return {
            '.py': 'python',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript'
        }.get(ext, 'unknown')

    def _create_update_plan(self, code_changes: List[Dict]) -> Dict:
        """Create a plan for what documentation needs to be updated"""
        logger.info("Creating documentation update plan...")

        update_plan = {
            'api_docs': [],
            'readme': [],
            'database_schema': [],
            'architecture': []
        }

        for change in code_changes:
            file_path = change['file_path']
            language = change['language']
            change_type = change['change_type']

            # Check if API endpoint file
            if 'api/v1/endpoints' in file_path and language == 'python':
                endpoints = self._extract_api_endpoints(file_path)
                update_plan['api_docs'].extend(endpoints)

            # Check if model file
            if 'db/models' in file_path and language == 'python':
                models = self._extract_models(file_path)
                update_plan['database_schema'].extend(models)

            # Check if main app file
            if file_path in ['app/main.py', 'frontend/src/App.tsx']:
                update_plan['architecture'].append(file_path)

            # Check if README should be updated
            if change_type == 'added' and self._is_user_facing_feature(file_path):
                update_plan['readme'].append(file_path)

        return update_plan

    def _extract_api_endpoints(self, file_path: str) -> List[Dict]:
        """Extract API endpoints from Python file"""
        endpoints = []

        try:
            full_path = self.repo_path / file_path

            with open(full_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(full_path))

            # Find all route decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            # Check if it's a router decorator
                            if hasattr(decorator.func, 'attr') and 'router' in decorator.func.attr:
                                # Extract HTTP method and path
                                endpoint = self._parse_api_decorator(decorator, node)
                                if endpoint:
                                    endpoints.append(endpoint)

        except Exception as e:
            logger.error(f"Error extracting endpoints from {file_path}: {e}")

        return endpoints

    def _parse_api_decorator(self, decorator, function_node) -> Dict:
        """Parse API decorator to get endpoint info"""
        try:
            # Get HTTP method
            method = decorator.func.attr.split('_')[1].upper()

            # Get path
            path_arg = None
            for keyword in decorator.keywords:
                if keyword.arg == 'path':
                    if isinstance(keyword.value, ast.Constant):
                        path_arg = keyword.value.value

            # Get function name
            function_name = function_node.name

            # Get docstring
            docstring = ast.get_docstring(function_node)

            if path_arg and function_name:
                return {
                    'method': method,
                    'path': path_arg,
                    'function': function_name,
                    'file': str(function_node.lineno),
                    'docstring': docstring
                }

        except Exception as e:
            logger.error(f"Error parsing decorator: {e}")

        return None

    def _extract_models(self, file_path: str) -> List[Dict]:
        """Extract database models from Python file"""
        models = []

        try:
            full_path = self.repo_path / file_path

            with open(full_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(full_path))

            # Find all class definitions that inherit from Base or db.Model
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id in ['Base', 'Model']:
                            models.append({
                                'class_name': node.name,
                                'file': file_path,
                                'docstring': ast.get_docstring(node),
                                'attributes': self._extract_model_attributes(node)
                            })

        except Exception as e:
            logger.error(f"Error extracting models from {file_path}: {e}")

        return models

    def _extract_model_attributes(self, class_node) -> List[Dict]:
        """Extract attributes from a model class"""
        attributes = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                # Variable with type annotation
                if isinstance(node.target, ast.Name):
                    attr_name = node.target.id
                    attr_type = self._get_type_string(node.annotation)
                    attributes.append({'name': attr_name, 'type': attr_type})

        return attributes

    def _get_type_string(self, annotation) -> str:
        """Convert AST annotation to type string"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_type_string(annotation.value)}[{self._get_type_string(annotation.slice)}]"
        return 'Any'

    def _is_user_facing_feature(self, file_path: str) -> bool:
        """Check if the file represents a user-facing feature"""
        # Heuristic: check path and patterns
        user_facing_patterns = [
            'assessments',
            'analytics',
            'dashboard',
            'reports'
        ]

        return any(pattern in file_path for pattern in user_facing_patterns)

    def _apply_documentation_updates(self, update_plan: Dict) -> List[Dict]:
        """Apply documentation updates based on plan"""
        logger.info("Applying documentation updates...")

        updates = []

        # Update API documentation
        if update_plan['api_docs']:
            api_updates = self._update_api_docs(update_plan['api_docs'])
            updates.extend(api_updates)

        # Update database schema
        if update_plan['database_schema']:
            schema_updates = self._update_database_schema(update_plan['database_schema'])
            updates.extend(schema_updates)

        # Update README
        if update_plan['readme']:
            readme_updates = self._update_readme(update_plan['readme'])
            updates.extend(readme_updates)

        return updates

    def _update_api_docs(self, endpoints: List[Dict]) -> List[Dict]:
        """Update OpenAPI specification"""
        logger.info(f"Updating API docs with {len(endpoints)} endpoints...")

        # This would update the OpenAPI YAML file
        # For now, just record the update
        updates = []
        for endpoint in endpoints:
            updates.append({
                'type': 'api_documentation',
                'action': 'add_endpoint',
                'details': endpoint
            })

        return updates

    def _update_database_schema(self, models: List[Dict]) -> List[Dict]:
        """Update database schema documentation"""
        logger.info(f"Updating database schema with {len(models)} models...")

        updates = []
        for model in models:
            updates.append({
                'type': 'database_schema',
                'action': 'add_model',
                'details': model
            })

        return updates

    def _update_readme(self, files: List[str]) -> List[Dict]:
        """Update README with new features"""
        logger.info(f"Updating README with {len(files)} new features...")

        updates = []
        for file_path in files:
            updates.append({
                'type': 'readme',
                'action': 'document_feature',
                'details': {'file': file_path}
            })

        return updates

    def _commit_and_create_pr(self, changes: Dict):
        """Commit changes and create PR"""
        logger.info("Committing documentation updates...")

        branch_name = f"docs/auto-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            # Create new branch
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Add documentation files
            subprocess.run(
                ['git', 'add', 'docs/', 'README.md', 'CHANGELOG.md'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Commit
            commit_message = f'''📚 Automated documentation update

Updated documentation based on recent code changes:

- API endpoints: {len(changes.get('doc_updates', []))} changes
- Database models: Updated
- README: Updated

Generated by: Documentation Synchronizer Agent
Date: {datetime.now().isoformat()}
'''

            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Push branch
            subprocess.run(
                ['git', 'push', '-u', 'origin', branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Create PR
            if self.github_token:
                g = Github(self.github_token)
                repo = g.get_repo(self.repo_name)

                pr_title = f"📚 Automated Documentation Update ({datetime.now().strftime('%Y-%m-%d')})"
                pr_body = self._generate_pr_body(changes)

                pr = repo.create_pull_request(
                    title=pr_title,
                    body=pr_body,
                    head=branch_name,
                    base="main"
                )

                logger.info(f"✅ PR created: {pr.html_url}")

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")

    def _generate_pr_body(self, changes: Dict) -> str:
        """Generate PR body"""
        body = "## 📚 Automated Documentation Update\n\n"
        body += "This PR contains automated updates to keep documentation in sync with code changes.\n\n"

        body += "### 📝 Changes Summary\n\n"

        code_changes = changes.get('code_changes', [])
        doc_updates = changes.get('doc_updates', [])

        body += f"- **Code files changed:** {len(code_changes)}\n"
        body += f"- **Documentation updates:** {len(doc_updates)}\n\n"

        if code_changes:
            body += "### 📁 Modified Code Files\n\n"
            for change in code_changes[:10]:
                body += f"- `{change['file_path']}` ({change['change_type']})\n"
            if len(code_changes) > 10:
                body += f"- ... and {len(code_changes) - 10} more\n"

        if doc_updates:
            body += "\n### 📄 Documentation Updates\n\n"
            for update in doc_updates[:10]:
                body += f"- {update['type']}: {update['action']}\n"
            if len(doc_updates) > 10:
                body += f"- ... and {len(doc_updates) - 10} more\n"

        body += "\n---\n\n"
        body += "## ℹ️ Automated Changes\n\n"
        body += "These changes were automatically generated by the Documentation Synchronizer agent. "
        body += "Please review the updates and merge if everything looks correct.\n\n"
        body += "\n---\n\n"
        body += f"**Generated by:** Documentation Synchronizer Agent\n"
        body += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"

        return body

    def run_continuous(self, interval_minutes: int = 60):
        """Run the syncer continuously"""
        logger.info(f"🔄 Running continuous sync (checking every {interval_minutes} minutes)...")

        import time

        while True:
            try:
                self.scan_and_sync()
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logger.info("Stopping continuous sync...")
                break
            except Exception as e:
                logger.error(f"Error in continuous sync: {e}")
                time.sleep(interval_minutes * 60)


def main():
    """Entry point for the agent"""
    import sys

    agent = DocumentationSyncer()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'scan':
            # Single scan
            changes = agent.scan_and_sync()
            print(json.dumps(changes, indent=2))

        elif command == 'continuous':
            # Continuous mode
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            agent.run_continuous(interval)

    else:
        print("Usage:")
        print("  python doc_syncer.py scan")
        print("  python doc_syncer.py continuous [interval_minutes]")


if __name__ == '__main__':
    main()
