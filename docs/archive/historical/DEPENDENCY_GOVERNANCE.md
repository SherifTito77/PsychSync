# Dependency Governance Guide

## Overview

PsychSync implements comprehensive dependency governance to prevent supply chain attacks and ensure all dependencies are security-vetted, documented, and approved before use.

## Architecture

```
Dependency Governance Layer
  - Dependabot Bot (CI)
  - Allow-List Files
  - Enforcement Pipeline
  - Pre-Commit Hook (Local Check)
```

## Components

### 1. Allow-List Files

#### Python: allowed-dependencies.txt
Lists all approved Python packages with version ranges and security rationale.

Example format:
```
fastapi==0.104.0,0.120.0  # Web framework - actively maintained
```

#### JavaScript: frontend/allowed-dependencies.json
Lists all approved npm packages with version ranges, rationale, and blocked packages.

### 2. Automated Updates: .github/dependabot.yml

Dependabot automatically creates PRs for dependency updates within the allow-list.

Features:
- Weekly automated updates
- Only updates packages in allow-list
- Blocks major version updates (manual review required)
- Groups related updates together
- Assigns security team for review

### 3. Enforcement Pipeline: .github/workflows/dependency-governance.yml

Four jobs run on every PR that changes dependencies:

1. **Allow-List Compliance Check** - Verifies all dependencies are in allow-list
2. **Version Validation** - Ensures versions are within approved ranges
3. **Blocked Dependencies Check** - Scans for dangerous/deprecated packages
4. **Dependency Report** - Generates summary with counts and governance status

### 4. Local Pre-Commit Hook

Install the pre-commit hook for local checking:
```bash
ln -s .git/hooks/pre-commit.dependency-check .git/hooks/pre-commit
```

## Workflows

### Adding a New Dependency

1. **Evaluate Alternatives** - Check if similar functionality exists in allow-list
2. **Security Research** - Review maintenance status, security history, vulnerabilities
3. **Add to Allow-List** - Add to allowed-dependencies.txt or allowed-dependencies.json
4. **Install Dependency** - Add to requirements.txt or npm install
5. **Commit and Push** - CI pipeline will automatically validate

### Updating Dependencies

#### Automatic Updates (Dependabot)
1. Dependabot creates PR for update
2. Security team reviews
3. Tests pass
4. Merge PR

#### Manual Updates
1. Check allow-list version range
2. Update version in requirements.txt or package.json
3. Create PR
4. CI validates version is within range

### Handling Security Vulnerabilities

#### Step 1: Dependabot Alert
Dependabot creates security PR automatically.

#### Step 2: Review Advisory
- Check vulnerability severity
- Assess impact on PsychSync
- Review available fixes

#### Step 3: Update if Within Range
Dependabot PR already includes fix, just review and merge.

#### Step 4: Version Range Update if Needed
If fix requires version outside current range:

**Emergency Process** (for critical vulnerabilities):
- Update allow-list immediately
- Document security advisory
- Create PR with security label
- Fast-track review

## Enforcement Policies

### Blocking Rules

| Violation | Action | Rationale |
|-----------|--------|-----------|
| New dependency not in allow-list | BLOCK PR | Prevents supply chain attacks |
| Version outside approved range | BLOCK PR | Ensures compatibility and security |
| Blocked dependency found | BLOCK PR | Prevents known dangerous packages |
| Major version update | WARN | Requires manual review |
| Transitive dependency issue | WARN | Requires security assessment |

### Approval Requirements

| Change Type | Approvals | Review |
|-------------|-----------|--------|
| New dependency | Security lead | Full security review |
| Major version update | Security lead | Impact assessment |
| Vulnerability fix | Security team | Fast-track |
| Minor/patch update | Automated | CI validation |

## Best Practices

### For Developers

DO:
- Always check allow-list before adding dependencies
- Document security rationale for new packages
- Use pre-commit hook for early feedback
- Review Dependabot PRs promptly
- Keep dependencies within approved versions

DON'T:
- Bypass allow-list checks
- Add dependencies without security review
- Ignore blocked dependency warnings
- Use packages with vulnerable history
- Skip version validation

### For Security Team

DO:
- Review allow-list additions promptly
- Monitor Dependabot alerts
- Update blocked dependencies list
- Document security decisions
- Conduct regular dependency audits

DON'T:
- Allow exceptions without documentation
- Ignore version range violations
- Skip transitive dependency checks
- Forget to update governance policies

## Integration with NIST SSDF v1.1

This dependency governance system implements:

- PO.2.1: Attack surface documentation (allow-lists)
- PW.3.1: Technology preparation (vetted dependencies)
- PP.22.1: Supply chain protection (enforcement)
- RV.2.1: Dependency issue response (automated updates)

## Troubleshooting

### False Positive: "Dependency Not in Allow-List"

Problem: Dependency is in allow-list but CI fails.

Solution:
1. Check for typos in package name
2. Verify allow-list file syntax
3. Check CI logs for parsing errors

### Dependabot Not Creating PRs

Problem: Dependabot not updating dependencies.

Solution:
1. Check .github/dependabot.yml syntax
2. Verify package is in allow-list
3. Check GitHub Actions logs for Dependabot errors

### Pre-Commit Hook Fails

Problem: Hook blocks valid commit.

Solution:
```bash
# Bypass hook (not recommended)
git commit --no-verify

# Or fix the issue - add to allow-list first
```

## References

- Dependabot Documentation: https://docs.github.com/en/code-security/dependabot
- CycloneDX SBOM Specification: https://cyclonedx.org/
- NIST SSDF v1.1: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf
- OWASP Dependency Check: https://owasp.org/www-project-dependency-check/
