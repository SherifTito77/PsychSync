#!/bin/bash

# Corporate Psychology API Test Script
# This script tests the Corporate Psychology Encoding System API endpoints
#
# Usage:
#   1. Update YOUR_EMAIL and YOUR_PASSWORD below
#   2. Run: bash test_corporate_psychology.sh
#   3. Requires: jq (brew install jq on macOS)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION - UPDATE THESE VALUES
# ═══════════════════════════════════════════════════════════════

BASE_URL="http://localhost:8000"
YOUR_EMAIL="your-email@example.com"
YOUR_PASSWORD="your-password-here"

# ═══════════════════════════════════════════════════════════════
# COLORS FOR OUTPUT
# ═══════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════

print_section() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# ═══════════════════════════════════════════════════════════════
# STEP 1: LOGIN
# ═══════════════════════════════════════════════════════════════

print_section "STEP 1: Logging in to get access token"

if [ "$YOUR_EMAIL" = "your-email@example.com" ]; then
    print_error "Please update YOUR_EMAIL and YOUR_PASSWORD in the script before running!"
    exit 1
fi

print_info "Sending login request to: $BASE_URL/api/v1/auth-unified/login"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth-unified/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$YOUR_EMAIL&password=$YOUR_PASSWORD")

# Check if login was successful
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token // empty')
ORG_ID=$(echo $LOGIN_RESPONSE | jq -r '.user.organization_id // empty')
USER_EMAIL=$(echo $LOGIN_RESPONSE | jq -r '.user.email // empty')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    print_error "Login failed! Check your credentials."
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

print_success "Login successful!"
echo -e "   User Email: ${GREEN}$USER_EMAIL${NC}"
echo -e "   Organization ID: ${GREEN}$ORG_ID${NC}"
echo -e "   Access Token: ${GREEN}${ACCESS_TOKEN:0:50}...${NC}"

# ═══════════════════════════════════════════════════════════════
# STEP 2: RUN PSYCHOLOGY ANALYSIS
# ═══════════════════════════════════════════════════════════════

print_section "STEP 2: Running Corporate Psychology Analysis"

print_info "Analyzing organization: $ORG_ID"
print_info "Measurement period: Last 30 days"

ANALYSIS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/corporate-psychology/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{
  \"organization_id\": \"$ORG_ID\",
  \"team_id\": null,
  \"measurement_period_days\": 30,
  \"include_culture_metrics\": true,
  \"include_wellness_metrics\": true,
  \"include_behavioral_metrics\": true,
  \"include_communication_metrics\": true
}")

# Parse response
SUCCESS=$(echo $ANALYSIS_RESPONSE | jq -r '.success // false')
SIGNALS_GENERATED=$(echo $ANALYSIS_RESPONSE | jq -r '.signals_generated // 0')
INTERVENTIONS_RECOMMENDED=$(echo $ANALYSIS_RESPONSE | jq -r '.interventions_recommended // 0')

if [ "$SUCCESS" = "true" ]; then
    print_success "Analysis completed successfully!"
    echo -e "   Signals Generated: ${GREEN}$SIGNALS_GENERATED${NC}"
    echo -e "   Interventions Recommended: ${GREEN}$INTERVENTIONS_RECOMMENDED}${NC}"

    # Show full response if verbose
    if [ "$1" = "--verbose" ]; then
        echo -e "\n${YELLOW}Full Response:${NC}"
        echo $ANALYSIS_RESPONSE | jq '.'
    fi
else
    print_error "Analysis failed!"
    echo "Response: $ANALYSIS_RESPONSE"
fi

# ═══════════════════════════════════════════════════════════════
# STEP 3: GET PSYCHOLOGY METRICS
# ═══════════════════════════════════════════════════════════════

print_section "STEP 3: Retrieving Psychology Metrics"

METRICS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/corporate-psychology/metrics/$ORG_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Check if metrics exist
METRICS_ERROR=$(echo $METRICS_RESPONSE | jq -r '.detail // empty')

if [ -n "$METRICS_ERROR" ]; then
    print_info "No metrics found yet. Run the analysis first (Step 2)."
else
    print_success "Metrics retrieved!"

    # Extract key metrics
    HEALTH_INDEX=$(echo $METRICS_RESPONSE | jq -r '.organizational_health_index // "N/A"')
    RISK_SCORE=$(echo $METRICS_RESPONSE | jq -r '.overall_risk_score // "N/A"')
    RISK_HORIZON=$(echo $METRICS_RESPONSE | jq -r '.risk_horizon // "N/A"')
    CLI=$(echo $METRICS_RESPONSE | jq -r '.cognitive_load_index // "N/A"')
    TSC=$(echo $METRICS_RESPONSE | jq -r '.trust_stability_score // "N/A"')

    echo -e "\n   📊 ${YELLOW}Organizational Health Index:${NC} ${GREEN}$HEALTH_INDEX${NC}/100"
    echo -e "   ⚠️  ${YELLOW}Overall Risk Score:${NC} ${RED}$RISK_SCORE${NC}/100"
    echo -e "   🎯 ${YELLOW}Risk Horizon:${NC} $RISK_HORIZON"
    echo -e ""
    echo -e "   🧠 ${YELLOW}Cognitive Load Index (CLI):${NC} $CLI"
    echo -e "   🤝 ${YELLOW}Trust Stability Score (TSC):${NC} $TSC"

    # Show all 6 encodings
    echo -e "\n   ${BLUE}All 6 Core Encodings:${NC}"
    echo "   ─────────────────────────────────────────"
    echo -e "   • Cognitive Load Index:       $CLI"
    echo -e "   • Trust Stability Score:      $TSC"
    echo -e "   • Emotional Volatility:       $(echo $METRICS_RESPONSE | jq -r '.emotional_volatility_score // "N/A"')"
    echo -e "   • Coordination Friction:      $(echo $METRICS_RESPONSE | jq -r '.coordination_friction_score // "N/A"')"
    echo -e "   • Psychological Debt:         $(echo $METRICS_RESPONSE | jq -r '.psychological_debt_score // "N/A"')"
    echo -e "   • Recovery & Resilience:      $(echo $METRICS_RESPONSE | jq -r '.recovery_resilience_score // "N/A"')"

    # Show full response if verbose
    if [ "$1" = "--verbose" ]; then
        echo -e "\n${YELLOW}Full Response:${NC}"
        echo $METRICS_RESPONSE | jq '.'
    fi
fi

# ═══════════════════════════════════════════════════════════════
# STEP 4: GET SYSTEM SIGNALS
# ═══════════════════════════════════════════════════════════════

print_section "STEP 4: Retrieving System Signals"

SIGNALS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/corporate-psychology/signals/$ORG_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Check if signals exist
SIGNALS_ERROR=$(echo $SIGNALS_RESPONSE | jq -r '.detail // empty')

if [ -n "$SIGNALS_ERROR" ]; then
    print_info "No signals found yet. Run the analysis first (Step 2)."
else
    SIGNAL_COUNT=$(echo $SIGNALS_RESPONSE | jq 'length')
    print_success "Retrieved $SIGNAL_COUNT system signals!"

    if [ "$SIGNAL_COUNT" -gt 0 ]; then
        echo -e "\n${YELLOW}Active Alerts:${NC}"
        echo "$SIGNALS_RESPONSE" | jq -r '.[] | "   \(.severity | ascii_upcase): \(.signal_summary)\n   Impact: \(.operational_impact)\n   Horizon: \(.risk_horizon)\n"'

        # Show full response if verbose
        if [ "$1" = "--verbose" ]; then
            echo -e "\n${YELLOW}Full Response:${NC}"
            echo $SIGNALS_RESPONSE | jq '.'
        fi
    else
        echo -e "   ${GREEN}No active alerts! Organization is healthy. 🎉${NC}"
    fi
fi

# ═══════════════════════════════════════════════════════════════
# STEP 5: GET INTERVENTIONS
# ═══════════════════════════════════════════════════════════════

print_section "STEP 5: Retrieving Structural Interventions"

INTERVENTIONS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/corporate-psychology/interventions/$ORG_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Check if interventions exist
INTERVENTIONS_ERROR=$(echo $INTERVENTIONS_RESPONSE | jq -r '.detail // empty')

if [ -n "$INTERVENTIONS_ERROR" ]; then
    print_info "No interventions found yet. Run the analysis first (Step 2)."
else
    INTERVENTION_COUNT=$(echo $INTERVENTIONS_RESPONSE | jq 'length')
    print_success "Retrieved $INTERVENTION_COUNT interventions!"

    if [ "$INTERVENTION_COUNT" -gt 0 ]; then
        echo -e "\n${YELLOW}Recommended Interventions:${NC}"
        echo "$INTERVENTIONS_RESPONSE" | jq -r '.[] | "   • \(.intervention_title)\n     Status: \(.status)\n     Expected: \(.expected_outcomes)\n"'

        # Show full response if verbose
        if [ "$1" = "--verbose" ]; then
            echo -e "\n${YELLOW}Full Response:${NC}"
            echo $INTERVENTIONS_RESPONSE | jq '.'
        fi
    else
        echo -e "   ${GREEN}No interventions needed! 🎉${NC}"
    fi
fi

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

print_section "✅ TEST COMPLETE"

echo -e "${GREEN}All Corporate Psychology API endpoints tested successfully!${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo -e "   1. View the dashboard: ${BLUE}http://localhost:5173/admin/corporate-psychology${NC}"
echo -e "   2. Run analysis with different time periods"
echo -e "   3. Explore team-level metrics by passing team_id"
echo -e "   4. Check Swagger UI: ${BLUE}http://localhost:8000/docs${NC}\n"

echo -e "${YELLOW}Verbose mode:${NC} Run with ${GREEN}--verbose${NC} flag to see full API responses"
echo -e "${YELLOW}Example:${NC} ${GREEN}bash test_corporate_psychology.sh --verbose${NC}\n"
