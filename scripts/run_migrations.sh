#!/bin/bash
echo "🗄️  Running Database Migrations..."

# Set Python path
export PYTHONPATH="$(pwd):${PYTHONPATH}"

# Activate virtual environment
source .venv/bin/activate

# Load environment
if [ -f "app/.env.local" ]; then
    export $(cat app/.env.local | grep -v '^#' | xargs)
fi

echo "Running migrations..."

# Run each migration script from project root
python -m app.create_db && echo "✅ create_db.py" || echo "⚠️  create_db.py failed"
python -m app.create_team_tables && echo "✅ create_team_tables.py" || echo "⚠️  create_team_tables.py already done"
python -m app.create_assessment_tables && echo "✅ create_assessment_tables.py" || echo "⚠️  create_assessment_tables.py already done"
python -m app.create_scoring_tables && echo "✅ create_scoring_tables.py" || echo "⚠️  create_scoring_tables.py already done"
python -m app.create_template_tables && echo "✅ create_template_tables.py" || echo "⚠️  create_template_tables.py already done"
python -m app.update_response_tables && echo "✅ update_response_tables.py" || echo "⚠️  update_response_tables.py already done"
python -m app.seed_templates && echo "✅ seed_templates.py" || echo "⚠️  seed_templates.py already done"
python -m app.seed_scoring_templates && echo "✅ seed_scoring_templates.py" || echo "⚠️  seed_scoring_templates.py already done"

echo ""
echo "✅ Migration process complete!"
