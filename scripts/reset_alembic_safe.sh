#!/bin/bash
# Safe Alembic reset - DO NOT RUN IN PRODUCTION
# Only for development when migrations are broken

echo "⚠️  This will reset all Alembic state. Are you sure? (yes/no)"
read confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Mark current state as head without running migrations
alembic stamp head

# Show current state
alembic current
alembic heads
