#!/usr/bin/env python3
"""
Autonomous Agent: PR Coverage Gatekeeper
Tests each incoming PR and rejects if coverage < 90%
Provides detailed coverage reports
"""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from git import Repo

# GitHub API
from github import Github, GithubException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agents/pr_coverage_tester.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PRCoverageTester:
    """Autonomous agent that tests PR coverage and rejects if below threshold"""

    def __init__(self):
        self.repo_path = Path(os.getcwd()).parent
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPOSITORY", "psychsync/psychsync")

        # Coverage requirements
        self.min_coverage = float(os.getenv("MIN_COVERAGE", "90.0"))
        self.min_file_coverage = float(os.getenv("MIN_FILE_COVERAGE", "80.0"))

        # Test configuration
        self.test_command = os.getenv(
            "TEST_COMMAND",
            "pytest tests/ --cov=app --cov-report=json --cov-report=term",
        )
        self.source_dirs = ["app/", "frontend/src/"]

        logger.info(
            f"🎯 Coverage thresholds: Overall {self.min_coverage}%, File {self.min_file_coverage}%"
        )

    def test_pr_coverage(self, pr_number: int) -> Dict[str, any]:
        """
        Test a specific PR's coverage
        Returns: Test results with coverage metrics
        """
        logger.info(f"🧪 Testing coverage for PR #{pr_number}...")

        if not self.github_token:
            logger.error("GITHUB_TOKEN not set")
            return {"success": False, "error": "Missing GITHUB_TOKEN"}

        try:
            g = Github(self.github_token)
            repo = g.get_repo(self.repo_name)
            pr = repo.get_pull(pr_number)

            # 1. Fetch PR changes
            changed_files = self._get_changed_files(pr)
            logger.info(f"Found {len(changed_files)} changed files")

            # 2. Checkout PR branch
            self._checkout_pr_branch(pr)

            # 3. Install dependencies
            self._install_dependencies()

            # 4. Run tests with coverage
            coverage_results = self._run_coverage_tests()

            # 5. Analyze coverage for changed files
            file_coverage = self._analyze_file_coverage(changed_files, coverage_results)

            # 6. Check if coverage meets requirements
            passes = self._check_coverage_thresholds(coverage_results, file_coverage)

            # 7. Post results as PR comment
            self._post_coverage_comment(pr, coverage_results, file_coverage, passes)

            # 8. Fail the PR if coverage too low
            if not passes["overall_pass"]:
                logger.info(
                    f"❌ PR #{pr_number} rejected: Coverage {passes['overall_coverage']:.1f}% < {self.min_coverage}%"
                )
                self._reject_pr(pr, passes)
                return {"success": False, "reason": "low_coverage", "passes": passes}
            else:
                logger.info(
                    f"✅ PR #{pr_number} passed: Coverage {passes['overall_coverage']:.1f}%"
                )
                return {"success": True, "passes": passes}

        except Exception as e:
            logger.error(f"Error testing PR #{pr_number}: {e}")
            return {"success": False, "error": str(e)}

    def _get_changed_files(self, pr) -> List[str]:
        """Get list of files changed in the PR"""
        changed_files = []

        for file in pr.get_files():
            # Only test source files (not tests, docs, etc.)
            if any(file.filename.startswith(src_dir) for src_dir in self.source_dirs):
                if file.filename.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                    changed_files.append(file.filename)

        return changed_files

    def _checkout_pr_branch(self, pr):
        """Checkout the PR branch locally"""
        branch_name = pr.head.ref

        logger.info(f"Checking out branch: {branch_name}")

        # Fetch the branch
        subprocess.run(
            ["git", "fetch", "origin", f"pull/{pr.number}/head:{branch_name}"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Checkout the branch
        subprocess.run(
            ["git", "checkout", branch_name],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        logger.info(f"Checked out {branch_name}")

    def _install_dependencies(self):
        """Install test dependencies"""
        logger.info("Installing dependencies...")

        # Backend dependencies
        subprocess.run(
            ["pip", "install", "-q", "-r", "requirements.txt"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["pip", "install", "-q", "-r", "requirements-dev.txt"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Frontend dependencies (if needed)
        frontend_path = self.repo_path / "frontend"
        if frontend_path.exists():
            subprocess.run(
                ["npm", "ci", "--silent"],
                cwd=frontend_path,
                check=True,
                capture_output=True,
            )

        logger.info("Dependencies installed")

    def _run_coverage_tests(self) -> Dict:
        """Run tests and collect coverage data"""
        logger.info("Running coverage tests...")

        try:
            # Run pytest with coverage
            result = subprocess.run(
                self.test_command.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            # Parse coverage output
            coverage_output = result.stdout + result.stderr

            # Parse coverage JSON if available
            coverage_file = self.repo_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                logger.info("Coverage tests completed")
                return {"raw_output": coverage_output, "json_data": coverage_data}
            else:
                # Parse from terminal output
                return self._parse_terminal_coverage(coverage_output)

        except Exception as e:
            logger.error(f"Coverage tests failed: {e}")
            raise

    def _parse_terminal_coverage(self, output: str) -> Dict:
        """Parse coverage from pytest terminal output"""
        coverage_data = {}

        # Extract overall coverage percentage
        match = re.search(r"total\s+(\d+)\s+\d+\s+(\d+)%", output)
        if match:
            coverage_data["total"] = {"percent_covered": float(match.group(2))}

        # Extract file-level coverage
        file_matches = re.findall(r"([^\s]+)\s+(\d+)\s+\d+\s+(\d+)%", output)
        coverage_data["files"] = {}
        for filename, lines, percent in file_matches:
            if any(src_dir in filename for src_dir in self.source_dirs):
                coverage_data["files"][filename] = {
                    "percent_covered": float(percent),
                    "num_statements": int(lines),
                }

        return {"raw_output": output, "json_data": coverage_data}

    def _analyze_file_coverage(
        self, changed_files: List[str], coverage_results: Dict
    ) -> Dict[str, float]:
        """Analyze coverage for specifically changed files"""
        file_coverage = {}

        coverage_json = coverage_results.get("json_data", {})
        files_data = coverage_json.get("files", {})

        for file_path in changed_files:
            if file_path in files_data:
                file_coverage[file_path] = files_data[file_path]["percent_covered"]
            else:
                # New file - needs to be fully tested
                file_coverage[file_path] = (
                    0.0 if self._file_has_tests(file_path) else None
                )

        return file_coverage

    def _file_has_tests(self, file_path: str) -> bool:
        """Check if there are test files for this source file"""
        # Convert source path to test path
        if "app/" in file_path:
            test_file = file_path.replace("app/", "tests/test_")
        elif "frontend/src/" in file_path:
            test_file = file_path.replace("frontend/src/", "frontend/src/__tests__/")
        else:
            return False

        test_path = self.repo_path / test_file
        return test_path.exists()

    def _check_coverage_thresholds(
        self, coverage_results: Dict, file_coverage: Dict[str, float]
    ) -> Dict:
        """Check if coverage meets all thresholds"""
        overall_coverage = 0.0
        if "json_data" in coverage_results:
            overall_coverage = (
                coverage_results["json_data"]
                .get("total", {})
                .get("percent_covered", 0.0)
            )

        # Check overall threshold
        overall_pass = overall_coverage >= self.min_coverage

        # Check file-level threshold
        file_failures = []
        for file_path, coverage in file_coverage.items():
            if coverage is not None and coverage < self.min_file_coverage:
                file_failures.append(
                    {
                        "file": file_path,
                        "coverage": coverage,
                        "required": self.min_file_coverage,
                    }
                )

        file_pass = len(file_failures) == 0

        return {
            "overall_coverage": overall_coverage,
            "overall_pass": overall_pass,
            "file_pass": file_pass,
            "file_failures": file_failures,
            "all_pass": overall_pass and file_pass,
        }

    def _post_coverage_comment(
        self, pr, coverage_results: Dict, file_coverage: Dict[str, float], passes: Dict
    ):
        """Post coverage report as PR comment"""
        comment = self._generate_coverage_report(
            coverage_results, file_coverage, passes
        )

        try:
            # Create or update comment
            issue = pr.as_issue()

            # Look for existing comment from this bot
            existing_comments = issue.get_comments()
            bot_comment_id = None

            for comment in existing_comments:
                if comment.user.type == "Bot" and "Coverage Report" in comment.body:
                    bot_comment_id = comment.id
                    break

            if bot_comment_id:
                # Update existing comment
                issue.get_comment(bot_comment_id).edit(comment)
                logger.info("Updated existing coverage comment")
            else:
                # Create new comment
                issue.create_comment(comment)
                logger.info("Posted new coverage comment")

        except Exception as e:
            logger.error(f"Failed to post coverage comment: {e}")

    def _generate_coverage_report(
        self, coverage_results: Dict, file_coverage: Dict[str, float], passes: Dict
    ) -> str:
        """Generate formatted coverage report"""
        overall_coverage = passes["overall_coverage"]

        # Status emoji
        if passes["all_pass"]:
            status = "✅ COVERAGE PASSED"
        else:
            status = "❌ COVERAGE FAILED"

        report = f"""## 📊 Coverage Report

{status}

### Overall Coverage: **{overall_coverage:.1f}%** (Required: {self.min_coverage}%)

"""

        if not passes["overall_pass"]:
            report += f"⚠️ Overall coverage is **{self.min_coverage - overall_coverage:.1f}%** below threshold!\n\n"

        # File-level coverage
        if file_coverage:
            report += "### 📁 File-Level Coverage\n\n"
            report += "| File | Coverage | Required | Status |\n"
            report += "|------|----------|----------|--------|\n"

            for file_path, coverage in file_coverage.items():
                if coverage is not None:
                    status_emoji = "✅" if coverage >= self.min_file_coverage else "❌"
                    report += f"| {file_path} | {coverage:.1f}% | {self.min_file_coverage}% | {status_emoji} |\n"
                else:
                    report += f"| {file_path} | N/A | {self.min_file_coverage}% | ⚠️ No tests |\n"

            # Show failing files
            if passes["file_failures"]:
                report += "\n### ❌ Files Below Threshold\n\n"
                for failure in passes["file_failures"]:
                    report += f"- **{failure['file']}**: {failure['coverage']:.1f}% (required: {failure['required']}%)\n"

        # Coverage breakdown
        if "json_data" in coverage_results and "files" in coverage_results["json_data"]:
            report += "\n### 📈 Detailed Coverage Breakdown\n\n"

            files = coverage_results["json_data"]["files"]
            sorted_files = sorted(files.items(), key=lambda x: x[1]["percent_covered"])

            report += "| File | Statements | Missed | Coverage |\n"
            report += "|------|------------|--------|----------|\n"

            for file_path, data in sorted_files[:20]:  # Top 20 files
                if any(src_dir in file_path for src_dir in self.source_dirs):
                    statements = data["num_statements"]
                    missed = data["num_missing"]
                    coverage = data["percent_covered"]
                    report += (
                        f"| {file_path} | {statements} | {missed} | {coverage:.1f}% |\n"
                    )

            if len(sorted_files) > 20:
                report += f"| ... and {len(sorted_files) - 20} more files |\n"

        # Recommendations
        report += "\n### 💡 Recommendations\n\n"

        if not passes["overall_pass"]:
            report += "1. ❗ Increase overall test coverage to meet the 90% threshold\n"

        if passes["file_failures"]:
            report += "2. ❗ Add tests for files with low coverage (listed above)\n"
            report += "3. ❗ Ensure new code has corresponding tests\n"
        else:
            report += "1. ✅ All files meet minimum coverage requirements\n"

        report += "\n---\n\n"
        report += f"**Tested by:** PR Coverage Tester Agent\n"
        report += f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        report += f"**PR:** #{pr.number}\n"

        return report

    def _reject_pr(self, pr, passes: Dict):
        """Reject the PR by failing status checks"""
        try:
            # Create failing status check
            pr.create_status(
                state="failure",
                context=f"coverage/{self.min_coverage}%",
                description=f"Coverage {passes['overall_coverage']:.1f}% < {self.min_coverage}%",
                target_url="https://github.com/psychsync/psychsync/actions",
            )

            # Also add labels
            pr.add_to_labels("coverage: fail", "needs: tests")

            logger.info(f"PR #{pr.number} rejected due to low coverage")

        except Exception as e:
            logger.error(f"Failed to reject PR: {e}")

    def watch_prs(self):
        """Continuously watch for new PRs and test them"""
        logger.info("👀 Watching for new PRs...")

        if not self.github_token:
            logger.error("GITHUB_TOKEN not set")
            return

        g = Github(self.github_token)
        repo = g.get_repo(self.repo_name)

        # Get open PRs
        open_prs = repo.get_pulls(state="open")

        for pr in open_prs:
            # Skip if already tested
            if self._already_tested(pr):
                logger.info(f"PR #{pr.number} already tested, skipping")
                continue

            logger.info(f"🧪 Testing PR #{pr.number}: {pr.title}")

            # Test the PR
            result = self.test_pr_coverage(pr.number)

            # Mark as tested
            self._mark_as_tested(pr)

    def _already_tested(self, pr) -> bool:
        """Check if PR was already tested by this agent"""
        for comment in pr.get_issues_comments():
            if comment.user.type == "Bot" and "Coverage Report" in comment.body:
                return True
        return False

    def _mark_as_tested(self, pr):
        """Mark PR as tested (by adding a label)"""
        try:
            # The comment itself serves as the mark
            pass
        except Exception as e:
            pass


def main():
    """Entry point for the agent"""
    import sys

    agent = PRCoverageTester()

    # Check if PR number provided
    if len(sys.argv) > 1:
        pr_number = int(sys.argv[1])
        result = agent.test_pr_coverage(pr_number)
        print(json.dumps(result, indent=2))
    else:
        # Watch mode
        agent.watch_prs()


if __name__ == "__main__":
    main()
