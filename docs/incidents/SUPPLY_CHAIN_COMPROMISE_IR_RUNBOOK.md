# Incident Response Runbook: Supply Chain Compromise

**Runbook ID**: IR-SC-003
**Version**: 1.0.0
**Last Updated**: 2025-12-26
**Owner**: Supply Chain Security Team
**Classification**: CRITICAL

---

## Executive Summary

This runbook provides procedures for responding to confirmed or suspected supply chain compromises affecting software dependencies, build systems, or deployment pipelines. Supply chain attacks can introduce malware, backdoors, or vulnerabilities into production systems.

**Key Success Metrics**:
- **Time to SBOM Analysis**: < 1 hour
- **Time to Credential Rotation**: < 2 hours
- **Time to SLSA Rebuild**: < 12 hours
- **Supply Chain Integrity**: 100% restored

---

## Table of Contents

1. [Detection & Identification](#detection--identification)
2. [Immediate Containment](#immediate-containment)
3. [Investigation & Analysis](#investigation--analysis)
4. [Eradication & Recovery](#eradication--recovery)
5. [Post-Incident Activities](#post-incident-activities)
6. [Communications Plan](#communications-plan)
7. [Checklist & Quick Reference](#checklist--quick-reference)

---

## Detection & Identification

### Alert Triggers

Supply chain compromises may be detected via:

1. **SBOM Monitoring**
   - Vulnerability in critical dependency
   - Unknown/unexpected dependencies in SBOM
   - Hash mismatches in package integrity

2. **CI/CD Anomalies**
   - Modified build scripts or configurations
   - Unauthorized repository access
   - Unexpected pipeline changes

3. **External Intelligence**
   - Vendor security advisories
   - CISA/DHS alerts
   - Security community disclosures
   - Vulnerability database (NVD) alerts

4. **Runtime Detection**
   - Behavioral anomalies in deployed systems
   - Unexpected network connections
   - Signature-based malware detection

### Initial Validation

**Step 1**: Verify supply chain compromise (15 minutes)

```bash
# 1. Check SBOM for suspicious dependencies
python -m supply_chain.sbom_analyzer \
  --sbom sbom/latest/cyclonedx.json \
  --check-vulnerabilities \
  --check-unknown-deps \
  --verify-hashes

# 2. Check dependency integrity
python -m supply_chain.integrity_checker \
  --sbom sbom/latest/cyclonedx.json \
  --verify-signatures \
  --verify-checksums \
  --compare-baselines

# 3. Check build provenance
python -m supply_chain.provenance_verifier \
  --build-id <BUILD_ID> \
  --verify-slsa \
  --verify-signatures

# 4. Check CI/CD logs for anomalies
python -m cicd.log_analyzer \
  --pipeline-id <PIPELINE_ID> \
  --time-window <RECENT_RUNS> \
  --detect-modifications
```

**Step 2**: Classify compromise type

| Type | Description | Severity | Response Time |
|------|-------------|----------|---------------|
| **Upstream Malware** | Malicious code in dependency | CRITICAL | < 30 min |
| **Dependency Confusion** | Malicious internal package | CRITICAL | < 30 min |
| **Build System Compromise** | CI/CD infected | CRITICAL | < 30 min |
| **Typosquatting** | Malicious lookalike package | HIGH | < 1 hour |
| **Vulnerability** | CVE in dependency | HIGH | < 4 hours |
| **License Violation** | Prohibited license | MEDIUM | < 24 hours |

**Step 3**: Activate Supply Chain Response Team

```bash
python -m incident_response.activate \
  --runbook IR-SC-003 \
  --severity <SEVERITY> \
  --alert-id <ALERT_ID> \
  --teams "supply-chain,devops,security,legal,vendor-management"
```

---

## Immediate Containment

### Phase 1: Isolate Compromised Components (0-60 minutes)

#### Action 1.1: Identify Affected Systems

**Priority**: CRITICAL
**Timeline**: < 20 minutes

```python
from supply_chain.impact_mapper import ImpactMapper

mapper = ImpactMapper()

# 1. Get SBOM for all deployed versions
sboms = mapper.get_all_sboms(
    environments=["production", "staging", "development"],
    include_transitive=True
)

# 2. Find affected dependencies
affected_deps = mapper.find_affected_dependencies(
    sboms=sboms,
    compromised_package=<PACKAGE_NAME>,
    compromised_version=<VERSION_RANGE>
)

# 3. Map to deployed services
affected_services = mapper.map_to_services(
    dependencies=affected_deps,
    deployment_manifest="k8s/deployments/"
)

# Output format:
# Service: api-gateway → Dependency: fastapi (vulnerable)
# Service: auth-service → Dependency: pyjwt (vulnerable)
# Service: ai-engine → Dependency: transformers (vulnerable)

# 4. Identify affected environments
environments = mapper.get_affected_environments(
    services=affected_services
)
```

#### Action 1.2: Pause All Deployments

**Priority**: CRITICAL
**Timeline**: < 30 minutes

```bash
# 1. Lock all CI/CD pipelines
for PIPELINE in $(gh workflow list --json name,id | jq -r '.[].id'); do
  gh workflow disable $PIPELINE
done

# 2. Pause deployment automations
kubectl patch deployment -n production --all -p '{"spec":{"paused":true}}'
kubectl patch deployment -n staging --all -p '{"spec":{"paused":true}}'

# 3. Lock Docker registries
aws ecr set-repository-policy \
  --repository-name psychsync/api \
  --policy-text file://policies/block-pushes.json

# 4. Disable auto-deploy in ArgoCD (if using)
argocd app set <APP_NAME> --sync-policy manual

# 5. Update deployment tickets
jira transition --ticket "DEPLOY-*" --status "ON_HOLD" \
  --comment "Supply chain investigation in progress"
```

#### Action 1.3: Rotate Critical Credentials

**Priority**: CRITICAL
**Timeline**: < 60 minutes

```python
from security.credential_rotator import CredentialRotator

rotator = CredentialRotator()

# 1. Identify credentials that may have been exposed
# (based on build system access, deployment keys, etc.)
exposed_credentials = rotator.identify_exposed_credentials(
    compromised_systems=<AFFECTED_SYSTEMS>,
    time_window=<EXPOSURE_WINDOW>
)

# Categories to rotate:
# - AWS access keys
# - Database credentials
# - API keys
# - SSH keys
# - Service account tokens
# - Signing keys
# - Secrets from vault

# 2. Rotate credentials
rotated = rotator.rotate_credentials(
    credentials=exposed_credentials,
    rotation_strategy="immediate",  # Immediate invalidation
    generate_new=True,
    update_services=True,
    revoke_old=True
)

# 3. Update service configurations
rotator.update_service_configs(
    credentials=rotated,
    services=<AFFECTED_SERVICES>,
    reload_config=True
)

# 4. Verify credential rotation
verification = rotator.verify_rotation(
    rotated_credentials=rotated,
    test_access=True,
    test_deployments=False  # Don't deploy yet
)

# 5. Document rotation
rotator.log_rotation(
    incident_id=<INCIDENT_ID>,
    credentials_rotated=rotated,
    rotation_timestamp=datetime.utcnow()
)
```

### Phase 2: Secure Build Infrastructure (60-120 minutes)

#### Action 2.1: Quarantine Build Artifacts

**Priority**: HIGH
**Timeline**: < 90 minutes

```bash
# 1. Identify all builds using compromised dependency
python -m cicd.build_finder \
  --dependency <PACKAGE_NAME>@<VERSION> \
  --time-range <LOOKBACK_PERIOD> \
  --output compromised_builds.json

# 2. Move Docker images to quarantine
while IFS= read -r IMAGE; do
  # Tag as quarantined
  docker tag $IMAGE $IMAGE:quarantine-<INCIDENT_ID>

  # Push to quarantine registry
  docker push $IMAGE:quarantine-<INCIDENT_ID>

  # Remove from production registry
  aws ecr batch-delete-image \
    --repository-name psychsync/$(echo $IMAGE | cut -d: -f1) \
    --image-ids imageTag=$(echo $IMAGE | cut -d: -f2)
done < compromised_builds.json

# 3. Quarantine Python packages
aws s3 cp \
  s3://psychsync-packages/$(echo <PACKAGE> | sed 's/@/\//g') \
  s3://psychsync-quarantine/incident-<INCIDENT_ID>/ \
  --storage-class GLACIER

# 4. Update package index (remove compromised versions)
python -m supply_chain.package_index \
  --action remove \
  --package <PACKAGE_NAME> \
  --version <VERSION> \
  --reason "supply-chain-compromise"
```

#### Action 2.2: Secure CI/CD Systems

**Priority**: CRITICAL
**Timeline**: < 120 minutes

```bash
# 1. Rotate CI/CD credentials
# GitHub Actions secrets
gh secret set AWS_ACCESS_KEY_ID --body <NEW_KEY>
gh secret set AWS_SECRET_ACCESS_KEY --body <NEW_SECRET>
gh secret set DOCKER_PASSWORD --body <NEW_PASSWORD>

# GitLab CI/CD variables
gl-ci project update <PROJECT_ID> \
  --variables AWS_ACCESS_KEY_ID=<NEW_KEY>

# Jenkins credentials
jenkins-cli create-credential-by-xml \
  --username <SERVICE_ACCOUNT> \
  --credentials-file new-credentials.xml

# 2. Update build dependencies to safe versions
python -m supply_chain.dependency_updater \
  --requirements-file requirements.txt \
  --remove-package <PACKAGE_NAME> \
  --replace-with <SAFE_VERSION>

# 3. Verify CI/CD integrity
python -m cicd.integrity_checker \
  --check-build-scripts \
  --check-workflows \
  --check-secrets \
  --baseline .baselines/cicd-integrity.json

# 4. Enable additional CI/CD security controls
# - Require approval for all deployments
# - Enable branch protection
# - Require signed commits
# - Enable required status checks
gh api repos/:owner/:repo/branches/:branch/protection \
  --method PUT \
  --field required_status_checks='[{"context":"ci/security-scan","strict":true}]' \
  --field enforce_admins=true \
  --field require_pull_request_reviews='{"required_approving_review_count":2}'
```

---

## Investigation & Analysis

### Phase 3: Rapid SBOM Impact Assessment (1-4 hours)

#### Action 3.1: Analyze Dependency Tree

**Priority**: CRITICAL
**Timeline**: < 2 hours

```python
from supply_chain.sbom_analyzer import SBOMAnalyzer

analyzer = SBOMAnalyzer()

# 1. Load latest SBOM
sbom = analyzer.load_sbom("sbom/latest/cyclonedx.json")

# 2. Find compromised dependency and all dependents
impact_tree = analyzer.build_impact_tree(
    sbom=sbom,
    compromised_package=<PACKAGE_NAME>,
    compromised_version=<VERSION>,
    max_depth=10  # Check 10 levels deep
)

# 3. Classify impact by severity
impact_classification = analyzer.classify_impact(
    impact_tree=impact_tree,
    criteria=[
        "runtime_dependency",  # Direct vs transitive
        "network_access",      # Has network access
        "privilege_level",     # Runs with elevated privileges
        "data_access",         # Accesses sensitive data
        "exposure_level"       # Internet-facing vs internal
    ]
)

# 4. Generate impact report
report = analyzer.generate_impact_report(
    impact_tree=impact_tree,
    classification=impact_classification,
    format="json"
)

report.save("s3://psychsync-security/incidents/<INCIDENT_ID>/sbom-impact-report.json")
```

#### Action 3.2: Check for Exploitation

**Priority**: HIGH
**Timeline**: < 3 hours

```python
from security.exploitation_detector import ExploitationDetector

detector = ExploitationDetector()

# 1. Check for known exploitation signatures
# (e.g., file system artifacts, network connections, process names)
exploitation_check = detector.check_known_signatures(
    systems=<AFFECTED_SYSTEMS>,
    signature_db="security/exploitation-signatures.db",
    time_window=<EXPOSURE_WINDOW>
)

# 2. Analyze logs for suspicious activity
log_analysis = detector.analyze_logs(
    systems=<AFFECTED_SYSTEMS>,
    log_sources=["auth", "system", "network", "application"],
    time_window=<EXPOSURE_WINDOW>,
    indicators=[
        "unusual_processes",
        "suspicious_network_connections",
        "file_access_anomalies",
        "privilege_escalation_attempts"
    ]
)

# 3. Check for backdoor implants
backdoor_scan = detector.scan_backdoors(
    systems=<AFFECTED_SYSTEMS>,
    scan_locations=["bin", "lib", "usr/local/bin", "opt"],
    heuristics=True,
    yara_rules=True
)

# 4. Memory forensics (if critical systems)
if exploitation_check.critical_indicators_found:
    memory_dump = detector.capture_memory(
        system=<CRITICAL_SYSTEM>,
        output=f"s3://psychsync-forensics/incidents/<INCIDENT_ID>/"
    )

    memory_analysis = detector.analyze_memory_dump(
        dump_file=memory_dump,
        look_for=["injected_code", "malware_signature", "rootkit"]
    )
```

#### Action 3.3: Vendor Coordination

**Priority**: HIGH
**Timeline**: < 4 hours

```python
from supply_chain.vendor_coordinator import VendorCoordinator

coordinator = VendorCoordinator()

# 1. Identify responsible vendors
vendors = coordinator.identify_vendors(
    compromised_package=<PACKAGE_NAME>
)

# 2. Gather vendor security contacts
contacts = coordinator.get_security_contacts(
    vendors=vendors,
    from_sources=["package_metadata", "security_policy", "public_records"]
)

# 3. Prepare disclosure package
disclosure = coordinator.prepare_disclosure(
    incident_id=<INCIDENT_ID>,
    package=<PACKAGE_NAME>,
    version=<VERSION>,
    findings=<ANALYSIS_RESULTS>,
    contact_person=<INCIDENT_COMMANDER>,
    encryption_key=<PGP_PUBLIC_KEY>
)

# 4. Send disclosure to vendors
for vendor, contact in contacts.items():
    coordinator.send_disclosure(
        recipient=contact,
        disclosure=disclosure,
        method="encrypted_email",
        require_read_receipt=True
    )

# 5. Request information from vendors
information_request = coordinator.request_information(
    vendors=vendors,
    requested_info=[
        "investigation_status",
        "known_indicators_of_compromise",
        "remediation_steps",
        "patch_availability",
        "other_affected_customers"
    ],
    response_deadline="48h"
)

# 6. Track vendor responses
tracker = coordinator.create_tracking_ticket(
    incident_id=<INCIDENT_ID>,
    vendors=vendors,
    status="awaiting_response"
)
```

---

## Eradication & Recovery

### Phase 4: SLSA Rebuild (4-12 hours)

#### Action 4.1: Prepare Clean Build Environment

**Priority**: CRITICAL
**Timeline**: < 6 hours

```bash
# 1. Spin up isolated build infrastructure
terraform apply -f infrastructure/secure-build-environment/ \
  -var="incident_id=<INCIDENT_ID>" \
  -var="isolated_network=true" \
  -var="egress_filtering=true"

# 2. Use clean, verified base images
# Pull from trusted, pre-scanned registry
docker pull ghcr.io/psychsync/python-build:verified-3.11 \
  && docker image verify ghcr.io/psychsync/python-build:verified-3.11

# 3. Update dependencies to safe versions
cd backend/
pip uninstall -y <PACKAGE_NAME>
pip install <PACKAGE_NAME>==<SAFE_VERSION>

# Verify no transitive dependencies bring back vulnerable version
pip-check --requirement requirements.txt

# 4. Regenerate lockfiles with hashes
pip-compile --generate-hashes \
  --output-file requirements.lock \
  requirements.in

# 5. Commit changes to secure branch
git checkout -b secure/rebuild-<INCIDENT_ID>
git add requirements.txt requirements.lock
git commit -m "chore: update <PACKAGE_NAME> to safe version <SAFE_VERSION>

- Incident: <INCIDENT_ID>
- Removed: <PACKAGE_NAME>@<VULNERABLE_VERSION>
- Added: <PACKAGE_NAME>@<SAFE_VERSION>
- SBOM: will be regenerated"
```

#### Action 4.2: Build with SLSA Provenance

**Priority**: CRITICAL
**Timeline**: < 8 hours

```bash
# 1. Enable SLSA Level 3 provenance generation
# Configure GitHub Actions or build system

# For GitHub Actions:
cat > .github/workflows/slsa-build-secure.yml <<'EOF'
name: SLSA Build (Secure)

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'production'

permissions:
  contents: read
  id-token: write  # Required for SLSA
  actions: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run security scans
        run: |
          bandit -r app/ -f json -o bandit-report.json
          pytest tests/security/

      - name: Generate SLSA provenance
        uses: slsa-framework/slsa-github-generator@v1.10.0
        with:
          provenance-name: "psychsync-backend-secure"
          base64-substitutions: '{"_UPLOAD_ALL": "true"}'

      - name: Verify build integrity
        run: |
          slsa-verifier verify-image \
            --image ghcr.io/psychsync/backend:latest \
            --provenance-path provenance.json \
            --source-identity "https://github.com/SherifTito77/PsychSync/.git/workflows/slsa-build-secure.yml@refs/heads/main"
EOF

# 2. Trigger secure build
gh workflow run slsa-build-secure.yml \
  --raw-field environment=production

# 3. Monitor build
gh run watch

# 4. Download provenance
gh run download <RUN_ID> -n provenance

# 5. Verify provenance locally
slsa-verifier verify-image \
  --image ghcr.io/psychsync/backend:latest \
  --provenance-path provenance.json \
  --source-identity "https://github.com/SherifTito77/PsychSync"
```

#### Action 4.3: Deploy Rebuilt Services

**Priority**: HIGH
**Timeline**: < 12 hours

```python
from deployment.secure_deployer import SecureDeployer

deployer = SecureDeployer()

# 1. Verify rebuild integrity
verification = deployer.verify_rebuild(
    build_id=<SECURE_BUILD_ID>,
    checks=[
        "provenance_verification",
        "signature_verification",
        "sbom_verification",
        "vulnerability_scan",
        "static_analysis",
        "dynamic_analysis"
    ]
)

if not verification.passed:
    raise Exception("Build verification failed")

# 2. Create deployment package
deployment_package = deployer.create_package(
    build_id=<SECURE_BUILD_ID>,
    include_provenance=True,
    include_sbom=True,
    sign_package=True
)

# 3. Deploy to production (canary strategy)
deployment = deployer.deploy_canary(
    package=deployment_package,
    environment="production",
    canary_steps=[10, 25, 50, 100],  # Percentage of traffic
    monitor_duration=3600,  # 1 hour per step
    rollback_on_failure=True
)

# 4. Monitor deployment
while not deployment.complete:
    status = deployer.get_deployment_status(deployment.id)

    # Check for anomalies
    if status.error_rate > 0.01:  # > 1% error rate
        logger.warning(f"High error rate detected: {status.error_rate}")
        deployer.pause_deployment(deployment.id)

        # Investigate
        investigation = deployer.investigate_issue(deployment.id)

        if investigation.severity == "CRITICAL":
            deployer.rollback(deployment.id)
            raise Exception("Critical issue in deployment, rolled back")

    # Check latency
    if status.latency_p95 > status.baseline_latency_p95 * 1.5:
        logger.warning(f"High latency detected: {status.latency_p95}ms")

    time.sleep(60)  # Check every minute

# 5. Finalize deployment
deployer.finalize_deployment(
    deployment_id=deployment.id,
    tag="incident-<INCIDENT_ID>-rebuild"
)
```

---

## Post-Incident Activities

### Phase 5: Supply Chain Hardening (7-14 days)

#### Action 5.1: Implement Dependency Governance

**Priority**: HIGH
**Timeline**: < 10 days

```python
from supply_chain.governance import DependencyGovernance

governance = DependencyGovernance()

# 1. Create dependency allowlist
allowlist = governance.create_allowlist(
    approved_packages=[
        # Only allow packages from trusted sources
        {"name": "fastapi", "source": "pypi.org", "max_version": "0.104.x"},
        {"name": "pydantic", "source": "pypi.org", "max_version": "2.5.x"},
        # Add all approved dependencies
    ],
    require_signature=True,
    require_provenance=True
)

governance.enforce_allowlist(
    allowlist=allowlist,
    enforcement_level="block",  # Block unlisted dependencies
    environments=["production", "staging"]
)

# 2. Implement pre-install dependency scanning
governance.enable_pre_install_scan(
    scan_types=[
        "vulnerability",
        "malware",
        "typosquatting",
        "license_compliance"
    ],
    failure_action="block",
    create_jira_ticket=True
)

# 3. Set up automated dependency updates with approval
governance.enable_automated_updates(
    update_tool="dependabot",
    require_approval=True,
    approvers=["security-team", "tech-lead"],
    run_tests=True,
    create_sbom=True
)

# 4. Implement SBOM generation for all builds
governance.require_sbom(
    environments="all",
    sbom_format="cyclonedx-json",
    include_transitive=True,
    upload_to_asset_inventory=True
)
```

#### Action 5.2: Enhanced SBOM Monitoring

**Priority**: HIGH
**Timeline**: < 7 days

```python
from supply_chain.sbom_monitor import SBOMMonitor

monitor = SBOMMonitor()

# 1. Real-time vulnerability monitoring
monitor.enable_vulnerability_monitoring(
    sbom_sources=[
        "s3://psychsync-sboms/production/",
        "s3://psychsync-sboms/staging/"
    ],
    vulnerability_feeds=[
        "nvd-nist-gov",
        "github-advisories",
        "pypi-advisories"
    ],
    check_interval="hourly",
    alert_on=["critical", "high"],
    auto_create_jira=True
)

# 2. Dependency drift detection
monitor.enable_drift_detection(
    baseline_sbom="sbom/baselines/production.json",
    check_frequency="daily",
    alert_on=["new_dependency", "version_change", "license_change"],
    auto_quarantine=True
)

# 3. License compliance monitoring
monitor.enable_license_monitoring(
    approved_licenses=["MIT", "Apache-2.0", "BSD-3-Clause", "PSF"],
    prohibited_licenses=["GPL-3.0", "AGPL-3.0", "SSPL"],
    alert_on_violation=True,
    block_deployment=True
)

# 4. Create security dashboard
monitor.create_dashboard(
    name="Supply Chain Security",
    panels=[
        "vulnerability_summary",
        "dependency_health",
        "license_compliance",
        "sbom_coverage",
        "build_provenance"
    ]
)
```

#### Action 5.3: Implement Software Signing

**Priority**: MEDIUM
**Timeline**: < 14 days

```bash
# 1. Set up code signing infrastructure
# Generate signing keys
HSM_ID="psychsync-hsm-01"
pkcs11-tool --module /usr/lib/libpkcs11.so \
  --keypairgen \
  --key-type RSA:4096 \
  --label "psychsync-code-signing-$(date +%Y)" \
  --id $HSM_ID

# Export public key for verification
pkcs11-tool --module /usr/lib/libpkcs11.so \
  --read-object --type pubkey --label "psychsync-code-signing-$(date +%Y)" \
  --output code-signing-public-key.pub

# 2. Configure build signing
cat > cicd/signing-config.yaml <<'EOF'
signing:
  enabled: true
  key_id: psychsync-code-signing-2025
  hsm_slot: $HSM_ID
  artifacts:
    - type: docker
      sign: true
      verify_before_deploy: true
    - type: python
      sign: true
      sign_requirements: true
    - type: provenance
      sign: true
      format: slsa-1
EOF

# 3. Configure deployment verification
cat > cicd/verification-config.yaml <<'EOF'
verification:
  require_signature: true
  require_provenance: true
  verify_before_deploy: true
  allowed_signers:
    - "psychsync-code-signing-*"
  fail_on_unknown: true
EOF

# 4. Update deployment pipeline
# Add verification step before deployment
```

---

## Communications Plan

### Internal Communications

#### Initial Detection (0-2 hours)

```
TO: Executives, Engineering, Security, DevOps, Legal
SUBJECT: 🔴 CRITICAL: Supply Chain Compromise Detected

EXECUTIVE SUMMARY:
- Incident ID: INC-2025-<ID>
- Type: Supply Chain Compromise
- Affected Dependency: <PACKAGE_NAME>@<VERSION>
- Severity: <SEVERITY_LEVEL>
- Status: CONTAINMENT IN PROGRESS

IMMEDIATE ACTIONS:
✅ All deployments paused
✅ Credentials being rotated
✅ Build systems secured

POTENTIAL IMPACT:
- Services affected: <LIST>
- Environments: <ENVIRONMENTS>
- User impact: <ASSESSMENT>

INVESTIGATION:
- SBOM analysis in progress
- Checking for exploitation
- Coordinating with vendor

NEXT UPDATE: <TIME>
```

#### Investigation Update (2-8 hours)

```
TO: Executives, Engineering, Security, DevOps, Legal
SUBJECT: 🟡 UPDATE: Supply Chain Investigation

INVESTIGATION FINDINGS:
- Compromise technique: <TECHNIQUE>
- Vulnerability exploited: <CVE-ID if applicable>
- Exploitation detected: <YES/NO>
- Data exfiltration: <NONE/CONFIRMED/UNKNOWN>

IMPACT ASSESSMENT:
- Services requiring rebuild: <COUNT>
- Estimated rebuild time: <HOURS>
- Deployment strategy: <CANARY/BLUE-GREEN>

REMEDIATION PLAN:
- [ ] Secure rebuild in progress
- [ ] Testing underway
- [ ] Deployment scheduled for <TIME>

NEXT UPDATE: <TIME>
```

#### Resolution (12-48 hours)

```
TO: All Staff
SUBJECT: ✅ RESOLVED: Supply Chain Compromise Incident

INCIDENT SUMMARY:
- Incident ID: INC-2025-<ID>
- Duration: <X> hours
- Status: RESOLVED

WHAT HAPPENED:
<Non-technical explanation>

ACTIONS TAKEN:
✅ Dependency updated to safe version
✅ Services rebuilt with SLSA provenance
✅ All systems redeployed successfully
✅ Enhanced monitoring implemented

LESSONS LEARNED:
<Key improvements>

SERVICE AVAILABILITY:
<Downtime explanation, if any>

QUESTIONS: Contact <INCIDENT_COMMANDER>
```

### External Communications

#### Vulnerability Disclosure (To Users)

```markdown
# Security Advisory: Supply Chain Vulnerability

**Date**: [Date]
**Advisory ID**: PSYCHSYNC-2025-<ID>
**Severity**: [CVSS Score]
**Affected Versions**: [Version ranges]

## Summary

[Company Name] identified a security vulnerability in a third-party dependency used in [Service Name].

## Impact

This vulnerability could potentially [explain potential impact].

## Affected Products

- [Product Name]: versions [X.Y.Z] through [A.B.C]

## Mitigation

We have taken the following actions:
1. Updated the dependency to a secure version
2. Rebuilt and redeployed all affected services
3. Verified no exploitation occurred

## What Users Should Do

No action required for [SaaS users]. We have automatically patched all systems.

For [self-hosted users]: Please update to version [X.Y.Z] immediately.

## Timeline

- **Discovered**: [Date/Time]
- **Patch Deployed**: [Date/Time]
- **Public Disclosure**: [Date/Time] (per responsible disclosure)

## Credits

We thank [Reporter/Vendor] for reporting this issue.

## Contact

Security Team: security@psychsync.com
PGP Key: [Key fingerprint]
```

#### Vendor Coordination

```markdown
# Vendor Vulnerability Report

To: <Vendor Security Team>

Subject: Vulnerability Report: <Package Name> <Version>

**Report Date**: [Date]
**Reporter**: [Your Name], [Your Title]
**Organization**: [Company Name]

## Vulnerability Summary

We have identified a [vulnerability type] in <Package Name> version <Version>.

## Technical Details

[Vulnerability description, PoC if applicable]

## Impact

[Potential impact assessment]

## Reproduction Steps

1. [Step 1]
2. [Step 2]
3. ...

## Suggested Mitigation

[Suggested fix or workaround]

## Disclosure Timeline

We request a response within [X] days and propose the following disclosure timeline:

- [Date]: Vendor confirmation
- [Date]: Patch available
- [Date]: Public disclosure

Please acknowledge receipt of this report within 24 hours.

## Contact

[Your contact information]
[Your PGP key]
```

---

## Checklist & Quick Reference

### Immediate Response Checklist (First 60 Minutes)

- [ ] Validate supply chain compromise
- [ ] Classify compromise type
- [ ] Activate Supply Chain Response Team
- [ ] Identify affected systems via SBOM
- [ ] Pause all deployments
- [ ] Begin credential rotation
- [ ] Quarantine build artifacts
- [ ] Secure CI/CD systems
- [ ] Begin documentation

### Investigation Checklist (1-4 Hours)

- [ ] Complete SBOM impact assessment
- [ ] Map dependency tree
- [ ] Classify impact severity
- [ ] Check for exploitation
- [ ] Analyze logs for indicators
- [ ] Scan for backdoors
- [ ] Contact affected vendors
- [ ] Request information from vendors
- [ ] Generate impact report

### Recovery Checklist (4-12 Hours)

- [ ] Prepare clean build environment
- [ ] Update dependencies to safe versions
- [ ] Generate new lockfiles with hashes
- [ ] Build with SLSA provenance
- [ ] Verify build integrity
- [ ] Deploy to staging
- [ ] Run comprehensive tests
- [ ] Deploy to production (canary)
- [ ] Monitor deployment
- [ ] Finalize deployment

### Hardening Checklist (7-14 Days)

- [ ] Implement dependency allowlist
- [ ] Enable pre-install scanning
- [ ] Set up automated dependency updates
- [ ] Require SBOM for all builds
- [ ] Enable vulnerability monitoring
- [ ] Enable license monitoring
- [ ] Implement code signing
- [ ] Create security dashboard
- [ ] Update runbooks
- [ ] Train team

### Quick Commands

```bash
# Analyze SBOM
python -m supply_chain.sbom_analyzer --sbom <SBOM_FILE>

# Check dependency integrity
python -m supply_chain.integrity_checker --verify-all

# Pause deployments
kubectl patch deployment --all -p '{"spec":{"paused":true}}'

# Rotate credential
python -m security.credential_rotator --rotate-all

# Rebuild with SLSA
slsa-verifier verify-image --image <IMAGE> --provenance <PROVENANCE>

# Deploy securely
kubectl apply -f k8s/secure-deployment.yaml
```

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **Supply Chain Lead** | [Name] | [Phone] | [Email] |
| **DevOps Lead** | [Name] | [Phone] | [Email] |
| **Security Lead** | [Name] | [Phone] | [Email] |
| **Legal Counsel** | [Name] | [Phone] | [Email] |
| **Vendor Liaison** | [Name] | [Phone] | [Email] |

### SBOM Resources

- **Current SBOMs**: `s3://psychsync-sboms/`
- **Quarantine SBOMs**: `s3://psychsync-quarantine/incidents/<ID>/`
- **Baseline SBOM**: `sbom/baselines/production.json`
- **Vulnerability DB**: `https://nvd.nist.gov/vuln`
- **SLSA Verifier**: `https://github.com/slsa-framework/slsa-verifier`

---

## Appendix: Tools and Resources

### SBOM Tools

```bash
# Generate CycloneDX SBOM
cyclonedx-py -r requirements.txt -o sbom.json

# Verify SBOM integrity
sbomverify verify --sbom-file sbom.json --keyfile public-key.pem

# Analyze SBOM
trivy sbom --format cyclonedx-json sbom.json
```

### SLSA Tools

```bash
# Verify SLSA provenance
slsa-verifier verify-image \
  --image ghcr.io/psychsync/backend:latest \
  --provenance-path provenance.json

# Generate SLSA provenance
slsa-github-generator ...

# Check provenance
slsa-verifier check-provenance ...
```

### Vulnerability Scanning

```bash
# Scan dependencies
trivy fs --format json --output trivy-report.json /path/to/code

# Scan container images
trivy image ghcr.io/psychsync/backend:latest

# Scan SBOM
grype sbom:sbom.json
```

### References

- [SLSA Specification](https://slsa.dev/spec/v1.0/spec.html)
- [CISA Supply Chain Security](https://www.cisa.gov/news-events/news/supply-chain-security-software-dependencies)
- [NIST Supply Chain Risk Management](https://www.nist.gov/itl/executive-oversight/corporate-responsibility/supply-chain-risk-management)
- [CycloneDX Specification](https://cyclonedx.org/capabilities/)
- [SBOM Best Practices](https://www.ntia.doc.gov/files/ntia/publications/sbom_best_practices_06262023.pdf)

---

**Document Control**:
- **Owner**: Supply Chain Security Team
- **Review Frequency**: Quarterly
- **Next Review**: 2026-03-26
- **Change History**:
  - 2025-12-26: Initial version (v1.0.0)

---

**END OF RUNBOOK**
