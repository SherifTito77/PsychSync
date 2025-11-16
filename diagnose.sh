#!/bin/bash
echo "🔍 PsychSync Diagnostic"
echo "======================="

echo "1. Python Path:"
echo $PYTHONPATH

echo ""
echo "2. Virtual Environment:"
which python
python --version

echo ""
echo "3. PostgreSQL:"
pg_isready -h localhost -p 5432 && echo "✅ Running" || echo "❌ Not running"

echo ""
echo "4. Database Connection:"
psql -d psychsync_db -U psychsync_user -c "SELECT 'OK' as status;" 2>&1

echo ""
echo "5. Environment File:"
ls -la app/.env.local app/.env 2>&1

echo ""
echo "6. Python Imports:"
python -c "import sys; sys.path.insert(0, '$(pwd)'); from app.core import config; print('✅ Imports work')" 2>&1

echo ""
echo "7. Ports:"
lsof -i :8000 -i :5173 2>&1

echo ""
echo "======================="
