#!/bin/bash
# test_auth_validation.sh - PsychSync Authentication Flow Test

API_URL="http://localhost:8000"
EMAIL="test@psychsync.validation"
PASSWORD="SecurePass123!"
NAME="Test Validation User"

echo "🔍 PsychSync Authentication Validation"
echo "====================================="

# 1. Test user registration
echo "1. Testing user registration..."
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\",
    \"name\": \"$NAME\"
  }")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $REGISTER_BODY"

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ User registration successful"
else
    echo "❌ User registration failed"
    exit 1
fi

# 2. Test user login
echo -e "\n2. Testing user login..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $LOGIN_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token // empty')
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
        echo "✅ User login successful"
        echo "Token obtained: ${TOKEN:0:20}..."
    else
        echo "❌ Login succeeded but no token received"
        exit 1
    fi
else
    echo "❌ User login failed"
    exit 1
fi

# 3. Test protected route access
echo -e "\n3. Testing protected route access..."
PROFILE_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$PROFILE_RESPONSE" | tail -n1)
PROFILE_BODY=$(echo "$PROFILE_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $PROFILE_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Protected route access successful"
else
    echo "❌ Protected route access failed"
    exit 1
fi

# 4. Test invalid token
echo -e "\n4. Testing invalid token rejection..."
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/users/me" \
  -H "Authorization: Bearer invalid_token_12345")

HTTP_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)

echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ Invalid token properly rejected"
else
    echo "❌ Invalid token should return 401"
    exit 1
fi

# 5. Test duplicate registration
echo -e "\n5. Testing duplicate registration prevention..."
DUP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"AnotherPass123!\",
    \"name\": \"Duplicate User\"
  }")

HTTP_CODE=$(echo "$DUP_RESPONSE" | tail -n1)

echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "409" ]; then
    echo "✅ Duplicate registration properly prevented"
else
    echo "❌ Duplicate registration should be prevented"
    exit 1
fi

echo -e "\n====================================="
echo "✅ Authentication validation complete!"
echo "====================================="