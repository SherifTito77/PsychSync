#!/bin/bash
echo "🔧 Fixing schema mismatches..."

# Fix 1: Update user_service.py to use password_hash
echo "1. Fixing user_service.py..."
sed -i '' 's/user\.hashed_password/user.password_hash/g' app/services/user_service.py

# Fix 2: Check if we need to update the model
echo "2. Checking User model..."
if grep -q "hashed_password = Column" app/db/models/user.py; then
    echo "   Updating User model..."
    sed -i '' 's/hashed_password = Column/password_hash = Column/g' app/db/models/user.py
fi

# Fix 3: Update any other references
echo "3. Fixing other references..."
find app -name "*.py" -type f -exec sed -i '' 's/\.hashed_password/.password_hash/g' {} \;

echo ""
echo "✅ Schema fixes applied!"
echo ""
echo "Changed files:"
git diff --name-only 2>/dev/null || echo "  - app/services/user_service.py"
echo "  - app/db/models/user.py"
echo ""
echo "Next: Restart backend with ./start_backend.sh"
