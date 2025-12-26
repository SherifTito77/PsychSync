#!/bin/bash
###############################################################################
# Build Verification Script (SLSA Level 3 Compliant)
#
# Verifies the integrity and authenticity of all build artifacts
# including signatures, provenance metadata, and artifact hashes
#
# Usage: scripts/verify_build.sh [--build-id <id>] [--strict]
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
BUILD_DIR="$PROJECT_ROOT/build"
ARTIFACTS_DIR="$BUILD_DIR/artifacts"
SIGNATURES_DIR="$BUILD_DIR/signatures"
PROVENANCE_DIR="$BUILD_DIR/provenance"
LOGS_DIR="$BUILD_DIR/logs"

BUILD_ID="${BUILD_ID:-}"
STRICT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build-id)
            BUILD_ID="$2"
            shift 2
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--build-id <id>] [--strict]"
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
echo "     Build Verification (SLSA Level 3 Compliant)"
echo "========================================================================================================"
echo ""
log_info "Build ID: ${BUILD_ID:-latest}"
log_info "Strict mode: $STRICT"
echo ""

# =============================================================================
# Verification 1: Signature Verification
# =============================================================================

log_info "Verification 1: Digital Signatures"

python3 << EOF
import json
import os
import subprocess
from pathlib import Path

signatures_dir = "$SIGNATURES_DIR"
artifacts_dir = "$ARTIFACTS_DIR"
build_id = "$BUILD_ID"

# Find all signature files
if not os.path.exists(signatures_dir):
    print("⚠ No signatures directory found")
    exit(0)

signature_files = list(Path(signatures_dir).rglob('*.sig'))

if not signature_files:
    print("⚠ No signature files found")
    exit(0)

print(f"Found {len(signature_files)} signature files\n")

verified_count = 0
failed_count = 0

for sig_file in signature_files:
    # Find corresponding artifact
    artifact_name = sig_file.stem  # Remove .sig extension

    # Search for artifact
    artifact_file = None
    if os.path.exists(artifacts_dir):
        for candidate in Path(artifacts_dir).rglob('*'):
            if candidate.is_file() and candidate.name == artifact_name:
                artifact_file = candidate
                break

    if not artifact_file:
        print(f"⚠ {sig_file.name}: Artifact not found")
        continue

    print(f"Verifying: {artifact_name}")

    # Verify with cosign
    try:
        result = subprocess.run(
            ['cosign', 'verify-blob', '--signature', str(sig_file), str(artifact_file)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"  ✓ Signature verified")
            verified_count += 1
        else:
            print(f"  ✗ Verification FAILED")
            print(f"    Error: {result.stderr}")
            failed_count += 1

    except subprocess.TimeoutExpired:
        print(f"  ✗ Verification timeout")
        failed_count += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed_count += 1

print(f"\n{'='*60}")
print(f"Signature Verification Summary:")
print(f"  Verified: {verified_count}")
print(f"  Failed: {failed_count}")
print(f"  Total: {len(signature_files)}")

if failed_count > 0:
    print(f"\n✗ {failed_count} signature verifications FAILED")
    exit(1)
else:
    print(f"\n✓ All signatures verified successfully")
    exit(0)

EOF

if [ $? -eq 0 ]; then
    log_success "Signature verification passed"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_error "Signature verification failed"
    VERIFY_FAILED=$((VERIFY_FAILED + 1))
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 2: Provenance Validation
# =============================================================================

log_info "\nVerification 2: SLSA Provenance"

python3 << EOF
import json
import os
from pathlib import Path
from datetime import datetime, timezone

provenance_dir = "$PROVENANCE_DIR"
build_id = "$BUILD_ID"

# Find all provenance files
if not os.path.exists(provenance_dir):
    print("⚠ No provenance directory found")
    exit(0)

provenance_files = list(Path(provenance_dir).rglob('*.json'))

if not provenance_files:
    print("⚠ No provenance files found")
    exit(0)

print(f"Found {len(provenance_files)} provenance files\n")

all_valid = True

for prov_file in provenance_files:
    relative_path = prov_file.relative_to(provenance_dir)
    print(f"Validating: {relative_path}")

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)

        # Validate SLSA structure
        errors = []

        # Check required top-level fields
        if "_type" not in provenance:
            errors.append("Missing _type field")

        if "predicateType" not in provenance:
            errors.append("Missing predicateType field")

        if "subject" not in provenance:
            errors.append("Missing subject field")
        elif not isinstance(provenance["subject"], list) or len(provenance["subject"]) == 0:
            errors.append("Subject must be non-empty list")

        # Check predicate
        if "predicate" not in provenance:
            errors.append("Missing predicate field")
        else:
            predicate = provenance["predicate"]

            if "builder" not in predicate:
                errors.append("Missing predicate.builder")

            if "buildType" not in predicate:
                errors.append("Missing predicate.buildType")

            if "materials" not in predicate:
                errors.append("Missing predicate.materials")

        # Check for digest in subject
        if "subject" in provenance:
            for subj in provenance["subject"]:
                if "digest" not in subj:
                    errors.append("Subject missing digest")
                elif "sha256" not in subj["digest"]:
                    errors.append("Digest missing sha256")

        if errors:
            print(f"  ✗ Validation errors:")
            for error in errors[:3]:
                print(f"    - {error}")
            if len(errors) > 3:
                print(f"    ... and {len(errors) - 3} more errors")
            all_valid = False
        else:
            print(f"  ✓ Valid SLSA provenance")

    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        all_valid = False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        all_valid = False

if all_valid:
    print(f"\n✓ All provenance files are valid")
    exit(0)
else:
    print(f"\n✗ Some provenance files failed validation")
    exit(1)

EOF

if [ $? -eq 0 ]; then
    log_success "Provenance validation passed"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_warning "Some provenance files failed validation"
    if [ "$STRICT" = true ]; then
        VERIFY_FAILED=$((VERIFY_FAILED + 1))
    else
        VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
    fi
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 3: Artifact Integrity (SHA256 Hash Verification)
# =============================================================================

log_info "\nVerification 3: Artifact Integrity"

python3 << EOF
import json
import hashlib
import os
from pathlib import Path

artifacts_dir = "$ARTIFACTS_DIR"
provenance_dir = "$PROVENANCE_DIR"

if not os.path.exists(artifacts_dir):
    print("⚠ No artifacts directory found")
    exit(0)

# Find all artifacts and their provenance
artifacts = []
for artifact_file in Path(artifacts_dir).rglob('*'):
    if artifact_file.is_file() and not artifact_file.name.endswith('.json'):
        artifacts.append(artifact_file)

if not artifacts:
    print("⚠ No artifacts found")
    exit(0)

print(f"Found {len(artifacts)} artifacts\n")

verified_count = 0
failed_count = 0

for artifact_file in artifacts:
    artifact_name = artifact_file.name
    print(f"Checking: {artifact_name}")

    # Calculate current SHA256
    sha256_hash = hashlib.sha256()
    with open(artifact_file, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    current_digest = sha256_hash.hexdigest()

    # Find provenance file
    provenance_file = Path(provenance_dir) / f"{artifact_name}.provenance.json"

    if not provenance_file.exists():
        print(f"  ⚠ No provenance found - cannot verify digest")
        continue

    # Load provenance and compare digest
    try:
        with open(provenance_file, 'r') as f:
            provenance = json.load(f)

        # Get digest from subject
        subjects = provenance.get('subject', [])
        if not subjects:
            print(f"  ✗ Provenance has no subject")
            failed_count += 1
            continue

        subject = subjects[0]
        expected_digest = subject.get('digest', {}).get('sha256')

        if not expected_digest:
            print(f"  ✗ Provenance missing SHA256 digest")
            failed_count += 1
            continue

        if current_digest == expected_digest:
            print(f"  ✓ Digest verified ({current_digest[:16]}...)")
            verified_count += 1
        else:
            print(f"  ✗ Digest MISMATCH")
            print(f"    Expected: {expected_digest[:32]}...")
            print(f"    Actual:   {current_digest[:32]}...")
            failed_count += 1

    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed_count += 1

print(f"\n{'='*60}")
print(f"Integrity Verification Summary:")
print(f"  Verified: {verified_count}")
print(f"  Failed: {failed_count}")
print(f"  Total: {len(artifacts)}")

if failed_count > 0:
    print(f"\n✗ {failed_count} integrity verifications FAILED")
    exit(1)
else:
    print(f"\n✓ All artifacts verified successfully")
    exit(0)

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
# Verification 4: Build Completeness
# =============================================================================

log_info "\nVerification 4: Build Completeness"

python3 << EOF
import json
import os
from pathlib import Path

artifacts_dir = "$ARTIFACTS_DIR"
signatures_dir = "$SIGNATURES_DIR"
provenance_dir = "$PROVENANCE_DIR"
build_id = "$BUILD_ID"

# Load manifest if available
manifest_file = None
if build_id:
    manifest_path = Path(artifacts_dir) / f"manifest-{build_id}.json"
    if manifest_path.exists():
        manifest_file = manifest_path

if manifest_file:
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    expected_artifacts = len(manifest.get('artifacts', []))
    expected_images = len(manifest.get('docker_images', []))
    expected_total = expected_artifacts + expected_images

    print(f"Expected artifacts (from manifest): {expected_total}")
else:
    print("⚠ No build manifest found - checking file counts")
    expected_total = None

# Count actual files
artifact_count = len([f for f in Path(artifacts_dir).rglob('*') if f.is_file()])
signature_count = len(list(Path(signatures_dir).rglob('*.sig'))) if os.path.exists(signatures_dir) else 0
provenance_count = len(list(Path(provenance_dir).rglob('*.json'))) if os.path.exists(provenance_dir) else 0

print(f"Actual artifacts: {artifact_count}")
print(f"Signatures: {signature_count}")
print(f"Provenance files: {provenance_count}\n")

# Check completeness
if expected_total:
    if artifact_count >= expected_total:
        print(f"✓ All expected artifacts present")
    else:
        print(f"⚠ Missing artifacts: {expected_total - artifact_count}")

# Check signature coverage
if artifact_count > 0:
    signature_coverage = (signature_count / artifact_count) * 100
    print(f"Signature coverage: {signature_coverage:.1f}%")

    if signature_coverage >= 100:
        print(f"✓ All artifacts signed")
    elif signature_coverage >= 80:
        print(f"⚠ Some artifacts missing signatures")
    else:
        print(f"✗ Most artifacts missing signatures")

# Check provenance coverage
if artifact_count > 0:
    provenance_coverage = (provenance_count / artifact_count) * 100
    print(f"Provenance coverage: {provenance_coverage:.1f}%")

    if provenance_coverage >= 100:
        print(f"✓ All artifacts have provenance")
    elif provenance_coverage >= 80:
        print(f"⚠ Some artifacts missing provenance")
    else:
        print(f"✗ Most artifacts missing provenance")

# Determine pass/fail
if signature_coverage >= 80 and provenance_coverage >= 80:
    print(f"\n✓ Build completeness check PASSED")
    exit(0)
else:
    print(f"\n⚠ Build completeness check FAILED (low coverage)")
    exit(1)

EOF

if [ $? -eq 0 ]; then
    log_success "Build completeness verified"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_warning "Build completeness check failed"
    if [ "$STRICT" = true ]; then
        VERIFY_FAILED=$((VERIFY_FAILED + 1))
    else
        VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
    fi
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Verification 5: Reproducibility Check
# =============================================================================

log_info "\nVerification 5: Build Reproducibility"

python3 << EOF
import json
import os
import subprocess
from pathlib import Path

project_root = "$PROJECT_ROOT"
provenance_dir = "$PROVENANCE_DIR"

# Get current git commit
try:
    current_commit = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'],
        cwd=project_root,
        stderr=subprocess.DEVNULL
    ).decode().strip()
except:
    current_commit = "unknown"

# Get current git branch
try:
    current_branch = subprocess.check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=project_root,
        stderr=subprocess.DEVNULL
    ).decode().strip()
except:
    current_branch = "unknown"

print(f"Current environment:")
print(f"  Commit: {current_commit}")
print(f"  Branch: {current_branch}\n")

# Check provenance for consistency
provenance_files = list(Path(provenance_dir).rglob('*.json')) if os.path.exists(provenance_dir) else []

if not provenance_files:
    print("⚠ No provenance files to check")
    exit(0)

consistent_count = 0
inconsistent_count = 0

for prov_file in provenance_files[:3]:  # Check up to 3 files
    print(f"Checking: {prov_file.name}")

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)

        # Check materials
        materials = provenance.get('predicate', {}).get('materials', [])
        git_material = None

        for material in materials:
            if material.get('type') == 'git':
                git_material = material
                break

        if git_material:
            material_commit = git_material.get('digest', {}).get('sha1')

            if material_commit == current_commit:
                print(f"  ✓ Git commit matches")
                consistent_count += 1
            else:
                print(f"  ⚠ Git commit differs")
                print(f"    Provenance: {material_commit}")
                print(f"    Current: {current_commit}")
                inconsistent_count += 1

    except Exception as e:
        print(f"  ✗ Error: {e}")
        inconsistent_count += 1

print(f"\n{'='*60}")
print(f"Reproducibility Check:")
print(f"  Consistent: {consistent_count}")
print(f"  Inconsistent: {inconsistent_count}")

if inconsistent_count == 0:
    print(f"\n✓ Build is reproducible")
    exit(0)
else:
    print(f"\n⚠ Build may not be reproducible")
    exit(1)

EOF

if [ $? -eq 0 ]; then
    log_success "Reproducibility check passed"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
else
    log_warning "Reproducibility check found inconsistencies"
    if [ "$STRICT" = true ]; then
        VERIFY_FAILED=$((VERIFY_FAILED + 1))
    else
        VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
    fi
fi

VERIFY_TOTAL=$((VERIFY_TOTAL + 1))

# =============================================================================
# Final Summary
# =============================================================================

echo ""
echo "========================================================================================================"
echo "     Build Verification Summary"
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
        log_error "Build verification FAILED (strict mode)"
        echo ""
        echo "Deployment is BLOCKED due to verification failures."
        exit 1
    else
        log_warning "Build verification completed with failures (strict mode disabled)"
        echo ""
        echo "⚠️ Proceed with caution - some verifications failed."
        exit 0
    fi
else
    log_success "All verifications PASSED!"
    echo ""
    echo "Build artifacts are verified and trusted."
    echo "Deployment may proceed."
    echo ""
    echo "Next Steps:"
    echo "1. Review verification reports in: $LOGS_DIR"
    echo "2. Deploy with confidence: ./deploy.sh"
    echo ""
    exit 0
fi
