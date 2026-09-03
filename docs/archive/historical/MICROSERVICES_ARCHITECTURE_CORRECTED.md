# ✅ Microservices Architecture - Corrected

## 📊 PsychSync Microservices Deployment

**Date**: 2026-01-17
**Status**: All services operational

---

## 🎯 Service Architecture

PsychSync now runs on a **microservices architecture** with services properly separated across different ports:

```
┌─────────────────────────────────────────────────────────────┐
│                    PsychSync Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │   Main Application    │  │  AI Engineering      │         │
│  │   Port: 8000         │  │  Prompts Service     │         │
│  │                      │  │  Port: 5000          │         │
│  │  Core Features:      │  │                      │         │
│  │  - Auth              │  │  50+ Prompts:        │         │
│  │  - Users             │  │  - Architecture      │         │
│  │  - Assessments       │  │  - API & Security    │         │
│  │  - Clinical          │  │  - Testing           │         │
│  │  - Teams             │  │  - Frontend          │         │
│  │                      │  │  - Data & Analytics  │         │
│  └──────────────────────┘  │  - DevOps            │         │
│                           └──────────────────────┘         │
│                                                               │
│  ┌──────────────────────┐                                    │
│  │  AI Agents Service   │                                    │
│  │  Port: 5002          │                                    │
│  │                      │                                    │
│  │  20 Automation:      │                                    │
│  │  - Security (3)      │                                    │
│  │  - Development (8)   │                                    │
│  │  - Operations (9)    │                                    │
│  └──────────────────────┘                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Service Details

### 1. Main Application
- **Port**: 8000
- **URL**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Purpose**: Core PsychSync SaaS platform
- **Features**:
  - Authentication & authorization
  - User management
  - Clinical assessments
  - Team management
  - Analytics & reporting

### 2. AI Engineering Prompts Service
- **Port**: 5000
- **URL**: http://localhost:5000
- **Directory**: `app.ai/agents/prompts/`
- **Purpose**: 50+ curated engineering analysis prompts
- **Categories**:
  - Architecture & Design (13 prompts)
  - API & Security (7 prompts)
  - Testing & Quality (6 prompts)
  - Frontend Engineering (8 prompts)
  - Data & Analytics (6 prompts)
  - DevOps & Deployment (10 prompts)
  - Risk & Governance (2 prompts)

**Usage**:
```bash
cd app.ai/agents/prompts
python web_interface.py
# Access at http://localhost:5000
```

### 3. AI Agents Service
- **Port**: 5002
- **URL**: http://localhost:5002
- **Documentation**: http://localhost:5002/docs
- **Purpose**: 20 AI-powered automation agents
- **Categories**:
  - Security Agents (3):
    - Security Headers Validator
    - Encryption Strategy Advisor
    - Unsafe Script Detector
  - Development Agents (8):
    - Coding Style Enforcer
    - Performance Regression Detector
    - Localization Key Detector
    - Slow Endpoint Tracker
    - Release Notes Generator
    - Permission Gap Detector
    - Test Coverage Reporter
    - Refactoring Target Proposer
  - Operations Agents (9):
    - UX Telemetry Tracker
    - Environment Config Detector
    - Incident Mitigation Planner
    - Dependency Updater
    - PR-Jira Mapper
    - Uptime Monitor
    - Stability Score Calculator
    - Architecture Drift Detector
    - Bug Environment Creator

**Usage**:
```bash
./start-ai-agents.sh
# Or directly:
python3 app.ai.agents_service.py
# Access at http://localhost:5002/docs
```

---

## 🚀 Quick Start

### Start All Services

```bash
# Terminal 1: Main Application (already running)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: AI Engineering Prompts (already running)
cd app.ai/agents/prompts
python web_interface.py

# Terminal 3: AI Agents Service (already running)
./start-ai-agents.sh
```

### Access Points

```bash
# Main Application
curl http://localhost:8000/health

# AI Engineering Prompts
curl http://localhost:5000/

# AI Agents Service
curl http://localhost:5002/health
```

---

## 📚 Documentation

- **Main App**: http://localhost:8000/docs
- **AI Prompts**: http://localhost:5000 (Web interface)
- **AI Agents**: http://localhost:5002/docs
- **AI Agents README**: `AI_AGENTS_SERVICE_README.md`
- **AI Prompts README**: `app.ai/agents/prompts/README.md`

---

## ✅ Verification

All services are currently operational:

```bash
# Check service status
lsof -i :8000  # Main Application
lsof -i :5000  # AI Engineering Prompts
lsof -i :5002  # AI Agents Service
```

---

## 🔗 Architecture Benefits

### Microservices Advantages

1. **Independent Deployment**: Each service can be deployed independently
2. **Fault Isolation**: Failure in one service doesn't affect others
3. **Technology Diversity**: Services can use different tech stacks
4. **Scalability**: Each service scales based on its own load
5. **Development Speed**: Teams can work on services independently

### Service Communication

- **Shared Database**: PostgreSQL accessed by all services
- **Shared Cache**: Redis for caching across services
- **Shared Authentication**: JWT tokens for API security
- **File System**: Shared logs and storage

---

## 🎉 Summary

**Services Running**: 3
- Main Application: Port 8000 ✅
- AI Engineering Prompts: Port 5000 ✅
- AI Agents Service: Port 5002 ✅

**Total Agents/Prompts**: 72
- Engineering Prompts: 52
- Automation Agents: 20

**Architecture**: Microservices ✅

---

**Generated**: 2026-01-17
**Status**: Operational
**Version**: 2.0.0 (Corrected)
