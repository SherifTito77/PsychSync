
# PsychSync — Practical Execution Playbook (Beginner Friendly)

This playbook turns your PDF plan into step‑by‑step actions you can execute even if you’re new to coding. Follow it in order. Copy/paste shell commands exactly. Everything assumes **macOS** with **VS Code**, **Docker Desktop**, and **GitHub**.

> Tip: Wherever you see `YOUR_ORG` or `yourname`, replace with your own values.

---

## 0) One‑Time Setup (30–60 min)

1. **Install core tools**
   - Install Homebrew (if you don’t have it):  
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
   - Install tools:  
     ```bash
     brew install --cask visual-studio-code docker
     brew install git python node postgresql
     ```

2. **Create folders**
   ```bash
   mkdir -p ~/psychsync/{app,frontend,infra,docs}
   cd ~/psychsync
   ```

3. **Create GitHub repos (web UI)**
   - Create a GitHub **organization** (optional) or just use your account.
   - Create two repos: `psychsync-app`, `psychsync-frontend`.
   - Clone them locally:
     ```bash
     cd ~/psychsync
     git clone https://github.com/YOUR_ORG/psychsync-app app
     git clone https://github.com/YOUR_ORG/psychsync-frontend frontend
     ```

4. **VS Code extensions (from VS Code marketplace)**
   - Python, Pylance
   - Docker
   - GitHub Pull Requests and Issues
   - Thunder Client (or use Postman app)
   - ESLint, Prettier (frontend)

---

## 1) app Skeleton (FastAPI) — Day 1

1. **Create virtualenv & install deps**
   ```bash
   cd ~/psychsync/app
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary alembic pydantic-settings python-multipart passlib[bcrypt] pyjwt fastapi-users[sqlalchemy] email-validator
   ```

2. **Project structure**
   ```bash
   mkdir -p app/{api,core,models,schemas,services,auth}
   touch app/{__init__.py,main.py}
   ```

3. **Environment variables**
   ```bash
   touch .env
   echo 'DATABASE_URL=postgresql+asyncpg://psychsync_user:password@localhost/psychsync_db' >> .env
   echo 'SECRET_KEY='$(python -c 'import secrets; print(secrets.token_urlsafe(32))') >> .env
   ```

4. **Local Postgres using Docker**
   ```bash
   docker run --name pg-psychsync -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=psychsync -p 5432:5432 -d postgres:16
   ```

5. **SQLAlchemy base & Alembic**
   ```bash
   alembic init alembic
   ```
   - Edit `alembic.ini` and set `sqlalchemy.url` to `DATABASE_URL` (use env var via `script.py.mako` or set directly while learning).
   - Create `app/models/base.py`:
     ```python
     from sqlalchemy.orm import DeclarativeBase
     class Base(DeclarativeBase):
         pass
     ```

6. **User model (minimal)**
   ```python
   # app/models/user.py
   from sqlalchemy import Column, UUID(as_uuid=True), String, Boolean
   from .base import Base
   class User(Base):
       __tablename__ = "users"
       id = Column(UUID(as_uuid=True), primary_key=True, index=True)
       email = Column(String, unique=True, index=True, nullable=False)
       hashed_password = Column(String, nullable=False)
       is_active = Column(Boolean, default=True)
       is_superuser = Column(Boolean, default=False)
   ```

7. **Generate & run migration**
   ```bash
   alembic revision -m "create users" --autogenerate
   alembic upgrade head
   ```

8. **FastAPI app bootstrap**
   ```python
   # app/main.py
   from fastapi import FastAPI
   app = FastAPI(title="PsychSync API")
   @app.get("/health")
   def health():
       return {"status": "ok"}
   ```
   Run:
   ```bash
   uvicorn app.main:app --reload
   # visit http://127.0.0.1:8000/docs
   ```

---

## 2) Auth (Email/Password + JWT) — Day 2

> We’ll use **fastapi-users** to simplify auth.

1. **Wire fastapi-users**
   ```bash
   pip install fastapi-users[sqlalchemy]
   ```

2. **Create user DB adapter & router**
   - Follow fastapi-users docs pattern:
     - user table (already created)
     - `UserRead`, `UserCreate` schemas
     - JWT strategy using your `SECRET_KEY`
   - Example files to create:
     - `app/auth/deps.py`
     - `app/auth/schemas.py`
     - `app/auth/users.py`
   - Register routes in `main.py`:
     ```python
     from fastapi import FastAPI
     from app.auth.users import auth_router, users_router
     app = FastAPI()
     app.include_router(auth_router, prefix="/auth", tags=["auth"])
     app.include_router(users_router, prefix="/users", tags=["users"])
     ```

3. **Test with Thunder Client/Postman**
   - `POST /auth/register` `{email, password}`
   - `POST /auth/jwt/login` (form-data: username, password) ⇒ returns `access_token`

---

## 3) Frontend Skeleton (React + Vite + TS) — Day 3

1. **Create project**
   ```bash
   cd ~/psychsync/frontend
   npm create vite@latest . -- --template react-ts
   npm install
   npm install react-router-dom axios zustand
   npm install -D eslint prettier @types/node
   ```

2. **Auth state & API client**
   - Create `src/lib/api.ts` (axios instance with baseURL `http://localhost:8000` and token header).
   - Create `src/store/auth.ts` with Zustand to store token & user.

3. **Routes**
   - `Login.tsx`, `Register.tsx`, `Dashboard.tsx`
   - ProtectedRoute component that checks token in store before rendering.

4. **Run**
   ```bash
   npm run dev
   # visit http://127.0.0.1:5173
   ```

---

## 4) Core Data Models — Day 4–5

Create minimal ERD (start simple, expand later):

- **User** (id, email, hashed_password, is_active, is_superuser)
- **Team** (id, name, owner_id)
- **Membership** (id, team_id, user_id, role)
- **Framework** (id, name, description)
- **Question** (id, framework_id, text, scale_min, scale_max, reverse_scored?)
- **Response** (id, question_id, user_id, team_id, score)
- **Result** (id, user_id, framework_id, payload_json)

**Steps**  
1. Create SQLAlchemy models for each table.  
2. `alembic revision --autogenerate -m "core tables"` then `alembic upgrade head`.  
3. Seed frameworks & questions using CSV:
   ```bash
   mkdir -p seed && touch seed/questions.csv
   # Put headers: framework,name,text,scale_min,scale_max,reverse
   # Add 10–20 rows to start
   ```
   Write a small `seed.py` to read CSV and insert records.

---

## 5) Team Management (Week 3 from your plan) — Day 6–7

1. **Endpoints**
   - `POST /teams` (name)
   - `GET /teams` (list for current user)
   - `GET /teams/{id}`
   - `PATCH /teams/{id}` (rename)
   - `DELETE /teams/{id}` (safe delete)
   - `POST /teams/{id}/members` (add by email + role)
   - `DELETE /teams/{id}/members/{userId}`

2. **Frontend**
   - Team list page + “Create Team” dialog
   - Team detail page: members table (add/remove) + roles

3. **Permissions**
   - Only owner can delete team; members can view.

---

## 6) Assessment Engine (Weeks 4–5) — Days 8–12

1. **Deliver questions**
   - `GET /assessments/start?framework=MBTI&team_id=...` returns list of questions with IDs.
2. **Record responses**
   - `POST /assessments/submit` body: `[ {question_id, score}, ... ]`
3. **Scoring (start rule‑based)**
   - **MBTI**: map answers to 4 dichotomies (E/I, S/N, T/F, J/P).  
   - **Big Five**: average per trait (O,C,E,A,N) with reverse‑scored items.  
   - **DISC**: score per quadrant (D, I, S, C).  
   Store in `Result.payload_json` (e.g., `{ "MBTI": "INTJ", "BigFive": {...} }`).

4. **Results API & UI**
   - `GET /results/me?framework=...`  
   - Charts in frontend (Recharts or chart.js) to show profiles + comparisons.  

5. **Exports**
   - `GET /results/{id}/export?format=pdf|csv` (start with CSV).

---

## 7) Basic Analytics Dashboard (Week 6) — Days 13–14

1. **app metrics endpoints**
   - `GET /metrics/team/{id}` returns:
     - compatibility_score (0–100, simple average to start)
     - type distribution (counts per MBTI/BigFive)
     - trend (average changes over time)

2. **Frontend dashboard**
   - Metric cards + pie/bar charts; team selector.

---

## 8) Team Optimization (Week 7) — Days 15–16

Start with a **simple heuristic** (no ML yet):
- Reward diversity across MBTI letters.
- Penalize extreme imbalance (e.g., all `I`).
- Score = +1 for each letter diversity, −1 for repeated imbalances.

**Endpoints**
- `POST /optimize/team` with team members ⇒ returns ranked recommendations (e.g., “invite an E and a J profile”).

---

## 9) Advanced Analytics (Week 8) — Days 17–18

- Add **trend detection** (moving averages per trait).  
- Add **team health score** (combine compatibility and variance).  
- Implement a simple **predictive model** later; for now, produce rule‑based insights.

---

## 10) Integrations (Weeks 9–10) — Days 19–22

**Slack**
1. Create a Slack App at api.slack.com → Features → **OAuth & Permissions**: add `chat:write` scope.
2. Install to workspace; copy **Bot User OAuth Token**.
3. app: add `/integrations/slack/test` that posts a message to a channel using the token.

**Email**
1. Create a SendGrid account. Get API key.
2. Add `/integrations/email/send` to send onboarding emails.

**Calendar (Google)**
1. Create a Google Cloud project → OAuth consent (internal) → create credentials.
2. Use the official client to create events/reminders from your app.

---

## 11) Mobile & PWA (Week 11) — Days 23–24

1. Add a `manifest.json` and service worker (`vite-plugin-pwa`).
2. Audit with Chrome Lighthouse (PWA tab).  
3. Ensure all assessment pages are **touch‑friendly**.

---

## 12) Security & Compliance (Week 12) — Days 25–26

1. **GDPR starter**
   - `GET /me/export` (zip of user data JSON/CSVs)
   - `DELETE /me` (soft-delete, then background purge)
2. **Audit logs**
   - Record login, assessment submission, member changes.
3. **SSO** (later): document plan; start with email/password.

---

## 13) Testing & QA (Weeks 13–16) — Days 27–32

1. **app**
   ```bash
   pip install pytest pytest-asyncio httpx
   pytest -q
   ```
   - Aim for tests for auth, teams, assessments.

2. **Frontend**
   ```bash
   npm install -D vitest @testing-library/react @testing-library/jest-dom cypress
   npx cypress open
   ```

3. **Performance**
   - Use **k6** (brew install k6) and write a simple script to hit `/assessments/start` and `/submit`.

4. **Bug bash & polish**
   - Do a 2‑hour session clicking through all flows; log issues in GitHub.

---

## 14) Deploy & Launch (Weeks 17–20) — Days 33–36

**Beginner Path (Easiest)**
1. Use **Railway** or **Render** (managed Postgres, free tiers).  
2. Add `Dockerfile` for app:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY app/requirements.txt .
   RUN pip install -r requirements.txt
   COPY app ./
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
3. Frontend: `npm run build` and deploy to **Netlify** or **Vercel**.

**Advanced Path (Kubernetes later)**
- Containerize both apps, push to GHCR, deploy to a managed K8s (GKE/AKS/EKS) with Ingress + TLS.

**Monitoring & Logs**
- Create Sentry projects (frontend + app) and install SDKs.
- Uptime checks with UptimeRobot.

---

## 15) Beta & Feedback (Week 18) — Day 37

1. Use **Tally.so** or **Typeform** for signups.
2. Create an Intercom/Crisp widget or a simple “Feedback” page.
3. Schedule 5 user interviews; record issues & requests.

---

## 16) Launch Prep & Go‑Live (Weeks 19–20) — Days 38–40

1. Landing page (value prop, screenshots, CTA).
2. 90‑second demo video (Loom or screen recording).
3. Final regression test (click every flow).
4. Go‑live: turn on prod URLs, monitor Sentry/UptimeRobot for 48h.

---

## Checklists You Can Tick

### Definition of Done (per feature)
- [ ] Code + unit tests
- [ ] API/UX reviewed
- [ ] Passed E2E scenario
- [ ] Security review (env vars, secrets, auth guarded)
- [ ] Docs updated

### Release Checklist
- [ ] All high/critical bugs resolved
- [ ] Smoke tests pass in prod
- [ ] Backups verified
- [ ] Rollback plan
- [ ] Monitoring dashboards green

---

## Quick FAQ

- **Do I need Kubernetes now?** No. Start with Render/Railway + Netlify/Vercel. Learn K8s later.
- **What if I’m stuck with auth?** Keep fastapi-users; use its examples.
- **How many questions to start?** 10–20 per framework, then expand based on feedback.

---

You’ve got this. Do one small block per day, commit to GitHub, and you’ll be live quickly. 
