#!/usr/bin/env python3
"""
Autonomous Agent: Crash Log Analyzer
Reads crash logs and automatically locates code responsible
Uses stack trace analysis and code mapping
"""

import ast
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# GitHub API
from github import Github

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agents/crash_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CrashLogAnalyzer:
    """
    Autonomous agent that analyzes crash logs and identifies responsible code

    Features:
    - Parses stack traces from various sources (Sentry, application logs, etc.)
    - Maps stack frames to source code
    - Identifies the problematic line of code
    - Analyzes patterns and common issues
    - Creates GitHub issues with detailed analysis
    - Suggests fixes based on crash type
    """

    def __init__(self):
        self.repo_path = Path(os.getcwd()).parent
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPOSITORY', 'psychsync/psychsync')

        # Crash patterns
        self.crash_patterns = {
            'AttributeError': r'AttributeError:\s*(.+)',
            'TypeError': r'TypeError:\s*(.+)',
            'KeyError': r'KeyError:\s*[\'"](.+)[\'"]',
            'ValueError': r'ValueError:\s*(.+)',
            'ImportError': r'ImportError:\s*(.+)',
            'ZeroDivisionError': r'ZeroDivisionError:\s*(.+)',
            'IndexError': r'IndexError:\s*(.+)',
            'SQLAlchemyError': r'sqlalchemy\.\w+Error:\s*(.+)',
            'AssertionError': r'AssertionError:\s*(.+)',
        }

        # Stack trace patterns (Python)
        self.stack_trace_patterns = [
            # Python traceback
            r'Traceback \(most recent call last\):',
            r'  File "(.+)", line (\d+), in (.+)',
            r'    (.+)',
            # Error line
            r'(\w+Error): (.+)',
        ]

        logger.info("🔍 Crash Log Analyzer initialized")

    def analyze_crash_log(self, crash_log: str, source: str = 'unknown') -> Dict:
        """
        Analyze a crash log and identify the root cause

        Args:
            crash_log: The crash log text
            source: Source of the crash log (sentry, application log, etc.)

        Returns:
            Analysis results with identified code location
        """
        logger.info(f"🔍 Analyzing crash log from {source}...")

        results = {
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'error_type': None,
            'error_message': None,
            'stack_trace': [],
            'responsible_code': [],
            'suggested_fixes': [],
            'related_issues': [],
            'severity': 'unknown'
        }

        # 1. Extract error type and message
        error_info = self._extract_error_info(crash_log)
        results.update(error_info)

        # 2. Parse stack trace
        stack_trace = self._parse_stack_trace(crash_log)
        results['stack_trace'] = stack_trace

        if not stack_trace:
            logger.warning("No stack trace found in crash log")
            return results

        # 3. Identify responsible code
        responsible_code = self._identify_responsible_code(stack_trace)
        results['responsible_code'] = responsible_code

        # 4. Determine severity
        results['severity'] = self._determine_severity(error_info, stack_trace)

        # 5. Suggest fixes
        suggested_fixes = self._suggest_fixes(error_info, stack_trace, responsible_code)
        results['suggested_fixes'] = suggested_fixes

        # 6. Find related issues
        related_issues = self._find_related_issues(error_info)
        results['related_issues'] = related_issues

        logger.info(f"✅ Crash analysis complete: {results['error_type']} at {responsible_code[0]['file_path'] if responsible_code else 'unknown'}")
        return results

    def _extract_error_info(self, crash_log: str) -> Dict:
        """Extract error type and message from crash log"""
        error_info = {
            'error_type': None,
            'error_message': None,
            'full_error': None
        }

        for error_type, pattern in self.crash_patterns.items():
            match = re.search(pattern, crash_log)
            if match:
                error_info['error_type'] = error_type
                error_info['error_message'] = match.group(1)
                break

        # Extract full error line
        error_match = re.search(r'(\w+Error:\s*.+)', crash_log)
        if error_match:
            error_info['full_error'] = error_match.group(1)

        return error_info

    def _parse_stack_trace(self, crash_log: str) -> List[Dict]:
        """Parse stack trace from crash log"""
        stack_frames = []

        lines = crash_log.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Look for stack frame pattern
            frame_match = re.match(r'  File "([^"]+)", line (\d+), in (\w+)', line)
            if frame_match:
                file_path = frame_match.group(1)
                line_number = int(frame_match.group(2))
                function_name = frame_match.group(3)

                # Get the code line
                code_line = None
                if i + 1 < len(lines):
                    code_line = lines[i + 1].strip()

                stack_frames.append({
                    'file_path': file_path,
                    'line_number': line_number,
                    'function_name': function_name,
                    'code_line': code_line,
                    'in_app': self._is_app_code(file_path)
                })

            i += 1

        # Reverse to have most recent call first
        stack_frames.reverse()

        logger.info(f"Parsed {len(stack_frames)} stack frames")
        return stack_frames

    def _is_app_code(self, file_path: str) -> bool:
        """Check if the file is application code (not library code)"""
        # Check if it's in our codebase
        app_directories = ['app/', 'frontend/src/', 'ai/', 'agents/']

        for app_dir in app_directories:
            if file_path.startswith(app_dir):
                return True

        return False

    def _identify_responsible_code(self, stack_trace: List[Dict]) -> List[Dict]:
        """Identify the most likely responsible code location"""
        responsible_frames = []

        # Filter to only application code
        app_frames = [frame for frame in stack_trace if frame['in_app']]

        if not app_frames:
            # If no app code, take top 3 frames
            app_frames = stack_trace[:3]

        for frame in app_frames[:3]:  # Top 3 most likely frames
            file_path = frame['file_path']
            line_number = frame['line_number']

            # Locate the actual code
            code_context = self._get_code_context(file_path, line_number)

            responsible_frames.append({
                **frame,
                'code_context': code_context,
                'git_blame': self._get_git_blame(file_path, line_number)
            })

        return responsible_frames

    def _get_code_context(self, file_path: str, line_number: int, context_lines: int = 5) -> Dict:
        """Get code context around the problematic line"""
        full_path = self.repo_path / file_path

        if not full_path.exists():
            return {'error': f'File not found: {file_path}'}

        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()

            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)

            context_lines_list = []
            for i in range(start, end):
                prefix = '>>> ' if i == line_number - 1 else '    '
                context_lines_list.append(f"{prefix}{i + 1}: {lines[i].rstrip()}")

            return {
                'file_path': file_path,
                'line_number': line_number,
                'context': '\n'.join(context_lines_list),
                'problematic_line': lines[line_number - 1].strip() if line_number <= len(lines) else None
            }

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {'error': str(e)}

    def _get_git_blame(self, file_path: str, line_number: int) -> Optional[Dict]:
        """Get git blame information for the problematic line"""
        try:
            result = subprocess.run(
                ['git', 'blame', '-L', f'{line_number},{line_number}', '--', file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                blame_output = result.stdout
                # Parse git blame output
                # Format: <commit> (<author> <date> <time> <timezone>) <line number>) <line content>
                match = re.match(r'(\w+)\s+\(([^)]+)\)\s+', blame_output)
                if match:
                    return {
                        'commit': match.group(1),
                        'author_info': match.group(2)
                    }

        except Exception as e:
            logger.error(f"Error running git blame: {e}")

        return None

    def _determine_severity(self, error_info: Dict, stack_trace: List[Dict]) -> str:
        """Determine severity of the crash"""
        error_type = error_info.get('error_type', '')

        # Critical errors
        if error_type in ['AttributeError', 'TypeError', 'KeyError', 'SQLAlchemyError']:
            # Check if it's in request handler
            for frame in stack_trace:
                if 'api/v1/endpoints' in frame['file_path']:
                    return 'critical'

        # High severity
        if error_type in ['ValueError', 'IndexError', 'ImportError']:
            return 'high'

        # Medium severity
        if error_type in ['ZeroDivisionError', 'AssertionError']:
            return 'medium'

        return 'low'

    def _suggest_fixes(self, error_info: Dict, stack_trace: List[Dict], responsible_code: List[Dict]) -> List[str]:
        """Suggest potential fixes based on error type and context"""
        fixes = []

        error_type = error_info.get('error_type', '')
        error_message = error_info.get('error_message', '')

        # Error-specific fixes
        if error_type == 'AttributeError':
            fixes.append("Add null/None check before accessing the attribute")
            fixes.append("Verify the object has the expected attributes using hasattr()")
            fixes.append("Add try-except block to handle missing attributes gracefully")

        elif error_type == 'KeyError':
            fixes.append(f"Use .get() method instead of direct dictionary access for key: '{error_message}'")
            fixes.append("Check if key exists before accessing: if 'key' in dict")
            fixes.append("Use dict.get('key', default_value) to provide a default")

        elif error_type == 'TypeError':
            fixes.append("Verify type compatibility before operation")
            fixes.append("Add type checking: isinstance(value, expected_type)")
            fixes.append("Convert types explicitly if needed: str(), int(), etc.")

        elif error_type == 'ValueError':
            fixes.append("Add input validation before processing")
            fixes.append("Use try-except to catch and handle ValueError gracefully")
            fixes.append("Log the invalid value for debugging")

        elif error_type == 'SQLAlchemyError':
            fixes.append("Add database transaction rollback in error handler")
            fixes.append("Verify database connection is healthy before query")
            fixes.append("Add retry logic for transient database errors")
            fixes.append("Check query syntax and parameters")

        elif error_type == 'IndexError':
            fixes.append("Check list/array length before accessing index")
            fixes.append("Use try-except to catch IndexError")
            fixes.append("Add bounds checking: if 0 <= index < len(array)")

        elif error_type == 'ImportError':
            fixes.append("Verify the module is installed (requirements.txt or package.json)")
            fixes.append("Check Python path and module location")
            fixes.append("Ensure relative imports are used correctly in packages")

        # General fixes based on code context
        if responsible_code:
            for frame in responsible_code[:1]:  # Most likely frame
                if frame['code_line']:
                    fixes.append(f"Review line {frame['line_number']} in {frame['file_path']}")
                    fixes.append(f"Code: {frame['code_line']}")

        # Add testing recommendation
        fixes.append("Add unit tests to cover this error case")
        fixes.append("Add integration tests to prevent regression")

        return fixes

    def _find_related_issues(self, error_info: Dict) -> List[str]:
        """Find related GitHub issues"""
        if not self.github_token:
            return []

        related_issues = []

        try:
            g = Github(self.github_token)
            repo = g.get_repo(self.repo_name)

            # Search for issues with similar error
            error_type = error_info.get('error_type', '')
            if error_type:
                issues = repo.get_issues(state='all', labels=[f'error:{error_type}'])

                for issue in issues[:5]:  # Top 5 related issues
                    related_issues.append({
                        'number': issue.number,
                        'title': issue.title,
                        'state': issue.state,
                        'url': issue.html_url
                    })

        except Exception as e:
            logger.error(f"Error finding related issues: {e}")

        return related_issues

    def create_github_issue(self, analysis: Dict, crash_log: str) -> Optional[str]:
        """Create a GitHub issue with the crash analysis"""
        if not self.github_token:
            logger.error("GITHUB_TOKEN not set")
            return None

        try:
            g = Github(self.github_token)
            repo = g.get_repo(self.repo_name)

            # Generate issue title
            title = f"🐛 {analysis['error_type']}: {analysis.get('error_message', 'Crash in production')}"
            title = title[:100]  # Truncate if too long

            # Generate issue body
            body = self._generate_issue_body(analysis, crash_log)

            # Determine labels
            labels = ['bug', 'crash', f'error:{analysis["error_type"]}']
            if analysis['severity'] == 'critical':
                labels.append('severity:critical')
                labels.append('priority:high')

            # Check for duplicate
            existing_issues = repo.get_issues(state='all')
            for issue in existing_issues:
                if title.lower() in issue.title.lower():
                    logger.info(f"Similar issue already exists: #{issue.number}")
                    return issue.html_url

            # Create issue
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels
            )

            logger.info(f"✅ Created GitHub issue: {issue.html_url}")
            return issue.html_url

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return None

    def _generate_issue_body(self, analysis: Dict, crash_log: str) -> str:
        """Generate GitHub issue body from analysis"""
        body = "## 🐛 Crash Analysis\n\n"

        # Error summary
        body += f"### Error Type\n\n**{analysis['error_type']}**\n\n"
        if analysis.get('error_message'):
            body += f"**Message:** `{analysis['error_message']}`\n\n"

        # Severity
        body += f"### Severity\n\n{analysis['severity'].upper()}\n\n"

        # Responsible code
        if analysis['responsible_code']:
            body += "### 📍 Likely Responsible Code\n\n"

            for i, frame in enumerate(analysis['responsible_code'][:3], 1):
                body += f"**Frame {i}:** `{frame['file_path']}:{frame['line_number']}`\n\n"

                # Code context
                if 'code_context' in frame and 'context' in frame['code_context']:
                    body += "```python\n"
                    body += frame['code_context']['context']
                    body += "\n```\n\n"

                # Git blame
                if frame.get('git_blame'):
                    blame = frame['git_blame']
                    body += f"*Last modified by {blame['author_info']} (commit {blame['commit'][:7]})*\n\n"

        # Stack trace
        if analysis['stack_trace']:
            body += "### 📚 Stack Trace\n\n"
            body += "```python\n"
            for frame in analysis['stack_trace'][:10]:
                body += f'  File "{frame['file_path']}", line {frame['line_number']}, in {frame['function_name']}\n'
                if frame.get('code_line'):
                    body += f"    {frame['code_line']}\n"
            body += "```\n\n"

        # Suggested fixes
        if analysis['suggested_fixes']:
            body += "### 💡 Suggested Fixes\n\n"
            for fix in analysis['suggested_fixes']:
                body += f"- {fix}\n"
            body += "\n"

        # Related issues
        if analysis['related_issues']:
            body += "### 🔗 Related Issues\n\n"
            for issue in analysis['related_issues']:
                body += f"- #{issue['number']}: [{issue['title']}]({issue['url']}) ({issue['state']})\n"
            body += "\n"

        # Full crash log
        body += "### 📋 Full Crash Log\n\n"
        body += "<details>\n"
        body += "<summary>Click to expand</summary>\n\n"
        body += "```\n"
        body += crash_log[:2000]  # Truncate if too long
        if len(crash_log) > 2000:
            body += "\n... (truncated)"
        body += "```\n"
        body += "\n</details>\n"

        # Metadata
        body += "\n---\n\n"
        body += f"**Detected by:** Crash Log Analyzer Agent\n"
        body += f"**Analysis Date:** {analysis['timestamp']}\n"
        body += f"**Source:** {analysis['source']}\n"

        return body

    def watch_error_logs(self, log_file: str = None):
        """
        Continuously watch error logs and analyze new crashes

        Args:
            log_file: Path to log file to watch (if None, monitors from Sentry)
        """
        logger.info(f"👀 Watching error logs from {log_file or 'Sentry'}...")

        if log_file:
            self._watch_log_file(log_file)
        else:
            # Watch Sentry (if configured)
            self._watch_sentry()

    def _watch_log_file(self, log_file: str):
        """Watch a log file for new errors"""
        import time

        log_path = Path(log_file)

        if not log_path.exists():
            logger.error(f"Log file not found: {log_file}")
            return

        # Get current size
        last_size = log_path.stat().st_size

        logger.info(f"Monitoring {log_file} for new errors...")

        while True:
            time.sleep(60)  # Check every minute

            current_size = log_path.stat().st_size

            if current_size > last_size:
                # Read new content
                with open(log_path, 'r') as f:
                    f.seek(last_size)
                    new_content = f.read()

                # Check for errors in new content
                if 'ERROR' in new_content or 'CRITICAL' in new_content or 'Exception' in new_content:
                    logger.info("🚨 New error detected, analyzing...")

                    # Analyze the crash
                    analysis = self.analyze_crash_log(new_content, source=log_file)

                    # Create GitHub issue
                    self.create_github_issue(analysis, new_content)

                last_size = current_size

    def _watch_sentry(self):
        """Watch Sentry for new errors"""
        logger.info("Sentry monitoring not yet implemented")
        # TODO: Implement Sentry integration
        pass


def main():
    """Entry point for the agent"""
    import sys

    agent = CrashLogAnalyzer()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'analyze':
            # Analyze a crash log file
            if len(sys.argv) > 2:
                crash_log_file = sys.argv[2]

                with open(crash_log_file, 'r') as f:
                    crash_log = f.read()

                analysis = agent.analyze_crash_log(crash_log, source=crash_log_file)

                # Create GitHub issue
                agent.create_github_issue(analysis, crash_log)

                print(json.dumps(analysis, indent=2))

        elif command == 'watch':
            # Watch logs continuously
            log_file = sys.argv[2] if len(sys.argv) > 2 else None
            agent.watch_error_logs(log_file)

    else:
        print("Usage:")
        print("  python crash_analyzer.py analyze <crash_log_file>")
        print("  python crash_analyzer.py watch [log_file]")


if __name__ == '__main__':
    main()
