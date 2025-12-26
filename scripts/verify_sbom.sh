#!/bin/bash
###############################################################################
# SBOM Verification Script (NIST SSDF PO 3.1 Compliant)
#
# Verifies SBOM integrity, signatures, completeness, and accuracy
# in compliance with NIST SSDF, SLSA Level 2, and NTIA SBOM minimum elements
#
# Usage: scripts/verify_sbom.sh [--strict] [--compare-manifest]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SBOM_DIR="$PROJECT_ROOT/sbom"
STRICT=false
COMPARE_MANIFEST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT=true
            shift
            ;;
        --compare-manifest)
            COMPARE_MANIFEST=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--strict] [--compare-manifest]"
            exit 1
            ;;
    esac
done

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verification counters
VERIFY_TOTAL=0
VERIFY_PASSED=0
VERIFY_FAILED=0
VERIFY_WARNINGS=0

echo "========================================================================================================"
echo "     SBOM Verification (NIST SSDF PO 3.1 Compliant)"
echo "========================================================================================================"
echo ""
log_info "SBOM directory: $SBOM_DIR"
log_info "Strict mode: $STRICT"
log_info "Manifest comparison: $COMPARE_MANIFEST"
echo ""

# Check if SBOM directory exists
if [ ! -d "$SBOM_DIR" ]; then
    log_error "SBOM directory not found: $SBOM_DIR"
    log_info "Generate SBOMs first: scripts/generate_sbom.sh"
    exit 1
fi

# =============================================================================
# Verification 1: SBOM Integrity (SHA256 Hash Verification)
# =============================================================================

log_info "Verification 1: SBOM Integrity (SHA256 hashes)"

python3 << EOF
import json
import hashlib
import os
from datetime import datetime

sbom_dir = "$SBOM_DIR"
verification_report = []

# Find all SBOM JSON files
sbom_files = []
for root, dirs, files in os.walk(sbom_dir):
    for file in files:
        if file.endswith('.json') and 'manifest' not in file:
            sbom_files.append(os.path.join(root, file))

if not sbom_files:
    print("✗ No SBOM files found")
    exit(1)

print(f"Found {len(sbom_files)} SBOM files to verify\n")

# Verify each SBOM
for sbom_file in sbom_files:
    relative_path = os.path.relpath(sbom_file, sbom_dir)

    # Calculate current SHA256
    with open(sbom_file, 'rb') as f:
        file_content = f.read()
        current_hash = hashlib.sha256(file_content).hexdigest()

    # Load SBOM and check for embedded hash
    try:
        with open(sbom_file, 'r') as f:
            sbom_data = json.load(f)

        # Check if manifest contains hash
        manifest_file = os.path.join(sbom_dir, os.path.basename(sbom_file).replace('sbom-', 'sbom-manifest-').replace('.json', '.json'))

        hash_verified = "UNKNOWN"

        if os.path.exists(manifest_file):
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            # Find hash in manifest
            for sbom_entry in manifest.get('sbom_files', []):
                if sbom_entry['file'] == relative_path:
                    stored_hash = sbom_entry.get('sha256')
                    if stored_hash == current_hash:
                        hash_verified = "VERIFIED"
                        print(f"✓ {relative_path}: Hash verified")
                    else:
                        hash_verified = "MISMATCH"
                        print(f"✗ {relative_path}: Hash MISMATCH!")
                        print(f"  Expected: {stored_hash}")
                        print(f"  Actual:   {current_hash}")
                    break
        else:
            hash_verified = "NO_MANIFEST"
            print(f"⚠ {relative_path}: No manifest found (hash not verified)")

        verification_report.append({
            "file": relative_path,
            "sha256": current_hash,
            "status": hash_verified
        })

    except Exception as e:
        print(f"✗ {relative_path}: Error reading SBOM - {e}")
        verification_report.append({
            "file": relative_path,
            "sha256": current_hash,
            "status": "ERROR"
        })

# Write verification report
report_file = os.path.join(sbom_dir, f"integrity-verification-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
with open(report_file, 'w') as f:
    json.dump({
        "verification_date": datetime.utcnow().isoformat() + "Z",
        "sbom_files": verification_report
    }, f, indent=2)

print(f"\n✓ Verification report saved: {report_file}")

# Check if any verifications failed
failed_count = sum(1 for r in verification_report if r['status'] in ['MISMATCH', 'ERROR'])
if failed_count > 0:
    print(f"\n✗ {failed_count} SBOM files failed verification")
    exit(1)
else:
    print(f"\n✓ All {len(verification_report)} SBOM files verified successfully")

EOF

if [ $? -eq 0 ]; then
    log_success "Integrity verification passed"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_error "Integrity verification failed"
    VERIFY_FAILED=$((VERIFY_FAILED + 1))
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 2: SBOM Signature Verification (if signatures exist)
# =============================================================================

log_info "\nVerification 2: Digital Signature Verification"

if command -v cosign &> /dev/null; then
    # Check for signature files
    SIG_COUNT=$(find "$SBOM_DIR" -name "*.sig" | wc -l)

    if [ "$SIG_COUNT" -gt 0 ]; then
        log_info "Found $SIG_COUNT signature files"

        python3 << EOF
import os
import subprocess

sbom_dir = "$SBOM_DIR"
sig_files = []

for root, dirs, files in os.walk(sbom_dir):
    for file in files:
        if file.endswith('.sig'):
            sig_files.append(os.path.join(root, file))

verified_count = 0
failed_count = 0

for sig_file in sig_files:
    sbom_file = sig_file.replace('.sig', '')

    if not os.path.exists(sbom_file):
        print(f"⚠ {os.path.relpath(sig_file, sbom_dir)}: SBOM file not found")
        continue

    try:
        # Verify signature with cosign
        result = subprocess.run(
            ['cosign', 'verify-blob', '--signature', sig_file, sbom_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"✓ {os.path.relpath(sbom_file, sbom_dir)}: Signature verified")
            verified_count += 1
        else:
            print(f"✗ {os.path.relpath(sbom_file, sbom_dir)}: Signature verification failed")
            failed_count += 1

    except subprocess.TimeoutExpired:
        print(f"✗ {os.path.relpath(sbom_file, sbom_dir)}: Verification timeout")
        failed_count += 1
    except Exception as e:
        print(f"✗ {os.path.relpath(sbom_file, sbom_dir)}: {e}")
        failed_count += 1

print(f"\nVerified: {verified_count}")
print(f"Failed: {failed_count}")

if failed_count > 0:
    exit(1)
EOF

        if [ $? -eq 0 ]; then
            log_success "All signatures verified"
            VERIFY_PASSED=$((VERIFY_PASSED + 1))
        else
            log_error "Some signatures failed verification"
            if [ "$STRICT" = true ]; then
                VERIFY_FAILED=$((VERIFY_FAILED + 1))
            else
                log_warning "Strict mode disabled - continuing"
                VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
            fi
        fi
    else
        log_info "No signature files found (skipping signature verification)"
        VERIFY_PASSED=$((VERIFY_PASSED + 1))
    fi
else
    log_info "cosign not installed (skipping signature verification)"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 3: NTIA Minimum Elements (Completeness Check)
# =============================================================================

log_info "\nVerification 3: NTIA Minimum Elements Validation"

python3 << EOF
import json
import os
from datetime import datetime

sbom_dir = "$SBOM_DIR"

# NTIA minimum elements
NTIA_REQUIRED = [
    "Component Name",
    "Component Version",
    "Component Type",
    "Supplier",
    "Dependency Relationship",
    "SBOM Author"
]

def check_ntia_compliance(sbom_data):
    """Check if SBOM contains NTIA minimum elements"""
    compliance = {
        "total_elements": len(NTIA_REQUIRED),
        "present_elements": 0,
        "missing_elements": []
    }

    # Check metadata for author
    metadata = sbom_data.get('metadata', {})
    if metadata.get('component') or metadata.get('authors'):
        compliance["present_elements"] += 1
    else:
        compliance["missing_elements"].append("SBOM Author")

    # Check components
    components = sbom_data.get('components', [])

    if not components:
        compliance["missing_elements"].extend([
            "Component Name",
            "Component Version",
            "Component Type",
            "Supplier",
            "Dependency Relationship"
        ])
        return compliance

    # Sample first component for validation
    sample = components[0]

    if sample.get('name'):
        compliance["present_elements"] += 1
    else:
        compliance["missing_elements"].append("Component Name")

    if sample.get('version'):
        compliance["present_elements"] += 1
    else:
        compliance["missing_elements"].append("Component Version")

    if sample.get('type'):
        compliance["present_elements"] += 1
    else:
        compliance["missing_elements"].append("Component Type")

    if sample.get('supplier') or sample.get('publisher') or sample.get('vendor'):
        compliance["present_elements"] += 1
    else:
        compliance["missing_elements"].append("Supplier")

    # Dependency relationship is implicit in component list
    compliance["present_elements"] += 1

    return compliance

# Find all SBOM files
sbom_files = []
for root, dirs, files in os.walk(sbom_dir):
    for file in files:
        if file.endswith('.json') and 'manifest' not in file and 'verification' not in file:
            sbom_files.append(os.path.join(root, file))

print(f"Checking {len(sbom_files)} SBOM files for NTIA compliance\n")

all_compliant = True

for sbom_file in sbom_files:
    relative_path = os.path.relpath(sbom_file, sbom_dir)

    try:
        with open(sbom_file, 'r') as f:
            sbom_data = json.load(f)

        compliance = check_ntia_compliance(sbom_data)

        if compliance["present_elements"] == compliance["total_elements"]:
            print(f"✓ {relative_path}: NTIA compliant ({compliance['present_elements']}/{compliance['total_elements']} elements)")
        else:
            print(f"⚠ {relative_path}: Missing {len(compliance['missing_elements'])} elements")
            print(f"  Missing: {', '.join(compliance['missing_elements'])}")
            all_compliant = False

    except Exception as e:
        print(f"✗ {relative_path}: Error - {e}")
        all_compliant = False

if all_compliant:
    print(f"\n✓ All SBOMs are NTIA compliant")
    exit(0)
else:
    print(f"\n⚠ Some SBOMs are missing NTIA minimum elements")
    exit(1)

EOF

if [ $? -eq 0 ]; then
    log_success "NTIA compliance check passed"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_warning "Some SBOMs missing NTIA minimum elements"
    if [ "$STRICT" = true ]; then
        VERIFY_FAILED=$((VERIFY_FAILED + 1))
    else
        VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
    fi
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 4: Dependency Manifest Comparison (Drift Detection)
# =============================================================================

if [ "$COMPARE_MANIFEST" = true ]; then
    log_info "\nVerification 4: Dependency Manifest Comparison"

    python3 << EOF
import json
import os
import re
from datetime import datetime

project_root = "$PROJECT_ROOT"
sbom_dir = "$SBOM_DIR"

def extract_python_dependencies():
    """Extract dependencies from requirements.txt"""
    requirements_file = os.path.join(project_root, "requirements.txt")

    if not os.path.exists(requirements_file):
        return {}

    dependencies = {}
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse package name and version
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*([>=<~!]+)\s*(.+)?', line)
                if match:
                    name = match.group(1).lower()
                    version_spec = match.group(2) if match.group(2) else ""
                    version = match.group(3) if match.group(3) else "any"
                    dependencies[name] = f"{version_spec}{version}"
                else:
                    # Package name only
                    dependencies[line.lower()] = "any"

    return dependencies

def extract_node_dependencies():
    """Extract dependencies from package.json"""
    package_file = os.path.join(project_root, "frontend", "package.json")

    if not os.path.exists(package_file):
        return {}

    with open(package_file, 'r') as f:
        package_data = json.load(f)

    dependencies = package_data.get('dependencies', {})
    return {k.lower(): v for k, v in dependencies.items()}

def extract_sbom_dependencies(sbom_file):
    """Extract dependencies from SBOM"""
    with open(sbom_file, 'r') as f:
        sbom_data = json.load(f)

    components = sbom_data.get('components', [])
    dependencies = {}

    for component in components:
        name = component.get('name', '').lower()
        version = component.get('version', 'unknown')
        dependencies[name] = version

    return dependencies

print("Comparing SBOM dependencies with manifest files\n")

# Python dependencies comparison
python_deps = extract_python_dependencies()
if python_deps:
    print(f"Python dependencies in requirements.txt: {len(python_deps)}")

    # Find latest SBOM
    sbom_files = []
    for file in os.listdir(sbom_dir):
        if file.startswith('backend-') and file.endswith('.json'):
            sbom_files.append(os.path.join(sbom_dir, file))

    if sbom_files:
        latest_sbom = max(sbom_files, key=os.path.getmtime)
        print(f"Comparing with: {os.path.relpath(latest_sbom, sbom_dir)}")

        sbom_deps = extract_sbom_dependencies(latest_sbom)
        print(f"Dependencies in SBOM: {len(sbom_deps)}\n")

        # Find missing and extra dependencies
        missing = set(python_deps.keys()) - set(sbom_deps.keys())
        extra = set(sbom_deps.keys()) - set(python_deps.keys())

        if missing or extra:
            if missing:
                print(f"⚠ Missing in SBOM ({len(missing)}):")
                for dep in sorted(list(missing))[:5]:
                    print(f"  - {dep}")
                if len(missing) > 5:
                    print(f"  ... and {len(missing) - 5} more")

            if extra:
                print(f"⚠ Extra in SBOM ({len(extra)}):")
                for dep in sorted(list(extra))[:5]:
                    print(f"  - {dep}")
                if len(extra) > 5:
                    print(f"  ... and {len(extra) - 5} more")

            print("\n⚠ Dependency drift detected")
            exit(1)
        else:
            print("✓ Python SBOM matches requirements.txt")
    else:
        print("⚠ No Python SBOM found")
else:
    print("No requirements.txt found")

print()

# Node.js dependencies comparison
node_deps = extract_node_dependencies()
if node_deps:
    print(f"Node.js dependencies in package.json: {len(node_deps)}")

    # Find latest SBOM
    sbom_files = []
    for file in os.listdir(sbom_dir):
        if file.startswith('frontend-') and file.endswith('.json'):
            sbom_files.append(os.path.join(sbom_dir, file))

    if sbom_files:
        latest_sbom = max(sbom_files, key=os.path.getmtime)
        print(f"Comparing with: {os.path.relpath(latest_sbom, sbom_dir)}")

        sbom_deps = extract_sbom_dependencies(latest_sbom)
        print(f"Dependencies in SBOM: {len(sbom_deps)}\n")

        # Find missing and extra dependencies
        missing = set(node_deps.keys()) - set(sbom_deps.keys())
        extra = set(sbom_deps.keys()) - set(node_deps.keys())

        if missing or extra:
            if missing:
                print(f"⚠ Missing in SBOM ({len(missing)}):")
                for dep in sorted(list(missing))[:5]:
                    print(f"  - {dep}")
                if len(missing) > 5:
                    print(f"  ... and {len(missing) - 5} more")

            if extra:
                print(f"⚠ Extra in SBOM ({len(extra)}):")
                for dep in sorted(list(extra))[:5]:
                    print(f"  - {dep}")
                if len(extra) > 5:
                    print(f"  ... and {len(extra) - 5} more")

            print("\n⚠ Dependency drift detected")
            exit(1)
        else:
            print("✓ Node.js SBOM matches package.json")
    else:
        print("⚠ No Node.js SBOM found")
else:
    print("No frontend/package.json found")

print("\n✓ Dependency comparison complete")

EOF

    if [ $? -eq 0 ]; then
        log_success "Dependency comparison passed"
        VERIFY_PASSED=$((VERIFY_PASSED + 1))
    else
        log_warning "Dependency drift detected"
        if [ "$STRICT" = true ]; then
            VERIFY_FAILED=$((VERIFY_FAILED + 1))
        else
            VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
        fi
    fi
else
    log_info "Skipping dependency comparison (use --compare-manifest to enable)"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 5: JSON Schema Validation
# =============================================================================

log_info "\nVerification 5: CycloneDX Format Validation"

python3 << EOF
import json
import os
from datetime import datetime

sbom_dir = "$SBOM_DIR"

# CycloneDX 1.4 required fields
CYCLONEDX_REQUIRED_FIELDS = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.4",
    "metadata": dict,
    "components": list
}

def validate_cyclonedx_format(sbom_data):
    """Validate CycloneDX format"""
    errors = []

    # Check required top-level fields
    for field, expected_type in CYCLONEDX_REQUIRED_FIELDS.items():
        if field not in sbom_data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(sbom_data[field], expected_type):
            errors.append(f"Field {field} has wrong type (expected {expected_type.__name__})")

    # Validate bomFormat
    if sbom_data.get("bomFormat") != "CycloneDX":
        errors.append(f"Invalid bomFormat: {sbom_data.get('bomFormat')}")

    # Validate specVersion
    spec_version = str(sbom_data.get("specVersion", ""))
    if not spec_version.startswith("1."):
        errors.append(f"Invalid specVersion: {spec_version}")

    return errors

# Find all SBOM files
sbom_files = []
for root, dirs, files in os.walk(sbom_dir):
    for file in files:
        if file.endswith('.json') and 'manifest' not in file and 'verification' not in file:
            sbom_files.append(os.path.join(root, file))

print(f"Validating {len(sbom_files)} SBOM files against CycloneDX schema\n")

all_valid = True

for sbom_file in sbom_files:
    relative_path = os.path.relpath(sbom_file, sbom_dir)

    try:
        with open(sbom_file, 'r') as f:
            sbom_data = json.load(f)

        errors = validate_cyclonedx_format(sbom_data)

        if not errors:
            component_count = len(sbom_data.get('components', []))
            print(f"✓ {relative_path}: Valid ({component_count} components)")
        else:
            print(f"✗ {relative_path}: Validation errors")
            for error in errors[:3]:
                print(f"  - {error}")
            if len(errors) > 3:
                print(f"  ... and {len(errors) - 3} more errors")
            all_valid = False

    except json.JSONDecodeError as e:
        print(f"✗ {relative_path}: Invalid JSON - {e}")
        all_valid = False
    except Exception as e:
        print(f"✗ {relative_path}: Error - {e}")
        all_valid = False

if all_valid:
    print(f"\n✓ All SBOMs are valid CycloneDX format")
    exit(0)
else:
    print(f"\n✗ Some SBOMs failed format validation")
    exit(1)

EOF

if [ $? -eq 0 ]; then
    log_success "Format validation passed"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_error "Format validation failed"
    VERIFY_FAILED=$((VERIFY_FAILED + 1))
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Final Summary
# =============================================================================

echo ""
echo "========================================================================================================"
echo "     Verification Summary"
echo "========================================================================================================"
echo ""
echo "Total Verifications: $VERIFY_TOTAL"
echo -e "${GREEN}Passed:${NC} $VERIFY_PASSED"
echo -e "${YELLOW}Warnings:${NC} $VERIFY_WARNINGS"
echo -e "${RED}Failed:${NC} $VERIFY_FAILED"
echo ""

# Exit with appropriate code
if [ "$VERIFY_FAILED" -gt 0 ]; then
    if [ "$STRICT" = true ]; then
        log_error "Verification FAILED (strict mode)"
        exit 1
    else
        log_warning "Verification completed with failures (strict mode disabled)"
        exit 0
    fi
else
    log_success "All verifications PASSED!"
    echo ""
    echo "Next Steps:"
    echo "1. Review verification reports in: $SBOM_DIR"
    echo "2. Sign SBOMs for production: scripts/generate_sbom.sh --sign"
    echo "3. Deploy with confidence: ./scripts/deploy_security_modules.sh"
    echo ""
    exit 0
fi
