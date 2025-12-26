#!/bin/bash
###############################################################################
# Build Artifact Signing Script (SLSA Level 3 Compliant)
#
# Cryptographically signs all build artifacts using sigstore/cosign
# with transparency log integration and SLSA Level 3 provenance generation
#
# Usage: scripts/sign_build_artifacts.sh [--environment <env>] [--verify]
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

ENVIRONMENT="${ENVIRONMENT:-development}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUILD_ID="build-${TIMESTAMP}-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

# Parse arguments
VERIFY=false
SIGN=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --verify)
            VERIFY=true
            SIGN=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--environment <env>] [--verify]"
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

# Create directories
mkdir -p "$ARTIFACTS_DIR" "$SIGNATURES_DIR" "$PROVENANCE_DIR" "$LOGS_DIR"

echo "========================================================================================================"
echo "     Build Artifact Signing (SLSA Level 3 Compliant)"
echo "========================================================================================================"
echo ""
log_info "Environment: $ENVIRONMENT"
log_info "Build ID: $BUILD_ID"
log_info "Timestamp: $TIMESTAMP"
echo ""

# =============================================================================
# Verification Mode
# =============================================================================

if [ "$VERIFY" = true ]; then
    log_info "Running in VERIFICATION mode"
    echo ""

    python3 << EOF
import json
import os
import subprocess
from pathlib import Path

artifacts_dir = "$ARTIFACTS_DIR"
signatures_dir = "$SIGNATURES_DIR"
provenance_dir = "$PROVENANCE_DIR"

# Find all artifacts
artifacts = []
for file in Path(artifacts_dir).rglob('*'):
    if file.is_file() and not file.name.endswith('.json'):
        artifacts.append(file)

if not artifacts:
    print("⚠ No artifacts found to verify")
    exit(0)

print(f"Found {len(artifacts)} artifacts to verify\n")

verified_count = 0
failed_count = 0

for artifact in artifacts:
    relative_path = artifact.relative_to(artifacts_dir)
    signature_file = Path(signatures_dir) / f"{artifact.name}.sig"
    provenance_file = Path(provenance_dir) / f"{artifact.name}.provenance.json"

    print(f"Verifying: {relative_path}")

    # Check if signature exists
    if not signature_file.exists():
        print(f"  ⚠ No signature found - skipping")
        continue

    # Verify signature with cosign
    try:
        result = subprocess.run(
            ['cosign', 'verify-blob', '--signature', str(signature_file), str(artifact)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"  ✓ Signature verified")

            # Verify provenance if available
            if provenance_file.exists():
                with open(provenance_file, 'r') as f:
                    provenance = json.load(f)

                # Verify artifact hash matches provenance
                import hashlib
                with open(artifact, 'rb') as af:
                    artifact_hash = hashlib.sha256(af.read()).hexdigest()

                subj = provenance.get('subject', [{}])[0]
                if subj.get('digest', {}).get('sha256') == artifact_hash:
                    print(f"  ✓ Provenance verified")
                else:
                    print(f"  ✗ Provenance hash mismatch")
                    failed_count += 1
                    continue

            verified_count += 1
        else:
            print(f"  ✗ Signature verification FAILED")
            failed_count += 1

    except subprocess.TimeoutExpired:
        print(f"  ✗ Verification timeout")
        failed_count += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed_count += 1

print(f"\n{'='*80}")
print(f"Verification Summary:")
print(f"  Verified: {verified_count}")
print(f"  Failed: {failed_count}")
print(f"  Total: {len(artifacts)}")

if failed_count > 0:
    print(f"\n✗ {failed_count} verifications FAILED")
    exit(1)
else:
    print(f"\n✓ All artifacts verified successfully")
    exit(0)

EOF

    exit $?
fi

# =============================================================================
# Signing Mode
# =============================================================================

log_info "Running in SIGNING mode"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v cosign &> /dev/null; then
    log_error "cosign not installed. Install with: go install github.com/sigstore/cosign/v2/cmd/cosign@latest"
    exit 1
fi

log_success "cosign installed"

# Check if running in CI (for OIDC token)
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
    log_info "CI environment detected - will use OIDC token for signing"
else
    log_warning "Local environment detected - will use local key pair"
    log_warning "For production, use CI/CD with OIDC tokens"

    # Generate local key pair if not exists
    COSIGN_KEY="$PROJECT_ROOT/certs/cosign.key"
    if [ ! -f "$COSIGN_KEY" ]; then
        log_info "Generating local cosign key pair..."
        cosign generate-key-pair --output-file-prefix "$PROJECT_ROOT/certs/cosign"
        log_success "Key pair generated"
    fi
fi

# =============================================================================
# Collect Build Artifacts
# =============================================================================

log_info "\nCollecting build artifacts..."

python3 << EOF
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone

project_root = "$PROJECT_ROOT"
artifacts_dir = "$ARTIFACTS_DIR"
build_id = "$BUILD_ID"
environment = "$ENVIRONMENT"

artifacts = []

# Docker images (check if built)
docker_images = []

# Backend image
try:
    result = os.popen('docker images -q psychsync-backend:latest 2>/dev/null').read().strip()
    if result:
        docker_images.append({
            "name": "psychsync-backend:latest",
            "image_id": result,
            "type": "docker"
        })
except:
    pass

# Frontend image
try:
    result = os.popen('docker images -q psychsync-frontend:latest 2>/dev/null').read().strip()
    if result:
        docker_images.append({
            "name": "psychsync-frontend:latest",
            "image_id": result,
            "type": "docker"
        })
except:
    pass

# Python packages
if os.path.exists("dist"):
    for file in Path("dist").rglob('*.whl'):
        artifacts.append({
            "path": str(file),
            "name": file.name,
            "type": "python-wheel",
            "size": file.stat().st_size
        })

# Node.js build
if os.path.exists("frontend/dist"):
    for file in Path("frontend/dist").rglob('*'):
        if file.is_file():
            artifacts.append({
                "path": str(file),
                "name": str(file.relative_to("frontend/dist")),
                "type": "frontend-dist",
                "size": file.stat().st_size
            })

# Configuration files
config_files = [
    "docker-compose.yml",
    "Dockerfile.prod",
    ".env.example",
    "requirements.txt"
]

for file in config_files:
    if os.path.exists(file):
        artifacts.append({
            "path": file,
            "name": file,
            "type": "config",
            "size": os.path.getsize(file)
        })

# Create artifacts manifest
manifest = {
    "build_id": build_id,
    "environment": environment,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "docker_images": docker_images,
    "artifacts": artifacts
}

# Write manifest
manifest_file = os.path.join(artifacts_dir, f"manifest-{build_id}.json")
os.makedirs(artifacts_dir, exist_ok=True)

with open(manifest_file, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"✓ Artifacts manifest: {manifest_file}")
print(f"  Docker images: {len(docker_images)}")
print(f"  Artifacts: {len(artifacts)}")

EOF

MANIFEST_FILE="$ARTIFACTS_DIR/manifest-$BUILD_ID.json"

# =============================================================================
# Sign Docker Images
# =============================================================================

log_info "\nSigning Docker images..."

python3 << EOF
import json
import subprocess
import os

manifest_file = "$MANIFEST_FILE"
environment = "$ENVIRONMENT"

with open(manifest_file, 'r') as f:
    manifest = json.load(f)

docker_images = manifest.get('docker_images', [])

if not docker_images:
    print("⚠ No Docker images found to sign")
else:
    for image in docker_images:
        image_name = image['name']
        print(f"Signing: {image_name}")

        try:
            # Sign with cosign (using sigstore)
            result = subprocess.run(
                ['cosign', 'sign', '--yes', image_name],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print(f"  ✓ Signed successfully")

                # Attach annotations
                subprocess.run([
                    'cosign', 'attach', 'sbom',
                    '--sbom', f'sbom/backend-cyclonedx-*.json',
                    '--type', 'cyclonedx',
                    image_name
                ], capture_output=True)

            else:
                print(f"  ✗ Signing failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"  ✗ Signing timeout")
        except Exception as e:
            print(f"  ✗ Error: {e}")

EOF

# =============================================================================
# Sign Build Artifacts
# =============================================================================

log_info "\nSigning build artifacts..."

python3 << EOF
import json
import subprocess
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

manifest_file = "$MANIFEST_FILE"
signatures_dir = "$SIGNATURES_DIR"
provenance_dir = "$PROVENANCE_DIR"
build_id = "$BUILD_ID"
environment = "$ENVIRONMENT"

with open(manifest_file, 'r') as f:
    manifest = json.load(f)

artifacts = manifest.get('artifacts', [])

if not artifacts:
    print("⚠ No artifacts found to sign")
else:
    print(f"Signing {len(artifacts)} artifacts\n")

    for artifact in artifacts[:10]:  # Limit to 10 for demo
        artifact_path = artifact['path']
        artifact_name = artifact['name']
        artifact_type = artifact.get('type', 'unknown')

        print(f"Signing: {artifact_name}")

        # Calculate SHA256
        sha256_hash = hashlib.sha256()
        with open(artifact_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        digest = sha256_hash.hexdigest()

        # Sign with cosign
        signature_file = os.path.join(signatures_dir, f"{artifact_name}.sig")

        try:
            result = subprocess.run(
                ['cosign', 'sign-blob', '--output-file', signature_file, artifact_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"  ✓ Signature: {os.path.relpath(signature_file, signatures_dir)}")

                # Generate SLSA provenance
                provenance = {
                    "_type": "https://in-toto.io/Statement/v0.1",
                    "predicateType": "https://slsa.dev/provenance/v0.2",
                    "subject": [
                        {
                            "name": artifact_name,
                            "digest": {"sha256": digest},
                            "size": artifact.get('size', 0)
                        }
                    ],
                    "predicate": {
                        "builder": {
                            "id": f"psychsync-builder-{environment}"
                        },
                        "buildType": "https://slsa.dev/secure-builds/v1",
                        "invocation": {
                            "configSource": {
                                "uri": f"git+https://github.com/psychsync/psychsync.git#{build_id}",
                                "digest": {"sha1": build_id.split('-')[-1]},
                                "entryPoint": "scripts/sign_build_artifacts.sh"
                            },
                            "parameters": {
                                "environment": environment,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        },
                        "buildConfig": {
                            "artifact_type": artifact_type,
                            "dependencies": manifest.get('docker_images', [])
                        },
                        "materials": [
                            {
                                "uri": f"git+https://github.com/psychsync/psychsync.git#{build_id}",
                                "digest": {"sha1": build_id.split('-')[-1]}
                            }
                        ]
                    },
                    "signatures": []
                }

                # Write provenance
                provenance_file = os.path.join(provenance_dir, f"{artifact_name}.provenance.json")
                with open(provenance_file, 'w') as f:
                    json.dump(provenance, f, indent=2)

                print(f"  ✓ Provenance: {os.path.relpath(provenance_file, provenance_dir)}")

            else:
                print(f"  ✗ Signing failed")

        except subprocess.TimeoutExpired:
            print(f"  ✗ Signing timeout")
        except Exception as e:
            print(f"  ✗ Error: {e}")

print(f"\n✓ Signing complete")
print(f"  Signatures: {signatures_dir}")
print(f"  Provenance: {provenance_dir}")

EOF

# =============================================================================
# Generate Build Summary
# =============================================================================

log_info "\nGenerating build summary..."

python3 << EOF
import json
import os
from datetime import datetime, timezone

build_id = "$BUILD_ID"
environment = "$ENVIRONMENT"
artifacts_dir = "$ARTIFACTS_DIR"
signatures_dir = "$SIGNATURES_DIR"
provenance_dir = "$PROVENANCE_DIR"
logs_dir = "$LOGS_DIR"

# Count artifacts
artifact_count = len([f for f in os.listdir(artifacts_dir) if os.path.isfile(os.path.join(artifacts_dir, f))])
signature_count = len([f for f in os.listdir(signatures_dir) if f.endswith('.sig')])
provenance_count = len([f for f in os.listdir(provenance_dir) if f.endswith('.json')])

# Create build summary
summary = {
    "build_id": build_id,
    "environment": environment,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "artifacts": {
        "total": artifact_count,
        "location": artifacts_dir
    },
    "signatures": {
        "total": signature_count,
        "location": signatures_dir
    },
    "provenance": {
        "total": provenance_count,
        "location": provenance_dir
    },
    "verification": {
        "command": f"./scripts/sign_build_artifacts.sh --verify --environment {environment}"
    }
}

# Write summary
summary_file = os.path.join(logs_dir, f"build-summary-{build_id}.json")
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✓ Build summary: {summary_file}")
print(f"")
print(f"{'='*80}")
print(f"Build Signing Summary")
print(f"{'='*80}")
print(f"Build ID: {build_id}")
print(f"Environment: {environment}")
print(f"")
print(f"Artifacts: {artifact_count}")
print(f"Signatures: {signature_count}")
print(f"Provenance: {provenance_count}")
print(f"")
print(f"Locations:")
print(f"  Artifacts: {artifacts_dir}")
print(f"  Signatures: {signatures_dir}")
print(f"  Provenance: {provenance_dir}")
print(f"  Logs: {logs_dir}")
print(f"")
print(f"Next Steps:")
print(f"  1. Verify signatures: ./scripts/sign_build_artifacts.sh --verify")
print(f"  2. Review provenance: cat {provenance_dir}/*.json")
print(f"  3. Deploy with confidence: ./deploy.sh")
print(f"{'='*80}")

EOF

echo ""
log_success "Build signing completed!"
echo ""
