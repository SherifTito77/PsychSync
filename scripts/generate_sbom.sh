#!/bin/bash
###############################################################################
# SBOM Generation Script (NIST SSDF PO 3.1 Compliant)
#
# Generates Software Bill of Materials (SBOM) for all project artifacts
# in compliance with NIST SSDF, SLSA Level 2, and NTIA SBOM minimum elements
#
# Usage: scripts/generate_sbom.sh [--sign|--verify]
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
OUTPUT_DIR="$PROJECT_ROOT/sbom"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SIGN_KEY="${SIGN_KEY:-$PROJECT_ROOT/certs/sbom-signing-key.pem}"

# Parse arguments
SIGN=false
VERIFY=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --sign)
            SIGN=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--sign] [--verify] [--clean]"
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

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "========================================================================================================"
echo "     SBOM Generation (NIST SSDF PO 3.1 Compliant)"
echo "========================================================================================================"
echo ""
log_info "Output directory: $OUTPUT_DIR"
log_info "Timestamp: $TIMESTAMP"
echo ""

# =============================================================================
# SBOM Generation for Python Backend
# =============================================================================

log_info "Generating SBOM for Python backend..."

cd "$PROJECT_ROOT"

# Generate requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    log_info "Generating requirements.txt from virtual environment..."
    pip freeze > requirements.txt
fi

# Method 1: Using CycloneDX Python (preferred)
log_info "Generating CycloneDX SBOM for Python..."

python3 << 'EOF'
import sys
import json
from datetime import datetime

try:
    from cyclonedx.model.component import Component
    from cyclonedx.model.bom import Bom
    from cyclonedx.parser.requirements import RequirementsFileParser
    from cyclonedx.output import get_instance

    # Parse requirements.txt
    parser = RequirementsFileParser()
    requirements_file = "requirements.txt"

    try:
        with open(requirements_file, 'r') as f:
            content = f.read()

        # Parse requirements
        components = parser.parse(content)

        # Create BOM
        bom = Bom()
        bom.components = components

        # Output CycloneDX JSON
        output_dir = "sbom"
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CycloneDX JSON
        json_output = get_instance(bom, "json")
        json_file = f"{output_dir}/backend-cyclonedx-{timestamp}.json"
        with open(json_file, 'w') as f:
            json_output.output_to_file(f, validate=True)
        print(f"✓ Generated: {json_file}")

        # CycloneDX XML
        xml_output = get_instance(bom, "xml")
        xml_file = f"{output_dir}/backend-cyclonedx-{timestamp}.xml"
        with open(xml_file, 'w') as f:
            xml_output.output_to_file(f)
        print(f"✓ Generated: {xml_file}")

    except Exception as e:
        print(f"✗ CycloneDX generation failed: {e}")
        sys.exit(1)

except ImportError:
    print("✗ CycloneDX not installed. Run: pip install cyclonedx-bom cyclonedx-python")
    sys.exit(1)
EOF

# Method 2: Using pip-audit (alternative)
log_info "Generating pip-audit SBOM (alternative)..."

pip-audit --format json --output-dir "$OUTPUT_DIR" || log_warning "pip-audit SBOM generation failed"

# =============================================================================
# SBOM Generation for Node.js Frontend
# =============================================================================

log_info "Generating SBOM for Node.js frontend..."

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"

    # Generate CycloneDX SBOM
    log_info "Generating CycloneDX SBOM for Node.js..."

    # Try using @cyclonedx/cyclonedx-npm if installed
    if npm list @cyclonedx/cyclonedx-npm &> /dev/null; then
        npx @cyclonedx/cyclonedx-npm --output-file "$OUTPUT_DIR/frontend-cyclonedx-$TIMESTAMP.json" || \
            log_warning "CycloneDX npm generation failed"
    fi

    # Try using sbomify if installed
    if npm list sbomify &> /dev/null; then
        npx sbomify --output "$OUTPUT_DIR/frontend-sbomify-$TIMESTAMP.json" || \
            log_warning "sbomify generation failed"
    fi

    # Generate package-lock.json SBOM manually as fallback
    if [ -f "package-lock.json" ]; then
        log_info "Extracting dependency tree from package-lock.json..."

        python3 << EOF
import json
from datetime import datetime

package_lock = "frontend/package-lock.json"
output_dir = "sbom"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

try:
    with open(package_lock, 'r') as f:
        lock_data = json.load(f)

    dependencies = {}

    def extract_dependencies(deps, prefix=""):
        if not isinstance(deps, dict):
            return

        for name, info in deps.items():
            if name.startswith('node_modules'):
                continue

            dep_name = f"{prefix}{name}" if prefix else name
            dep_version = info.get('version', 'unknown')
            dependencies[dep_name] = dep_version

            # Extract transitive dependencies
            if 'dependencies' in info:
                extract_dependencies(info['dependencies'], f"{dep_name} > ")

    # Extract dependencies from lockfile structure
    if 'dependencies' in lock_data:
        extract_dependencies(lock_data['dependencies'])

    # Create minimal SBOM
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": {
                "name": "psychsync-frontend",
                "type": "application",
                "version": "1.0.0"
            },
            "tools": [
                {
                    "vendor": "PsychSync",
                    "name": "manual-extraction",
                    "version": "1.0"
                }
            ]
        },
        "components": [
            {
                "name": name,
                "version": version,
                "purl": f"pkg:npm/{name}@{version}",
                "type": "library"
            }
            for name, version in dependencies.items()
        ]
    }

    # Write SBOM
    import os
    os.makedirs(output_dir, exist_ok=True)
    sbom_file = f"{output_dir}/frontend-manual-{timestamp}.json"

    with open(sbom_file, 'w') as f:
        json.dump(sbom, f, indent=2)

    print(f"✓ Generated: {sbom_file}")

except Exception as e:
    print(f"✗ Manual SBOM generation failed: {e}")

EOF
    fi

    cd "$PROJECT_ROOT"
fi

# =============================================================================
# Docker Image SBOM (if applicable)
# =============================================================================

log_info "Generating Docker image SBOM..."

if check_installed trivy; then
    # Generate SBOM for backend Docker image
    if [ -f "Dockerfile" ]; then
        log_info "Generating SBOM for Docker image..."

        # Build image tag
        IMAGE_TAG="psychsync-backend:local-$TIMESTAMP"

        # Note: Actually building the image may take time
        # Uncomment if you want to build and scan the actual image
        # docker build -t $IMAGE_TAG .

        # Generate SBOM from Dockerfile (without building)
        log_info "Generating Docker SBOM from image (without building)..."
        trivy image --format cyclonedx --output "$OUTPUT_DIR/docker-backend-$TIMESTAMP.json" psychsync-backend:latest || \
            log_warning "Docker SBOM generation failed (image may not exist locally)"
    fi
fi

# =============================================================================
# Metadata and Manifest
# =============================================================================

log_info "Generating SBOM manifest..."

python3 << EOF
import json
from datetime import datetime
import os
import subprocess
import hashlib

output_dir = "sbom"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Gather metadata
metadata = {
    "sbom_format": "CycloneDX",
    "spec_version": "1.4",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "project": "PsychSync",
    "version": "1.0.0",
    "description": "PsychSync SaaS Platform - Complete SBOM",
    "generator": {
        "name": "PsychSync Secure SDLC",
        "version": "1.0",
        "documentation": "docs/SECURITY_QUICK_START_DEVELOPER.md"
    },
    "build_environment": {
        "os": subprocess.run(['uname', '-s'], capture_output=True, text=True).stdout.strip(),
        "python_version": subprocess.run(['python3', '--version'], capture_output=True, text=True).stdout.strip(),
        "node_version": subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip() if os.path.exists('/usr/bin/node') else "Not installed"
    },
    "sbom_files": []
}

# List all generated SBOM files
for root, dirs, files in os.walk(output_dir):
    for file in files:
        if file.endswith('.json') or file.endswith('.xml'):
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, output_dir)

            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            metadata["sbom_files"].append({
                "file": rel_path,
                "sha256": file_hash,
                "format": "CycloneDX" if file.endswith('.json') else "SPDX"
            })

# Write manifest
manifest_file = f"{output_dir}/sbom-manifest-{timestamp}.json"
with open(manifest_file, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"✓ Generated: {manifest_file}")

EOF

# =============================================================================
# Signing (Optional)
# =============================================================================

if [ "$SIGN" = true ]; then
    log_info "Signing SBOM files..."

    if check_installed cosign; then
        # Sign each SBOM file
        for sbom_file in "$OUTPUT_DIR"/*.json; do
            if [ -f "$sbom_file" ]; then
                log_info "Signing: $sbom_file"

                # Sign with sigstore/cosign
                # Note: This requires GitHub Actions or other OIDC provider
                cosign sign-blob "$sbom_file" || log_warning "Failed to sign $sbom_file"
            fi
        done
    else
        log_warning "sigstore/cosign not installed. Skipping signing."
    fi
fi

# =============================================================================
# Verification (Optional)
# =============================================================================

if [ "$VERIFY" = true ]; then
    log_info "Verifying SBOM signatures..."

    for sbom_file in "$OUTPUT_DIR"/*.sig; do
        if [ -f "$sbom_file" ]; then
            cosign verify-blob "$sbom_file" || log_error "Verification failed for $sbom_file"
        fi
    done
fi

# =============================================================================
# Cleanup Old SBOMs
# =============================================================================

if [ "$CLEAN" = true ]; then
    log_info "Cleaning old SBOM files (older than 7 days)..."

    find "$OUTPUT_DIR" -name "*.json" -mtime +7 -delete
    find "$OUTPUT_DIR" -name "*.xml" -mtime +7 -delete

    log_success "Old SBOM files cleaned up"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "========================================================================================================"
log_success "SBOM generation completed!"
echo "========================================================================================================"
echo ""
log_info "SBOM Location: $OUTPUT_DIR"
echo ""
log_info "Generated Files:"
ls -lh "$OUTPUT_DIR" | tail -n +2
echo ""
log_info "Next Steps:"
echo "1. Review SBOM files: cat sbom/backend-cyclonedx-*.json"
echo "2. Scan for vulnerabilities: scripts/scan_dependencies.sh"
echo "3. Verify SBOM integrity: scripts/verify_sbom.sh"
echo "4. Sign SBOMs (for production): scripts/generate_sbom.sh --sign"
echo ""
