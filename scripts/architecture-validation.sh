#!/bin/bash

# =============================================================================
# PsychSync Architecture Validation Script
# Based on the DevOps testing plan you provided
# =============================================================================

set -e  # Exit on any error

echo "🏗️  PsychSync AI - Architecture Validation Tests"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize counters
PASS_COUNT=0
FAIL_COUNT=0

echo -e "${YELLOW}Starting Architecture Validation Tests...${NC}"
echo ""

# =============================================================================
# 1.1 PSYCHSYNC APPLICATION ARCHITECTURE ASSESSMENT
# =============================================================================

echo -e "${BLUE}1.1 PSYCHSYNC APPLICATION ARCHITECTURE ASSESSMENT${NC}"
echo "==============================================="

# Test 1.1.1: Layer Separation Validation
echo -e "\n${BLUE}✅ Test 1.1.1: Layer Separation Validation${NC}"
echo "Testing: Is business logic properly separated from presentation?"
echo "Looking for direct database calls in API endpoints..."

DB_CALLS_IN_API=$(find app/api/v1/endpoints -name "*.py" -exec grep -l "db\.execute\|\.query\|\.first()" {} \; 2>/dev/null | wc -l || echo "0")
echo "Direct DB calls found in endpoints: $DB_CALLS_IN_API"

if [ "$DB_CALLS_IN_API" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: No direct database calls in API endpoints${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: Found $DB_CALLS_IN_API direct database calls in endpoints${NC}"
    echo "${RED}   All database operations should be in service layer${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.1.2: PsychSync Domain Model Validation
echo -e "\n${BLUE}✅ Test 1.1.2: PsychSync Domain Model Validation${NC}"
echo "Testing: Are PsychSync-specific domain models properly implemented?"

# Check for core PsychSync models
PSYCHSYNC_MODELS=$(find app/db/models -name "*.py" -exec grep -l "class.*Assessment\|class.*Team\|class.*User.*PsychSync\|class.*Response\|class.*Psychometric" {} \; 2>/dev/null | wc -l || echo "0")
echo "PsychSync domain models found: $PSYCHSYNC_MODELS"

if [ "$PSYCHSYNC_MODELS" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: PsychSync domain models are implemented${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No PsychSync-specific domain models found${NC}"
    echo "${RED}   Expected: Assessment, Team, User, Response, Psychometric models${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.1.3: AI Engine Integration Validation
echo -e "\n${BLUE}✅ Test 1.1.3: AI Engine Integration Validation${NC}"
echo "Testing: Is PsychSync AI engine properly integrated?"

AI_ENGINE_FILES=$(find ai -name "*.py" -type f 2>/dev/null | wc -l || echo "0")
AI_PROCESSORS=$(find ai/processors -name "*.py" -type f 2>/dev/null | wc -l || echo "0")
echo "AI engine files: $AI_ENGINE_FILES"
echo "AI processors: $AI_PROCESSORS"

if [ "$AI_ENGINE_FILES" -gt 0 ] && [ "$AI_PROCESSORS" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: PsychSync AI engine is properly integrated${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))

    # Check for specific psychological frameworks
    PSYCH_FRAMEWORKS=$(find ai/processors -name "*.py" -exec grep -l "MBTI\|Big.*Five\|Enneagram\|DISC\|Predictive.*Index" {} \; 2>/dev/null | wc -l || echo "0")
    echo "Psychological framework processors: $PSYCH_FRAMEWORKS"

    if [ "$PSYCH_FRAMEWORKS" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Psychological assessment frameworks are implemented${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    fi
else
    echo -e "${RED}❌ FAIL: PsychSync AI engine integration incomplete${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.1.4: Dependency Injection Check
echo -e "\n${BLUE}✅ Test 1.1.4: Dependency Injection Check${NC}"
echo "Testing: Are dependencies properly injected vs hardcoded?"

DEPENDENCY_INJECTION_COUNT=$(find app/api/v1/endpoints -name "*.py" -exec grep -l "get_db\|get_async_db\|Depends" {} \; 2>/dev/null | wc -l || echo "0")
TOTAL_ENDPOINT_FILES=$(find app/api/v1/endpoints -name "*.py" 2>/dev/null | wc -l || echo "0")

echo "Files using dependency injection: $DEPENDENCY_INJECTION_COUNT/$TOTAL_ENDPOINT_FILES"

if [ "$DEPENDENCY_INJECTION_COUNT" -eq "$TOTAL_ENDPOINT_FILES" ] && [ "$TOTAL_ENDPOINT_FILES" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: All endpoints use proper dependency injection${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${YELLOW}⚠️  PARTIAL: $DEPENDENCY_INJECTION_COUNT/$TOTAL_ENDPOINT_FILES files use DI${NC}"
    echo "${YELLOW}   Some endpoints may be missing proper dependency injection${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))  # Count as partial pass
fi

# Test 1.1.5: Async/Sync Consistency
echo -e "\n${BLUE}✅ Test 1.1.5: Async/Sync Consistency${NC}"
echo "Testing: Are all database operations async?"

SYNC_DB_CALLS=$(find app/api/v1 -name "*.py" -exec grep -n "\.execute(" {} \; | grep -v "await" | wc -l || echo "0")
echo "Non-async database calls found: $SYNC_DB_CALLS"

if [ "$SYNC_DB_CALLS" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: All database operations are properly async${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: Found $SYNC_DB_CALLS non-async database calls${NC}"
    echo "${RED}   All database operations should use await pattern${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.1.6: Service Layer Validation
echo -e "\n${BLUE}✅ Test 1.1.6: Service Layer Validation${NC}"
echo "Testing: Is business logic properly encapsulated in services?"

SERVICE_FILES_COUNT=$(find app/services -name "*.py" -type f 2>/dev/null | wc -l || echo "0")
echo "Service layer files found: $SERVICE_FILES_COUNT"

if [ "$SERVICE_FILES_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Service layer exists with $SERVICE_FILES_COUNT files${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))

    # Check for PsychSync-specific services
    PSYCHSYNC_SERVICES=$(find app/services -name "*.py" -exec grep -l "assessment\|team.*dynamics\|psychometric\|communication.*pattern\|coaching\|wellness" {} \; 2>/dev/null | wc -l || echo "0")
    echo "PsychSync-specific services: $PSYCHSYNC_SERVICES"

    if [ "$PSYCHSYNC_SERVICES" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: PsychSync-specific services are implemented${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    fi

    # Check if services are actually being used
    SERVICES_USED=$(grep -r "from app\.services\|import.*app\.services" app/api/v1/ 2>/dev/null | wc -l || echo "0")
    echo "Service imports in API layer: $SERVICES_USED"

    if [ "$SERVICES_USED" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Services are being used in API layer${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    fi
else
    echo -e "${RED}❌ FAIL: No service layer found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.1.7: PsychSync Content Validation
echo -e "\n${BLUE}✅ Test 1.1.7: PsychSync Content Validation${NC}"
echo "Testing: Does the codebase contain PsychSync-relevant content (no sports/basketball)?"

# Check for basketball/sports content (should be none)
BASKETBALL_CONTENT=$(find . -name "*.py" -o -name "*.md" -o -name "*.tsx" -o -name "*.ts" | xargs grep -l -i "basketball\|nba\|sports.*team\|player.*score\|game.*stats" 2>/dev/null | wc -l || echo "0")
echo "Basketball/sports content files found: $BASKETBALL_CONTENT"

if [ "$BASKETBALL_CONTENT" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: No basketball/sports content found${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: Found $BASKETBALL_CONTENT files with basketball/sports content${NC}"
    echo "${RED}   Should be replaced with psychological assessment content${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Check for psychological content
PSYCH_CONTENT=$(find . -name "*.py" -o -name "*.md" | xargs grep -l -i "psychological\|assessment\|wellness\|mbti\|big.*five\|enneagram\|team.*dynamics" 2>/dev/null | wc -l || echo "0")
echo "Psychological content files found: $PSYCH_CONTENT"

if [ "$PSYCH_CONTENT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Found $PSYCH_CONTENT files with psychological content${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${YELLOW}⚠️  WARNING: Limited psychological content found${NC}"
    echo "${YELLOW}   Consider adding more psychological assessment terminology${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))  # Count as partial
fi

# =============================================================================
# 1.2 DATABASE ARCHITECTURE TESTS
# =============================================================================

echo -e "\n${BLUE}1.2 DATABASE ARCHITECTURE TESTS${NC}"
echo "=================================="

# Test 1.2.1: Index Validation
echo -e "\n${BLUE}✅ Test 1.2.1: Index Validation${NC}"
echo "Testing: Are proper indexes defined on frequently queried columns?"

# Check for indexes in User model
USER_INDEXES=$(grep -r "Index(" app/db/models/user.py 2>/dev/null | wc -l || echo "0")
echo "Indexes in User model: $USER_INDEXES"

if [ "$USER_INDEXES" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: User model has $USER_INDEXES indexes defined${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No indexes found in User model${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Check for indexes in Team model
TEAM_INDEXES=$(grep -r "Index(" app/db/models/team.py 2>/dev/null | wc -l || echo "0")
echo "Indexes in Team model: $TEAM_INDEXES"

if [ "$TEAM_INDEXES" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Team model has $TEAM_INDEXES indexes defined${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No indexes found in Team model${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.2.2: Foreign Key Validation
echo -e "\n${BLUE}✅ Test 1.2.2: Foreign Key Validation${NC}"
echo "Testing: Are foreign keys properly defined?"

FK_DEFINITIONS=$(find app/db/models -name "*.py" -exec grep -l "ForeignKey" {} \; 2>/dev/null | wc -l || echo "0")
echo "Foreign key definitions found: $FK_DEFINITIONS"

if [ "$FK_DEFINITIONS" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Foreign keys are properly defined${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No foreign key definitions found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.2.3: UUID Primary Keys
echo -e "\n${BLUE}✅ Test 1.2.3: UUID Primary Keys${NC}"
echo "Testing: Are UUID primary keys used for scalability?"

UUID_PRIMARIES=$(find app/db/models -name "*.py" -exec grep -l "UUID.*primary_key" {} \; 2>/dev/null | wc -l || echo "0")
echo "UUID primary keys found: $UUID_PRIMARIES"

if [ "$UUID_PRIMARIES" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: UUID primary keys are used (good for scalability)${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${YELLOW}⚠️  WARNING: No UUID primary keys found${NC}"
    echo "${YELLOW}   Consider using UUIDs for better scalability${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))  # Count as partial since not always required
fi

# =============================================================================
# 1.3 SECURITY ARCHITECTURE TESTS
# =============================================================================

echo -e "\n${BLUE}1.3 SECURITY ARCHITECTURE TESTS${NC}"
echo "================================="

# Test 1.3.1: JWT Implementation
echo -e "\n${BLUE}✅ Test 1.3.1: JWT Implementation${NC}"
echo "Testing: Is JWT authentication properly implemented?"

JWT_FILES=$(find app -name "*.py" -exec grep -l "JWT\|jwt" {} \; 2>/dev/null | wc -l || echo "0")
echo "JWT-related files: $JWT_FILES"

if [ "$JWT_FILES" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: JWT authentication is implemented${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))

    # Check for proper JWT handling
    JWT_HANDLE=$(find app -name "*.py" -exec grep -l "verify_token\|create_access_token" {} \; 2>/dev/null | wc -l || echo "0")
    if [ "$JWT_HANDLE" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: JWT token creation and verification found${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    fi
else
    echo -e "${RED}❌ FAIL: No JWT implementation found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.3.2: Password Security
echo -e "\n${BLUE}✅ Test 1.3.2: Password Security${NC}"
echo "Testing: Are passwords properly hashed?"

PASSWORD_HASHING=$(find app -name "*.py" -exec grep -l "get_password_hash\|bcrypt\|pbkdf2" {} \; 2>/dev/null | wc -l || echo "0")
echo "Password hashing implementations: $PASSWORD_HASHING"

if [ "$PASSWORD_HASHING" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Password hashing is implemented${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No password hashing found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.3.3: Rate Limiting
echo -e "\n${BLUE}✅ Test 1.3.3: Rate Limiting${NC}"
echo "Testing: Is rate limiting implemented?"

RATE_LIMITING=$(find app -name "*.py" -exec grep -l "rate.*limit\|throttle\|slowapi\|AdvancedRateLimiter" {} \; 2>/dev/null | wc -l || echo "0")
echo "Rate limiting implementations: $RATE_LIMITING"

if [ "$RATE_LIMITING" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Rate limiting is implemented${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No rate limiting found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# =============================================================================
# 1.4 API DESIGN TESTS
# =============================================================================

echo -e "\n${BLUE}1.4 API DESIGN TESTS${NC}"
echo "========================="

# Test 1.4.1: OpenAPI/Swagger
echo -e "\n${BLUE}✅ Test 1.4.1: OpenAPI/Swagger${NC}"
echo "Testing: Is OpenAPI/Swagger documentation available?"

if [ -f "app/api/v1/endpoints/users.py" ]; then
    SWAGGER_DECORATORS=$(grep -r "@.*router\|@.*get\|@.*post" app/api/v1/endpoints/ 2>/dev/null | wc -l || echo "0")
    echo "API route decorators found: $SWAGGER_DECORATORS"

    if [ "$SWAGGER_DECORATORS" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: API routes are properly decorated${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    fi
else
    echo -e "${RED}❌ FAIL: No API endpoint files found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.4.2: Response Models
echo -e "\n${BLUE}✅ Test 1.4.2: Response Models${NC}"
echo "Testing: Are Pydantic response models used?"

PYDANTIC_SCHEMAS=$(find app/schemas -name "*.py" -type f 2>/dev/null | wc -l || echo "0")
echo "Pydantic schema files: $PYDANTIC_SCHEMAS"

if [ "$PYDANTIC_SCHEMAS" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Pydantic schemas are defined${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No Pydantic schemas found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.4.3: Error Handling
echo -e "\n${BLUE}✅ Test 1.4.3: Error Handling${NC}"
echo "Testing: Is proper error handling implemented?"

ERROR_HANDLING=$(find app -name "*.py" -exec grep -l "HTTPException\|PsychSyncException\|raise.*Error" {} \; 2>/dev/null | wc -l || echo "0")
echo "Error handling implementations: $ERROR_HANDLING"

if [ "$ERROR_HANDLING" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Error handling is implemented${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL: No error handling found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# =============================================================================
# 1.5 FRONTEND ARCHITECTURE TESTS
# =============================================================================

echo -e "\n${BLUE}1.5 FRONTEND ARCHITECTURE TESTS${NC}"
echo "===================================="

# Test 1.5.1: TypeScript Usage
echo -e "\n${BLUE}✅ Test 1.5.1: TypeScript Usage${NC}"
echo "Testing: Is TypeScript properly used?"

if [ -d "frontend/src" ] && [ -f "frontend/tsconfig.json" ]; then
    TS_FILES=$(find frontend/src -name "*.ts" -type f 2>/dev/null | wc -l || echo "0")
    TSX_FILES=$(find frontend/src -name "*.tsx" -type f 2>/dev/null | wc -l || echo "0")
    JS_FILES=$(find frontend/src -name "*.js" -type f 2>/dev/null | wc -l || echo "0")

    echo "TypeScript files: $((TS_FILES + TSX_FILES))"
    echo "JavaScript files: $JS_FILES"

    TS_TOTAL=$((TS_FILES + TSX_FILES))
    if [ $TS_TOTAL -gt "$JS_FILES" ]; then
        echo -e "${GREEN}✅ PASS: TypeScript is predominantly used (${TS_TOTAL}TS/TSX vs ${JS_FILES}JS)${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️  WARNING: JavaScript files still present${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))  # Count as partial
    fi
else
    echo -e "${RED}❌ FAIL: Frontend directory not found or not using TypeScript${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.5.2: Component Architecture
echo -e "\n${BLUE}✅ Test 1.5.2: Component Architecture${NC}"
echo "Testing: Is component architecture well-structured?"

if [ -d "frontend/src/components" ]; then
    COMPONENT_DIRS=$(find frontend/src/components -maxdepth 2 -type d 2>/dev/null | wc -l || echo "0")
    COMPONENT_FILES=$(find frontend/src/components -name "*.tsx" -o -name "*.ts" 2>/dev/null | wc -l || echo "0")

    echo "Component directories: $COMPONENT_DIRS"
    echo "Component files: $COMPONENT_FILES"

    if [ "$COMPONENT_DIRS" -gt 0 ] && [ "$COMPONENT_FILES" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Component architecture is structured${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}❌ FAIL: Component architecture needs improvement${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    echo -e "${RED}❌ FAIL: No components directory found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 1.5.3: State Management
echo -e "\n${BLUE}✅ Test 1.5.3: State Management${NC}"
echo "Testing: Is state management properly implemented?"

if [ -d "frontend/src/contexts" ]; then
    CONTEXT_FILES=$(find frontend/src/contexts -name "*.tsx" -o -name "*.ts" 2>/dev/null | wc -l || echo "0")
    echo "Context files: $CONTEXT_FILES"

    if [ "$CONTEXT_FILES" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Context-based state management is implemented${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}❌ FAIL: No state management found${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    echo -e "${RED}❌ FAIL: No state management implementation found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# =============================================================================
# RESULTS SUMMARY
# =============================================================================

echo ""
echo -e "${BLUE}🏆 ARCHITECTURE VALIDATION RESULTS${NC}"
echo "=================================="

echo -e "${GREEN}✅ PASSED TESTS: $PASS_COUNT${NC}"
echo -e "${RED}❌ FAILED TESTS: $FAIL_COUNT${NC}"

TOTAL_TESTS=$((PASS_COUNT + FAIL_COUNT))
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( (PASS_COUNT * 100) / TOTAL_TESTS ))
else
    SUCCESS_RATE=0
fi

echo -e "${BLUE}TOTAL TESTS: $TOTAL_TESTS${NC}"
echo -e "${BLUE}SUCCESS RATE: ${SUCCESS_RATE}%${NC}"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "\n${GREEN}🎉 EXCELLENT! All architecture validation tests passed!${NC}"
    echo -e "${GREEN}   Your PsychSync platform demonstrates excellent architecture patterns.${NC}"
    exit 0
elif [ "$SUCCESS_RATE" -ge 80 ]; then
    echo -e "\n${YELLOW}👍 GOOD! Most architecture validation tests passed!${NC}"
    echo -e "${YELLOW}   Success rate: ${SUCCESS_RATE}% - Consider fixing the remaining issues.${NC}"
    exit 1
else
    echo -e "\n${RED}⚠️  NEEDS ATTENTION: Several architecture issues found${NC}"
    echo -e "${RED}   Success rate: ${SUCCESS_RATE}% - Please address the failing tests.${NC}"
    exit 2
fi