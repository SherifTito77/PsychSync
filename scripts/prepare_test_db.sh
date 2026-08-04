#!/bin/bash
set -e
echo "Preparing test database schema..."
export DATABASE_URL=postgresql+asyncpg://psychsync_user:dev_password@localhost:5432/psychsync_test
alembic upgrade head
echo "✅ Test database schema is ready."
