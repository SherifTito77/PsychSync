# Secret Management Guidance for PsychSync

**Compliance**: SOC 2, HIPAA §164.312(e)(1), NIST SP 800-53 Rev 5
**Version**: 1.0
**Last Updated**: 2025-12-26

---

## Executive Summary

This guide establishes best practices for managing secrets (API keys, passwords, certificates, tokens) in the PsychSync platform. Following these practices ensures:

- **Zero secrets in code** - No hardcoded credentials in source code
- **Auditability** - All secret access is logged and monitored
- **Rotation capability** - Secrets can be rotated without downtime
- **Least privilege** - Each secret has minimal required permissions
- **Encryption at rest** - Secrets are encrypted in storage

---

## Table of Contents

1. [Secret Categories](#secret-categories)
2. [Storage Architecture](#storage-architecture)
3. [Secret Storage Solutions](#secret-storage-solutions)
4. [Key Rotation Strategies](#key-rotation-strategies)
5. [Access Control](#access-control)
6. [Audit Logging](#audit-logging)
7. [Environment-Specific Guidance](#environment-specific-guidance)
8. [CI/CD Integration](#cicd-integration)
9. [Compliance Mapping](#compliance-mapping)

---

## Secret Categories

### 1. Application Secrets
| Secret Type | Example | Rotation Frequency | Storage Location |
|-------------|---------|-------------------|------------------|
| Database passwords | `DATABASE_URL`, `DB_PASSWORD` | Quarterly | Secrets Manager |
| JWT signing keys | `JWT_SECRET`, `SECRET_KEY` | Quarterly | Secrets Manager |
| API keys (external) | `OPENAI_API_KEY`, `STRIPE_KEY` | Per provider policy | Secrets Manager |
| OAuth secrets | `GOOGLE_CLIENT_SECRET` | Annually | Secrets Manager |

### 2. Infrastructure Secrets
| Secret Type | Example | Rotation Frequency | Storage Location |
|-------------|---------|-------------------|------------------|
| AWS access keys | `AWS_ACCESS_KEY_ID` | Quarterly | AWS Secrets Manager |
| Service account keys | `GCP_SERVICE_ACCOUNT` | Annually | Secret Manager |
| SSL/TLS certificates | `*.psychsync.com` | Before expiry | Certificate Manager |
| SSH keys | `ssh-rsa AAAA...` | Annually | Secrets Manager |

### 3. Third-Party Credentials
| Service | Secret Type | Rotation Frequency | Storage Location |
|---------|-------------|-------------------|------------------|
| SendGrid | API Key | Quarterly | Secrets Manager |
| Slack | Bot Token | Quarterly | Secrets Manager |
| OpenAI | API Key | Per policy | Secrets Manager |
| Anthropic | API Key | Per policy | Secrets Manager |
| Redis | `REDIS_PASSWORD` | Quarterly | Secrets Manager |

---

## Storage Architecture

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PsychSync Application                   │
│  (No secrets hardcoded - all loaded from environment)      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Environment Variables                       │
│  Loaded at runtime from secret management system           │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   AWS SM     │   │  HashiCorp   │   │   Azure KV   │
│ (Production) │   │   Vault      │   │  (Optional)  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Encrypted   │
                    │   Storage     │
                    │   (KMS/GCP)   │
                    └───────────────┘
```

### Implementation Pattern

**Python (FastAPI) - Recommended Approach:**

```python
# app/core/config.py
from pydantic-settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Load secrets from environment variables"""

    # Database
    database_url: str  # Loaded from AWS Secrets Manager

    # JWT
    jwt_secret: str  # Loaded from AWS Secrets Manager

    # API Keys
    openai_api_key: str
    stripe_secret_key: str

    # Third-party
    sendgrid_api_key: str

    class Config:
        env_file = ".env.prod"  # Only for local dev
        case_sensitive = True

settings = Settings()
```

**Loading from AWS Secrets Manager:**

```python
import boto3
import json
from typing import Dict

def load_secrets_from_aws(secret_name: str, region: str = "us-east-1") -> Dict[str, str]:
    """Load secrets from AWS Secrets Manager"""

    client = boto3.client('secretsmanager', region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret

    except Exception as e:
        logger.error(f"Failed to load secret {secret_name}: {e}")
        raise

# Usage in startup:
# export AWS_SECRET_ID=psychsync/prod/secrets
# secrets = load_secrets_from_aws(os.getenv('AWS_SECRET_ID'))
```

---

## Secret Storage Solutions

### Option 1: AWS Secrets Manager (Recommended for AWS)

**Pros:**
- Native AWS integration
- Automatic secret rotation
- IAM-based access control
- CloudTrail logging

**Setup:**

```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure

# Store a secret
aws secretsmanager create-secret \
  --name psychsync/prod/database \
  --description "Production database credentials" \
  --secret-string '{"username":"postgres","password":"your-password","host":"db.psychsync.com"}'

# Enable automatic rotation (30 days)
aws secretsmanager rotate-secret \
  --secret-id psychsync/prod/database \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789:function:rotate-db-password \
  --rotation-rules AutomaticallyAfterDays=30
```

**IAM Policy for Application:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:psychsync/prod/*"
      ]
    }
  ]
}
```

**Cost:** ~$0.40 per secret per month + $0.05 per 10,000 API calls

---

### Option 2: HashiCorp Vault (Multi-Cloud)

**Pros:**
- Cloud-agnostic
- Advanced features (dynamic secrets, encryption as a service)
- Open-source version available

**Setup:**

```bash
# Install Vault
brew tap hashicorp/tap
brew install vault

# Start Vault server (dev mode for testing)
vault server -dev

# Store a secret
vault kv put secret/psychsync/database \
  username="postgres" \
  password="your-password" \
  host="db.psychsync.com"

# Retrieve a secret
vault kv get -field=password secret/psychsync/database

# Enable AWS secrets engine
vault secrets enable -path=aws aws
vault write aws/config/root \
  access_key=$AWS_ACCESS_KEY_ID \
  secret_key=$AWS_SECRET_ACCESS_KEY \
  region=us-east-1
```

**Python Integration:**

```python
import hvac
import os

class VaultSecretLoader:
    """Load secrets from HashiCorp Vault"""

    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR'),
            token=os.getenv('VAULT_TOKEN')
        )

    def get_secret(self, path: str) -> dict:
        """Retrieve secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']

# Usage
loader = VaultSecretLoader()
db_creds = loader.get_secret('secret/psychsync/database')
database_url = f"postgresql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}"
```

---

### Option 3: Environment Variables (Development Only)

**⚠️ WARNING:** Only use this for LOCAL DEVELOPMENT. Never commit .env files.

```bash
# .env.local (NEVER COMMIT)
DATABASE_URL=postgresql://user:pass@localhost:5432/psychsync
JWT_SECRET=dev-secret-key-only
OPENAI_API_KEY=sk-dev-key
```

**Security Measures:**
1. Add `.env.local` to `.gitignore`
2. Add `.env.*` to `.gitignore` (except `.env.example`)
3. Validate in CI that no .env files are committed
4. Use `.env.example` with placeholder values:

```bash
# .env.example (COMMIT THIS)
DATABASE_URL=postgresql://user:password@localhost:5432/psychsync
JWT_SECRET=your-jwt-secret-here
OPENAI_API_KEY=your-openai-api-key-here
```

---

## Key Rotation Strategies

### Rotation Strategy Matrix

| Secret Type | Rotation Method | Downtime Required | Automation |
|-------------|-----------------|-------------------|------------|
| Database password | Toggle between 2 secrets | No | ✅ Yes |
| JWT signing key | Dual-key deployment | No | ✅ Yes |
| API keys | Provider-specific | Maybe | ⚠️ Partial |
| Certificates | ACME/Let's Encrypt | No | ✅ Yes |
| AWS Keys | IAM rotation | No | ✅ Yes |

---

### Strategy 1: Zero-Downtime Database Password Rotation

**Concept:** Maintain two passwords simultaneously, rotate one at a time.

**Implementation:**

```python
# app/core/database.py
from databases import Database
from typing import List

class MultiPasswordDatabase:
    """Support multiple database passwords for rotation"""

    def __init__(self, database_urls: List[str]):
        """
        database_urls: List of connection strings with different passwords
        """
        self.databases = [Database(url) for url in database_urls]
        self.primary_db = self.databases[0]

    async def connect(self):
        """Try all passwords, use first working one"""
        for db in self.databases:
            try:
                await db.connect()
                self.primary_db = db
                logger.info(f"Connected with database URL: {db.url}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect: {e}")
                continue

        raise Exception("All database passwords failed")

    async def execute(self, query, values=None):
        """Execute query on primary database"""
        return await self.primary_db.execute(query, values)

# Usage in config.py
DATABASE_URLS = [
    os.getenv('DATABASE_URL_PRIMARY'),    # Current password
    os.getenv('DATABASE_URL_SECONDARY')   # Previous password (grace period)
]

database = MultiPasswordDatabase(DATABASE_URLS)
```

**Rotation Steps:**

1. **Generate new password** (stored in Secrets Manager)
2. **Add new password to database user**:
   ```sql
   ALTER USER psychsync_user WITH PASSWORD 'new_password';
   -- Keep old password for now
   ```
3. **Update application** to include both passwords
4. **Deploy application** (now supports both passwords)
5. **Remove old password** after 24 hours:
   ```sql
   ALTER USER psychsync_user WITH PASSWORD 'new_password';
   -- Old password no longer works
   ```
6. **Update application** to remove old password from config

---

### Strategy 2: Dual JWT Key Rotation

**Concept:** Support multiple JWT signing keys with key IDs.

**Implementation:**

```python
# app/core/security.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt
from typing import Dict

class JWTKeyManager:
    """Manage multiple JWT signing keys for rotation"""

    def __init__(self):
        self.keys: Dict[str, str] = {
            "key_2025_01": os.getenv('JWT_SECRET_2025_01'),
            "key_2025_02": os.getenv('JWT_SECRET_2025_02'),
        }
        self.primary_key_id = "key_2025_02"

    def encode_token(self, payload: dict) -> str:
        """Encode JWT with primary key"""
        payload['kid'] = self.primary_key_id  # Key ID
        return jwt.encode(payload, self.keys[self.primary_key_id], algorithm='HS256')

    def decode_token(self, token: str) -> dict:
        """Decode JWT with any key (try all)"""
        try:
            # Get key ID from header
            header = jwt.get_unverified_header(token)
            key_id = header.get('kid')

            # Use specific key if available
            if key_id and key_id in self.keys:
                return jwt.decode(token, self.keys[key_id], algorithms=['HS256'])

            # Try all keys (for legacy tokens without kid)
            for key in self.keys.values():
                try:
                    return jwt.decode(token, key, algorithms=['HS256'])
                except jwt.InvalidSignatureError:
                    continue

            raise jwt.InvalidTokenError("No valid key found")

        except Exception as e:
            logger.error(f"JWT decode error: {e}")
            raise

# Usage
jwt_manager = JWTKeyManager()

# Encode (uses primary key)
token = jwt_manager.encode_token({"user_id": "123"})

# Decode (tries all keys)
payload = jwt_manager.decode_token(token)
```

**Rotation Steps:**

1. **Generate new secret** (`JWT_SECRET_2025_03`)
2. **Add to Secrets Manager** and application config
3. **Update `primary_key_id`** to new key
4. **Deploy application**
5. **Keep old keys** for at least 30 days (to validate existing tokens)
6. **Remove old keys** after token expiry period

---

### Strategy 3: API Key Rotation (Third-Party Services)

**Challenge:** Some services don't support multiple keys simultaneously.

**Workaround:**

```python
# app/services/api_key_rotator.py
import asyncio
from typing import Optional

class APIKeyRotator:
    """Handle API key rotation with fallback mechanism"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.primary_key = os.getenv(f'{service_name}_API_KEY')
        self.previous_key = os.getenv(f'{service_name}_API_KEY_PREV')

    async def make_request(self, url: str, **kwargs):
        """Make API request with fallback to previous key"""
        headers = kwargs.pop('headers', {})

        # Try primary key first
        headers['Authorization'] = f'Bearer {self.primary_key}'
        response = await self._http_request(url, headers=headers, **kwargs)

        if response.status_code == 401:  # Unauthorized
            # Try previous key
            logger.warning(f"Primary key failed, trying previous key for {self.service_name}")
            headers['Authorization'] = f'Bearer {self.previous_key}'
            response = await self._http_request(url, headers=headers, **kwargs)

        return response

    async def _http_request(self, url, headers, **kwargs):
        # Actual HTTP request implementation
        pass

# Usage
openai_rotator = APIKeyRotator('OPENAI')
response = await openai_rotator.make_request('https://api.openai.com/v1/models')
```

---

## Access Control

### Principle of Least Privilege

**Application IAM Policy (Production):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadProductionSecrets",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:psychsync/prod/*"
      ]
    },
    {
      "Sid": "DenyDevelopmentSecrets",
      "Effect": "Deny",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:psychsync/dev/*"
      ]
    },
    {
      "Sid": "DenySecretManagement",
      "Effect": "Deny",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:RotateSecret"
      ],
      "Resource": "*"
    }
  ]
}
```

### Developer Access (Secrets Management)

**Developers should NOT have direct access to production secrets.**

Instead, use:
1. **IAM roles** for deployment pipelines
2. **Secrets Manager approval workflow** for emergency access
3. **Audit logging** for all secret access

**Emergency Access Process:**

```bash
# Developer requests temporary access
aws secretsmanager get-secret-value \
  --secret-id psychsync/prod/database \
  --profile emergency-access-profile

# Requires:
# 1. Manager approval (AWS Approval Workflow)
# 2. MFA authentication
# 3. Time-limited access (1 hour)
# 4. Auto-revocation after expiry
```

---

## Audit Logging

### AWS CloudTrail Integration

All Secrets Manager access is logged to CloudTrail by default.

**Enable CloudTrail:**

```bash
# Create S3 bucket for logs
aws s3 mb s3://psychsync-cloudtrail-logs

# Create CloudTrail
aws cloudtrail create-trail \
  --name psychsync-secret-audit \
  --s3-bucket-name psychsync-cloudtrail-logs

# Enable logging
aws cloudtrail start-logging --name psychsync-secret-audit
```

**Query Audit Logs (Athena):**

```sql
-- Find all secret access in last 24 hours
SELECT
  userIdentity.principalId,
  eventTime,
  sourceIPAddress,
  eventName,
  resources
FROM cloudtrail_logs
WHERE eventsource = 'secretsmanager.amazonaws.com'
  AND eventTime > now() - interval '24' hour
ORDER BY eventTime DESC;
```

### Custom Audit Logging

**Log all secret access in application:**

```python
# app/core/audit_logger.py
from datetime import datetime
import json

class SecretAccessLogger:
    """Log all secret access for auditing"""

    def __init__(self):
        self.logger = logging.getLogger('audit.secret_access')

    def log_access(self, secret_name: str, user_id: str, action: str):
        """Log secret access event"""

        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'secret_name': secret_name,
            'user_id': user_id,
            'action': action,  # 'read', 'rotate', 'delete'
            'source_ip': request.client.host if request else None,
            'user_agent': request.headers.get('user-agent') if request else None,
        }

        # Structured logging (JSON format)
        self.logger.info(json.dumps(event))

        # Send to SIEM (Security Information and Event Management)
        # self.send_to_siem(event)

# Usage in config.py
audit_logger = SecretAccessLogger()
secret_value = load_secrets_from_aws('psychsync/prod/database')
audit_logger.log_access('psychsync/prod/database', user_id='system', action='read')
```

---

## Environment-Specific Guidance

### Development Environment

**Guidelines:**
- ✅ Use `.env.local` files (never committed)
- ✅ Use placeholder secrets for testing (`test_secret_123`)
- ✅ Document required secrets in `.env.example`
- ❌ Never use production secrets
- ❌ Never commit `.env` files

**Example:**

```bash
# .env.example (COMMIT THIS)
DATABASE_URL=postgresql://user:password@localhost:5432/psychsync
JWT_SECRET=dev-jwt-secret
OPENAI_API_KEY=sk-test-key
REDIS_URL=redis://localhost:6379

# .env.local (DO NOT COMMIT)
DATABASE_URL=postgresql://dev:actual-password@localhost:5432/psychsync
JWT_SECRET=some-random-secret-string-here
OPENAI_API_KEY=sk-actual-dev-key-here
REDIS_URL=redis://localhost:6379
```

### Staging Environment

**Guidelines:**
- ✅ Use separate secrets from production
- ✅ Store in AWS Secrets Manager (staging prefix)
- ✅ Implement same rotation policies as production
- ⚠️ Use production-like data (anonymized)

**Secret Naming Convention:**

```bash
psychsync/staging/database
psychsync/staging/jwt
psychsync/staging/openai_api_key
```

### Production Environment

**Guidelines:**
- ✅ Use AWS Secrets Manager or HashiCorp Vault
- ✅ Enable automatic rotation (30-90 days)
- ✅ Implement audit logging
- ✅ Use IAM roles (not access keys)
- ✅ Enable encryption at rest (KMS)
- ❌ NO environment files
- ❌ NO hardcoded secrets
- ❌ NO .env files

**Secret Naming Convention:**

```bash
psychsync/prod/database
psychsync/prod/jwt
psychsync/prod/openai_api_key
psychsync/prod/stripe_secret_key
```

---

## CI/CD Integration

### GitHub Actions: Load Secrets at Runtime

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Load secrets from AWS Secrets Manager
        run: |
          # Fetch secrets and export as environment variables
          SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id psychsync/prod/secrets --query SecretString --output text)

          # Export to GitHub Actions environment
          echo "DATABASE_URL=$(echo $SECRET_JSON | jq -r '.DATABASE_URL')" >> $GITHUB_ENV
          echo "JWT_SECRET=$(echo $SECRET_JSON | jq -r '.JWT_SECRET')" >> $GITHUB_ENV
          echo "OPENAI_API_KEY=$(echo $SECRET_JSON | jq -r '.OPENAI_API_KEY')" >> $GITHUB_ENV

      - name: Deploy application
        run: |
          # Secrets are now available as $DATABASE_URL, $JWT_SECRET, etc.
          ./deploy.sh

      - name: Verify deployment
        run: |
          curl -f https://api.psychsync.com/health || exit 1
```

### Secret Rotation in CI/CD

```yaml
# .github/workflows/rotate-secrets.yml
name: Rotate Secrets

on:
  schedule:
    - cron: '0 0 1 * *'  # First day of every month
  workflow_dispatch:

jobs:
  rotate-database-password:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ROTATION_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_ROTATION_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Generate new password
        run: |
          NEW_PASSWORD=$(openssl rand -base64 32)
          echo "NEW_PASSWORD=$NEW_PASSWORD" >> $GITHUB_ENV

      - name: Update database password
        run: |
          PGPASSWORD=$OLD_PASSWORD psql -h db.psychsync.com -U postgres -d psychsync -c \
            "ALTER USER postgres WITH PASSWORD '${NEW_PASSWORD}';"

      - name: Update AWS Secrets Manager
        run: |
          aws secretsmanager update-secret \
            --secret-id psychsync/prod/database \
            --secret-string "{\"username\":\"postgres\",\"password\":\"${NEW_PASSWORD}\"}"

      - name: Restart application
        run: |
          kubectl rollout restart deployment/psychsync-api -n production
```

---

## Compliance Mapping

### SOC 2 Type II Compliance

| Requirement | Implementation | Evidence |
|-------------|----------------|----------|
| **CC6.1**: Logical and physical access controls | IAM roles, least privilege | IAM policies |
| **CC6.6**: Encryption of confidential information | KMS encryption at rest | KMS key policies |
| **CC7.2**: Periodic rotation of credentials | Automatic rotation every 90 days | Rotation schedule |
| **CC7.3**: Unique credentials for each user | No shared credentials | Audit logs |

### HIPAA §164.312(e)(1) - Transmission Security

| Requirement | Implementation | Evidence |
|-------------|----------------|----------|
| Encryption of PHI in transit | TLS 1.3 for all connections | SSL/TLS configuration |
| Encryption of PHI at rest | KMS encryption (AES-256) | KMS key policies |
| Access controls | Role-based access control | IAM policies |

### NIST SP 800-53 Rev 5

| Control | Implementation |
|---------|----------------|
| **IA-5(1)**: Authenticator Management | Automated secret rotation |
| **IA-5(7)**: Authenticator Protection | Password hashing with Argon2id |
| **SC-12**: Cryptographic Key Management and Establishment | KMS for encryption at rest |
| **SC-28**: Protection of Information at Rest | Encryption in Secrets Manager |
| **AU-2**: Audit Events | CloudTrail integration |

---

## Monitoring and Alerting

### CloudWatch Alarms

```bash
# Alert on failed secret access
aws cloudwatch put-metric-alarm \
  --alarm-name psychsync-secret-access-failure \
  --alarm-description "Alert on failed secret access attempts" \
  --metric-name AuthenticationFailures \
  --namespace AWS/SecretsManager \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# SNS topic for alerts
aws sns create-topic --topic psychsync-security-alerts
```

### Monitoring Dashboard (Grafana)

```json
{
  "dashboard": {
    "title": "Secret Access Monitoring",
    "panels": [
      {
        "title": "Secret Access Rate",
        "query": "sum(rate(secret_access_count[5m]))"
      },
      {
        "title": "Failed Access Attempts",
        "query": "sum(rate(secret_access_failures[5m]))"
      },
      {
        "title": "Secret Rotation Status",
        "query": "last_secret_rotation_time"
      }
    ]
  }
}
```

---

## Quick Start Checklist

### Day 1: Initial Setup
- [ ] Install AWS CLI and configure credentials
- [ ] Create AWS Secrets Manager
- [ ] Store first secret (test connection)
- [ ] Configure IAM role for application
- [ ] Enable CloudTrail logging
- [ ] Add `.env.example` to git repo
- [ ] Add all `.env*` files to `.gitignore`

### Week 1: Migrate Existing Secrets
- [ ] Audit all hardcoded secrets in code
- [ ] Move database credentials to Secrets Manager
- [ ] Move JWT secret to Secrets Manager
- [ ] Move API keys to Secrets Manager
- [ ] Update application to load from environment
- [ ] Test in staging environment

### Month 1: Production Rollout
- [ ] Deploy to production with Secrets Manager
- [ ] Enable automatic rotation (90 days)
- [ ] Set up monitoring and alerting
- [ ] Document emergency access process
- [ ] Train developers on new process

### Ongoing: Maintenance
- [ ] Review secret access logs weekly
- [ ] Rotate secrets on schedule
- [ ] Update documentation
- [ ] Audit IAM permissions quarterly
- [ ] Test disaster recovery procedures

---

## Further Reading

- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

---

## Appendix: Example Secret Definitions

### AWS Secrets Manager Secret Structure

```json
{
  "psychsync/prod/database": {
    "engine": "postgres",
    "host": "db.psychsync.com",
    "port": 5432,
    "username": "psychsync_user",
    "password": "secure-random-password",
    "dbname": "psychsync_prod",
    "sslmode": "require"
  },
  "psychsync/prod/jwt": {
    "secret_key": "random-256-bit-secret",
    "algorithm": "HS256",
    "expiration_hours": 24
  },
  "psychsync/prod/openai": {
    "api_key": "sk-openai-key",
    "organization": "org-psychsync"
  },
  "psychsync/prod/redis": {
    "host": "redis.psychsync.com",
    "port": 6379,
    "password": "redis-password",
    "tls": "true"
  }
}
```

---

**Document Owner:** Security Team
**Approval:** CTO, CISO
**Review Date:** Quarterly (next: 2026-03-26)
