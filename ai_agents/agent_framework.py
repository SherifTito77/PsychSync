"""
AI Agent Framework for PsychSync
Autonomous agents for code quality, testing, and optimization
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import ast
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Priority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_name: str
    status: AgentStatus
    timestamp: datetime
    duration_seconds: float
    findings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    raw_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "findings_count": len(self.findings),
            "findings": self.findings,
            "metrics": self.metrics,
            "recommendations_count": len(self.recommendations),
            "recommendations": self.recommendations,
            "errors_count": len(self.errors),
            "errors": self.errors,
            "raw_output_length": len(self.raw_output)
        }


@dataclass
class AgentConfig:
    """Configuration for an AI agent"""
    name: str
    description: str
    category: str  # code_quality, testing, security, performance, documentation
    enabled: bool = True
    auto_schedule: bool = False
    schedule_interval: Optional[str] = None  # cron format
    priority: Priority = Priority.MEDIUM
    timeout_seconds: int = 300
    max_retries: int = 3
    required_tools: List[str] = field(default_factory=list)


class BaseAgent:
    """Base class for all AI agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
        self.logger = logging.getLogger(f"agent.{config.name}")

    def execute(self, context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute the agent's primary task

        Args:
            context: Execution context with project info, configs, etc.

        Returns:
            AgentResult with findings and recommendations
        """
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        self.execution_count += 1

        self.logger.info(f"Starting execution: {self.config.name}")

        try:
            # Run the actual implementation
            findings, metrics, recommendations = self._run(context or {})

            duration = time.time() - start_time
            self.status = AgentStatus.COMPLETED
            self.last_execution = datetime.now()

            result = AgentResult(
                agent_name=self.config.name,
                status=self.status,
                timestamp=self.last_execution,
                duration_seconds=duration,
                findings=findings,
                metrics=metrics,
                recommendations=recommendations,
                raw_output=str(findings)
            )

            self.logger.info(
                f"Execution completed: {self.config.name} "
                f"in {duration:.2f}s - {len(findings)} findings"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            self.status = AgentStatus.FAILED

            self.logger.error(f"Execution failed: {self.config.name} - {e}")

            return AgentResult(
                agent_name=self.config.name,
                status=self.status,
                timestamp=datetime.now(),
                duration_seconds=duration,
                errors=[str(e)]
            )

    def _run(self, context: Dict[str, Any]) -> tuple:
        """
        Override this method in subclasses

        Returns:
            Tuple of (findings, metrics, recommendations)
        """
        raise NotImplementedError("Subclasses must implement _run method")

    def can_run(self) -> bool:
        """Check if agent has all required tools and dependencies"""
        return self.config.enabled


class AgentOrchestrator:
    """Orchestrates multiple AI agents"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_history: List[AgentResult] = []
        self.logger = logging.getLogger("orchestrator")

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.config.name] = agent
        self.logger.info(f"Registered agent: {agent.config.name}")

    def execute_agent(
        self,
        agent_name: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Execute a specific agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent not found: {agent_name}")

        agent = self.agents[agent_name]
        if not agent.can_run():
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.SKIPPED,
                timestamp=datetime.now(),
                duration_seconds=0,
                errors=["Agent cannot run - missing dependencies or disabled"]
            )

        result = agent.execute(context)
        self.execution_history.append(result)
        return result

    def execute_all(
        self,
        category: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, AgentResult]:
        """Execute all agents or all agents in a category"""
        results = {}

        for name, agent in self.agents.items():
            if category and agent.config.category != category:
                continue

            if agent.can_run():
                results[name] = self.execute_agent(name, context)

        return results

    def get_report(self, last_n: int = 50) -> Dict[str, Any]:
        """Generate execution report"""
        recent_results = self.execution_history[-last_n:]

        # Calculate statistics
        total_executions = len(recent_results)
        successful = sum(1 for r in recent_results if r.status == AgentStatus.COMPLETED)
        failed = sum(1 for r in recent_results if r.status == AgentStatus.FAILED)

        # Group by category
        by_category = {}
        for result in recent_results:
            agent = self.agents.get(result.agent_name)
            if agent:
                cat = agent.config.category
                if cat not in by_category:
                    by_category[cat] = {"total": 0, "successful": 0, "findings": 0}
                by_category[cat]["total"] += 1
                if result.status == AgentStatus.COMPLETED:
                    by_category[cat]["successful"] += 1
                by_category[cat]["findings"] += len(result.findings)

        return {
            "summary": {
                "total_executions": total_executions,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total_executions*100):.1f}%" if total_executions > 0 else "N/A"
            },
            "by_category": by_category,
            "recent_results": [r.to_dict() for r in recent_results[:10]]
        }

    def save_report(self, filepath: str):
        """Save execution report to file"""
        report = self.get_report()

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Report saved to: {filepath}")


# Utility functions for agents
def run_command(cmd: List[str], cwd: Optional[Path] = None) -> tuple:
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def find_files(
    project_root: Path,
    pattern: str,
    exclude_patterns: List[str] = None
) -> List[Path]:
    """Find files matching a pattern"""
    exclude_patterns = exclude_patterns or [
        "node_modules",
        ".git",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        "venv",
        ".venv"
    ]

    files = []
    for file_path in project_root.rglob(pattern):
        # Check if file should be excluded
        if any(excl in str(file_path) for excl in exclude_patterns):
            continue
        files.append(file_path)

    return files


def read_file(file_path: Path) -> str:
    """Read file contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return ""


def analyze_code_complexity(code: str) -> Dict[str, int]:
    """Analyze code complexity metrics"""
    try:
        tree = ast.parse(code)

        functions = 0
        classes = 0
        imports = 0
        lines_of_code = len(code.split('\n'))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions += 1
            elif isinstance(node, ast.ClassDef):
                classes += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports += 1

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "lines_of_code": lines_of_code,
            "complexity_score": functions + classes * 2 + imports
        }
    except Exception as e:
        return {"error": "Could not parse code"}


if __name__ == "__main__":
    # Test the framework
    logger.info("AI Agent Framework initialized")
    logger.info(f"Project root: {Path.cwd()}")
