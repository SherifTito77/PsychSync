#!/bin/bash
#
# Production Deployment Script for IR Automation Tools
#
# This script automates the deployment of the incident response
# automation tools to production environments.
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        PsychSync IR Automation Tools - Deployment         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}✗ Error: Must run from project root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠ This script will:${NC}"
echo "  1. Verify IR automation tools are present"
echo "  2. Run the test suite (19 tests)"
echo "  3. Create production directories"
echo "  4. Set up configuration files"
echo "  5. Generate deployment summary"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

# Step 1: Verify IR tools exist
echo -e "\n${BLUE}[1/5] Verifying IR automation tools...${NC}"

TOOLS=(
    "ml/security/poisoning_detector.py"
    "supply_chain/sbom_analyzer.py"
    "security/credential_rotator.py"
    "ml/training/secure_trainer.py"
)

ALL_TOOLS_PRESENT=true
for tool in "${TOOLS[@]}"; do
    if [ -f "$tool" ]; then
        echo -e "${GREEN}✓${NC} $tool"
    else
        echo -e "${RED}✗${NC} $tool (missing)"
        ALL_TOOLS_PRESENT=false
    fi
done

if [ "$ALL_TOOLS_PRESENT" = false ]; then
    echo -e "${RED}✗ Some tools are missing. Cannot proceed.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All IR tools verified${NC}"

# Step 2: Run tests
echo -e "\n${BLUE}[2/5] Running IR automation tool tests...${NC}"
python tests/integration/test_ir_automation_tools.py > /tmp/ir_test_results.txt 2>&1
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}✗ Tests failed. Review output below:${NC}"
    cat /tmp/ir_test_results.txt
    exit 1
fi

# Parse test results
TOTAL_TESTS=$(grep "Total Tests:" /tmp/ir_test_results.txt | awk '{print $3}')
PASSED_TESTS=$(grep "Passed:" /tmp/ir_test_results.txt | awk '{print $2}')

echo -e "${GREEN}✓ All tests passed (${PASSED_TESTS}/${TOTAL_TESTS})${NC}"
rm /tmp/ir_test_results.txt

# Step 3: Create production directories
echo -e "\n${BLUE}[3/5] Setting up production directories...${NC}"

DIRECTORIES=(
    "config/ir_tools"
    "checkpoints/secure_training"
    "audit_logs/model_training"
    "audit_logs/credential-rotation"
    "reports/poisoning-detection"
    "reports/sbom-analysis"
    "backups/credentials"
    "data/corpora"
    "data/baselines"
    "sbom"
)

for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
    echo -e "${GREEN}✓${NC} Created: $dir"
done

echo -e "${GREEN}✓ Directories created${NC}"

# Step 4: Create configuration files
echo -e "\n${BLUE}[4/5] Creating configuration files...${NC}"

# Poisoning Detector Config
cat > config/ir_tools/poisoning_detector_config.json << 'EOF'
{
  "z_score_threshold": 3.0,
  "min_samples_for_stats": 100,
  "backdoor_patterns": ["TODO", "FIXME", "XXX", "HACK"],
  "enable_provenance_check": true,
  "label_flip_threshold": 0.1
}
EOF
echo -e "${GREEN}✓${NC} config/ir_tools/poisoning_detector_config.json"

# SBOM Analyzer Config
cat > config/ir_tools/sbom_analyzer_config.json << 'EOF'
{
  "allowed_licenses": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"],
  "prohibited_licenses": ["GPL-3.0", "AGPL-3.0", "SSPL", "CPOL"],
  "enable_vulnerability_queries": true,
  "query_nvd": true,
  "query_github": true,
  "query_pypi": true,
  "nvd_api_key": "",
  "github_token": "",
  "request_timeout_seconds": 30
}
EOF
echo -e "${GREEN}✓${NC} config/ir_tools/sbom_analyzer_config.json"

# Credential Rotator Config
cat > config/ir_tools/credential_rotator_config.json << 'EOF'
{
  "backup_before_rotation": true,
  "backup_dir": "backups/credentials",
  "verify_after_rotation": true,
  "enable_rollback": true,
  "rotation_timeout_seconds": 300,
  "connection_timeout_seconds": 30,
  "max_retries": 3
}
EOF
echo -e "${GREEN}✓${NC} config/ir_tools/credential_rotator_config.json"

# Secure Trainer Config
cat > config/ir_tools/secure_trainer_config.json << 'EOF'
{
  "checkpoint_dir": "checkpoints/secure_training",
  "audit_log_dir": "audit_logs/model_training",
  "enable_gradient_monitoring": true,
  "enable_adversarial_detection": true,
  "enable_backdoor_detection": true,
  "anomaly_threshold": 2.0,
  "save_every_n_epochs": 1,
  "max_checkpoints_to_keep": 5,
  "gradient_explosion_threshold": 100.0,
  "gradient_vanishing_threshold": 1e-07,
  "loss_spike_multiplier": 3.0
}
EOF
echo -e "${GREEN}✓${NC} config/ir_tools/secure_trainer_config.json"

echo -e "${GREEN}✓ Configuration files created${NC}"

# Step 5: Generate deployment summary
echo -e "\n${BLUE}[5/5] Generating deployment summary...${NC}"

# Count lines of code
POISONING_LOC=$(wc -l < ml/security/poisoning_detector.py 2>/dev/null || echo "0")
SBOM_LOC=$(wc -l < supply_chain/sbom_analyzer.py 2>/dev/null || echo "0")
ROTATOR_LOC=$(wc -l < security/credential_rotator.py 2>/dev/null || echo "0")
TRAINER_LOC=$(wc -l < ml/training/secure_trainer.py 2>/dev/null || echo "0")
TOTAL_LOC=$((POISONING_LOC + SBOM_LOC + ROTATOR_LOC + TRAINER_LOC))

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              IR AUTOMATION TOOLS - DEPLOYMENT              ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Status: ${YELLOW}READY FOR PRODUCTION${GREEN}                             ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Tools Deployed:                                               ║${NC}"
echo -e "${GREEN}║  ┌─────────────────────────────────────────────────────────┐ ║${NC}"
echo -e "${GREEN}║  │ 1. Data Poisoning Detector                    ${POISONING_LOC} LOC │ ║${NC}"
echo -e "${GREEN}║  │    ml/security/poisoning_detector.py                   │ ║${NC}"
echo -e "${GREEN}║  ├─────────────────────────────────────────────────────────┤ ║${NC}"
echo -e "${GREEN}║  │ 2. SBOM Analyzer                              ${SBOM_LOC} LOC │ ║${NC}"
echo -e "${GREEN}║  │    supply_chain/sbom_analyzer.py                      │ ║${NC}"
echo -e "${GREEN}║  ├─────────────────────────────────────────────────────────┤ ║${NC}"
echo -e "${GREEN}║  │ 3. Credential Rotator                         ${ROTATOR_LOC} LOC │ ║${NC}"
echo -e "${GREEN}║  │    security/credential_rotator.py                      │ ║${NC}"
echo -e "${GREEN}║  ├─────────────────────────────────────────────────────────┤ ║${NC}"
echo -e "${GREEN}║  │ 4. Secure Model Trainer                      ${TRAINER_LOC} LOC │ ║${NC}"
echo -e "${GREEN}║  │    ml/training/secure_trainer.py                      │ ║${NC}"
echo -e "${GREEN}║  └─────────────────────────────────────────────────────────┘ ║${NC}"
echo -e "${GREEN}║  Total: ${TOTAL_LOC} lines of production code                      ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Testing:                                                     ║${NC}"
echo -e "${GREEN}║  • Integration Tests: ${YELLOW}${PASSED_TESTS}/${TOTAL_TESTS} passing${GREEN}                        ║${NC}"
echo -e "${GREEN}║  • Test Coverage: ${YELLOW}19 test scenarios${GREEN}                          ║${NC}"
echo -e "${GREEN}║  • Test File: ${YELLOW}tests/integration/test_ir_automation_tools.py${GREEN}   ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Configuration Files Created:                                  ║${NC}"
echo -e "${GREEN}║  • config/ir_tools/poisoning_detector_config.json            ║${NC}"
echo -e "${GREEN}║  • config/ir_tools/sbom_analyzer_config.json                 ║${NC}"
echo -e "${GREEN}║  • config/ir_tools/credential_rotator_config.json            ║${NC}"
echo -e "${GREEN}║  • config/ir_tools/secure_trainer_config.json                ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Documentation:                                                ║${NC}"
echo -e "${GREEN}║  • Complete Guide: ${YELLOW}docs/IR_AUTOMATION_TOOLS_GUIDE.md${GREEN}        ║${NC}"
echo -e "${GREEN}║  • Incident Runbooks: ${YELLOW}docs/incidents/${GREEN}                        ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Quick Start Commands:                                        ║${NC}"
echo -e "${GREEN}║  # Test poisoning detection                                   ║${NC}"
echo -e "${GREEN}║  python -m ml.security.poisoning_detector \\                 ║${NC}"
echo -e "${GREEN}║      --corpus data/corpora/test --corpus-id TEST_001         ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║  # Analyze SBOM                                               ║${NC}"
echo -e "${GREEN}║  python -m supply_chain.sbom_analyzer \\                      ║${NC}"
echo -e "${GREEN}║      --sbom sbom/latest/cyclonedx.json                        ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║  # Test credential rotation (dry-run)                         ║${NC}"
echo -e "${GREEN}║  python -m security.credential_rotator \\                     ║${NC}"
echo -e "${GREEN}║      --credentials config/creds.json --dry-run                ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║  # Train model with monitoring                                ║${NC}"
echo -e "${GREEN}║  python -m ml.training.secure_trainer \\                      ║${NC}"
echo -e "${GREEN}║      --corpus-path data/train --model-config config/model.json ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Integration with Incident Response Runbooks:                 ║${NC}"
echo -e "${GREEN}║  • LLM Data Leakage: docs/incidents/LLM_DATA_LEAKAGE_IR_...  ║${NC}"
echo -e "${GREEN}║  • Poisoned Corpora: docs/incidents/POISONED_CORPORA_IR_...   ║${NC}"
echo -e "${GREEN}║  • Supply Chain:     docs/incidents/SUPPLY_CHAIN_COMPROMISE_ ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✅ IR Automation Tools deployment complete!${NC}\n"

echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Review configuration in ${YELLOW}config/ir_tools/${NC}"
echo -e "  2. Update SBOM analyzer config with API keys (optional)"
echo -e "  3. Test each tool with sample data"
echo -e "  4. Integrate with incident response procedures"
echo -e "  5. See ${YELLOW}docs/IR_AUTOMATION_TOOLS_GUIDE.md${NC} for complete guide\n"
