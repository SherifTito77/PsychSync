#!/bin/bash

# PsychSync Quick Login Script
# This script automatically logs you in and stores tokens in localStorage

echo "🚀 PsychSync Quick Login"
echo "========================"

# Test user credentials
EMAIL="test@example.com"
PASSWORD="password"

echo "Email: $EMAIL"
echo "Password: $PASSWORD"
echo ""

# Get tokens from backend
echo "🔐 Getting authentication tokens..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=$EMAIL&password=$PASSWORD")

# Extract tokens
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login failed! Make sure backend is running on localhost:8000"
    exit 1
fi

echo "✅ Login successful!"
echo ""

# Get user info
USER_INFO=$(curl -s -X GET "http://localhost:8000/api/v1/users/users/me" \
     -H "Authorization: Bearer $ACCESS_TOKEN")

USER_EMAIL=$(echo $USER_INFO | python -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null)
USER_NAME=$(echo $USER_INFO | python -c "import sys, json; print(json.load(sys.stdin)['full_name'])" 2>/dev/null)

echo "👤 Logged in as: $USER_NAME ($USER_EMAIL)"
echo ""

# Create localStorage setup script
echo "💾 Creating browser localStorage setup..."
cat > set-tokens.js << 'EOF'
// Copy this script and run it in your browser console on localhost:5173
localStorage.setItem('access_token', 'ACCESS_TOKEN_PLACEHOLDER');
localStorage.setItem('refresh_token', 'REFRESH_TOKEN_PLACEHOLDER');
localStorage.setItem('user', JSON.stringify({
    email: 'test@example.com',
    full_name: 'Test User',
    is_active: true,
    id: 'bbc97a1b-211c-4f02-994d-011d94170647'
}));
console.log('✅ Tokens and user data set in localStorage!');
console.log('You can now access protected pages without logging in.');
EOF

# Replace placeholders with actual tokens
sed -i '' "s/ACCESS_TOKEN_PLACEHOLDER/$ACCESS_TOKEN/g" set-tokens.js
sed -i '' "s/REFRESH_TOKEN_PLACEHOLDER/$REFRESH_TOKEN/g" set-tokens.js

echo "📋 Auto-Login Instructions:"
echo "1. Open your browser and go to: http://localhost:5173"
echo "2. Open Developer Console (F12 or Cmd+Opt+J)"
echo "3. Copy and paste the following JavaScript code:"
echo ""
echo "----------------------------------------"
cat set-tokens.js
echo "----------------------------------------"
echo ""
echo "4. Press Enter to execute the code"
echo "5. Refresh the page - you'll be automatically logged in!"
echo ""
echo "🎉 You're now ready to use PsychSync without manual login!"

# Clean up
rm set-tokens.js