# 🤖 AI Engineering Prompts - PsychSync

A comprehensive, AI-powered engineering analysis and improvement system for the PsychSync codebase. This tool provides 50+ curated prompts for automated codebase analysis, architecture improvements, and best practices enforcement.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Available Prompts](#available-prompts)
- [Examples](#examples)
- [Web Interface](#web-interface)
- [Contributing](#contributing)

---

## ✨ Features

- **50+ Engineering Prompts** across 6 categories
- **CLI & Web Interface** for flexible usage
- **Smart Filtering** by scope, complexity, and category
- **Search Functionality** to find exactly what you need
- **Export Capabilities** to save prompts for documentation
- **Interactive Mode** for guided exploration
- **Beautiful Terminal UI** with rich formatting
- **Comprehensive Documentation** for each prompt

---

## 🔧 Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

1. **Navigate to the prompts directory:**
   ```bash
   cd app.ai/agents/prompts
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Make the CLI executable (Linux/Mac):**
   ```bash
   chmod +x prompt_engineer.py
   ```

4. **Verify installation:**
   ```bash
   python prompt_engineer.py --help
   ```

---

## 🚀 Quick Start

### 1. List All Categories

```bash
python prompt_engineer.py list --categories
```

**Output:**
```
╔══════════════════════════════════════════════════════════════╗
║ 🤖 PsychSync AI Engineering Prompts                          ║
║ Comprehensive AI-Powered Codebase Analysis                  ║
╚══════════════════════════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID                 ┃ Icon  ┃ Category Name           ┃ Description                                   ┃ Prompts ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ architecture        │ 🏗️    │ Architecture & Design   │ System architecture analysis and design...     │ 13      │
│ api                 │ 🔒    │ API & Security          │ API design, validation, and security...       │ 7       │
│ testing             │ 🧪    │ Testing & Quality       │ Test coverage, QA, and quality assurance      │ 6       │
│ frontend            │ ⚛️    │ Frontend Engineering    │ Frontend architecture, performance, and UX    │ 8       │
│ data                │ 📊    │ Data & Analytics        │ Data management, retention, and analytics     │ 6       │
│ devops              │ 🚀    │ DevOps & Deployment     │ Deployment, infrastructure, and operations    │ 10      │
│ risk                │ ⚠️    │ Risk & Governance       │ Risk analysis, compliance, and governance     │ 2       │
└────────────────────┴───────┴─────────────────────────┴────────────────────────────────────────────────┴─────────┘
```

### 2. View All Prompts

```bash
python prompt_engineer.py list
```

### 3. Show Prompt Details

```bash
python prompt_engineer.py show audit-architecture
```

### 4. Interactive Mode

```bash
python prompt_engineer.py interactive
```

---

## 📖 Usage Guide

### Command-Line Interface

#### List Commands

**List all categories:**
```bash
python prompt_engineer.py list --categories
```

**List all prompts:**
```bash
python prompt_engineer.py list
```

**List prompts in a category:**
```bash
python prompt_engineer.py list --category architecture
python prompt_engineer.py list --category frontend
python prompt_engineer.py list --category testing
```

#### Show Command

**View prompt details:**
```bash
python prompt_engineer.py show audit-architecture
python prompt_engineer.py show backend-performance
python prompt_engineer.py show react-optimization
```

**Export prompt to file:**
```bash
python prompt_engineer.py show audit-architecture --export architecture_audit.md
```

#### Search Command

**Search by keyword:**
```bash
python prompt_engineer.py search "performance"
python prompt_engineer.py search "security"
python prompt_engineer.py search "database"
```

#### Filter Command

**Filter by scope:**
```bash
python prompt_engineer.py filter --scope backend
python prompt_engineer.py filter --scope frontend
python prompt_engineer.py filter --scope api
python prompt_engineer.py filter --scope database
```

**Filter by complexity:**
```bash
python prompt_engineer.py filter --complexity low
python prompt_engineer.py filter --complexity medium
python prompt_engineer.py filter --complexity high
```

#### Statistics

**View registry statistics:**
```bash
python prompt_engineer.py stats
```

#### Interactive Mode

**Launch interactive mode:**
```bash
python prompt_engineer.py interactive
```

In interactive mode, you can:
1. List all categories
2. Browse by category
3. Search prompts
4. View prompt details
5. Filter by scope
6. Filter by complexity

---

## 🎯 Available Prompts

### 🏗️ Architecture & Design (13 prompts)

1. **audit-architecture** - Audit Architecture Bottlenecks
2. **backend-performance** - Backend Performance Improvement Plan
3. **refactoring-roadmap** - Refactoring Roadmap
4. **dependency-analysis** - Dependency Risk Analysis
5. **error-handling-standards** - Error Handling Standards
6. **microservice-split** - Microservice Splitting Plan
7. **async-conversion** - Async Task Conversion
8. **caching-strategy** - Caching Strategy Enhancement
9. **db-query-analysis** - Database Query Analysis
10. **schema-evolution** - Schema Evolution Plan
11. **observability-plan** - Observability Improvement Recommendations
12. **cpu-memory-optimization** - CPU/Memory Optimization Suggestions

### 🔒 API & Security (7 prompts)

1. **api-validation-rules** - API Input Validation Rules
2. **rate-limiting-review** - API Rate Limiting Review
3. **llm-api-docs** - LLM-Based API Documentation
4. **log-failure-analysis** - Backend Log Failure Pattern Analysis
5. **auth-flow-improvements** - Authentication Flow Improvements
6. **security-headers** - Security Headers for API Responses
7. **race-condition-detection** - Race Condition Detection

### 🧪 Testing & Quality (6 prompts)

1. **integration-test-gaps** - Integration Test Coverage Gaps
2. **regression-test-suite** - Automated Regression Test Suite
3. **ci-linting-rules** - CI Linting Rules
4. **qa-acceptance-criteria** - QA Acceptance Criteria
5. **combined-race-conditions** - Frontend & Backend Race Conditions
6. **load-testing-scenarios** - Load Testing Scenarios

### ⚛️ Frontend Engineering (8 prompts)

1. **state-management-audit** - State Management Anti-Patterns Audit
2. **react-optimization** - React Component Performance Optimization
3. **lazy-loading-strategy** - Lazy Loading Strategy
4. **global-vs-local-state** - Global vs Local State Evaluation
5. **bundle-size-optimization** - Bundle Size Reduction
6. **accessibility-improvements** - Frontend Accessibility Improvements
7. **ui-consistency-audit** - UI Consistency Audit
8. **css-architecture** - CSS Architecture Analysis

### 📊 Data & Analytics (6 prompts)

1. **data-retention-strategy** - Data Retention & Archiving Strategy
2. **async-job-queue** - Async Job Queue Evaluation
3. **team-analytics-model** - Team Analytics Data Model
4. **usage-score-formula** - Customer Usage Score Formula
5. **event-driven-roadmap** - Event-Driven Architecture Roadmap
6. **logging-taxonomy** - Logging Taxonomy & Naming Conventions

### 🚀 DevOps & Deployment (10 prompts)

1. **code-style-guide** - Code Style Guide
2. **pr-validation-rules** - Pull Request Validation Rules
3. **complexity-analysis** - Module Complexity Analysis
4. **dead-code-detection** - Dead Code & Unused Modules Detection
5. **feature-flagging-system** - Feature Flagging System Design
6. **multi-tenant-plan** - Multi-Tenant Architecture Plan
7. **zero-downtime-deployment** - Zero-Downtime Deployment Plan
8. **migration-rollback** - Automated Migration Rollback Strategy
9. **enterprise-scalability** - Enterprise Scalability Requirements

### ⚠️ Risk & Governance (2 prompts)

1. **risk-analysis** - Comprehensive Risk Analysis
2. **engineering-kpis** - Engineering KPIs for Performance & Reliability

---

## 💡 Examples

### Example 1: Pre-Deployment Architecture Audit

Before a major deployment, run a comprehensive architecture audit:

```bash
# View the architecture audit prompt
python prompt_engineer.py show audit-architecture

# Export for documentation
python prompt_engineer.py show audit-architecture --export pre_deployment_audit.md
```

### Example 2: Performance Optimization Sprint

For a performance-focused sprint:

```bash
# List all performance-related prompts
python prompt_engineer.py search "performance"

# View backend performance plan
python prompt_engineer.py show backend-performance

# View React optimization guide
python prompt_engineer.py show react-optimization

# Filter by performance scope
python prompt_engineer.py filter --scope performance
```

### Example 3: Security Review

For a security review:

```bash
# Search for security prompts
python prompt_engineer.py search "security"

# View authentication improvements
python prompt_engineer.py show auth-flow-improvements

# View API validation rules
python prompt_engineer.py show api-validation-rules
```

### Example 4: Tech Debt Cleanup

For technical debt reduction:

```bash
# View refactoring roadmap
python prompt_engineer.py show refactoring-roadmap

# Find dead code
python prompt_engineer.py show dead-code-detection

# Analyze complexity
python prompt_engineer.py show complexity-analysis
```

### Example 5: Scaling Preparation

When preparing for scaling:

```bash
# View scalability requirements
python prompt_engineer.py show enterprise-scalability

# Check database schema evolution
python prompt_engineer.py show schema-evolution

# Review caching strategy
python prompt_engineer.py show caching-strategy

# Plan microservice split
python prompt_engineer.py show microservice-split
```

---

## 🌐 Web Interface

A beautiful web interface is available for easier prompt browsing and execution.

### Start the Web Server

```bash
python web_interface.py
```

The web interface will be available at: **http://localhost:5000**

### Features

- 🎨 Modern, responsive UI
- 🔍 Real-time search and filtering
- 📋 Category browsing
- 📝 Detailed prompt views
- 💾 One-click export
- 🌙 Dark/light theme toggle
- 📱 Mobile-friendly design

### Web Interface Usage

1. **Browse**: Click on categories to view prompts
2. **Search**: Use the search bar to find specific prompts
3. **Filter**: Filter by scope, complexity, or category
4. **View**: Click on any prompt to see full details
5. **Export**: Download prompts as Markdown files

---

## 🛠️ Advanced Usage

### Custom Registry Path

Use a custom prompts registry:

```bash
python prompt_engineer.py --registry /path/to/custom_registry.yaml list
```

### Integration with CI/CD

Add prompt execution to your CI/CD pipeline:

```yaml
# .github/workflows/ai-analysis.yml
name: AI Engineering Analysis

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd app.ai/agents/prompts
          pip install -r requirements.txt

      - name: Run architecture audit
        run: |
          cd app.ai/agents/prompts
          python prompt_engineer.py show audit-architecture --export ../reports/architecture_audit.md

      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: ai-analysis-reports
          path: reports/
```

### Batch Export

Export all prompts to a directory:

```bash
#!/bin/bash
# export_all_prompts.sh

mkdir -p exported_prompts

for category in architecture api testing frontend data devops risk; do
  mkdir -p "exported_prompts/$category"
done

python prompt_engineer.py list | grep -E '^[a-z-]+' | awk '{print $1}' | while read prompt_id; do
  python prompt_engineer.py show "$prompt_id" --export "exported_prompts/${prompt_id}.md"
done
```

---

## 📊 Prompt Metrics

| Metric | Count |
|--------|-------|
| **Total Prompts** | 52 |
| **Categories** | 7 |
| **Low Complexity** | 6 |
| **Medium Complexity** | 31 |
| **High Complexity** | 15 |
| **Average Estimated Time** | 12 minutes |

---

## 🤝 Contributing

### Adding New Prompts

1. Edit `prompts_registry.yaml`
2. Add your prompt to the appropriate category:

```yaml
- id: "your-new-prompt"
  name: "Your Prompt Name"
  prompt: "Your detailed prompt text here..."
  complexity: "medium"  # low, medium, or high
  estimated_time: "10-12 min"
  scope: ["backend", "api"]  # Relevant scopes
```

3. Test your new prompt:
   ```bash
   python prompt_engineer.py show your-new-prompt
   ```

4. Submit a pull request

### Prompt Guidelines

- **Be Specific**: Prompts should be clear and actionable
- **Include Context**: Explain what to analyze and why
- **Provide Examples**: Include specific files or patterns to check
- **Estimate Complexity**: Help users understand the effort required
- **Tag Appropriately**: Use correct scope labels for filtering

---

## 📝 License

This tool is part of the PsychSync project.

---

## 🆘 Support

For issues, questions, or contributions, please refer to the main PsychSync documentation.

---

**Version:** 1.0.0
**Last Updated:** 2025-01-17
**Project:** PsychSync
