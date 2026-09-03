#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# CORPORATE PSYCHOLOGY ANALYSIS - Complete Workflow Script
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on error

# Configuration
API_BASE="http://localhost:8000/api/v1"
EMAIL="${1:-YOUR_EMAIL}"
PASSWORD="${2:-YOUR_PASSWORD}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CORPORATE PSYCHOLOGY ANALYSIS WORKFLOW${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Authenticate
echo -e "${GREEN}Step 1: Authenticating...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/simple-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD")

echo "Login response: $LOGIN_RESPONSE"

# Check if login was successful
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Authentication successful!${NC}"
else
    echo -e "${YELLOW}✗ Authentication failed. Please check your credentials.${NC}"
    echo "Raw response: $LOGIN_RESPONSE"
    exit 1
fi

# Extract access token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access token: ${ACCESS_TOKEN:0:20}..."

# Step 2: Get organization ID
echo -e "\n${GREEN}Step 2: Getting organization ID...${NC}"
ORGS_RESPONSE=$(curl -s -X GET "$API_BASE/organizations" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Try to extract organization ID
ORG_ID=$(echo $ORGS_RESPONSE | jq -r '.[0].id // .id // empty' 2>/dev/null || echo "")

if [ -z "$ORG_ID" ] || [ "$ORG_ID" = "null" ]; then
    echo -e "${YELLOW}No organization found. Response: $ORGS_RESPONSE${NC}"
    echo "Please create an organization first, or provide the organization ID manually."
    exit 1
fi

echo -e "${GREEN}✓ Using organization ID: $ORG_ID${NC}"

# Step 3: Run the analysis
echo -e "\n${GREEN}Step 3: Running Corporate Psychology Analysis...${NC}"
ANALYSIS_RESPONSE=$(curl -s -X POST "$API_BASE/corporate-psychology/analyze" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"organization_id\": \"$ORG_ID\",
    \"team_id\": null,
    \"measurement_period_days\": 30,
    \"include_culture_metrics\": true,
    \"include_wellness_metrics\": true,
    \"include_behavioral_metrics\": true,
    \"include_communication_metrics\": true
  }")

echo "Analysis response:"
echo "$ANALYSIS_RESPONSE" | jq '.' 2>/dev/null || echo "$ANALYSIS_RESPONSE"

# Check if analysis was successful
if echo "$ANALYSIS_RESPONSE" | grep -q '"success":true'; then
    SIGNALS_COUNT=$(echo $ANALYSIS_RESPONSE | jq -r '.signals_generated // 0')
    INTERVENTIONS_COUNT=$(echo $ANALYSIS_RESPONSE | jq -r '.interventions_recommended // 0')
    echo -e "${GREEN}✓ Analysis complete!${NC}"
    echo -e "  • Signals generated: $SIGNALS_COUNT"
    echo -e "  • Interventions recommended: $INTERVENTIONS_COUNT"
else
    echo -e "${YELLOW}⚠ Analysis may have issues. Check the response above.${NC}"
fi

# Step 4: Get metrics
echo -e "\n${GREEN}Step 4: Getting psychology metrics...${NC}"
METRICS_RESPONSE=$(curl -s -X GET "$API_BASE/corporate-psychology/metrics/$ORG_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$METRICS_RESPONSE" | grep -q "organizational_health_index"; then
    HEALTH_INDEX=$(echo $METRICS_RESPONSE | jq -r '.organizational_health_index')
    RISK_SCORE=$(echo $METRICS_RESPONSE | jq -r '.overall_risk_score')
    echo -e "${GREEN}✓ Metrics retrieved!${NC}"
    echo -e "  • Organizational Health Index: $HEALTH_INDEX"
    echo -e "  • Overall Risk Score: $RISK_SCORE"
    echo ""
    echo "Full metrics:"
    echo "$METRICS_RESPONSE" | jq '.' 2>/dev/null || echo "$METRICS_RESPONSE"
else
    echo -e "${YELLOW}⚠ No metrics found yet. This is normal if this is the first analysis.${NC}"
fi

# Step 5: Get signals
echo -e "\n${GREEN}Step 5: Getting system signals...${NC}"
SIGNALS_RESPONSE=$(curl -s -X GET "$API_BASE/corporate-psychology/signals/$ORG_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

SIGNALS_COUNT=$(echo $SIGNALS_RESPONSE | jq 'length' 2>/dev/null || echo "0")

if [ "$SIGNALS_COUNT" != "0" ] && [ "$SIGNALS_COUNT" != "null" ]; then
    echo -e "${GREEN}✓ Found $SIGNALS_COUNT active signals${NC}"
    echo "$SIGNALS_RESPONSE" | jq '.' 2>/dev/null || echo "$SIGNALS_RESPONSE"
else
    echo -e "${YELLOW}⚠ No active signals found${NC}"
fi

# Step 6: Get interventions
echo -e "\n${GREEN}Step 6: Getting interventions...${NC}"
INTERVENTIONS_RESPONSE=$(curl -s -X GET "$API_BASE/corporate-psychology/interventions/$ORG_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

INTERVENTIONS_COUNT=$(echo $INTERVENTIONS_RESPONSE | jq 'length' 2>/dev/null || echo "0")

if [ "$INTERVENTIONS_COUNT" != "0" ] && [ "$INTERVENTIONS_COUNT" != "null" ]; then
    echo -e "${GREEN}✓ Found $INTERVENTIONS_COUNT interventions${NC}"
    echo "$INTERVENTIONS_RESPONSE" | jq '.' 2>/dev/null || echo "$INTERVENTIONS_RESPONSE"
else
    echo -e "${YELLOW}⚠ No interventions found${NC}"
fi

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Analysis complete! View results in the dashboard:${NC}"
echo -e "${YELLOW}http://localhost:5173/admin/corporate-psychology${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
