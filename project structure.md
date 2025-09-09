psychsync/
├── README.md
├── .gitignore
├── .env.example
├── azure-pipelines.yml
├── docs/                         # Documentation (setup, tech stack, ERDs)
│   ├── DEV_SETUP.md
│   ├── TECH_STACK.md
│   ├── ERDs/
│   │   ├── main.png
│   │   └── …
│   └── guides/
│       ├── database_playbook.md
│       ├── deployment_guide.md
│       └── api_reference.md
├── infra/                        # Infrastructure as Code (IaC + CI/CD)
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   └── docker-compose.yml
│   ├── k8s/                      # If you later go Kubernetes
│   └── scripts/
│       └── migrate.sh            # DB migrations automation
├── backend/
│   ├── alembic/                  # Alembic migrations
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── core/                  # Config & core utils
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/                    # Database models & sessions
│   │   │   ├── base.py
│   │   │   ├── models/
│   │   │   │   ├── user.py
│   │   │   │   ├── assessment.py
│   │   │   │   └── …
│   │   │   └── session.py
│   │   ├── api/                   # Routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── users.py
│   │   │   │   ├── assessments.py
│   │   │   │   └── …
│   │   ├── services/              # Business logic
│   │   ├── schemas/               # Pydantic schemas
│   │   └── tests/                 # Backend tests
│   ├── requirements.txt
│   └── pyproject.toml             # (Optional if moving to Poetry)
├── frontend/                      # React/Vite frontend
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── ai/                            # AI/ML components
│   ├── processors/
│   │   ├── assessment_processor.py
│   │   └── …
│   ├── engine.py
│   └── notebooks/                 # Jupyter notebooks for experiments
├── static/                        # Shared static files (served in prod by CDN)
├── templates/                     # Shared HTML/Jinja templates
└── tests/                         # End-to-end & integration tests
    ├── backend/
    ├── frontend/
    └── load/
