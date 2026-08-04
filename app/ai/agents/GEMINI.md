# GEMINI.md - AI Agent Development Mandates

This directory contains autonomous agents for code quality, testing, security, and performance.

## 🤖 Agent Philosophy
- **Augmentation, not Replacement:** Agents should assist human developers by providing findings and recommendations.
- **Traceability:** Every agent action must be logged with clear status (IDLE, RUNNING, COMPLETED, FAILED).
- **Safety First:** Agents that modify code must be run in a dry-run mode by default or require explicit human approval.

## 🛠 Framework Standards
- **Inheritance:** New agents MUST inherit from `app.ai.agents.agent_framework.BaseAgent`.
- **Config:** Every agent must have a detailed `AgentConfig` including category and priority.
- **Results:** Use the `AgentResult` dataclass to return findings. Ensure `raw_output` is captured for debugging.
- **Timeouts:** All agents must have a `timeout_seconds` to prevent rogue processes.

## 🔒 Security & Sanitization
- **LLM Safety:** If an agent uses an LLM, ensure all inputs are sanitized to prevent prompt injection.
- **Sandboxing:** Agents running shell commands should be restricted to the project root and monitored.
- **Secrets:** NEVER hardcode API keys or credentials in agent implementations. Use `app.core.config.settings`.

## 📂 Implementation Guide
1. **Define the Task:** Identify a repetitive task (e.g., "Find missing docstrings").
2. **Subclass BaseAgent:** Implement the `_run(self, context)` method.
3. **Register:** Add the agent to the `AgentOrchestrator` in `app.ai.agents/run_agents.py` (if it exists).
4. **Test:** Create a test case in `tests/ai/` to verify the agent's findings.

## ✅ Quality Checks
- **Error Handling:** Use try-except blocks within `_run` to ensure one agent's failure doesn't crash the orchestrator.
- **Metrics:** Capture execution time and number of findings in the `metrics` dictionary.
