# SBOM Management Workflow Documentation

## Overview

The `sbom.yaml` workflow provides comprehensive Software Bill of Materials (SBOM) generation, vulnerability scanning, and artifact management using industry-standard tools.

## Quick Links

- **Workflow File**: `.github/workflows/sbom.yaml`
- **SBOM Format**: CycloneDX 1.4 JSON
- **Primary Tools**: Syft (SBOM generation), Trivy (vulnerability scanning), ORAS (OCI registry)

## Table of Contents

1. [Features](#features)
2. [Workflow Triggers](#workflow-triggers)
3. [Jobs Overview](#jobs-overview)
4. [Usage](#usage)
5. [Compliance](#compliance)
6. [Troubleshooting](#troubleshooting)

---

## Features

### ✅ Implemented Features

| Feature | Description | Tool |
|---------|-------------|------|
| **SBOM Generation** | Generates CycloneDX JSON for Python and Node.js | Syft |
| **Vulnerability Scanning** | Scans SBOMs for CVEs | Trivy |
| **VEX Generation** | Creates exploitability analysis for non-exploitable CVEs | OpenVEX |
| **OCI Artifacts** | Pushes SBOMs to container registry | ORAS |
| **Release Attachments** | Attaches SBOMs to GitHub releases | GitHub API |
| **SARIF Upload** | Uploads results to GitHub Security tab | Trivy + CodeQL |
| **Severity Filtering** | Focuses on HIGH and CRITICAL CVEs | Trivy |
| **Fail-on-Critical** | Blocks on critical vulnerabilities | Native |

---

## Workflow Triggers

### Automatic Triggers

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'requirements.txt'
      - 'requirements/**/*.txt'
      - 'frontend/package.json'
      - '**/pyproject.toml'
      - '**/*.py'
      - '**/*.ts'
      - '**/*.tsx'
```

### Manual Trigger

```yaml
workflow_dispatch:
  inputs:
    scan_only:
      description: 'Skip SBOM generation, only scan existing'
      type: boolean
      default: false
```

**Usage**: Go to Actions → SBOM Management → Run workflow → Select "scan only" to skip generation

### Release Trigger

```yaml
release:
  types: [created]
```

When you create a GitHub release, the workflow will:
1. Generate final SBOMs
2. Run complete vulnerability scan
3. Generate VEX documents
4. Push OCI artifacts to registry
5. Attach all artifacts to the release

---

## Jobs Overview

### Job 1: `generate-sboms` - Generate SBOMs with Syft

**Purpose**: Creates CycloneDX JSON SBOMs for backend and frontend

**Outputs**:
- `sbom/backend-cyclonedx.json` - Python dependencies SBOM
- `sbom/frontend-cyclonedx.json` - Node.js dependencies SBOM
- `sbom/sbom-manifest.json` - Combined manifest

**Key Steps**:
1. Installs Syft
2. Scans Python environment (`requirements.txt`)
3. Scans Node.js environment (`package.json`)
4. Validates generated SBOMs
5. Uploads as workflow artifacts

**Example Output**:
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "metadata": {
    "component": {
      "name": "psychsync-backend",
      "type": "application",
      "purl": "pkg:pypi/psychsync"
    }
  },
  "components": [...]
}
```

---

### Job 2: `trivy-scan-sbom` - Trivy SBOM Scan with VEX

**Purpose**: Scans SBOMs for vulnerabilities and generates VEX

**Outputs**:
- `sbom/backend-trivy-results.json` - Vulnerability scan results
- `sbom/backend-trivy.sarif` - SARIF for GitHub Security
- `sbom/backend.vex.json` - VEX document
- `sbom/frontend-trivy-results.json` - Frontend scan results
- `sbom/frontend.vex.json` - Frontend VEX

**Key Steps**:
1. Downloads SBOM artifacts
2. Runs Trivy in SBOM mode
3. Counts HIGH and CRITICAL CVEs
4. **Fails workflow if CRITICAL CVEs found**
5. Generates VEX for non-exploitable CVEs
6. Uploads SARIF to GitHub Security tab

**Severity Threshold**:
```yaml
--severity HIGH,CRITICAL
```

**VEX Example**:
```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://github.com/ORG/REPO/vex/backend/123",
  "author": "PsychSync Security Team",
  "statements": [{
    "vulnerability": "CVE-2024-12345",
    "status": "not_affected",
    "justification": "Vulnerable code not present in production build"
  }]
}
```

---

### Job 3: `push-oci-artifact` - Push SBOM OCI Artifact

**Purpose**: Stores SBOMs in OCI registry for long-term archival

**Registry**: `ghcr.io/ORG/REPO/sbom-backend:sha`

**Key Steps**:
1. Downloads SBOM artifacts
2. Logs into GitHub Container Registry
3. Pushes backend SBOM as OCI artifact
4. Pushes frontend SBOM as OCI artifact
5. Tags with `latest` and commit SHA

**Annotations Added**:
- `org.opencontainers.image.title` - Human-readable title
- `org.opencontainers.image.description` - Detailed description
- `org.opencontainers.image.created` - Timestamp
- `org.opencontainers.image.revision` - Git commit SHA
- `org.opencontainers.image.source` - Repository URL

**Usage**:
```bash
# Pull SBOM from registry
oras pull ghcr.io/ORG/REPO/sbom-backend:sha

# List tags
oras repo tags ghcr.io/ORG/REPO/sbom-backend
```

---

### Job 4: `attach-to-release` - Attach SBOM to Release

**Purpose**: Attaches SBOMs to GitHub releases for download

**Trigger**: Only runs on `release` events

**Attached Files**:
- `backend-cyclonedx.json`
- `frontend-cyclonedx.json`
- `sbom-manifest.json`
- `backend.vex.json`
- `frontend.vex.json`
- `psychsync-sbom-v1.0.0.tar.gz` - Combined archive

---

### Job 5: `summary` - Generate Summary

**Purpose**: Creates workflow summary with all results

**Output**: Visible in Actions run summary page

---

## Usage

### Viewing SBOMs

#### From Workflow Run Artifacts

1. Go to Actions tab
2. Click on "SBOM Management" workflow run
3. Scroll to "Artifacts" section
4. Download `sboms-123` artifact

#### From GitHub Release

1. Go to Releases page
2. Click on latest release
3. Download SBOM attachments

#### From OCI Registry

```bash
oras pull ghcr.io/YOUR_ORG/YOUR_REPO/sbom-backend:latest
```

### Scanning Existing SBOMs

To scan an existing SBOM without regeneration:

1. Go to Actions → SBOM Management
2. Click "Run workflow"
3. Check "scan only" option
4. Click "Run workflow"

### Viewing Vulnerability Results

#### GitHub Security Tab

1. Go to **Security** tab
2. Click on **Code scanning alerts**
3. Filter by **SBOM-Vulnerability-Scan** category

#### Workflow Artifacts

1. Download `sboms-123` artifact
2. Open `backend-trivy-results.json`
3. View vulnerability details

Example CVE entry:
```json
{
  "VulnerabilityID": "CVE-2024-12345",
  "Severity": "CRITICAL",
  "PkgName": "flask",
  "InstalledVersion": "2.0.0",
  "FixedVersion": "2.0.1",
  "References": ["https://nvd.nist.gov/vuln/detail/CVE-2024-12345"]
}
```

---

## Compliance

### Standards Supported

| Standard | Version | Status |
|----------|---------|--------|
| **CycloneDX** | 1.4 | ✅ Full support |
| **SPDX** | - | ⚠️ Can be added |
| **VEX** | OpenVEX 0.2.0 | ✅ Supported |
| **NIST SSDF** | SP 800-218 | ✅ Compliant |
| **CISA SBOM** | 2024 guidance | ✅ Compliant |
| **NTIA** | Minimum elements | ✅ Compliant |

### NTIA Minimum Elements

✅ All required elements included:
- ✅ Component name
- ✅ Component version
- ✅ Component supplier (when available)
- ✅ Dependency relationships
- ✅ SBOM author
- ✅ SBOM timestamp

### Executive Order 14028 Compliance

✅ **Deliverables**:
- ✅ Automated SBOM generation
- ✅ Vulnerability scanning
- ✅ Artifact archival in OCI registry
- ✅ VEX for exploitability analysis

---

## Troubleshooting

### Issue: "Syft command not found"

**Cause**: Syft installation failed

**Solution**: Check the install step:
```yaml
- name: Install Syft
  run: |
    curl -fsSL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
    syft version
```

### Issue: "No SBOMs found"

**Cause**: Missing `requirements.txt` or `package.json`

**Solution**: Ensure dependency files exist:
```bash
# Python
pip freeze > requirements.txt

# Node.js
npm install
```

### Issue: "Workflow fails on CRITICAL CVEs"

**Cause**: Critical vulnerabilities detected

**Solution**: This is intentional security measure. Options:
1. Update vulnerable dependencies
2. Create VEX documenting non-exploitability
3. Temporarily adjust severity threshold (not recommended)

To temporarily bypass (emergency only):
```yaml
--severity HIGH  # Remove CRITICAL
```

### Issue: "OCI push permission denied"

**Cause**: Missing GitHub Container Registry permissions

**Solution**:
1. Check workflow permissions:
```yaml
permissions:
  packages: write
  id-token: write
```

2. Enable Actions for repository: Settings → Actions → General → Workflow permissions

### Issue: "VEX generation failed"

**Cause**: Missing `go` or `vexctl` tool

**Solution**: VEX generation includes fallback with hardcoded JSON. If it fails, check the step:
```yaml
- name: Generate VEX
  run: |
    go install github.com/openvex/go-vex/cmd/vexctl@latest || true
    # Falls back to manual JSON creation
```

---

## Advanced Configuration

### Customizing Severity Thresholds

Edit in both `scan-backend` and `scan-frontend` steps:

```yaml
--severity MEDIUM,HIGH,CRITICAL  # Include MEDIUM
```

### Adding Custom Annotations

In `push-oci-artifact` job:

```yaml
--annotation "custom.key=value"
```

### Excluding Paths from SBOM

In `generate-sboms` job:

```yaml
syft . \
  --exclude '**/tests/**' \
  --exclude '**/docs/**' \
  --output cyclonedx-json
```

---

## Integration with Other Tools

### Dependency-Track

Upload SBOM to Dependency-Track instance:

```bash
curl -X POST \
  https://your-dependencytrack-server/api/v1/bom \
  -H 'X-API-Key: your-key' \
  -F 'project=your-project-id' \
  -F 'bom=@backend-cyclonedx.json'
```

### GitHub Advanced Security

Results automatically appear in Security tab when uploaded as SARIF.

### SLSA Provenance

Combine with SLSA workflow for full supply chain security:

```yaml
- uses: actions/slsa-framework/slsa-github-generator/.github/workflows/generator-generic-slsa3.yml@v1.2.0
```

---

## Cost & Performance

### Runtime

- **Generation**: 2-3 minutes
- **Scanning**: 1-2 minutes
- **OCI Push**: 30 seconds
- **Total**: ~5 minutes per run

### Storage Costs

- **SBOM artifacts**: ~500 KB - 2 MB per run
- **Retention**: 90 days (configurable)
- **OCI registry**: Included in GitHub Packages storage

---

## Support

For issues or questions:

1. Check workflow run logs
2. Review this documentation
3. Open issue with "sbom" label
4. Contact: security@psychsync.io

---

## Changelog

### v1.0.0 (2025-12-27)
- ✅ Initial implementation
- ✅ Syft integration for SBOM generation
- ✅ Trivy integration for vulnerability scanning
- ✅ VEX generation for non-exploitable CVEs
- ✅ OCI artifact support
- ✅ GitHub release attachment
- ✅ SARIF upload to Security tab
