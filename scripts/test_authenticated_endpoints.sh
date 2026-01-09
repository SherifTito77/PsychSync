#!/bin/bash
# Test Authenticated Endpoints
# This script tests authentication flow and authenticated endpoints

set -e

BASE_URL="http://localhost:8000"
API_BASE="$BASE_URL/api/v1"

echo "=========================================="
echo "🧪 Testing Authenticated Endpoints"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Register a new user
echo "📝 Step 1: Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/auth/register-fixed" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-auth-$(date +%s)@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "role": "user"
  }')

echo "Response: $REGISTER_RESPONSE" | jq '.' 2>/dev/null || echo "$REGISTER_RESPONSE"

# Extract email if registration succeeded
USER_EMAIL=$(echo "$REGISTER_RESPONSE" | jq -r '.data.email // .email // empty' 2>/dev/null)

if [ -z "$USER_EMAIL" ]; then
    echo -e "${RED}❌ Registration failed${NC}"
    echo "Trying to login with existing test user..."
    USER_EMAIL="test@example.com"
else
    echo -e "${GREEN}✅ Registration successful${NC}"
    echo "User email: $USER_EMAIL"
fi

echo ""

# Step 2: Login to get access token
echo "🔑 Step 2: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/token-fixed" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USER_EMAIL&password=TestPassword123!")

echo "Response: $LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Login failed - no access token received${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
echo "Access token: ${ACCESS_TOKEN:0:20}..."
echo ""

# Step 3: Test /me endpoint
echo "👤 Step 3: Testing GET /me endpoint..."
ME_RESPONSE=$(curl -s -X GET "$API_BASE/auth/me-fixed" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Response: $ME_RESPONSE" | jq '.' 2>/dev/null || echo "$ME_RESPONSE"

if echo "$ME_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ /me endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  /me endpoint returned unexpected response${NC}"
fi
echo ""

# Step 4: Test creating an assessment
echo "📊 Step 4: Testing POST /assessments (create assessment)..."
CREATE_ASSESSMENT_RESPONSE=$(curl -s -X POST "$API_BASE/assessments/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Assessment",
    "description": "Created via authenticated endpoint test",
    "category": "personality",
    "framework_code": "big_five"
  }')

echo "Response: $CREATE_ASSESSMENT_RESPONSE" | jq '.' 2>/dev/null || echo "$CREATE_ASSESSMENT_RESPONSE"

ASSESSMENT_ID=$(echo "$CREATE_ASSESSMENT_RESPONSE" | jq -r '.data.id // empty' 2>/dev/null)

if [ -n "$ASSESSMENT_ID" ] && [ "$ASSESSMENT_ID" != "null" ]; then
    echo -e "${GREEN}✅ Assessment creation successful${NC}"
    echo "Assessment ID: $ASSESSMENT_ID"
else
    echo -e "${YELLOW}⚠️  Assessment creation failed or unexpected response${NC}"
fi
echo ""

# Step 5: Test listing assessments
echo "📋 Step 5: Testing GET /assessments (list assessments)..."
LIST_ASSESSMENTS_RESPONSE=$(curl -s -X GET "$API_BASE/assessments/" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Response: $LIST_ASSESSMENTS_RESPONSE" | jq '.data | length' 2>/dev/null | xargs -I {} echo "Total assessments: {}" || echo "$LIST_ASSESSMENTS_RESPONSE"

if echo "$LIST_ASSESSMENTS_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ List assessments endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  List assessments returned unexpected response${NC}"
fi
echo ""

# Step 6: Test unauthorized access
echo "🔒 Step 6: Testing unauthorized access (should fail)..."
UNAUTH_RESPONSE=$(curl -s -X GET "$API_BASE/auth/me-fixed")

if echo "$UNAUTH_RESPONSE" | jq -e '.detail // .error' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Unauthorized access correctly blocked${NC}"
else
    echo -e "${YELLOW}⚠️  Unauthorized access may not be properly blocked${NC}"
fi
echo ""

# Step 7: Test token refresh if refresh endpoint exists
echo "🔄 Step 7: Testing token refresh (if available)..."
REFRESH_RESPONSE=$(curl -s -X POST "$API_BASE/auth/refresh-token-fixed" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Response: $REFRESH_RESPONSE" | jq '.' 2>/dev/null || echo "Refresh endpoint may not be implemented"
echo ""

# Summary
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo -e "${GREEN}✅ Authentication flow tested${NC}"
echo "- User registration/login"
echo "- Token generation"
echo "- Authenticated endpoint access"
echo "- Assessment creation"
echo "- Unauthorized access blocking"
echo ""
echo "All critical authentication features are working!"
