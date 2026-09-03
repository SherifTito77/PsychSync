# 🚀 Quick Start Guide - AI Engineering Prompts

Get up and running with the AI Engineering Prompts tool in under 5 minutes!

## ⚡ 30-Second Setup

```bash
# Navigate to the prompts directory
cd app.ai/agents/prompts

# Install dependencies
pip install -r requirements.txt

# Verify installation
python prompt_engineer.py --version
```

That's it! You're ready to go.

---

## 🎯 5 Common Tasks

### 1️⃣ Browse All Prompts

```bash
python prompt_engineer.py list
```

**What you'll see:** A beautiful table with all 52 prompts, showing their complexity, estimated time, and scope.

---

### 2️⃣ Find Architecture Analysis Prompts

```bash
# List architecture category
python prompt_engineer.py list --category architecture

# Show specific prompt
python prompt_engineer.py show audit-architecture
```

**What you'll get:** Detailed architecture audit prompt with context, specific areas to analyze, and actionable recommendations.

---

### 3️⃣ Search for Performance Prompts

```bash
python prompt_engineer.py search "performance"
```

**Result:** All prompts related to performance optimization, including backend, frontend, and database performance.

---

### 4️⃣ Filter by Scope

```bash
# Backend prompts only
python prompt_engineer.py filter --scope backend

# Frontend prompts only
python prompt_engineer.py filter --scope frontend

# Database prompts only
python prompt_engineer.py filter --scope database
```

---

### 5️⃣ Interactive Mode (Recommended for Beginners)

```bash
python prompt_engineer.py interactive
```

**Features:**
- 📋 Browse categories
- 🔍 Search prompts
- 📝 View detailed prompts
- 💾 Export to files
- 🎯 Filter by scope/complexity

---

## 🌐 Launch Web Interface

```bash
python web_interface.py
```

Then open: **http://localhost:5000**

**Web Features:**
- 🎨 Beautiful modern UI
- 🔍 Real-time search
- 📊 Statistics dashboard
- 📥 One-click export
- 📱 Mobile-friendly

---

## 💡 Real-World Examples

### Example 1: Pre-Deployment Checklist

Before deploying to production:

```bash
# 1. Run architecture audit
python prompt_engineer.py show audit-architecture --export pre_deploy_audit.md

# 2. Check security
python prompt_engineer.py show auth-flow-improvements --export security_check.md

# 3. Review performance
python prompt_engineer.py show backend-performance --export perf_check.md

# 4. Check test coverage
python prompt_engineer.py show integration-test-gaps --export test_coverage.md
```

### Example 2: Tech Debt Sprint

For a technical debt-focused sprint:

```bash
# 1. Get refactoring roadmap
python prompt_engineer.py show refactoring-roadmap

# 2. Find dead code
python prompt_engineer.py show dead-code-detection

# 3. Analyze complexity
python prompt_engineer.py show complexity-analysis

# 4. Review dependencies
python prompt_engineer.py show dependency-analysis
```

### Example 3: Scaling Preparation

When preparing to scale:

```bash
# Filter for high-complexity architecture prompts
python prompt_engineer.py filter --complexity high

# Key prompts to review:
# - microservice-split
# - schema-evolution
# - enterprise-scalability
# - multi-tenant-plan
# - zero-downtime-deployment
```

---

## 🎓 Learning Path

### Week 1: Familiarization
```bash
# Day 1: Explore categories
python prompt_engineer.py list --categories

# Day 2: Try interactive mode
python prompt_engineer.py interactive

# Day 3: Export your first prompt
python prompt_engineer.py show api-validation-rules --export my_first_prompt.md
```

### Week 2: Integration
```bash
# Day 1: Search for your stack
python prompt_engineer.py search "fastapi"
python prompt_engineer.py search "react"

# Day 2: Filter by your role
python prompt_engineer.py filter --scope backend  # or frontend, api, etc.

# Day 3: Create your workflow
# Export prompts you use frequently
```

### Week 3: Customization
```bash
# Edit prompts_registry.yaml to add your own prompts
# Test your new prompts
python prompt_engineer.py show your-custom-prompt
```

---

## ⚙️ Configuration

### Change Registry Location

```bash
python prompt_engineer.py --registry /path/to/custom_registry.yaml list
```

### Set Up Alias (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias ai-prompts='cd /path/to/psychsync/app.ai/agents/prompts && python prompt_engineer.py'
alias ai-web='cd /path/to/psychsync/app.ai/agents/prompts && python web_interface.py'
```

Then use:
```bash
ai-prompts list
ai-prompts show audit-architecture
ai-web
```

---

## 📊 Prompt Statistics

| Metric | Value |
|--------|-------|
| Total Prompts | 52 |
| Categories | 7 |
| Avg. Duration | 12 min |
| High Complexity | 15 |
| Medium Complexity | 31 |
| Low Complexity | 6 |

---

## 🔧 Troubleshooting

### Issue: "Module not found"

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "Registry file not found"

```bash
# Make sure you're in the correct directory
pwd  # Should show .../psychsync/app.ai/agents/prompts

# Check if prompts_registry.yaml exists
ls -la prompts_registry.yaml
```

### Issue: Web interface won't start

```bash
# Check if port 5000 is available
lsof -i :5000

# Kill process using port 5000 (if needed)
kill -9 <PID>

# Or use a different port
# Edit web_interface.py and change port=5000 to port=5001
```

---

## 🎯 Next Steps

1. ✅ **Explore**: Run `python prompt_engineer.py interactive`
2. 📖 **Read**: Check the full [README.md](README.md)
3. 🌐 **Launch**: Start the web interface with `python web_interface.py`
4. 🤝 **Contribute**: Add your own prompts to the registry
5. 🔄 **Integrate**: Add to your CI/CD pipeline

---

## 💬 Tips & Tricks

### Tip 1: Create Prompt Playlists
Group frequently-used prompts:

```bash
# Create a file called my_playlist.sh
#!/bin/bash
python prompt_engineer.py show audit-architecture --export 01_architecture.md
python prompt_engineer.py show backend-performance --export 02_performance.md
python prompt_engineer.py show security-headers --export 03_security.md
```

### Tip 2: Use with AI Coding Tools
Export prompts and use them with Claude Code, GitHub Copilot, or ChatGPT:

```bash
python prompt_engineer.py show react-optimization --export prompt_for_ai.md
# Then paste the content into your AI tool
```

### Tip 3: Schedule Regular Audits
Add to your crontab for weekly automated checks:

```bash
# Every Sunday at midnight
0 0 * * 0 cd /path/to/app.ai/agents/prompts && ./weekly_audit.sh
```

---

## 📚 Resources

- **Full Documentation**: [README.md](README.md)
- **Prompt Registry**: [prompts_registry.yaml](prompts_registry.yaml)
- **API Documentation**: Run web interface and visit http://localhost:5000
- **Issue Tracker**: Report bugs or request features

---

**You're all set!** 🎉

Start exploring prompts and supercharge your engineering workflow.

```bash
python prompt_engineer.py interactive
```

---

*Last Updated: 2025-01-17*
*Version: 1.0.0*
