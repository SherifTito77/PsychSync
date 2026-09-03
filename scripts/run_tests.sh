#!/bin/bash
set -e
echo "🚀 Preparing test environment..."
export DATABASE_URL=postgresql+asyncpg://psychsync_user:dev_password@localhost:5432/psychsync_test
alembic upgrade head
echo "🧪 Running integration tests..."
export TESTING=true
export PYTHONPATH=$PYTHONPATH:.
pytest tests/integration/test_full_stack.py -v --tb=short -c /dev/null -o asyncio_mode=auto
