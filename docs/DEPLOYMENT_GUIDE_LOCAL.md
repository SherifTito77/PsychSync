# Local Deployment Guide (MacBook)
1. Create a virtual environment: `python3 -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install dependencies: `pip install -r app/requirements.txt`
4. Apply migrations: `alembic upgrade head`
5. Start the backend: `./start_local.sh`
6. Start frontend: `cd frontend && npm run dev`
7. Visit: `http://127.0.0.1:5173`
