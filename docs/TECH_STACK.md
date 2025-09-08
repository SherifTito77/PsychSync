# PsychSync – Tech Stack

This document captures the finalized technology decisions, pinned versions, and supporting tools for the PsychSync SaaS project.

---

## Core Technologies

### Frontend
- **Framework:** React 18
- **Language:** TypeScript
- **Runtime:** Node.js 18 (LTS)
- **Package Manager:** npm 9+

### Backend
- **Framework:** FastAPI 0.100+
- **Language:** Python 3.11
- **Testing:** pytest

### Database
- **Primary DB:** PostgreSQL 15
- **ORM:** SQLAlchemy / psycopg2

### AI / ML
- **Language:** Python (within backend services)
- **Libraries:** scikit-learn, pandas, numpy (pinned in `requirements.txt`)

### DevOps
- **Version Control:** GitHub + Azure DevOps (mirrored repo)
- **Containerization:** Docker (Alpine-based images)
- **CI/CD:** GitHub Actions
- **Deployment Config:** `azure-pipelines.yml`

### Monitoring & Error Tracking
- **Error Tracking:** Sentry
- **Monitoring (future-ready):** Grafana + Prometheus

---

## Tooling
- **Editor:** Visual Studio Code (recommended extensions: Python, Prettier, ESLint)
- **Formatting & Linting:**
  - Python → Black, Flake8
  - JavaScript/TypeScript → Prettier, ESLint
- **Pre-commit hooks:** Configured via `.pre-commit-config.yaml`

---

## Version Pinning
- **Python:** 3.11.x
- **React:** 18.x
- **Node.js:** 18.x (LTS)
- **FastAPI:** 0.100+
- **PostgreSQL:** 15.x

> All dependencies are locked via `requirements.txt` and `package-lock.json`.

---

## Notes
- Keep stack minimal due to hardware limitations (MacBook Pro 2015, low disk space).
- Kubernetes is deferred until later scaling phases (use Docker Compose locally).
