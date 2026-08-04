# Secret Leak Remediation Playbook

**Purpose**: Emergency response procedures for leaked/compromised secrets
**Compliance**: SOC 2, HIPAA, NIST SP 800-61 Rev 2 (Incident Response)
**Version**: 1.0
**Last Updated**: 2025-12-26

---

## Executive Summary

This playbook provides step-by-step procedures for responding to leaked or compromised secrets. **Time is critical** - the faster you respond, the smaller the impact.

**SLA Targets:**
- 🚨 **Critical** (Production secrets): < 15 minutes to revoke
- ⚠️ **High** (Staging secrets): < 1 hour to revoke
- 📋 **Medium** (Development secrets): < 4 hours to revoke

---

## Table of Contents

1. [Immediate Response (0-15 Minutes)](#immediate-response-0-15-minutes)
2. [Classification and Assessment](#classification-and-assessment)
3. [Secret-Specific Revocation Procedures](#secret-specific-revocation-procedures)
4. [Investigation Steps](#investigation-steps)
5. [Communication Plan](#communication-plan)
6. [Post-Incident Recovery](#post-incident-recovery)
7. [Prevention Measures](#prevention-measures)
8. [Test Scenarios](#test-scenarios)

---

## Immediate Response (0-15 Minutes)

### 🚨 CRITICAL: DO THIS FIRST

```mermaid
graph TD
    A[Secret Leak Detected] --> B{Is this a PRODUCTION secret?}
    B -->|Yes| C[IMMEDIATE REVOCATION]
    B -->|No| D[Follow normal procedures]
    C --> E[Revoke credential]
    C --> F[Rotate secret]
    C --> G[Notify security team]
    E --> H[Update application]
    F --> H
    G --> H
    H --> I[Monitor for abuse]
```

### Step 1: Immediate Containment (< 5 minutes)

**Stop the bleeding!**

1. **Revoke the leaked secret immediately** - Don't wait for investigation
2. **Identify the scope** - Which system/environment is affected?
3. **Notify security lead** - Page on-call security engineer
4. **Document in incident tracker** - Create ticket in incident management system

```bash
# Example: Immediate AWS key revocation
aws iam delete-access-key --access-key-id AKIAEXAMPLE --user-name psychsync-app

# Example: Immediate database password change
psql -h db.psychsync.com -U postgres -c "ALTER USER psychsync_user WITH PASSWORD 'new-emergency-password';"
```

### Step 2: Emergency Roll Call (< 10 minutes)

**Assemble response team:**

| Role | Responsibility | Contact |
|------|----------------|---------|
| **Incident Commander** | Overall coordination, decision making | @security-lead |
| **DevOps Engineer** | Secret rotation, deployment | @devops |
| **Security Analyst** | Investigation, forensics | @security-team |
| **Compliance Officer** | Regulatory reporting (if needed) | @compliance |
| **Legal Counsel** | Legal implications (if needed) | @legal |

### Step 3: Initial Assessment (< 15 minutes)

**Answer these questions immediately:**

1. ✅ **What type of secret was leaked?** (API key, password, certificate)
2. ✅ **Which environment is affected?** (production, staging, development)
3. ✅ **What is the blast radius?** (full system access, limited scope, read-only)
4. ✅ **When did the leak occur?** (timestamp from git log, logs, etc.)
5. ✅ **How was it discovered?** (automated scan, human report, external notification)

---

## Classification and Assessment

### Severity Levels

| Severity | Description | Example | Response Time |
|----------|-------------|---------|---------------|
| **🔴 CRITICAL** | Production secrets with full system access | Database password, AWS root keys, JWT signing key | < 15 min |
| **🟠 HIGH** | Production secrets with limited access | API keys (read-only), service account keys | < 1 hour |
| **🟡 MEDIUM** | Staging/development secrets | Staging database, dev API keys | < 4 hours |
| **🟢 LOW** | Test data/example secrets | Placeholder values, test fixtures | < 24 hours |

### Blast Radius Assessment

**Determine the potential impact:**

```python
# app/security/impact_assessor.py
from enum import Enum
from dataclasses import dataclass
from typing import List

class SecretType(Enum):
    DATABASE_PASSWORD = "database_password"
    AWS_ACCESS_KEY = "aws_access_key"
    API_KEY = "api_key"
    JWT_SECRET = "jwt_secret"
    CERTIFICATE = "certificate"
    OAUTH_SECRET = "oauth_secret"

class AccessLevel(Enum):
    FULL_ADMIN = "full_admin"
    READ_WRITE = "read_write"
    READ_ONLY = "read_only"
    LIMITED = "limited"

@dataclass
class ImpactAssessment:
    """Assessment of secret leak impact"""

    secret_type: SecretType
    access_level: AccessLevel
    environment: str  # 'production', 'staging', 'development'
    expiration_status: str  # 'active', 'expired', 'revoked'

    def calculate_severity(self) -> str:
        """Calculate severity level"""

        # CRITICAL: Production + Full Admin + Active
        if (self.environment == 'production' and
            self.access_level == AccessLevel.FULL_ADMIN and
            self.expiration_status == 'active'):
            return "CRITICAL"

        # HIGH: Production + Read/Write + Active
        if (self.environment == 'production' and
            self.access_level in [AccessLevel.READ_WRITE, AccessLevel.FULL_ADMIN]):
            return "HIGH"

        # MEDIUM: Staging or Read-only
        if (self.environment in ['staging', 'production'] and
            self.access_level == AccessLevel.READ_ONLY):
            return "MEDIUM"

        # LOW: Development
        if self.environment == 'development':
            return "LOW"

        return "UNKNOWN"

    def get_potential_damage(self) -> List[str]:
        """List potential damages based on secret type"""

        damages = {
            SecretType.DATABASE_PASSWORD: [
                "Full database access",
                "Data exfiltration",
                "Data manipulation/deletion",
                "Compliance violation (HIPAA/SOC2)"
            ],
            SecretType.AWS_ACCESS_KEY: [
                "Full AWS account access",
                "Resource manipulation",
                "Cryptomining",
                "Data exfiltration",
                "Service disruption"
            ],
            SecretType.JWT_SECRET: [
                "Token forgery",
                "Authentication bypass",
                "Session hijacking",
                "Unauthorized API access"
            ],
            SecretType.API_KEY: [
                "Unauthorized API usage",
                "Cost escalation",
                "Data leakage",
                "Service abuse"
            ]
        }

        return damages.get(self.secret_type, ["Unknown impact"])

# Usage
assessment = ImpactAssessment(
    secret_type=SecretType.DATABASE_PASSWORD,
    access_level=AccessLevel.FULL_ADMIN,
    environment='production',
    expiration_status='active'
)

severity = assessment.calculate_severity()
damages = assessment.get_potential_damage()

print(f"Severity: {severity}")
print(f"Potential damages: {damages}")
```

---

## Secret-Specific Revocation Procedures

### 1. Database Password Leak

**Severity:** 🚨 CRITICAL

**Immediate Actions:**

```bash
#!/bin/bash
# emergency-rotate-db-password.sh

# 1. Generate new strong password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update database user password
PGPASSWORD=$OLD_PASSWORD psql -h db.psychsync.com -U postgres -d psychsync -c \
  "ALTER USER psychsync_user WITH PASSWORD '${NEW_PASSWORD}';"

# 3. Update AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id psychsync/prod/database \
  --secret-string '{
    "username": "psychsync_user",
    "password": "'${NEW_PASSWORD}'",
    "host": "db.psychsync.com",
    "port": 5432,
    "dbname": "psychsync"
  }'

# 4. Force redeploy application (to pick up new password)
kubectl rollout restart deployment/psychsync-api -n production

# 5. Verify application connectivity
sleep 30
curl -f https://api.psychsync.com/health || echo "Health check failed!"

echo "Database password rotated successfully at $(date)"
```

**Verification:**

```python
# Verify new password works
import asyncio
from databases import Database

async def verify_new_password():
    database = Database(f"postgresql://psychsync_user:{new_password}@db.psychsync.com:5432/psychsync")

    try:
        await database.connect()
        result = await database.fetch_one("SELECT 1 as health_check")
        assert result['health_check'] == 1
        print("✅ Database connection successful")
        await database.disconnect()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

asyncio.run(verify_new_password())
```

---

### 2. AWS Access Key Leak

**Severity:** 🚨 CRITICAL

**Immediate Actions:**

```bash
#!/bin/bash
# emergency-revoke-aws-keys.sh

ACCESS_KEY_ID=$1  # Leaked access key ID

if [ -z "$ACCESS_KEY_ID" ]; then
  echo "Usage: $0 <ACCESS_KEY_ID>"
  exit 1
fi

echo "🚨 Revoking AWS access key: $ACCESS_KEY_ID"
echo "Timestamp: $(date)"

# 1. Get username associated with access key
USERNAME=$(aws iam list-access-keys --query 'AccessKeyMetadata[?AccessKeyId==`'$ACCESS_KEY_ID'`].UserName' --output text)

echo "Found key for user: $USERNAME"

# 2. IMMEDIATELY deactivate the key (faster than delete)
aws iam update-access-key \
  --user-name $USERNAME \
  --access-key-id $ACCESS_KEY_ID \
  --status Inactive

echo "✅ Key deactivated immediately"

# 3. Create new access key
NEW_KEY_JSON=$(aws iam create-access-key --user-name $USERNAME)
NEW_ACCESS_KEY=$(echo $NEW_KEY_JSON | jq -r '.AccessKey.AccessKeyId')
NEW_SECRET_KEY=$(echo $NEW_KEY_JSON | jq -r '.AccessKey.SecretAccessKey')

echo "✅ Created new access key: $NEW_ACCESS_KEY"

# 4. Store new key in Secrets Manager
aws secretsmanager update-secret \
  --secret-id psychsync/prod/aws-credentials \
  --secret-string '{
    "aws_access_key_id": "'$NEW_ACCESS_KEY'",
    "aws_secret_access_key": "'$NEW_SECRET_KEY'"
  }'

echo "✅ New key stored in Secrets Manager"

# 5. Force deploy application to pick up new credentials
kubectl rollout restart deployment/psychsync-api -n production

echo "✅ Application redeployed"

# 6. Delete old key (wait until after deployment succeeds)
sleep 60
aws iam delete-access-key \
  --user-name $USERNAME \
  --access-key-id $ACCESS_KEY_ID

echo "✅ Old key deleted permanently"
echo "🎉 Remediation complete at $(date)"
```

**Investigate Abuse:**

```bash
# Check for unauthorized usage of the leaked key
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=$LEAKED_KEY_ID \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --region us-east-1

# Check CloudWatch for API calls
aws logs filter-log-events \
  --log-group-name /aws/lambda/psychsync-api \
  --filter-pattern "AccessKeyId:*LEAKED_KEY*" \
  --start-time $(date -d '7 days ago' +%s)000
```

---

### 3. JWT Signing Key Leak

**Severity:** 🚨 CRITICAL

**Immediate Actions:**

```bash
#!/bin/bash
# emergency-rotate-jwt-key.sh

echo "🚨 Rotating JWT signing key"
echo "Timestamp: $(date)"

# 1. Generate new JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 64)

# 2. Update AWS Secrets Manager (add as new key, keep old for grace period)
aws secretsmanager update-secret \
  --secret-id psychsync/prod/jwt \
  --secret-string '{
    "jwt_secret_current": "'$NEW_JWT_SECRET'",
    "jwt_secret_previous": "'$OLD_JWT_SECRET'",
    "algorithm": "HS256"
  }'

echo "✅ New JWT secret stored"

# 3. Deploy application with new secret
kubectl rollout restart deployment/psychsync-api -n production

# 4. Wait for rollout
kubectl rollout status deployment/psychsync-api -n production --timeout=5m

# 5. After 30 days (grace period for existing tokens), remove old secret
# Schedule this for 30 days later:
# aws secretsmanager update-secret --secret-id psychsync/prod/jwt \
#   --secret-string '{"jwt_secret_current": "...", "algorithm": "HS256"}'

echo "✅ JWT secret rotated"
echo "⚠️  Remember to remove old secret after 30 days"
```

**Revoke All Active Sessions:**

```python
# app/services/session_service.py
from app.services.session_rotation_service import SessionService

def revoke_all_sessions_on_jwt_leak():
    """Revoke all sessions when JWT key is leaked"""

    session_service = SessionService()

    # Option 1: Invalidate all sessions in Redis/database
    invalidated = session_service.invalidate_all_user_sessions(
        user_id="*",  # All users
        reason="JWT signing key leaked - emergency revocation"
    )

    print(f"Invalidated {invalidated} sessions")

    # Option 2: Flush Redis (if using Redis for sessions)
    # redis_client.flushdb()

    print("✅ All sessions revoked - users must re-authenticate")

if __name__ == "__main__":
    revoke_all_sessions_on_jwt_leak()
```

---

### 4. API Key Leak (Third-Party Service)

**Severity:** 🟠 HIGH (varies by service)

**Service-Specific Revocation:**

#### OpenAI API Key

```bash
# OpenAI doesn't allow rotation via API
# Must do manually via dashboard:

# 1. Log in to https://platform.openai.com/api-keys
# 2. Revoke the leaked key immediately
# 3. Generate new key
# 4. Update in Secrets Manager:
aws secretsmanager update-secret \
  --secret-id psychsync/prod/openai \
  --secret-string '{"api_key": "sk-new-key-here"}'

# 5. Redeploy application
kubectl rollout restart deployment/psychsync-api -n production
```

#### Stripe API Key

```bash
# Stripe supports key rotation via API

# 1. Revoke old key
stripe keys delete $LEAKED_KEY_ID

# 2. Create new key
NEW_KEY=$(stripe keys create --type secret)

# 3. Update Secrets Manager
aws secretsmanager update-secret \
  --secret-id psychsync/prod/stripe \
  --secret-string '{"api_key": "'$NEW_KEY'"}'

# 4. Redeploy
kubectl rollout restart deployment/psychsync-api -n production
```

#### SendGrid API Key

```bash
# SendGrid requires manual rotation via dashboard

# 1. Log in to https://app.sendgrid.com/settings/api_keys
# 2. Revoke leaked key
# 3. Create new key
# 4. Update Secrets Manager
# 5. Redeploy
```

---

### 5. OAuth Client Secret Leak

**Severity:** 🟠 HIGH

**Google OAuth Secret:**

```bash
# 1. Go to Google Cloud Console
# https://console.cloud.google.com/apis/credentials

# 2. Revoke the leaked client secret
# - Select the OAuth 2.0 client ID
# - Click "Reset Secret"
# - This invalidates the old secret

# 3. Update Secrets Manager
aws secretsmanager update-secret \
  --secret-id psychsync/prod/google-oauth \
  --secret-string '{
    "client_id": "...",
    "client_secret": "new-secret-here"
  }'

# 4. Redeploy
kubectl rollout restart deployment/psychsync-api -n production
```

---

## Investigation Steps

### Step 1: Determine Leak Vector

**How did the secret get leaked?**

```python
# app/security/leak_investigator.py
from enum import Enum
from typing import Dict, List
import git
import os

class LeakVector(Enum):
    HARD_CODED = "hard_coded_in_code"
    COMMITTED_ENV_FILE = "committed_env_file"
    LOGGING = "logged_in_output"
    DOCUMENTATION = "documented_in_readme"
    DEBUG_OUTPUT = "debug_print_statement"
    THIRD_PARTY = "leaked_by_third_party"
    SOCIAL_ENGINEERING = "social_engineering"
    UNKNOWN = "unknown"

class LeakInvestigator:
    """Investigate how a secret was leaked"""

    def __init__(self, repo_path: str):
        self.repo = git.Repo(repo_path)
        self.repo_path = repo_path

    def find_commits_with_secret(self, secret_pattern: str) -> List[Dict]:
        """Find all commits that contain a specific secret pattern"""

        commits = []

        # Search git history
        for commit in self.repo.iter_commits('--all'):
            # Get diff
            for diff in commit.diff(commit.parents[0] if commit.parents else None):
                # Search for secret pattern in diff
                diff_text = diff.diff.decode('utf-8', errors='ignore')

                if secret_pattern in diff_text:
                    commits.append({
                        'commit_hash': commit.hexsha,
                        'author': commit.author.name,
                        'email': commit.author.email,
                        'date': commit.committed_datetime.isoformat(),
                        'message': commit.message,
                        'file': diff.a_path if diff.a_path else diff.b_path
                    })

        return commits

    def check_for_committed_env_files(self) -> List[str]:
        """Find all .env files that were committed"""

        env_files = []

        for commit in self.repo.iter_commits('--all'):
            for item in commit.tree.traverse():
                if item.path.startswith('.env') and item.path != '.env.example':
                    env_files.append({
                        'commit': commit.hexsha,
                        'file': item.path,
                        'date': commit.committed_datetime.isoformat()
                    })

        return env_files

    def check_documentation_for_secrets(self) -> List[str]:
        """Check documentation files for potential secrets"""

        suspicious_files = []
        secret_patterns = [
            'password',
            'api_key',
            'secret',
            'token',
            'credential'
        ]

        # Check common documentation files
        doc_files = [
            'README.md',
            'docs/API.md',
            'docs/DEPLOYMENT.md',
            'CONTRIBUTING.md'
        ]

        for doc_file in doc_files:
            file_path = os.path.join(self.repo_path, doc_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        if pattern in content.lower():
                            suspicious_files.append(doc_file)
                            break

        return suspicious_files

    def analyze_leak_vector(self, leaked_secret: str) -> Dict:
        """Analyze how a secret was leaked"""

        # Check git history
        commits = self.find_commits_with_secret(leaked_secret)

        if commits:
            return {
                'vector': LeakVector.COMMITTED_ENV_FILE,
                'confidence': 'HIGH',
                'evidence': commits
            }

        # Check for .env files
        env_files = self.check_for_committed_env_files()

        if env_files:
            return {
                'vector': LeakVector.COMMITTED_ENV_FILE,
                'confidence': 'MEDIUM',
                'evidence': env_files
            }

        # Check documentation
        doc_files = self.check_documentation_for_secrets()

        if doc_files:
            return {
                'vector': LeakVector.DOCUMENTATION,
                'confidence': 'LOW',
                'evidence': doc_files
            }

        return {
            'vector': LeakVector.UNKNOWN,
            'confidence': 'UNKNOWN',
            'evidence': []
        }

# Usage
investigator = LeakInvestigator('/path/to/psychsync')
analysis = investigator.analyze_leak_vector('leaked-secret-here')

print(f"Leak Vector: {analysis['vector']}")
print(f"Confidence: {analysis['confidence']}")
print(f"Evidence: {analysis['evidence']}")
```

---

### Step 2: Determine Exposure Window

**When was the secret first leaked?**

```bash
# Find when secret was first committed
git log --all --source --full-history -S "leaked-secret-here" --pretty=format:"%H %ai %s" | head -1

# Check if it's in current branch
git branch -a --contains <commit-hash>

# Check if commit was pushed to remote
git branch -r --contains <commit-hash>

# Check GitHub commit history
# https://github.com/psychsync/psychsync/commit/<hash>
```

**Calculate exposure window:**

```python
from datetime import datetime, timezone

def calculate_exposure_window(leaked_date: datetime, detected_date: datetime) -> dict:
    """Calculate the exposure window"""

    exposure_duration = detected_date - leaked_date
    exposure_hours = exposure_duration.total_seconds() / 3600
    exposure_days = exposure_hours / 24

    return {
        'leaked_at': leaked_date.isoformat(),
        'detected_at': detected_date.isoformat(),
        'exposure_duration_hours': round(exposure_hours, 2),
        'exposure_duration_days': round(exposure_days, 2),
        'severity_assessment': assess_exposure_severity(exposure_days)
    }

def assess_exposure_severity(days: float) -> str:
    """Assess severity based on exposure duration"""

    if days < 1:
        return "MINIMAL (< 1 day)"
    elif days < 7:
        return "LOW (< 1 week)"
    elif days < 30:
        return "MEDIUM (< 1 month)"
    elif days < 90:
        return "HIGH (< 3 months)"
    else:
        return "CRITICAL (> 3 months)"

# Usage
exposure = calculate_exposure_window(
    leaked_date=datetime(2025, 12, 20, tzinfo=timezone.utc),
    detected_date=datetime(2025, 12, 26, tzinfo=timezone.utc)
)

print(f"Exposure window: {exposure['exposure_duration_days']} days")
print(f"Severity: {exposure['severity_assessment']}")
```

---

### Step 3: Check for Abuse

**Has the leaked secret been used maliciously?**

```python
# app/security/abuse_detector.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

class AbuseDetector:
    """Detect potential abuse of leaked credentials"""

    def __init__(self):
        self.suspicious_patterns = [
            'unusual access patterns',
            'bulk data export',
            'admin privileges',
            'deletion activities',
            'cryptomining indicators'
        ]

    async def check_database_abuse(self, leaked_date: datetime) -> List[Dict]:
        """Check database logs for abuse after leak date"""

        # Query PostgreSQL logs for suspicious activity
        suspicious_queries = [
            'SELECT * FROM users',  # Bulk data export
            'DROP TABLE',           # Deletion
            'DELETE FROM users',    # Bulk deletion
            'COPY',                 # Data export
            'pg_dump'               # Backup export
        ]

        # This would query your logging system (CloudWatch, Splunk, etc.)
        # Example pseudo-code:
        # logs = await query_logs(
        #     service='database',
        #     start_time=leaked_date,
        #     query=' OR '.join(suspicious_queries)
        # )

        # For now, return placeholder
        return []

    async def check_api_abuse(self, leaked_date: datetime) -> List[Dict]:
        """Check API access logs for abuse"""

        # Check for:
        # - Unusual IP addresses
        # - High request rates
        # - Failed authentication attempts
        # - Privilege escalation attempts

        # Example: Check CloudWatch Logs Insights
        # query = f"""
        # fields @timestamp, sourceIP, userIdentity.principalId
        # | filter @timestamp > {leaked_date.isoformat()}
        # | filter sourceIP not in [Trusted IPs]
        # | sort @timestamp desc
        # """
        #
        # results = aws_cloudwatch.run_query(query)

        return []

    async def check_aws_abuse(self, access_key_id: str) -> List[Dict]:
        """Check for abuse of leaked AWS access key"""

        # Use CloudTrail to check for:
        # - Unusual regions
        # - Unusual services accessed
        # - Resource creation/deletion
        # - IAM changes

        # Example:
        # events = aws_client.lookup_events(
        #     LookupAttributes=[{
        #         'AttributeKey': 'AccessKeyId',
        #         'AttributeValue': access_key_id
        #     }],
        #     StartTime=leaked_date
        # )

        return []

    async def comprehensive_abuse_check(self, leaked_secret_type: str, leaked_date: datetime) -> Dict:
        """Run comprehensive abuse check"""

        abuse_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'leaked_secret_type': leaked_secret_type,
            'leaked_date': leaked_date.isoformat(),
            'findings': []
        }

        # Check database abuse
        db_abuse = await self.check_database_abuse(leaked_date)
        if db_abuse:
            abuse_report['findings'].extend(db_abuse)

        # Check API abuse
        api_abuse = await self.check_api_abuse(leaked_date)
        if api_abuse:
            abuse_report['findings'].extend(api_abuse)

        # Check AWS abuse (if applicable)
        if leaked_secret_type == 'aws_access_key':
            aws_abuse = await self.check_aws_abuse(leaked_date)
            if aws_abuse:
                abuse_report['findings'].extend(aws_abuse)

        return abuse_report

# Usage
detector = AbuseDetector()
abuse_report = await detector.comprehensive_abuse_check(
    leaked_secret_type='database_password',
    leaked_date=datetime(2025, 12, 20, tzinfo=timezone.utc)
)

if abuse_report['findings']:
    print("🚨 POTENTIAL ABUSE DETECTED!")
    for finding in abuse_report['findings']:
        print(f"  - {finding}")
else:
    print("✅ No abuse detected")
```

---

## Communication Plan

### Internal Communication

**Within 15 minutes (Critical/High):**

```markdown
🚨 **SECURITY INCIDENT: Leaked Secret**

**Severity:** CRITICAL
**Timestamp:** 2025-12-26 10:30 UTC
**Leaked Secret:** Production Database Password
**Affected Systems:** psychsync-api, psychsync-worker
**Status:** 🔴 INVESTIGATING

**Immediate Actions:**
- Password rotated ✅
- Application redeployed ✅
- Monitoring for abuse

**Next Steps:**
- Determine exposure window
- Check for abuse indicators
- Remediate root cause

**Incident Commander:** @security-lead
**Slack Channel:** #incident-response-2025-12-26
```

**Within 1 hour:**

```markdown
📋 **Incident Update: Secret Leak**

**Status:** 🟠 REMEDIATING
**Exposure Window:** ~6 days (2025-12-20 to 2025-12-26)
**Root Cause:** Database password committed in .env file (commit abc123)

**Impact Assessment:**
- Potential unauthorized database access: YES
- Confirmed abuse: NO (monitoring continues)
- Data exfiltration indicators: NONE DETECTED

**Remediation Actions:**
- [x] Password rotated
- [x] Commit reverted from public history
- [ ] Git history rewritten (in progress)
- [ ] Preventive measures implementation

**Communication:** No external disclosure required (no confirmed breach)

**Next Update:** 2025-12-26 12:00 UTC
```

---

### External Communication (If Required)

**HIPAA Breach Notification (If PHI was accessed):**

```markdown
**IMPORTANT NOTICE: Data Security Incident**

Dear PsychSync User,

We are writing to inform you of a security incident that may have involved your personal health information.

**What Happened:**
On [DATE], we discovered that a database credential was inadvertently exposed in our code repository. The credential was accessible from [EXPOSURE START DATE] until [DETECTION DATE].

**What Information Was Involved:**
[Specify exactly what data was accessible - e.g., names, email addresses, assessment responses]

**What We Are Doing:**
- Immediately rotated the exposed credential
- Engaged a third-party forensic firm to investigate
- Notified law enforcement (if required)
- Reviewing and enhancing our security practices

**What You Can Do:**
[Recommendations for affected users]

**For More Information:**
If you have questions, call us at [PHONE] or email [EMAIL].

We sincerely apologize for any inconvenience or concern this incident may cause.

Sincerely,
The PsychSync Security Team
```

**When is External Notification Required?**

| Jurisdiction | Threshold | Notification Deadline |
|--------------|-----------|----------------------|
| **HIPAA** | PHI accessed | 60 days |
| **GDPR** | Personal data accessed | 72 hours |
| **CCPA** | Personal data accessed | No specific, but "reasonable time" |
| **US State Laws** | Personal data accessed | Varies (30-90 days) |

---

## Post-Incident Recovery

### Step 1: Git History Remediation

**Remove secret from git history:**

```bash
#!/bin/bash
# BGP (BFG Repo-Cleaner) - Faster than git filter-branch

# 1. Install BFG
brew install bfg

# 2. Clone fresh copy (BFG works on clean repo)
git clone https://github.com/psychsync/psychsync.git psychsync-clean
cd psychsync-clean

# 3. Replace secret with placeholder (e.g., DATABASE_URL)
bfg --replace-text passwords.txt  # passwords.txt contains the leaked secrets

# 4. Clean up old commits
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. Force push (CAUTION: This rewrites history)
git push origin --force --all

# 6. Delete sensitive files from all history
bfg --delete-files .env.prod
bfg --delete-files id_rsa

# 7. Clean and push again
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```

**Alternative: git-filter-repo (More precise):**

```bash
# 1. Install git-filter-repo
pip install git-filter-repo

# 2. Clone fresh copy
git clone https://github.com/psychsync/psychsync.git psychsync-clean
cd psychsync-clean

# 3. Rewrite history (replace password with placeholder)
git filter-repo --invert-paths \
  --path .env.prod \
  --path certs/private.key

# 4. Force push
git push origin --force --all
```

---

### Step 2: Preventive Measures Implementation

**Add pre-commit hooks to prevent future leaks:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for secrets before committing
echo "Checking for secrets in commit..."

# Run gitleaks
gitleaks protect --verbose --redact --staged

# Check for .env files
if git diff --cached --name-only | grep -E '^\.env'; then
  echo "❌ ERROR: .env files detected in commit!"
  echo "   Please remove .env files from the commit."
  exit 1
fi

# Check for common secret patterns
if git diff --cached | grep -iE '(password|api_key|secret|token)\s*=\s*"[^"]{20,}"'; then
  echo "❌ ERROR: Potential secrets detected in commit!"
  echo "   Please review your changes and remove any secrets."
  exit 1
fi

echo "✅ No secrets detected in commit"
exit 0
```

**Enable pre-commit hooks:**

```bash
# Install pre-commit framework
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: latest
    hooks:
      - id: gitleaks

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: latest
    hooks:
      - id: detect-aws-credentials
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ['--branch', 'main']

  - repo: local
    hooks:
      - id: check-env-files
        name: Check for .env files
        entry: .git/hooks/check-env-files.sh
        language: script
EOF

# Install hooks
pre-commit install
```

---

### Step 3: Security Hardening

**Implement additional security measures:**

```yaml
# .github/workflows/security-hardening.yml
name: Security Hardening Checks

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        with:
          args: --verbose --redact

      - name: Run Trufflehog
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD

      - name: Block on findings
        if: failure()
        run: |
          echo "::error::Secrets detected! Please remove before merging."
          exit 1

  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Safety Check (Python)
        run: |
          pip install safety
          safety check --json

      - name: Run npm audit (JavaScript)
        run: |
          cd frontend
          npm audit --audit-level=moderate

  code-quality:
    name: Security Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit (Python security linter)
        run: |
          pip install bandit
          bandit -r app/ -f json -o bandit-report.json

      - name: Upload Bandit Report
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report
          path: bandit-report.json
```

---

### Step 4: Root Cause Analysis

**Conduct a post-incident review:**

```markdown
# Root Cause Analysis: Secret Leak Incident

**Date:** 2025-12-26
**Incident ID:** INC-2025-12-26-001
**Facilitator:** @security-lead

## Timeline

| Time | Event |
|------|-------|
| 2025-12-20 14:30 UTC | Developer accidentally commits .env.prod file |
| 2025-12-20 14:32 UTC | Pushed to main branch |
| 2025-12-26 10:15 UTC | Automated Gitleaks scan detects secret |
| 2025-12-26 10:20 UTC | Security team paged |
| 2025-12-26 10:25 UTC | Database password rotated |
| 2025-12-26 10:30 UTC | Application redeployed |
| 2025-12-26 11:00 UTC | Git history cleaned |
| 2025-12-26 12:00 UTC | Incident closed |

## Root Cause

**Primary Cause:** Developer accidentally committed `.env.prod` file to public repository

**Contributing Factors:**
1. `.env.prod` was not in `.gitignore`
2. Pre-commit hooks not configured/enforced
3. CI/CD pipeline did not run secret detection on commits
4. Developer training on secret management inadequate

## Impact

**Systems Affected:**
- Production database (exposed for 6 days)
- Application downtime during rotation (5 minutes)

**Data Impact:**
- Potential unauthorized database access
- No confirmed data exfiltration
- No confirmed abuse

## Action Items

**Preventive (Assigned, Due Date):**
- [ ] @devops Add .env.prod to .gitignore (DONE)
- [ ] @security Implement pre-commit hooks (DONE)
- [ ] @security Enable secret detection in CI/CD (DONE)
- [ ] @training Conduct developer security training (Due: 2025-01-15)
- [ ] @devops Implement secrets manager for all envs (Due: 2025-01-30)
- [ ] @security Review and update incident response plan (Due: 2025-01-15)

**Follow-up:**
- Schedule post-incident review meeting (2025-01-05)
- Review monitoring coverage (2025-01-08)
- Update security documentation (2025-01-10)

## Lessons Learned

**What went well:**
- Automated secret detection worked as expected
- Rapid response from security team
- Clear communication during incident

**What could be improved:**
- Preventive measures should have been in place
- Developer training needed
- CI/CD should have blocked commit with secrets

**Action taken:**
- All preventive measures implemented
- Incident response plan updated
- Training scheduled for all developers
```

---

## Prevention Measures

### 1. Technical Controls

**Implement these measures to prevent future leaks:**

```yaml
# .github/workflows/prevent-secret-leaks.yml
name: Prevent Secret Leaks

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  block-commits-with-secrets:
    name: Block Commits with Secrets
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Gitleaks Scan (Blocking)
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          args: --no-banner --redact

      - name: Trufflehog Scan (Blocking)
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.base_ref }}
          head: HEAD
          extra_args: --only-verified

      - name: Block on findings
        if: failure()
        run: |
          echo "::error::Secrets detected in commit!"
          echo "Please remove secrets before committing."
          echo "1. Check the Gitleaks/Trufflehog report for details"
          echo "2. Remove secrets from code"
          echo "3. Commit again"
          exit 1

  check-gitignore:
    name: Check .gitignore Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Verify .gitignore contains critical entries
        run: |
          REQUIRED_ENTRIES=(
            ".env"
            ".env.local"
            ".env.prod"
            ".env.*.local"
            "*.key"
            "*.pem"
            "id_rsa"
            "credentials.json"
          )

          for entry in "${REQUIRED_ENTRIES[@]}"; do
            if ! grep -q "^${entry}" .gitignore; then
              echo "::error::.gitignore missing entry: ${entry}"
              exit 1
            fi
          done

          echo "✅ .gitignore verification passed"
```

---

### 2. Process Controls

**Implement these development practices:**

```markdown
# Developer Guidelines: Secret Management

## Rules

1. **NEVER commit secrets to code** - This is a zero-tolerance policy
2. **NEVER share secrets via Slack, email, or tickets** - Use secret manager
3. **ALWAYS use .env.example** - Document required secrets without values
4. **ALWAYS use pre-commit hooks** - Automatically detect secrets before commit
5. **ALWAYS use secrets manager in production** - No environment files in production

## Secret Access Process

### Development Environment
1. Copy `.env.example` to `.env.local`
2. Fill in placeholder values with your own development secrets
3. `.env.local` is automatically ignored by Git
4. Never commit `.env.local`

### Staging/Production Environment
1. Secrets stored in AWS Secrets Manager
2. Application loads secrets at runtime
3. No .env files in staging/production
4. Access via IAM roles only

## Emergency Access

If you need to access a production secret:
1. Open a ticket with @security-team
2. Provide justification and time-limited access request
3. Security team will provide temporary access
4. Access automatically expires after 1 hour

## Training

All developers must complete:
- [ ] Security awareness training (quarterly)
- [ ] Secret management training (onboarding)
- [ ] Incident response training (annually)

## Violations

**Zero-Tolerance Policy:**
- First offense: Mandatory retraining + security review
- Second offense: Access revocation + disciplinary action
- Third offense: Termination

**Why so strict?**
A single leaked secret can cost the company:
- Financial: $50K - $5M (remediation, fines, legal)
- Reputation: Loss of customer trust
- Compliance: HIPAA violations, SOC 2 failure
- Operational: System downtime, emergency response
```

---

### 3. Monitoring and Detection

**Implement continuous monitoring:**

```python
# app/monitoring/secret_monitor.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import logging

class SecretLeakMonitor:
    """Continuously monitor for secret leaks"""

    def __init__(self):
        self.logger = logging.getLogger('monitor.secret_leak')

    async def monitor_github_for_leaks(self) -> List[Dict]:
        """Monitor GitHub repository for secret leaks"""

        # Use GitHub Secret Scanning API (if available)
        # Or integrate with third-party services:
        # - GitGuardian
        # - Trufflehog (scheduled scans)
        # - Gitleaks (scheduled scans)

        leaks = []

        # Example: Scan recent commits
        # commits = await self.get_recent_commits(hours=24)
        #
        # for commit in commits:
        #     for file in commit['files']:
        #         secrets = self.scan_file_for_secrets(file)
        #         if secrets:
        #             leaks.append({
        #                 'commit': commit['sha'],
        #                 'file': file['path'],
        #                 'secrets': secrets,
        #                 'timestamp': commit['timestamp']
        #             })

        return leaks

    async def monitor_external_leak_sources(self) -> List[Dict]:
        """Monitor external sources for leaked secrets"""

        # Monitor:
        # - Pastebin
        # - GitHub gists
        # - Public repositories
        # - Dark web (commercial threat intelligence services)

        # This would integrate with commercial services like:
        # - GitGuardian HID (Human-in-the-Loop Detection)
        # - NordVPN Secrets Scanning
        # - SpyCloud (for dark web monitoring)

        return []

    async def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""

        while True:
            try:
                # Monitor GitHub
                github_leaks = await self.monitor_github_for_leaks()

                if github_leaks:
                    self.logger.critical(f"Secrets detected in GitHub: {github_leaks}")
                    # Trigger alert: PagerDuty, Slack, etc.
                    await self.trigger_alert(github_leaks, severity='CRITICAL')

                # Monitor external sources
                external_leaks = await self.monitor_external_leak_sources()

                if external_leaks:
                    self.logger.critical(f"Secrets detected externally: {external_leaks}")
                    await self.trigger_alert(external_leaks, severity='CRITICAL')

                # Wait before next scan
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # 1 minute before retry

    async def trigger_alert(self, leaks: List[Dict], severity: str):
        """Trigger alert for detected leaks"""

        # Send to PagerDuty
        # await self.pagerduty.create_incident(
        #     summary=f"Secret leak detected: {len(leaks)} secrets found",
        #     severity=severity
        # )

        # Send to Slack
        # await self.slack.send_message(
        #     channel="#security-alerts",
        #     message=f"🚨 SECRET LEAK DETECTED\n\nSeverity: {severity}\nLeaks: {leaks}"
        # )

        # Create incident ticket
        # await self.jira.create_issue({
        #     'project': 'SEC',
        #     'summary': f'Secret leak detected - {severity}',
        #     'description': str(leaks),
        #     'priority': 'P1' if severity == 'CRITICAL' else 'P2'
        # })

        self.logger.critical(f"Alert triggered: {severity} - {leaks}")

# Run in production
monitor = SecretLeakMonitor()
asyncio.run(monitor.run_continuous_monitoring())
```

---

## Test Scenarios

### Scenario 1: Database Password Leaked

**Simulation:**

```bash
#!/bin/bash
# simulate-db-password-leak.sh

echo "🎭 Simulating database password leak scenario"
echo ""

# 1. Simulate leak: Commit .env file to repository
echo "1. Simulating leak: Committing .env.prod to repository..."
cat > .env.prod << EOF
DATABASE_URL=postgresql://postgres:super-secret-password@db.psychsync.com:5432/psychsync
JWT_SECRET=top-secret-jwt-key
EOF

git add .env.prod
git commit -m "Add production environment file"
git push origin simulate-leak-scenario

echo "✅ Leak simulated (commit pushed)"
echo ""

# 2. Wait for automated detection (CI/CD pipeline)
echo "2. Waiting for automated detection..."
sleep 60

# 3. Check if Gitleaks detected it
echo "3. Checking Gitleaks report..."
gitleaks detect --source . --report-path gitleaks-report.json

if [ $? -ne 0 ]; then
    echo "✅ Gitleaks detected the leak!"
else
    echo "❌ Gitleaks did not detect the leak (this is bad!)"
fi

# 4. Remediation: Revert commit
echo ""
echo "4. Remediation: Reverting commit..."
git revert HEAD --no-edit
git push origin simulate-leak-scenario

echo "✅ Commit reverted"

# 5. Verify remediation
echo ""
echo "5. Verifying remediation..."
if git show HEAD:.env.prod 2>/dev/null; then
    echo "❌ .env.prod still exists (remediation failed)"
else
    echo "✅ .env.prod removed (remediation successful)"
fi

echo ""
echo "🎯 Scenario complete"
echo "Summary: Leaked secret detected and remediated in < 5 minutes"
```

---

### Scenario 2: AWS Access Key Leaked

**Simulation:**

```bash
#!/bin/bash
# simulate-aws-key-leak.sh

echo "🎭 Simulating AWS access key leak scenario"
echo ""

# 1. Create test AWS access key (in a separate AWS account for testing)
echo "1. Creating test AWS access key..."
TEST_KEY_ID=$(aws iam create-access-key --user-name test-user --query 'AccessKey.AccessKeyId' --output text)
TEST_SECRET=$(aws iam create-access-key --user-name test-user --query 'AccessKey.SecretAccessKey' --output text)

echo "Test key created: $TEST_KEY_ID"

# 2. Simulate leak: Add key to code
echo ""
echo "2. Simulating leak: Adding AWS key to configuration file..."
cat > config/aws.py << EOF
AWS_ACCESS_KEY_ID = "$TEST_KEY_ID"
AWS_SECRET_ACCESS_KEY = "$TEST_SECRET"
AWS_REGION = "us-east-1"
EOF

git add config/aws.py
git commit -m "Add AWS configuration"
git push origin simulate-aws-leak

echo "✅ Leak simulated"
echo ""

# 3. Wait for detection
echo "3. Waiting for detection..."
sleep 60

# 4. Remediation: Delete key
echo ""
echo "4. Remediation: Deleting leaked AWS key..."
aws iam delete-access-key --access-key-id $TEST_KEY_ID --user-name test-user

echo "✅ Key deleted"

# 5. Create new key
echo ""
echo "5. Creating new key (rotation)..."
NEW_KEY_JSON=$(aws iam create-access-key --user-name test-user)
NEW_KEY_ID=$(echo $NEW_KEY_JSON | jq -r '.AccessKey.AccessKeyId')
NEW_SECRET=$(echo $NEW_KEY_JSON | jq -r '.AccessKey.SecretAccessKey')

echo "New key created: $NEW_KEY_ID"

# 6. Update configuration
echo ""
echo "6. Updating configuration with new key..."
cat > config/aws.py << EOF
AWS_ACCESS_KEY_ID = "$NEW_KEY_ID"
AWS_SECRET_ACCESS_KEY = "$NEW_SECRET"
AWS_REGION = "us-east-1"
EOF

git add config/aws.py
git commit -m "Rotate AWS credentials"
git push origin simulate-aws-leak

echo "✅ Key rotated"
echo ""
echo "🎯 Scenario complete"
echo "Summary: AWS key leaked, detected, revoked, and rotated in < 10 minutes"
```

---

## Quick Reference Cards

### Card 1: Immediate Response Checklist

**Print this and keep it at your desk!**

```
🚨 SECRET LEAK - IMMEDIATE RESPONSE

☐ 1. IDENTIFY: What type of secret? (Database, API Key, Certificate)
☐ 2. SEVERITY: Production? (CRITICAL < 15 min) / Staging? (HIGH < 1 hour)
☐ 3. REVOKE: Immediately revoke the leaked credential
☐ 4. ROTATE: Generate new secret
☐ 5. UPDATE: Update application configuration
☐ 6. DEPLOY: Redeploy application
☐ 7. VERIFY: Confirm application is working
☐ 8. NOTIFY: Page security team, create incident ticket
☐ 9. MONITOR: Watch for abuse indicators
☐ 10. DOCUMENT: Record timeline and actions taken

📞 EMERGENCY CONTACTS:
   Security Lead: @security-lead (Slack), +1-555-0100 (Pager)
   DevOps: @devops-on-call (Slack), +1-555-0101 (Pager)
   CTO: @cto (Slack), +1-555-0102 (Cell)

🔗 USEFUL LINKS:
   AWS Console: https://console.aws.amazon.com/
   Secrets Manager: https://console.aws.amazon.com/secretsmanager/
   Incident Tracker: https://psychsync.atlassian.net/jira/servicedesk/
```

---

### Card 2: Secret-Specific Revocation Commands

```
DATABASE PASSWORD:
  psql -h db.psychsync.com -U postgres -c "ALTER USER postgres WITH PASSWORD 'new-password';"
  aws secretsmanager update-secret --secret-id psychsync/prod/database --secret-string '{"password":"new-password"}'

AWS ACCESS KEY:
  aws iam update-access-key --access-key-id LEAKED_KEY --status Inactive
  aws iam delete-access-key --access-key-id LEAKED_KEY
  aws iam create-access-key --user-name USERNAME

JWT SECRET:
  openssl rand -base64 64  # Generate new secret
  aws secretsmanager update-secret --secret-id psychsync/prod/jwt --secret-string '{"jwt_secret":"NEW_SECRET"}'
  kubectl rollout restart deployment/psychsync-api -n production

API KEY (OpenAI, Stripe, etc.):
  1. Log in to provider dashboard
  2. Revoke leaked key
  3. Create new key
  4. Update in Secrets Manager
  5. Redeploy application

CERTIFICATE:
  certbot certonly --force-renewal -d api.psychsync.com
  kubectl create secret tls psychsync-tls --cert=/path/to/cert --key=/path/to/key
  kubectl rollout restart deployment/psychsync-api -n production
```

---

### Card 3: Detection and Monitoring Commands

```
CHECK GIT HISTORY FOR SECRETS:
  gitleaks detect --source . --verbose
  trufflehog filesystem ./

CHECK FOR .env FILES IN HISTORY:
  git log --all --full-history --source -- "*env*"

CHECK FOR SECRETS IN SPECIFIC COMMIT:
  git show COMMIT_HASH | grep -iE '(password|api_key|secret|token)'

AUDIT AWS CREDENTIAL USAGE:
  aws iam list-access-keys
  aws iam get-access-key-last-used --access-key-id KEY_ID

CHECK CLOUDTRAIL FOR ABUSE:
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=KEY_ID

MONITOR APPLICATION LOGS:
  kubectl logs -f deployment/psychsync-api -n production | grep -iE '(error|unauthorized|forbidden)'

CHECK DATABASE CONNECTIONS:
  psql -h db.psychsync.com -U postgres -c "SELECT * FROM pg_stat_activity WHERE usename = 'postgres';"
```

---

## Appendix: Incident Response Templates

### Template 1: Incident Report Form

```markdown
# Secret Leak Incident Report

**Incident ID:** INC-YYYY-MM-DD-###
**Date Detected:** YYYY-MM-DD HH:MM UTC
**Reported By:** [Name]
**Severity:** [CRITICAL/HIGH/MEDIUM/LOW]

## 1. Incident Description

**What was leaked?**
- [ ] Database password
- [ ] AWS access key
- [ ] API key
- [ ] JWT secret
- [ ] OAuth client secret
- [ ] Certificate/private key
- [ ] Other: ___________

**Where was it found?**
- [ ] Public GitHub repository
- [ ] Private GitHub repository
- [ ] Documentation
- [ ] Log files
- [ ] Pastebin/public paste
- [ ] Other: ___________

**When was it leaked?**
- First leaked: YYYY-MM-DD HH:MM UTC
- Detected: YYYY-MM-DD HH:MM UTC
- Exposure window: ____ days

## 2. Impact Assessment

**Potential impact:** [Describe what could happen with the leaked secret]

**Confirmed impact:** [Describe any confirmed abuse]

**Data affected:** [List any data that was accessible]

**Systems affected:** [List all affected systems]

## 3. Actions Taken

**Immediate actions (first 15 minutes):**
1.
2.
3.

**Remediation actions (first hour):**
1.
2.
3.

**Follow-up actions (first 24 hours):**
1.
2.
3.

## 4. Root Cause Analysis

**Primary cause:** [Why did this happen?]

**Contributing factors:** [What contributed to this incident?]

**Preventive measures needed:** [What will prevent this from happening again?]

## 5. Communication

**Internal stakeholders notified:**
- [ ] Security team
- [ ] DevOps team
- [ ] Management
- [ ] Legal/compliance (if required)

**External notification required:**
- [ ] No - internal only
- [ ] Yes - regulatory notification required
- [ ] Yes - customer notification required

## 6. Lessons Learned

**What went well:**

**What could be improved:**

**Action items:**

**Incident Commander:** _________________
**Report Date:** YYYY-MM-DD
```

---

### Template 2: Post-Incident Review Agenda

```markdown
# Post-Incident Review Agenda

**Incident:** SECRET LEAK - [INCIDENT_ID]
**Date:** YYYY-MM-DD
**Time:** HH:MM - HH:MM UTC
**Attendees:** [List]

## Agenda

### 1. Introduction (5 min)
- Purpose of review
- Ground rules (blameless, focus on learning)

### 2. Timeline Reconstruction (15 min)
- What happened?
- When did it happen?
- How was it detected?

### 3. Impact Assessment (10 min)
- What was the impact?
- What could have been the worst-case scenario?

### 4. Response Evaluation (10 min)
- What went well in the response?
- What could have been better?

### 5. Root Cause Analysis (20 min)
- Why did this happen?
- What were the contributing factors?
- 5 Whys analysis

### 6. Action Items (15 min)
- What preventive measures are needed?
- Who is responsible?
- What is the timeline?

### 7. Lessons Learned (10 min)
- What did we learn?
- How can we apply this learning?

### 8. Next Steps (5 min)
- Action item assignment
- Follow-up meeting scheduled

## Preparation

**Pre-read materials:**
- Incident report
- Timeline
- Impact assessment
- Root cause analysis

**Tools:**
- Whiteboard/flipchart
- Sticky notes
- Timer

## Facilitation Guidelines

- Keep the conversation focused on learning, not blaming
- Ensure everyone has a chance to speak
- Focus on systemic issues, not individual errors
- End with clear action items and owners
```

---

**Document Owner:** Security Team
**Approval:** CTO, CISO
**Review Date:** Quarterly (next: 2026-03-26)
**Next Exercise:** 2026-01-26 (Tabletop exercise)

---

## Additional Resources

**External Tools:**
- [Gitleaks](https://github.com/gitleaks/gitleaks) - Secret scanner
- [Trufflehog](https://github.com/trufflesecurity/trufflehog) - Deep secret scanner
- [GitGuardian](https://www.gitguardian.com/) - Commercial secret detection
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) - Security best practices

**Internal Resources:**
- Secret Management Guidance (see SECRET_MANAGEMENT_GUIDANCE.md)
- Security Runbook (see SECURITY_RUNBOOK.md)
- Incident Response Plan (see INCIDENT_RESPONSE_PLAN.md)

**Training:**
- [SANS SEC504: Hacker Tools](https://www.sans.org/cyber-security-courses/hacker-tools-techniques-exploits-incident-handling/)
- [SANS SEC560: Network Penetration Testing](https://www.sans.org/cyber-security-courses/network-penetration-testing-ethical-hacking/)
- [CISSP Certification](https://www.isc2.org/Certifications/CISSP)
