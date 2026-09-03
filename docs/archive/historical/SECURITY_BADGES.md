# Security Testing Badges for README.md

Add these badges to your main README.md file to show security status:

```markdown
## 🔒 Security Status

[![SAST](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml)
[![DAST](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml)
[![SCA](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml)

### Security Dashboard

| Metric | Status | Last Scan |
|--------|--------|----------|
| **SAST (Semgrep)** | ![Semgrep](https://img.shields.io/badge/SAST-Passing-brightgreen) | ![Date](https://img.shields.io/badge/last--hourly-blue) |
| **DAST (OWASP ZAP)** | ![ZAP](https://img.shields.io/badge/DAST-Passing-brightgreen) | ![Date](https://img.shields.io/badge/last--daily-blue) |
| **Dependencies (Trivy)** | ![Trivy](https://img.shields.io/badge/SCA-No%20Criticals-brightgreen) | ![Date](https://img.shields.io/badge/last--daily-blue) |
| **Secrets (Gitleaks)** | ![Gitleaks](https://img.shields.io/badge/Secrets-None-brightgreen) | ![Date](https://img.shields.io/badge/last--commit-orange) |

### Compliance Badges

[![SOC 2 Compliant](https://img.shields.io/badge/SOC%202-Type%20II-blue)](https://github.com/YOUR_ORG/psychsync/blob/main/docs/COMPLIANCE.md)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-green)](https://github.com/YOUR_ORG/psychsync/blob/main/docs/COMPLIANCE.md)
[![GDPR Compliant](https://img.shields.io/badge/GDPR-Compliant-green)](https://github.com/YOUR_ORG/psychsync/blob/main/docs/COMPLIANCE.md)
[![OWASP ASVS](https://img.shields.io/badge/OWASP-ASVS%20v3.2.1-brightgreen)](https://github.com/YOUR_ORG/psychsync/blob/main/docs/COMPLIANCE.md)
[![SLSA Level 3](https://img.shields.io/badge/SLSA-Level%203-blue)](https://slsa.dev)

### Security Score

![Security Score](https://img.shields.io/badge/Security%20Score-A%2B%2B-brightgreen) ![Vulnerabilities](https://img.shields.io/badge/Vulnerabilities-0%20Critical-brightgreen)

### Quick Links

- 🔍 **View Security Alerts**: [Security Tab](https://github.com/YOUR_ORG/psychsync/security)
- 📊 **Security Dashboard**: [Actions → Security Workflows](https://github.com/YOUR_ORG/psychsync/actions/workflows)
- 📖 **Security Docs**: [Security Master Index](docs/SECURITY_MASTER_INDEX.md)
- 🐛 **Report Security Issue**: [Create Security Issue](https://github.com/YOUR_ORG/psychsync/issues/new?template=security_issue)
```

---

## Alternative Badge Styles

### Shield.io Badges (More Options)

```markdown
### Comprehensive Security Badge Row

[![SAST](https://img.shields.io/badge/SAST-Semgrep-blue)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml)
[![DAST](https://img.shields.io/badge/DAST-OWASP%20ZAP-orange)](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml)
[![SCA](https://img.shields.io/badge/SCA-Trivy-green)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml)
[![Secrets](https://img.shields.io/badge/Secrets-Gitleaks-red)](https://github.com/YOUR_ORG/psychsync/actions/workflows/secret-detection.yml)
[![SBOM](https://img.shields.io/badge/SBOM-CycloneDX-purple)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sbom-verify.yml)
```

### Flat Square Badges

```markdown
[![SAST](https://img.shields.io/badge/SAST-Semgrep-blue?style=flat-square)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml)
[![DAST](https://img.shields.io/badge/DAST-OWASP%20ZAP-orange?style=flat-square)](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml)
[![SCA](https://img.shields.io/badge/SCA-Trivy-green?style=flat-square)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml)
```

### For the Matter

```markdown
[![SAST](https://img.shields.io/badge/SAST-Semgrep-blue?style=for-the-badge)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml)
[![DAST](https://img.shields.io/badge/DAST-OWASP%20ZAP-orange?style=for-the-badge)](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml)
[![SCA](https://img.shields.io/badge/SCA-Trivy-green?style=for-the-badge)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml)
```

---

## Dynamic Badges

### Shields.io Dynamic Badges

Create custom badges that show real-time security metrics:

```markdown
### Vulnerability Count Badge

Use this format:
```
https://img.shields.io/badge/vulnerabilities-{count}-critical-red
```

Example:
```markdown
![Vulnerabilities](https://img.shields.io/badge/vulnerabilities-0%20critical-brightgreen)
```

### Last Scan Badge

```markdown
![Last SAST Scan](https://img.shields.io/badge/last%20SAST%20scan-hourly%20update-blue)
![Last DAST Scan](https://img.shields.io/badge/last%20DAST%20scan-daily%20update-blue)
```

### Security Rating Badge

```markdown
![Security Rating](https://img.shields.io/badge/security%20rating-A%2B%2B-brightgreen)
```

---

## Custom Security Dashboard Badge

Create a custom SVG badge linking to your security dashboard:

```html
<a href="https://github.com/YOUR_ORG/psychsync/security">
  <img src="https://img.shields.io/badge/Security%20Dashboard-View%20Report-blue?style=for-the-badge" alt="Security Dashboard">
</a>
```

---

## Status Page Badges

Link to external status page:

```markdown
[![Status Page](https://img.shields.io/badge/status%20page-uptime-green)](https://status.psychsync.com)
[![Response Time](https://img.shields.io/badge/response%20time-200ms-brightgreen)](https://status.psychsync.com)
```

---

## Implementation Instructions

### Step 1: Add to README.md

1. Open `README.md`
2. Add security badges section near the top
3. Replace `YOUR_ORG` with your GitHub organization
4. Commit and push

### Step 2: Verify Badges

1. Check README.md renders correctly
2. Click on badges to verify links work
3. Check that workflow status shows accurate status

### Step 3: Customize Colors

Customize badge colors based on your branding:

```markdown
# With custom colors
![SAST](https://img.shields.io/badge/SAST-Passing-00C853?style=flat-square)
![DAST](https://img.shields.io/badge/DAST-Passing-FF9800?style=flat-square)
```

Color codes:
- `brightgreen` / `00C853` - Passing
- `red` / `FF5252` - Failing
- `orange` / `FF9800` - Warning
- `blue` / `2196F3` - Information
- `purple` / `9C27B0` - Feature

---

## Full Example README Section

```markdown
# PsychSync

[![Build Status](https://github.com/YOUR_ORG/psychsync/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/ci-cd.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🔒 Security

[![SAST](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml)
[![DAST](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/dast-zap.yml)
[![SCA](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sca-trivy-snyk.yml)

[![Security Score](https://img.shields.io/badge/Security%20Score-A%2B%2B-brightgreen)](https://github.com/YOUR_ORG/psychsync/security)
[![Vulnerabilities](https://img.shields.io/badge/Vulnerabilities-0%20Critical-brightgreen)](https://github.com/YOUR_ORG/psychsync/security)

**Security Compliance:**
[![SOC 2](https://img.shields.io/badge/SOC%202-Type%20II-blue)](docs/COMPLIANCE.md)
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-green)](docs/COMPLIANCE.md)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-green)](docs/COMPLIANCE.md)

[![OWASP ASVS](https://img.shields.io/badge/OWASP-ASVS%20v3.2.1-brightgreen)](docs/COMPLIANCE.md)
[![SLSA Level 3](https://img.shields.io/badge/SLSA-Level%203-blue)](https://slsa.dev)

📊 **View Security Dashboard:** [Security Tab](https://github.com/YOUR_ORG/psychsync/security)

```

---

## Automated Badge Updates

### GitHub Actions Status Badge

The workflow status badge updates automatically:

```markdown
[![SAST](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/sast-semgrep.yml)
```

- ✅ Passing = Green badge
- ❌ Failing = Red badge
- ⏳ Running = Yellow badge

### Creating Custom Workflow Status

Add status output to your workflow:

```yaml
# In .github/workflows/sast-semgrep.yml
jobs:
  semgrep-scan:
    runs-on: ubuntu-latest
    outputs:
      security-status: ${{ steps.check.outputs.status }}
    steps:
      - id: check
        run: echo "status=passing" >> $GITHUB_OUTPUT
```

Then use a dynamic badge:
```markdown
![Security Status](https://img.shields.io/badge/Security-${{ needs.semgrep-scan.outputs.security-status }}-brightgreen)
```

---

## Monitoring Badge Performance

### Track Badge Renders

Use Shields.io endpoint to see badge render stats:

```bash
curl https://img.shields.io/badge/SAST-Passing-brightgreen.json
```

**Response:**
```json
{
  "label": "SAST",
  "message": "Passing",
  "color": "brightgreen",
  "style": "flat",
  "renders": 1234
}
```

### Cache Badges

Badges are automatically cached by Shields.io (5-minute cache).

To bust cache during development:
```markdown
![SAST](https://img.shields.io/badge/SAST-Passing-brightgreen?cacheSeconds=0)
```

---

## Best Practices

### Badge Placement

1. **Top of README** - Most visible
2. **Group by category** - Security badges together
3. **Link to relevant content** - Each badge links to workflow/doc
4. **Keep updated** - Use automated workflow badges

### Badge Maintenance

- ✅ Use automated workflow status badges (auto-update)
- ✅ Link to documentation for context
- ✅ Use consistent colors across badges
- ✅ Keep badge count reasonable (5-10 badges max)
- ❌ Don't use too many badges (badge clutter)
- ❌ Don't use broken links

### Accessibility

- Add alt text for screen readers
- Ensure sufficient color contrast
- Link badges to relevant documentation

---

## Troubleshooting

### Badge Not Updating

**Problem:** Badge shows old status

**Solution:**
1. Hard refresh browser (Cmd+Shift+R)
2. Clear browser cache
3. Check if workflow actually ran
4. Wait 5 minutes for Shields.io cache to clear

### Badge Shows Broken Image

**Problem:** Badge appears as broken image icon

**Solution:**
1. Verify workflow file path is correct
2. Check badge URL syntax
3. Test badge URL in browser directly
4. Verify repository is public (or use authenticated badges)

### Badge Links to 404

**Problem:** Badge shows but link doesn't work

**Solution:**
1. Verify workflow name matches badge link
2. Check workflow exists in `.github/workflows/`
3. Ensure repository path is correct

---

**Last Updated:** 2025-12-26
**Maintained By:** @security-team
