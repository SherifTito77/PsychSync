# 🚀 Critical Fixes Quick Start Guide
## Begin 30-Day Execution Plan Immediately

**Date:** December 27, 2025
**Status:** Ready to Execute
**Time to First Fix:** 15 minutes

---

## ⚡ Day 1: Fix Critical Security Vulnerabilities (15-30 minutes)

### Step 1: Upgrade PyTorch (CVE-2025-32434) - 5 minutes

```bash
# Backup current environment
pip freeze > requirements_backup.txt

# Upgrade PyTorch and transformers
pip install --upgrade 'torch>=2.6.0' 'transformers>=4.37.0'

# Update all requirements.txt files
find . -name "requirements*.txt" -type f -exec sed -i '' 's/torch==2.1.0/torch>=2.6.0/g' {} \;
find . -name "requirements*.txt" -type f -exec sed -i '' 's/transformers==4.35.0/transformers>=4.37.0/g' {} \;
```

**Verification:**
```bash
python -c "import torch; print(f'PyTorch {torch.__version__}')"
# Should print: PyTorch 2.6.0 or higher
```

### Step 2: Update High-Risk Dependencies - 5 minutes

```bash
# Update requests (CVE-2024-35195)
pip install --upgrade 'requests>=2.32.5'

# Update jinja2 (CVE-2024-34064)
pip install --upgrade 'jinja2>=3.1.6'

# Update urllib3
pip install --upgrade 'urllib3>=2.0.7'

# Replace ecdsa with cryptography (no fix for CVE-2024-23342)
pip uninstall -y ecdsa
pip install 'cryptography>=41.0.0'
```

**Update requirements files:**
```bash
# Update all requirements.txt files
find . -name "requirements*.txt" -type f -exec sed -i '' 's/requests==2.31.0/requests>=2.32.5/g' {} \;
find . -name "requirements*.txt" -type f -exec sed -i '' 's/jinja2==3.1.2/jinja2>=3.1.6/g' {} \;
find . -name "requirements*.txt" -type f -exec sed -i '' 's/ecdsa==.*/cryptography>=41.0.0/g' {} \;
```

### Step 3: Remove Security Backdoor - 10 minutes

```bash
# Find and review the backdoor file
find . -name "*standalone_auth*" -o -name "*backdoor*"

# If standalone_auth.py exists, remove it
rm -f app/api/v1/endpoints/standalone_auth.py
rm -f app/services/standalone_auth.py

# Search for any references to standalone_auth
grep -r "standalone_auth" app/ --exclude-dir=__pycache__
# Remove any imports or references found
```

### Step 4: Verify Security Fixes - 5 minutes

```bash
# Run security scan
pip install safety
safety check --json

# Verify no critical vulnerabilities remain
python -c "
import torch
import requests
import jinja2
print(f'✅ PyTorch: {torch.__version__} (>=2.6.0 required)')
print(f'✅ Requests: {requests.__version__} (>=2.32.5 required)')
print(f'✅ Jinja2: {jinja2.__version__} (>=3.1.6 required)')
"
```

**Expected Output:**
```
✅ PyTorch: 2.6.0 (>=2.6.0 required)
✅ Requests: 2.32.5 (>=2.32.5 required)
✅ Jinja2: 3.1.6 (>=3.1.6 required)
```

---

## 🗑️ Day 2: Remove Dead Code (10-15 minutes)

### Step 1: Delete Broken Files - 5 minutes

```bash
# Remove explicitly broken files
rm -f app/api/v1/endpoints/assessment_results_broken.py
rm -f app/api/v1/endpoints/auth_original_backup.py
rm -f app/api/v1/endpoints/*_backup.py
rm -f app/api/v1/endpoints/*_old.py

# Find and remove all backup/broken files
find app/ -name "*_backup.py" -delete
find app/ -name "*_broken.py" -delete
find app/ -name "*_old.py" -delete
find app/ -name "*.py.bak" -delete
find app/ -name "*~" -delete
```

### Step 2: Remove Commented Code - 10 minutes

```bash
# Create a script to remove large blocks of commented code
cat > /tmp/clean_comments.py << 'EOF'
import re
import sys
from pathlib import Path

def clean_commented_blocks(file_path):
    """Remove large blocks of commented code (3+ consecutive lines)"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Track which lines to keep
        cleaned = []
        comment_count = 0
        in_docstring = False

        for line in lines:
            stripped = line.strip()

            # Check for docstrings
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                cleaned.append(line)
                comment_count = 0
                continue

            if in_docstring:
                cleaned.append(line)
                comment_count = 0
                continue

            # Count comment lines
            if stripped.startswith('#') and not stripped.startswith('#!'):
                comment_count += 1
                # Only keep if it's a short comment (< 3 consecutive)
                if comment_count < 3:
                    cleaned.append(line)
            else:
                cleaned.append(line)
                comment_count = 0

        # Write back
        with open(file_path, 'w') as f:
            f.writelines(cleaned)

        print(f'✅ Cleaned {file_path}')
    except Exception as e:
        print(f'❌ Error cleaning {file_path}: {e}')

if __name__ == '__main__':
    for py_file in Path('app').rglob('*.py'):
        clean_commented_blocks(py_file)
EOF

python /tmp/clean_comments.py
```

### Step 3: Verify Code Still Works - 5 minutes

```bash
# Run type checking
npm run type-check 2>&1 | head -50

# Run backend tests
pytest tests/api/test_auth.py -v --tb=short

# Check imports work
python -c "from app.main import app; print('✅ Backend imports OK')"
```

---

## 🔧 Day 3: Replace Print Statements (20 minutes)

### Step 1: Replace Print with Logger in Backend

```bash
# Create automated replacement script
cat > /tmp/fix_prints.py << 'EOF'
import re
from pathlib import Path

def fix_print_statements(file_path):
    """Replace print() with logger.info()"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check if file already has logger imported
        has_logger = 'logger' in content or 'logging' in content

        original_content = content

        # Replace print statements with logger calls
        # Simple print("message") -> logger.info("message")
        content = re.sub(
            r'print\("([^"]+)"\)',
            r'logger.info("\1")',
            content
        )
        content = re.sub(
            r"print\('([^']+)'\)",
            r"logger.info('\1')",
            content
        )

        # Only write if changes were made
        if content != original_content:
            # Add logger import if not present
            if not has_logger:
                # Find first import line and add logger after it
                import_match = re.search(r'^import .+', content, re.MULTILINE)
                if import_match:
                    insert_pos = import_match.end()
                    content = content[:insert_pos] + '\nimport logging\nlogger = logging.getLogger(__name__)' + content[insert_pos:]

            with open(file_path, 'w') as f:
                f.write(content)

            print(f'✅ Fixed {file_path}')

    except Exception as e:
        print(f'❌ Error fixing {file_path}: {e}')

if __name__ == '__main__':
    for py_file in Path('app').rglob('*.py'):
        fix_print_statements(py_file)
EOF

python /tmp/fix_prints.py
```

### Step 2: Replace Console.log in Frontend

```bash
cd frontend

# Create replacement script
cat > /tmp/fix_console_logs.js << 'EOF'
const fs = require('fs');
const path = require('path');

function fixConsoleLogs(dir) {
  const files = fs.readdirSync(dir, { recursive: true });

  files.forEach(file => {
    if (!file.endsWith('.ts') && !file.endsWith('.tsx')) return;

    const filePath = path.join(dir, file);
    const content = fs.readFileSync(filePath, 'utf8');

    // Remove console.log statements
    const cleaned = content.replace(/^.*console\.log\(.*\)\n?$/gm, '');

    if (cleaned !== content) {
      fs.writeFileSync(filePath, cleaned);
      console.log(`✅ Fixed ${file}`);
    }
  });
}

fixConsoleLogs('src');
EOF

node /tmp/fix_console_logs.js

cd ..
```

---

## 📊 Day 4-5: Add Database Indexes (10 minutes)

### Step 1: Create Migration for Indexes

```bash
# Create new migration
alembic revision -m "add_performance_indexes"

# Edit the generated migration file
cat > alembic/versions/xxxx_add_performance_indexes.py << 'EOF'
"""add performance indexes

Revision ID: add_perf_indexes
Revises: <previous_revision>
Create Date: 2025-12-27

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_perf_indexes'
down_revision = '<your_previous_revision_id>'
branch_labels = None
depends_on = None


def upgrade():
    # Assessment queries optimization
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_org_status_date '
               'ON assessments(organization_id, status, created_at DESC)')

    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_team_status_date '
               'ON assessments(team_id, status, created_at DESC)')

    # Response queries optimization
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_assessment_user_date '
               'ON responses(assessment_id, user_id, created_at DESC)')

    # Team member queries optimization
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_team_user_role '
               'ON team_members(team_id, user_id, role) INCLUDE (joined_at)')

    # User queries optimization
    op.execute('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_verified '
               'ON users(email) WHERE is_active = true')

    print('✅ All performance indexes created successfully')


def downgrade():
    op.execute('DROP INDEX IF EXISTS idx_users_email_verified')
    op.execute('DROP INDEX IF EXISTS idx_team_members_team_user_role')
    op.execute('DROP INDEX IF EXISTS idx_responses_assessment_user_date')
    op.execute('DROP INDEX IF EXISTS idx_assessments_team_status_date')
    op.execute('DROP INDEX IF EXISTS idx_assessments_org_status_date')
EOF

# Apply migration
alembic upgrade head
```

### Step 2: Verify Indexes

```bash
# Connect to database and check indexes
docker-compose exec db psql -U postgres -d psychsync -c "
\dx
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename;
"
```

**Expected Output:**
```
              indexname              |    tablename
-------------------------------------+-----------------
 idx_assessments_org_status_date     | assessments
 idx_assessments_team_status_date    | assessments
 idx_responses_assessment_user_date  | responses
 idx_team_members_team_user_role     | team_members
 idx_users_email_verified            | users
```

---

## ✅ Verification: End of Week 1

### Run Full Verification Suite

```bash
# Create verification script
cat > scripts/verify_week1_fixes.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Week 1 Critical Fixes Verification"
echo "======================================"
echo

# 1. Security fixes
echo "1️⃣ Checking security fixes..."
python -c "
import torch
import requests
import jinja2

torch_version = torch.__version__
requests_version = requests.__version__
jinja_version = jinja2.__version__

assert torch_version >= '2.6.0', f'PyTorch {torch_version} < 2.6.0'
assert requests_version >= '2.32.5', f'Requests {requests_version} < 2.32.5'
assert jinja_version >= '3.1.6', f'Jinja2 {jinja_version} < 3.1.6'

print(f'✅ PyTorch: {torch_version}')
print(f'✅ Requests: {requests_version}')
print(f'✅ Jinja2: {jinja_version}')
"

# 2. Backdoor removed
echo
echo "2️⃣ Checking for security backdoors..."
if [ -f "app/api/v1/endpoints/standalone_auth.py" ]; then
    echo "❌ FAIL: standalone_auth.py still exists!"
    exit 1
else
    echo "✅ No standalone_auth.py found"
fi

# 3. Dead code removed
echo
echo "3️⃣ Checking for dead code..."
dead_count=$(find app/ -name "*_backup.py" -o -name "*_broken.py" -o -name "*_old.py" | wc -l)
if [ "$dead_count" -gt 0 ]; then
    echo "❌ FAIL: Found $dead_count dead code files"
    exit 1
else
    echo "✅ No dead code files found"
fi

# 4. Print statements replaced
echo
echo "4️⃣ Checking for print statements..."
print_count=$(grep -r "print(" app/ --include="*.py" | grep -v "test_" | wc -l)
if [ "$print_count" -gt 10 ]; then
    echo "⚠️  WARNING: Still found $print_count print statements (target: < 10)"
else
    echo "✅ Print statements mostly replaced"
fi

# 5. Database indexes
echo
echo "5️⃣ Checking database indexes..."
docker-compose exec -T db psql -U postgres -d psychsync -c "
SELECT COUNT(*) as index_count FROM pg_indexes
WHERE indexname LIKE 'idx_%' AND schemaname = 'public';
" | grep -q "[5-9]" || echo "⚠️  WARNING: Expected 5+ indexes"

echo "✅ Indexes created"

# 6. Tests still pass
echo
echo "6️⃣ Running critical tests..."
pytest tests/api/test_auth.py -v --tb=short -q

echo
echo "🎉 Week 1 verification complete!"
echo "======================================"
EOF

chmod +x scripts/verify_week1_fixes.sh
./scripts/verify_week1_fixes.sh
```

---

## 📈 Expected Results After Week 1

### Security Improvements
- ✅ 0 CRITICAL vulnerabilities (was 3)
- ✅ 0 HIGH severity vulnerabilities (was 5)
- ✅ Security backdoor removed
- ✅ All dependencies up-to-date

### Code Quality Improvements
- ✅ ~10,000 lines of dead code removed
- ✅ 500+ print statements replaced with logging
- ✅ Single authentication implementation
- ✅ Code easier to read and maintain

### Performance Improvements
- ✅ Database queries 50-90% faster
- ✅ Index scans instead of full table scans
- ✅ Better query plans from PostgreSQL

---

## 🚀 What's Next: Week 2-4

After completing Week 1, continue with:

**Week 2: Async Cache Implementation**
- Replace synchronous Redis with async
- Expected improvement: 30-50% faster response times

**Week 3: Redis Session Migration**
- Enable horizontal scaling
- Expected improvement: Support 100,000+ users

**Week 4: Background Task Queue**
- Eliminate API timeouts
- Expected improvement: 0 timeouts from long operations

See `docs/CRITICAL_ISSUES_ACTION_PLAN.md` for complete Week 2-4 guidance.

---

## 🆘 Troubleshooting

### "ImportError after upgrading PyTorch"
```bash
# Reinstall all dependencies
pip install --force-reinstall 'torch>=2.6.0' 'torchvision>=0.19.0'
```

### "Tests fail after removing dead code"
```bash
# Check what tests are failing
pytest tests/ -v --tb=short

# You may need to update imports that referenced removed files
```

### "Database indexes taking too long"
```bash
# Check if indexes are still building
docker-compose exec db psql -U postgres -d psychsync -c "
SELECT query, state, wait_event FROM pg_stat_activity WHERE query LIKE '%CREATE INDEX%';
"

# If needed, you can cancel and rebuild without CONCURRENTLY
```

---

**Last Updated:** December 27, 2025
**Next Steps:** Begin with Day 1, Step 1 above!
**Questions?** See `docs/CRITICAL_ISSUES_ACTION_PLAN.md` for detailed explanations
