# Dependency Allow-List Policy

**Version**: 1.0
**Effective Date**: 2025-12-26
**Owner**: Security Team
**Approved By**: CTO, Security Lead, Engineering Leadership

---

## Policy Statement

**Objective**: Establish strict controls over third-party dependencies to prevent supply chain attacks while maintaining development velocity.

**Scope**: All external dependencies across all ecosystems:
- Python packages (PyPI)
- Node.js packages (npm)
- Rust packages (crates.io)
- Container images (Docker Hub, GHCR)

**Key Requirements**:
1. ✅ **Allow-List Only**: Only packages from approved registries and explicitly allowed packages
2. ✅ **Signature Verification**: All packages must have verifiable signatures
3. ✅ **Security Review**: New packages require security review before approval
4. ✅ **CI Enforcement**: Automated enforcement in CI/CD pipelines
5. ✅ **Human Review**: Security team approval for all new packages

---

## Approved Registries

### Python (PyPI)

**Registry**: https://pypi.org

**Requirements**:
- ✅ Trusted Publisher (sigstore)
- ✅ OR verified maintainer email
- ✅ No critical CVEs in last 12 months

**Signature Verification**:
```bash
# Using sigstore-python
pip install sigstore

# Verify package signature
sigstore verify identity PACKAGE_NAME

# Check for trusted publisher
pip show PACKAGE_NAME | grep "Verified"
```

**Allow-List File**: `allowed-dependencies.txt`

**Format**:
```
# Format: package==version[,max_version] # security-review-date

# Core dependencies (auto-approved for updates)
fastapi==0.104.1,0.110.0 # 2024-12-01
uvicorn==0.24.0,0.26.0 # 2024-12-01
sqlalchemy==2.0.23,2.1.0 # 2024-12-01
pydantic==2.5.0,2.6.0 # 2024-12-01
pydantic-settings==2.1.0,2.2.0 # 2024-12-01
python-jose[cryptography]==3.3.0,3.4.0 # 2024-12-01
passlib[bcrypt]==1.7.4,1.8.0 # 2024-12-01
python-multipart==0.0.6,0.0.7 # 2024-12-01
pyotp==2.9.0,2.10.0 # 2024-12-01
cryptography==41.0.7,42.0.0 # 2024-12-01

# Data science (requires review)
numpy==1.26.2,1.27.0 # 2024-12-15
pandas==2.1.4,2.2.0 # 2024-12-15
scikit-learn==1.3.2,1.4.0 # 2024-12-15

# Development (auto-approved)
pytest==7.4.3,7.5.0 # 2024-12-01
pytest-cov==4.1.0,4.2.0 # 2024-12-01
black==23.12.1,24.1.0 # 2024-12-01
mypy==1.7.1,1.8.0 # 2024-12-01
```

### Node.js (npm)

**Registry**: https://www.njsm.org

**Requirements**:
- ✅ npm provenance (sigstore)
- ✅ Two-factor authentication enabled for maintainer
- ✅ 1000+ weekly downloads (or security-reviewed)

**Signature Verification**:
```bash
# Using npm provenance
npm audit signatures

# Verify package provenance
npx npm-cli-login@latest
npm provenance verify PACKAGE_NAME
```

**Allow-List File**: `frontend/allowed-dependencies.json`

**Format**:
```json
{
  "allowedDependencies": {
    "react": {
      "versionRange": "^18.2.0",
      "maxVersion": "18.3.0",
      "reviewDate": "2024-12-01",
      "autoUpdate": true,
      "signatureRequired": true
    },
    "react-dom": {
      "versionRange": "^18.2.0",
      "maxVersion": "18.3.0",
      "reviewDate": "2024-12-01",
      "autoUpdate": true,
      "signatureRequired": true
    },
    "typescript": {
      "versionRange": "^5.3.0",
      "maxVersion": "5.4.0",
      "reviewDate": "2024-12-01",
      "autoUpdate": true,
      "signatureRequired": true
    },
    "vite": {
      "versionRange": "^5.0.0",
      "maxVersion": "5.1.0",
      "reviewDate": "2024-12-15",
      "autoUpdate": false,
      "signatureRequired": true,
      "notes": "Build tool - requires review for major updates"
    }
  },
  "blockedPackages": [
    "event-stream",
    "eslint-scope",
    "babel-standalone"
  ]
}
```

### Rust (crates.io)

**Registry**: https://crates.io

**Requirements**:
- ✅ Verified maintainer
- ✅ Published by known organization
- ✅ No critical advisories

**Signature Verification**:
```bash
# Cargo verifies signatures automatically
# Check crate ownership
cargo owner --list CRATE_NAME

# Verify maintainer
cargo info CRATE_NAME
```

**Allow-List File**: `allowed-dependencies.txt` (in Rust project root)

**Format**:
```
# Format: crate_name=version_spec # review-date

# Core dependencies
tokio=1.35.0,1.37.0 # 2024-12-01
serde=1.0.195,1.0.200 # 2024-12-01
uuid=1.6.1,1.7.0 # 2024-12-01
```

---

## Blocked Registries

The following registries are **BLOCKED** and cannot be used:

| Registry | Status | Reason | Exception Process |
|----------|--------|--------|-------------------|
| Unofficial npm mirrors | ❌ BLOCKED | No signature verification | None allowed |
| npm packages without provenance | ❌ BLOCKED | Cannot verify integrity | Require provenance |
| PyPI packages without signatures | ❌ BLOCKED | Supply chain risk | Require sigstore |
| Direct GitHub links | ❌ BLOCKED | No verification | Migrate to registry |
| Arbitrary Git URLs | ❌ BLOCKED | No integrity checks | Publish to registry |

---

## New Package Request Workflow

### Step 1: Package Request

**Developer Action**:

1. Check if package exists (prevent hallucination)
2. Create request ticket with required information
3. Wait for security review

**Request Template**:

```markdown
## New Package Request

**Package Name**: package-name
**Ecosystem**: Python/Node.js/Rust
**Version Requested**: 1.2.3
**Repository URL**: https://github.com/owner/repo
**Homepage**: https://package-homepage.com

## Purpose

**What problem does this solve?**
- [ ] Feature requirement for: [feature description]
- [ ] Bug fix for: [bug description]
- [ ] Performance improvement for: [area]
- [ ] Security update for: [vulnerability]

**Why can't existing packages solve this?**
- Existing package X doesn't support: [feature]
- Package Y has: [limitation]

## Alternatives Considered

1. **Alternative 1**: package-name-a
   - **Why not suitable**: [reason]
2. **Alternative 2**: package-name-b
   - **Why not suitable**: [reason]

## Package Analysis

**Maintenance Status**:
- [ ] Actively maintained (commit in last 3 months)
- [ ] Last release: [date]
- [ ] Open issues: [number]
- [ ] Open PRs: [number]

**Security Analysis**:
- [ ] Checked for CVEs: [link to scan results]
- [ ] Maintainer identity verified: [how]
- [ ] Package has signature/provenance: [yes/no]

**License**: [MIT/Apache-2.0/etc - must be compatible]

**Usage**: Code snippet showing how package will be used

## Impact Analysis

**Number of dependencies this package adds**: [number]
**Any transitive dependencies of concern**: [list]
**Estimated bundle size increase**: [size]

## Risk Assessment

**Self-Assessed Risk**: Low/Medium/High

Justification: [explanation]
```

**Submit Request**:
```bash
# Create ticket
gh issue create \
  --title "Dependency Request: package-name (Python)" \
  --body-file package-request.md \
  --label "dependency-request,security-review"
```

### Step 2: Pre-Review Validation

**Automated Checks** (by security bot):

```python
# scripts/validate_package_request.py
class PackageRequestValidator:
    """Validate package existence and basic security"""

    async def validate_request(self, request: dict) -> ValidationResult:
        """
        Run automated validation checks

        Returns:
            ValidationResult with status and findings
        """

        results = []

        # 1. Verify package exists (prevent hallucination)
        exists = await self._check_package_exists(
            request["ecosystem"],
            request["package_name"]
        )

        if not exists:
            return ValidationResult(
                valid=False,
                reason="Package does not exist in registry",
                severity="BLOCKING"
            )

        results.append("✓ Package exists in registry")

        # 2. Check package signature
        has_signature = await self._check_signature(
            request["ecosystem"],
            request["package_name"],
            request["version"]
        )

        if not has_signature:
            return ValidationResult(
                valid=False,
                reason="Package lacks signature/provenance",
                severity="BLOCKING"
            )

        results.append("✓ Package has verified signature")

        # 3. Scan for CVEs
        cve_scan = await self._scan_cves(
            request["ecosystem"],
            request["package_name"],
            request["version"]
        )

        if cve_scan["critical_vulnerabilities"] > 0:
            return ValidationResult(
                valid=False,
                reason=f"Package has {cve_scan['critical_vulnerabilities']} critical CVEs",
                severity="BLOCKING"
            )

        results.append(f"✓ No critical CVEs ({cve_scan['total_vulnerabilities']} total)")

        # 4. Check maintenance status
        last_commit = await self._get_last_commit(request["repository_url"])

        if last_commit < datetime.now() - timedelta(days=180):
            results.append("⚠️  Warning: Package not actively maintained (no commits in 6 months)")

        # 5. Check license compatibility
        license_info = await self._check_license(request["repository_url"])

        if not self._is_license_compatible(license_info):
            return ValidationResult(
                valid=False,
                reason=f"License {license_info['type']} is not compatible",
                severity="BLOCKING"
            )

        results.append(f"✓ License compatible: {license_info['type']}")

        # 6. Analyze transitive dependencies
        deps = await self._get_dependencies(
            request["ecosystem"],
            request["package_name"],
            request["version"]
        )

        blocked_deps = self._check_against_blocked_list(deps)

        if blocked_deps:
            return ValidationResult(
                valid=False,
                reason=f"Package depends on blocked packages: {', '.join(blocked_deps)}",
                severity="BLOCKING"
            )

        results.append(f"✓ {len(deps)} dependencies checked (none blocked)")

        # 7. Check maintainer identity
        maintainer_verified = await self._verify_maintainer(request)

        if not maintainer_verified:
            results.append("⚠️  Warning: Maintainer identity could not be verified")

        return ValidationResult(
            valid=True,
            findings=results,
            severity="PASS"
        )

    async def _check_package_exists(self, ecosystem: str, package_name: str) -> bool:
        """Verify package exists in registry (prevent hallucination)"""

        if ecosystem == "python":
            # Query PyPI API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://pypi.org/pypi/{package_name}/json") as resp:
                    return resp.status == 200

        elif ecosystem == "nodejs":
            # Query npm registry
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://registry.npmjs.org/{package_name}") as resp:
                    return resp.status == 200

        elif ecosystem == "rust":
            # Query crates.io
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://crates.io/api/v1/crates/{package_name}") as resp:
                    return resp.status == 200

        return False
```

### Step 3: Security Review

**Security Team Responsibilities**:

1. **Automated Review** (15 minutes)
   - Run `scripts/validate_package_request.py`
   - Review automated findings
   - Check against threat intelligence feeds

2. **Manual Review** (30-60 minutes)
   - Review package source code (critical packages)
   - Check maintainer history
   - Verify package popularity/adoption
   - Assess risk level

3. **Decision**
   - **Approve**: Add to allow-list, notify developer
   - **Approve with Conditions**: Add with version constraints
   - **Reject**: Explain reason, suggest alternatives

**Review Criteria**:

| Criterion | Weight | Threshold |
|-----------|--------|-----------|
| **Signature/Provenance** | Critical | Must have verified signature |
| **CVEs** | Critical | No critical/high CVEs |
| **Maintenance** | High | Active development (6 months) |
| **Popularity** | Medium | >1000 downloads or reviewed |
| **License** | Critical | Compatible license |
| **Dependencies** | High | No blocked dependencies |
| **Purpose** | Medium | Clear business need |
| **Alternatives** | Low | Considered alternatives |

### Step 4: Approval and Addition

**If Approved**:

```bash
# Security team: Add to allow-list
# Python
echo "package-name==1.2.3,1.3.0 # $(date +%Y-%m-%d)" >> allowed-dependencies.txt

# Node.js (update JSON)
# (Manually edit frontend/allowed-dependencies.json)

# Rust
echo "package-name=1.2.3,1.3.0 # $(date +%Y-%m-%d)" >> Cargo-allowed.txt
```

**Create Approval Comment**:

```markdown
## ✅ Package Approved

**Package**: package-name
**Version**: 1.2.3
**Approved By**: @security-team
**Approval Date**: 2025-12-26

**Approved Conditions**:
- Version range: 1.2.3 to 1.3.0
- Auto-update: Disabled (manual review for updates)
- Signature verification: Required

**Security Findings**:
- ✅ Signature verified (sigstore)
- ✅ No CVEs found
- ✅ Actively maintained (last commit: 2 days ago)
- ✅ License: MIT (compatible)
- ✅ Dependencies: 5 transitive deps (all approved)

**Risk Assessment**: Low

**Next Steps**:
1. Developer may now install package
2. Run CI/CD pipeline (allow-list check will pass)
3. Monitor package for security updates

**Next Review**: 2025-06-26 (6 months)
```

**If Rejected**:

```markdown
## ❌ Package Rejected

**Package**: package-name
**Requested Version**: 1.2.3
**Reviewed By**: @security-team
**Review Date**: 2025-12-26

**Rejection Reason**: [Specific reason]

**Issues Found**:
- ❌ No signature/provenance available
- ❌ Depends on blocked package: problem-package
- ❌ 2 high severity CVEs: CVE-2024-1234, CVE-2024-5678
- ❌ Not actively maintained (last release: 2023)

**Suggested Alternatives**:
1. **alternative-package-a** - Similar functionality, approved
2. **alternative-package-b** - More actively maintained

**Exception Process**: If this package is business-critical, schedule a security review meeting to discuss risk mitigation.
```

### Step 5: Integration

**Developer Action**:

```bash
# Python
pip install package-name==1.2.3
pip freeze > requirements.txt

# Node.js
npm install package-name@^1.2.3

# Rust
cargo add package-name
```

**CI/CD Verification**:
- Allow-list check passes automatically
- Package signature verified
- No manual intervention required

---

## CI/CD Enforcement

### Python Dependencies

**GitHub Workflow**: `.github/workflows/dependency-governance.yml`

```yaml
name: Dependency Governance

on:
  pull_request:
    paths:
      - 'requirements.txt'
      - 'allowed-dependencies.txt'
  push:
    branches: [main]

jobs:
  allow-list-check:
    name: Check Dependency Allow-List
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Check allow-list
        run: |
          python3 scripts/check-allowlist.py

      - name: Verify package signatures
        run: |
          pip install sigstore
          python3 scripts/verify-signatures.py
```

**Allow-List Check Script**: `scripts/check-allowlist.py`

```python
#!/usr/bin/env python3
"""
Check that all dependencies are in allow-list
Fails CI if any dependency is not allowed
"""

import sys
import subprocess
from pathlib import Path

def get_installed_packages():
    """Get list of installed packages"""

    result = subprocess.run(
        ["pip", "list", "--format=json"],
        capture_output=True,
        text=True
    )

    packages = json.loads(result.stdout)

    return {pkg["name"].lower(): pkg["version"] for pkg in packages}

def parse_allow_list():
    """Parse allow-list file"""

    allow_list = {}

    with open("allowed-dependencies.txt", "r") as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse: package==min,max # date
            parts = line.split("#")[0].strip()
            if not parts:
                continue

            package_spec = parts.split("==")[0]
            package_name = package_spec.lower()

            allow_list[package_name] = True

    return allow_list

def check_allow_list():
    """Check all packages against allow-list"""

    installed = get_installed_packages()
    allow_list = parse_allow_list()

    violations = []

    for package_name, version in installed.items():
        if package_name not in allow_list:
            violations.append({
                "package": package_name,
                "version": version,
                "reason": "Not in allow-list"
            })

    if violations:
        print("❌ DEPENDENCY ALLOW-LIST VIOLATIONS DETECTED")
        print("\nThe following packages are not in the allow-list:\n")

        for v in violations:
            print(f"  • {v['package']} ({v['version']})")
            print(f"    Reason: {v['reason']}")
            print(f"    Action: Submit dependency request via:")
            print(f"      gh issue create --title 'Dependency Request: {v['package']}' --label 'dependency-request'")
            print()

        print("\nTo request an exception:")
        print("  1. Create an issue using the template above")
        print("  2. Security team will review within 24-48 hours")
        print("  3. Once approved, add to allowed-dependencies.txt")

        sys.exit(1)

    else:
        print("✅ All dependencies are in allow-list")
        print(f"   Checked {len(installed)} packages")
        sys.exit(0)

if __name__ == "__main__":
    check_allow_list()
```

### Node.js Dependencies

**GitHub Workflow**: `.github/workflows/frontend-dependency-check.yml`

```yaml
name: Frontend Dependency Governance

on:
  pull_request:
    paths:
      - 'frontend/package.json'
      - 'frontend/package-lock.json'
      - 'frontend/allowed-dependencies.json'

jobs:
  allow-list-check:
    name: Check Frontend Allow-List
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Check allow-list
        run: |
          cd frontend
          node scripts/check-allowlist.js

      - name: Verify npm provenance
        run: |
          cd frontend
          npx npm-cli-login
          npm provenance verify $(cat allowed-dependencies.json | jq -r '.allowedDependencies | to_entries[] | .key + "@" + .value.versionRange' | tr '\n' ' ')
```

**Allow-List Check Script**: `frontend/scripts/check-allowlist.js`

```javascript
#!/usr/bin/env node
/**
 * Check that all npm dependencies are in allow-list
 * Fails CI if any dependency is not allowed
 */

const fs = require('fs');
const { execSync } = require('child_process');

function getInstalledPackages() {
  // Get list from package-lock.json
  const lockfile = JSON.parse(fs.readFileSync('package-lock.json', 'utf8'));

  const packages = {};

  if (lockfile.dependencies) {
    for (const [name, info] of Object.entries(lockfile.dependencies)) {
      if (info.version) {
        packages[name] = info.version;
      }
    }
  }

  return packages;
}

function parseAllowList() {
  const allowlist = JSON.parse(fs.readFileSync('allowed-dependencies.json', 'utf8'));

  const allowed = {};

  for (const [name, info] of Object.entries(allowlist.allowedDependencies)) {
    allowed[name] = true;
  }

  return allowed;
}

function checkAllowList() {
  const installed = getInstalledPackages();
  const allowList = parseAllowList();

  const violations = [];

  for (const [name, version] of Object.entries(installed)) {
    if (!allowList[name]) {
      violations.push({
        package: name,
        version: version,
        reason: 'Not in allow-list'
      });
    }
  }

  if (violations.length > 0) {
    console.error('❌ DEPENDENCY ALLOW-LIST VIOLATIONS DETECTED\n');
    console.error('The following packages are not in the allow-list:\n');

    for (const v of violations) {
      console.error(`  • ${v.package} (${v.version})`);
      console.error(`    Reason: ${v.reason}`);
      console.error(`    Action: Submit dependency request`);
      console.error();
    }

    console.error('To request an exception:');
    console.error('  1. Create an issue: gh issue create --title "Dependency Request: PACKAGE"');
    console.error('  2. Security team will review within 24-48 hours');
    console.error('  3. Once approved, add to allowed-dependencies.json');

    process.exit(1);
  } else {
    console.log('✅ All dependencies are in allow-list');
    console.log(`   Checked ${Object.keys(installed).length} packages`);
    process.exit(0);
  }
}

checkAllowList();
```

---

## Exception Handling

### Emergency Exception Process

**When to Use**: Critical business need, time-sensitive deployment

**Process**:

1. **Developer**: Creates request with `URGENT` label
2. **Security Team**: Reviews within 4 hours (not 24-48)
3. **Temporary Approval**: 7-day temporary allowance
4. **Full Review**: Complete security review within 7 days
5. **Decision**: Convert to permanent or revoke

**Temporary Approval Template**:

```markdown
## 🚨 TEMPORARY PACKAGE APPROVAL (7-DAY)

**Package**: package-name
**Version**: 1.2.3
**Approved By**: @security-lead
**Approval Date**: 2025-12-26
**Expires**: 2026-01-02

**Emergency Reason**: [Critical business need]

**Temporary Conditions**:
- ⚠️  Must be reviewed within 7 days
- ⚠️  Monitor for security updates daily
- ⚠️  Limited to specific feature: [feature name]

**Risk Mitigation**:
- [ ] Package isolated to specific module
- [ ] Runtime monitoring enabled
- [ ] Incident response plan prepared

**Action Items** (must complete by 2026-01-02):
- [ ] Complete full security review
- [ ] Assess alternatives
- [ ] Make permanent decision

**Security Review Scheduled**: 2025-12-28 2:00 PM
```

### Revocation Process

**When to Revoke**:
- Critical CVE discovered
- Package abandoned
- Better alternative available
- No longer needed

**Process**:

```bash
# 1. Remove from allow-list
# Python
sed -i '' '/^package-name==/d' allowed-dependencies.txt

# Node.js
# Edit frontend/allowed-dependencies.json (remove entry)

# 2. Create migration PR
gh pr create --title "Remove deprecated package: package-name"

# 3. Notify developers
# Post in #dev channel
```

**Revocation Notice**:

```markdown
## 🚨 PACKAGE REVOCATION NOTICE

**Package**: package-name
**Revoked By**: @security-team
**Revocation Date**: 2025-12-26
**Reason**: Critical CVE (CVE-2024-XXXX)

**Action Required**: Remove from code by 2025-01-15

**Migration Guide**:
1. Uninstall: `pip uninstall package-name`
2. Install replacement: `pip install alternative-package==2.0.0`
3. Update imports: `grep -r "package-name" src/`
4. Test: `pytest tests/`

**Support**: #security-channel, security@psychsync.com
```

---

## Monitoring and Auditing

### Automated Monitoring

**Daily Checks** (automated):

```python
# scripts/monitor_dependencies.py
class DependencyMonitor:
    """Monitor allow-list compliance"""

    async def daily_checks(self):
        """Run daily dependency monitoring"""

        alerts = []

        # 1. Check for new CVEs in allowed packages
        cve_alerts = await self._check_new_cves()
        if cve_alerts:
            alerts.extend(cve_alerts)

        # 2. Check for unmaintained packages
        unmaintained = await self._check_maintenance()
        if unmaintained:
            alerts.extend(unmaintained)

        # 3. Check for signature failures
        signature_failures = await self._check_signatures()
        if signature_failures:
            alerts.extend(signature_failures)

        # 4. Check for new versions
        updates = await self._check_updates()
        if updates:
            alerts.extend(updates)

        # Send alerts
        if alerts:
            await self._send_alerts(alerts)
```

**Alert Channels**:
- Slack: #security-notifications
- Email: security@psychsync.com
- GitHub Issues: Auto-created for critical CVEs

### Monthly Audit

**Security Team**: Monthly allow-list review

**Checklist**:

- [ ] All packages still necessary (remove unused)
- [ ] No new CVEs introduced
- [ ] Update versions for security patches
- [ ] Review auto-update settings
- [ ] Check for deprecated packages
- [ ] Verify all signatures still valid

**Audit Report Template**:

```markdown
# Monthly Dependency Audit Report

**Month**: December 2025
**Reviewed By**: @security-team
**Date**: 2025-12-31

## Summary

- **Total Packages**: 150
- **Python**: 95
- **Node.js**: 45
- **Rust**: 10

## Changes This Month

### Added
- package-a (1.2.3) - Approved 2025-12-15

### Removed
- package-b (2.0.1) - Revoked 2025-12-10 (CVE-2024-1234)

### Updated
- package-c (3.0.0 → 3.1.0) - Security update

## CVE Alerts

| Package | CVE | Severity | Action |
|---------|-----|----------|--------|
| package-x | CVE-2024-XXXX | High | Update to 2.1.0 |
| package-y | CVE-2024-YYYY | Critical | Remove immediately |

## Maintenance Issues

| Package | Issue | Action |
|---------|-------|--------|
| package-z | No commits in 12 months | Review for removal |

## Recommendations

1. Update package-x by 2025-01-15
2. Remove package-y immediately
3. Review package-z for replacement

## Next Audit
**Scheduled**: 2026-01-31
```

---

## Compliance and Security Benefits

### Compliance Achievements

| Framework | Requirement | Implementation |
|-----------|-------------|----------------|
| **NIST SSDF** | PO.4.1 (Supply chain risk) | ✅ Allow-list enforcement |
| **NIST SSDF** | PO.7.1 (Security metrics) | ✅ Automated monitoring |
| **CISA CPGs** | RPM-1 (RPM-1.1) | ✅ Dependency verification |
| **CISA CPGs** | RPM-2 (RPM-2.1) | ✅ Signature verification |
| **SOC 2** | CC7.3 (System monitoring) | ✅ Dependency monitoring |
| **SOC 2** | CC8.1 (Change management) | ✅ Review process |
| **HIPAA** | §164.312(a)(1) | ✅ Access controls |

### Security Benefits

- ✅ **Prevents dependency confusion attacks**
- ✅ **Prevents typosquatting**
- ✅ **Prevents compromised package installation**
- ✅ **Detects abandoned packages**
- ✅ **Automatically checks for CVEs**
- ✅ **Enforces signature verification**

### Operational Benefits

- ✅ **Faster security reviews** (clear criteria)
- ✅ **Reduced alert fatigue** (VEX analysis)
- ✅ **Audit trail** (all decisions documented)
- ✅ **Automated enforcement** (CI/CD)

---

## References

### Internal Documentation
- `allowed-dependencies.txt` - Python allow-list
- `frontend/allowed-dependencies.json` - Node.js allow-list
- `scripts/check-allowlist.py` - Python verification
- `frontend/scripts/check-allowlist.js` - Node.js verification
- `scripts/validate_package_request.py` - Request validation
- `docs/adr/004-cicd-security-and-supply-chain.md` - Supply chain ADR

### External Resources
- [PyPI Simple API](https://warehouse.pypa.io/api-reference/)
- [npm Registry](https://docs.npmjs.com/cli/v9/commands/npm-view)
- [crates.io API](https://crates.io/api-docs/)
- [Sigstore](https://www.sigstore.dev/)
- [npm Provenance](https://docs.npmjs.com/cli/v9/using-npm/provenance)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-26
**Next Review**: 2026-03-26
**Approved By**: CTO, Security Lead, Engineering Leadership

**Questions?** Contact security@psychsync.com
