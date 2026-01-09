# Production Secrets Management Guidelines for PsychSync

**Purpose:** Comprehensive guide for managing secrets securely in Kubernetes production environments
**Date:** 2025-12-27
**Platform:** Kubernetes (AWS EKS, GCP GKE, Azure AKS)
**Compliance:** SOC2, HIPAA, GDPR, PCI DSS

---

## 📋 Executive Summary

This guide provides a **defense-in-depth approach** to secrets management in Kubernetes, covering:

1. ✅ **Encryption at Rest** (Kubernetes native)
2. ✅ **External Secrets Management** (Vault, AWS Secrets Manager, etc.)
3. ✅ **Secrets Rotation** (Automated)
4. ✅ **Access Control** (RBAC, Audit Logging)
5. ✅ **Runtime Security** (No secrets in env vars, mounted as files)
6. ✅ **Backup & Recovery** (Disaster recovery for secrets)

**Security Principle:** Secrets should never be stored in plain text, committed to git, or exposed in logs.

---

## 🚨 Critical Security Requirements

### Requirements for Production

- ❌ **NO secrets in git repositories** (encrypted or not)
- ❌ **NO secrets in environment variables** (visible via `/proc`, child processes)
- ❌ **NO secrets in Docker images** (layer history, `docker inspect`)
- ❌ **NO secrets in ConfigMaps** (not encrypted, plaintext)
- ❌ **NO sharing of service account tokens** between pods

- ✅ **Encryption at rest** (Kubernetes etcd encryption)
- ✅ **Encryption in transit** (TLS for all API communication)
- ✅ **External secrets management** (Vault, AWS Secrets Manager, etc.)
- ✅ **Least privilege access** (RBAC for secrets)
- ✅ **Audit logging** (who accessed what secret when)
- ✅ **Automated rotation** (regular credential rotation)
- ✅ **Runtime injection** (secrets mounted as files, not env vars)

---

## 🔐 Layer 1: Kubernetes Native Secrets Encryption

### 1.1 Enable Encryption at Rest for etcd

**Problem:** By default, Kubernetes secrets are stored in **plaintext** in etcd.

**Solution:** Enable encryption at rest using Kubernetes Encryption Configuration.

**Implementation:**

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    # KMS plugin (recommended for production)
    - kms:
        name: aws-eks-kms
        endpoint: "unix:///var/run/kmsplugin/socket.sock"
        cachesize: 1000
        timeout: 3s
    # AES-GCM (fallback)
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-secret>
    # Secretbox (fallback)
    - secretbox:
        keys:
        - name: key1
          secret: <base64-encoded-secret>
    # Identity (plaintext - DO NOT USE IN PRODUCTION)
    - identity: {}
```

**Enable in API Server:**

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - name: kube-apiserver
    command:
    - kube-apiserver
    - --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
    - --encryption-provider-config-automatic-reload=true
    volumeMounts:
    - name: encryption-config
      mountPath: /etc/kubernetes/encryption-config.yaml
      readOnly: true
  volumes:
  - name: encryption-config
    hostPath:
      path: /etc/kubernetes/encryption-config.yaml
```

**Verify Encryption:**

```bash
# Create a test secret
kubectl create secret generic test-secret --from-literal=key=value -n psychsync

# Check etcd directly (should be encrypted)
ETCDCTL_API=3 etcdctl get /registry/secrets/default/test-secret ... | hexdump -C

# Should see encrypted data, not "key=value"
```

### 1.2 Pod Security Policies for Secrets

**Restrict secret access to necessary pods only:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: psychsync-backend
  namespace: psychsync
automountServiceAccountToken: false  # Don't mount service account token
```

```yaml
spec:
  template:
    spec:
      # Don't automount service account token
      automountServiceAccountToken: false

      # Only mount specific secrets
      volumes:
      - name: psychsync-secrets
        secret:
          secretName: psychsync-secrets
          optional: false

      containers:
      - name: backend
        # Mount secrets as files (NOT environment variables)
        volumeMounts:
        - name: psychsync-secrets
          mountPath: /etc/secrets
          readOnly: true
```

**Why mount as files instead of env vars?**
- Env vars visible via `/proc/<pid>/environ`
- Env vars accessible to child processes
- Env vars logged by some applications
- Mounted files have better audit trail
- Files can have permissions (0400)

---

## 🔐 Layer 2: External Secrets Operator (Recommended)

### 2.1 External Secrets Operator Architecture

**Problem:** Kubernetes secrets are still stored in etcd (even if encrypted).

**Solution:** Use **External Secrets Operator** to sync secrets from secure external sources (Vault, AWS Secrets Manager, etc.) into Kubernetes on-demand.

**Benefits:**
- ✅ Secrets stored in dedicated secrets manager (more secure than etcd)
- ✅ Fine-grained audit logging
- ✅ Automatic secret rotation
- ✅ Integration with cloud provider security
- ✅ Secrets not in git (only references)
- ✅ RBAC for secret access
- ✅ Version history of secrets

### 2.2 AWS Secrets Manager Setup

**Install External Secrets Operator:**

```bash
# Add Helm repo
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets \
  --create-namespace \
  --set installCRDs=true
```

**Create AWS Secrets Manager Secret:**

```bash
# Store secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name psychsync/production/database \
  --secret-string '{"username":"psychsync","password":"CHANGEME","host":"postgres.psychsync.svc.cluster.local","port":"5432","dbname":"psychsync"}'

# Store secret for JWT
aws secretsmanager create-secret \
  --name psychsync/production/jwt \
  --secret-string '{"secret_key":"CHANGEME-32-byte-key"}'

# Store secret for API keys
aws secretsmanager create-secret \
  --name psychsync/production/openai \
  --secret-string '{"api_key":"sk-CHANGEME"}'
```

**Create SecretStore (defines where to fetch secrets from):**

```yaml
# deploy/kubernetes/base/secretstore-aws.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: psychsync
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

**Create IAM Role for Service Account (IRSA):**

```yaml
# IAM policy for external-secrets-sa
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
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:psychsync/production/*"
      ]
    }
  ]
}
```

**Create ExternalSecret (defines which secrets to sync):**

```yaml
# deploy/kubernetes/base/externalsecret-database.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: psychsync-database
  namespace: psychsync
spec:
  refreshInterval: 1h  # Sync every hour
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: psychsync-database  # Name of K8s secret to create
    creationPolicy: Owner
    deletionPolicy: Retain  # Keep K8s secret if ExternalSecret is deleted
  data:
  - secretKey: DATABASE_URL  # Key in K8s secret
    remoteRef:
      key: psychsync/production/database  # Name in AWS Secrets Manager
      property: username  # JSON property (optional)
  - secretKey: DATABASE_USER
    remoteRef:
      key: psychsync/production/database
      property: username
  - secretKey: DATABASE_PASSWORD
    remoteRef:
      key: psychsync/production/database
      property: password
  - secretKey: DATABASE_HOST
    remoteRef:
      key: psychsync/production/database
      property: host
```

```yaml
# deploy/kubernetes/base/externalsecret-jwt.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: psychsync-jwt
  namespace: psychsync
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: psychsync-jwt
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
  - secretKey: JWT_SECRET_KEY
    remoteRef:
      key: psychsync/production/jwt
      property: secret_key
  - secretKey: JWT_ALGORITHM
    remoteRef:
      key: psychsync/production/jwt
      property: algorithm
```

**Use in Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: psychsync-backend
  namespace: psychsync
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        # Reference the synced secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: psychsync-database  # K8s secret created by ExternalSecret
              key: DATABASE_URL
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: psychsync-jwt
              key: JWT_SECRET_KEY

        # Or mount as files (recommended)
        volumeMounts:
        - name: database-secrets
          mountPath: /etc/secrets/database
          readOnly: true
      volumes:
      - name: database-secrets
        secret:
          secretName: psychsync-database
```

### 2.3 HashiCorp Vault Setup (Alternative to AWS)

**Install Vault:**

```bash
# Add Helm repo
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault
helm install vault hashicorp/vault \
  -n vault \
  --create-namespace \
  --set "server.dev.enabled=true"
```

**Configure Vault Kubernetes Auth:**

```bash
# Enable Kubernetes auth method
vault auth enable kubernetes

# Configure Kubernetes auth
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Create policy for PsychSync
vault policy write psychsync-policy - <<EOF
path "psychsync/data/production/*" {
  capabilities = ["read"]
}
EOF

# Create role for PsychSync service account
vault write auth/kubernetes/role/psychsync-backend \
  bound_service_account_names=psychsync-backend \
  bound_service_account_namespaces=psychsync \
  policies=psychsync-policy \
  ttl=24h
```

**Store secrets in Vault:**

```bash
# Enable KV secrets engine
vault secrets enable -path=psychsync kv-v2

# Store database credentials
vault kv put psychsync/production/database \
  username=psychsync \
  password=CHANGEME \
  host=postgres.psychsync.svc.cluster.local \
  port=5432 \
  dbname=psychsync

# Store JWT secret
vault kv put psychsync/production/jwt \
  secret_key=CHANGEME-32-byte-key \
  algorithm=HS256

# Store API keys
vault kv put psychsync/production/openai \
  api_key=sk-CHANGEME
```

**Create SecretStore for Vault:**

```yaml
# deploy/kubernetes/base/secretstore-vault.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: psychsync
spec:
  provider:
    vault:
      server: "https://vault.vault.svc.cluster.local:8200"
      path: "psychsync"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "psychsync-backend"
          serviceAccountRef:
            name: psychsync-backend
```

**Create ExternalSecret for Vault:**

```yaml
# deploy/kubernetes/base/externalsecret-vault.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: psychsync-database
  namespace: psychsync
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: psychsync-database
    creationPolicy: Owner
  data:
  - secretKey: DATABASE_URL
    remoteRef:
      key: production/database  # Vault path (without psychsync/ prefix)
      property: username
```

---

## 🔄 Layer 3: Secrets Rotation

### 3.1 Automated Rotation Strategy

**Database Credentials:**

```bash
#!/bin/bash
# scripts/rotate-database-password.sh

# Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update in AWS Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id psychsync/production/database \
  --secret-string "{\"username\":\"psychsync\",\"password\":\"$NEW_PASSWORD\",\"host\":\"postgres.psychsync.svc.cluster.local\",\"port\":\"5432\",\"dbname\":\"psychsync\"}"

# Update in PostgreSQL
PGPASSWORD="$OLD_PASSWORD" psql \
  -h postgres.psychsync.svc.cluster.local \
  -U psychsync \
  -d psychsync \
  -c "ALTER USER psychsync WITH PASSWORD '$NEW_PASSWORD';"

# Wait for External Secrets Operator to sync (max 1 hour)
sleep 5

# Trigger pod rollout to pick up new password
kubectl rollout restart deployment psychsync-backend -n psychsync

echo "Database password rotated successfully"
```

**Add to cron:**

```yaml
# Kubernetes CronJob for password rotation
apiVersion: batch/v1
kind: CronJob
metadata:
  name: rotate-database-password
  namespace: psychsync
spec:
  schedule: "0 2 1 * *"  # 2 AM on the 1st of every month
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: secret-rotator
          containers:
          - name: rotator
            image: psychsync/secret-rotator:v1.0.0
            command:
            - /scripts/rotate-database-password.sh
            env:
            - name: AWS_REGION
              value: "us-east-1"
            - name: CLUSTER_NAME
              value: "psychsync-production"
          restartPolicy: OnFailure
```

### 3.2 JWT Secret Rotation

**Strategy:**
- Use multiple JWT secrets (key versioning)
- Gradually migrate to new key
- Keep old key for 1 week (token expiry)

**Implementation:**

```python
# app/core/security.py
from datetime import datetime, timedelta

class JWTKeyManager:
    """Manage multiple JWT keys for rotation"""

    def __init__(self):
        self.keys = {
            "current": os.getenv("JWT_SECRET_KEY_V2"),
            "previous": os.getenv("JWT_SECRET_KEY_V1")
        }

    def encode(self, payload: dict) -> str:
        """Encode with current key"""
        return jwt.encode(payload, self.keys["current"], algorithm="HS256")

    def decode(self, token: str) -> dict:
        """Try current key first, then previous key"""
        try:
            return jwt.decode(token, self.keys["current"], algorithms=["HS256"])
        except jwt.InvalidTokenError:
            try:
                return jwt.decode(token, self.keys["previous"], algorithms=["HS256"])
            except jwt.InvalidTokenError:
                raise
```

**ExternalSecret for multiple versions:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: psychsync-jwt
  namespace: psychsync
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: psychsync-jwt
    creationPolicy: Owner
  data:
  - secretKey: JWT_SECRET_KEY_V1  # Previous version
    remoteRef:
      key: psychsync/production/jwt
      property: secret_key_v1
  - secretKey: JWT_SECRET_KEY_V2  # Current version
    remoteRef:
      key: psychsync/production/jwt
      property: secret_key_v2
```

---

## 🔍 Layer 4: Access Control & Auditing

### 4.1 RBAC for Secrets Access

**Principle:** Only allow necessary service accounts to access specific secrets.

```yaml
# deploy/kubernetes/base/rbac-secrets.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: psychsync-secrets-reader
  namespace: psychsync
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames:  # Only specific secrets
  - psychsync-database
  - psychsync-jwt
  - psychsync-api-keys
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: psychsync-secrets-reader-binding
  namespace: psychsync
subjects:
- kind: ServiceAccount
  name: psychsync-backend
  namespace: psychsync
roleRef:
  kind: Role
  name: psychsync-secrets-reader
  apiGroup: rbac.authorization.k8s.io
```

### 4.2 Audit Logging

**Enable Kubernetes Audit Logging:**

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log secret access
- level: RequestResponse
  verbs: ["get", "list", "watch"]
  resources:
  - group: ""
    resources: ["secrets"]

# Log secret creation/deletion
- level: Metadata
  verbs: ["create", "update", "delete"]
  resources:
  - group: ""
    resources: ["secrets"]

# Log all requests from system:masters (admin)
- level: RequestResponse
  userGroups: ["system:masters"]

# Log all other requests at metadata level
- level: Metadata
```

**Configure API Server:**

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - name: kube-apiserver
    command:
    - kube-apiserver
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    - --audit-log-path=/var/log/kubernetes/audit.log
    - --audit-log-maxage=30
    - --audit-log-maxbackup=10
    - --audit-log-maxsize=100
    volumeMounts:
    - name: audit-config
      mountPath: /etc/kubernetes/audit-policy.yaml
      readOnly: true
    - name: audit-log
      mountPath: /var/log/kubernetes
  volumes:
  - name: audit-config
    hostPath:
      path: /etc/kubernetes/audit-policy.yaml
  - name: audit-log
    hostPath:
      path: /var/log/kubernetes
```

**Send audit logs to CloudWatch/Splunk:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-audit-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/kubernetes/audit.log
      pos_file /var/log/fluentd-audit.log.pos
      tag kubernetes.audit
      <parse>
        @type json
      </parse>
    </source>

    <match kubernetes.**>
      @type cloudwatch_logs
      log_group_name kubernetes-audit-logs
      log_stream_name_from_tag true
      auto_create_stream true
    </match>
```

---

## 🚀 Layer 5: Best Practices

### 5.1 Development vs Production

**Development (OK):**
```yaml
# Use plaintext secrets for local development
apiVersion: v1
kind: Secret
metadata:
  name: psychsync-secrets-dev
  namespace: psychsync-dev
type: Opaque
stringData:
  DATABASE_URL: "postgresql://dev:dev@localhost:5432/psychsync"
  JWT_SECRET: "dev-secret-not-for-production"
```

**Production (REQUIRED):**
```yaml
# Use External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: psychsync-secrets-prod
  namespace: psychsync
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: psychsync-secrets
    creationPolicy: Owner
  dataFrom:
  - key: psychsync/production/all
```

### 5.2 GitOps with Secrets

**❌ BAD: Commit secrets to git (even encrypted)**

```yaml
# DON'T DO THIS
apiVersion: v1
kind: Secret
metadata:
  name: psychsync-secrets
stringData:
  DATABASE_PASSWORD: "super-secret-password"  # Visible in git history!
```

**✅ GOOD: Commit ExternalSecret manifest only**

```yaml
# deploy/kubernetes/base/externalsecret-database.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: psychsync-database
  namespace: psychsync
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: psychsync-database
  data:
  - secretKey: DATABASE_PASSWORD
    remoteRef:
      key: psychsync/production/database
      property: password
# NO ACTUAL SECRETS IN GIT - JUST REFERENCES!
```

### 5.3 Runtime Security

**❌ BAD: Secrets as environment variables**

```yaml
spec:
  containers:
  - name: backend
    env:
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: psychsync-secrets
          key: password
    # Visible via: kubectl exec -it pod -- env
    # Visible via: /proc/<pid>/environ
```

**✅ GOOD: Secrets as files**

```yaml
spec:
  containers:
  - name: backend
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
    env:
    - name: SECRETS_PATH
      value: "/etc/secrets"  # Just path, not actual secret
  volumes:
  - name: secrets
    secret:
      secretName: psychsync-secrets
      defaultMode: 0400  # Read-only for owner only
```

**Application code:**

```python
# app/core/config.py
from pathlib import Path
import json

class SecretsManager:
    """Load secrets from mounted files"""

    def __init__(self, secrets_path: str = "/etc/secrets"):
        self.secrets_path = Path(secrets_path)

    def get_secret(self, key: str) -> str:
        """Read secret from file"""
        secret_file = self.secrets_path / key
        if not secret_file.exists():
            raise ValueError(f"Secret {key} not found")

        return secret_file.read_text().strip()

# Usage
secrets = SecretsManager()
database_password = secrets.get_secret("DATABASE_PASSWORD")
```

### 5.4 Secrets Backup & Disaster Recovery

**Backup AWS Secrets Manager:**

```bash
#!/bin/bash
# scripts/backup-secrets.sh

BACKUP_DIR="/backup/secrets/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# List all secrets
SECRETS=$(aws secretsmanager list-secrets \
  --query "SecretList[?contains(Name, 'psychsync')].Name" \
  --output text)

# Backup each secret
for secret in $SECRETS; do
  echo "Backing up $secret"
  aws secretsmanager get-secret-value \
    --secret-id "$secret" \
    --query SecretString \
    --output text > "$BACKUP_DIR/$(basename $secret).json"
done

# Encrypt backup
gpg --encrypt --recipient security@psychsync.com "$BACKUP_DIR"/*

# Upload to S3 (versioned, encrypted bucket)
aws s3 sync "$BACKUP_DIR" s3://psychsync-secrets-backup/$(date +%Y%m%d)/

echo "Backup complete: $BACKUP_DIR"
```

**Restore from backup:**

```bash
#!/bin/bash
# scripts/restore-secrets.sh

BACKUP_DATE=$1
BACKUP_DIR="/tmp/secrets-restore"

# Download from S3
aws s3 sync s3://psychsync-secrets-backup/$BACKUP_DATE/ "$BACKUP_DIR/"

# Decrypt
gpg --decrypt "$BACKUP_DIR"/*.gpg > "$BACKUP_DIR/secrets.json"

# Restore each secret
for secret_file in "$BACKUP_DIR"/*.json; do
  secret_name=$(basename "$secret_file" .json)
  secret_value=$(cat "$secret_file")

  echo "Restoring $secret_name"
  aws secretsmanager put-secret-value \
    --secret-id "$secret_name" \
    --secret-string "$secret_value"
done

echo "Restore complete"
```

---

## 📊 Secrets Management Checklist

### Pre-Production

- [ ] Enable etcd encryption at rest
- [ ] Install External Secrets Operator
- [ ] Create SecretStore (AWS/Vault)
- [ ] Store all secrets in external manager
- [ ] Create ExternalSecret manifests
- [ ] Verify secrets sync correctly
- [ ] Test secret rotation
- [ ] Configure RBAC for secrets access
- [ ] Enable audit logging
- [ ] Setup backup/restore procedures

### Production Deployment

- [ ] NO secrets in git repository
- [ ] NO secrets in environment variables
- [ ] Secrets mounted as files only (mode 0400)
- [ ] All secrets have external source
- [ ] Automated rotation scheduled
- [ ] Monitoring for secret access
- [ ] Alert on secret access failures
- [ ] Documented disaster recovery
- [ ] Compliance audit passed

### Ongoing Maintenance

- [ ] Review secret access logs weekly
- [ ] Rotate secrets per schedule (90 days max)
- [ ] Test backup/restore quarterly
- [ ] Audit external secrets manager access
- [ ] Review and update RBAC policies
- [ ] Monitor for leaked secrets (git history, logs, etc.)

---

## 🎯 Recommended Architecture for PsychSync

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              PsychSync Namespace                      │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ExternalSecret  ┌──────────────┐ │  │
│  │  │   Backend    │ ◄───────────────►│  K8s Secret  │ │  │
│  │  │    Pod       │                   │ (ephemeral) │ │  │
│  │  └──────────────┘                   └──────┬───────┘ │  │
│  │         ▲                                   ▲         │  │
│  │         │                                   │         │  │
│  │    mounted as                            synced     │  │
│  │    files (0400)                       every hour    │  │
│  │                                           │         │  │
│  │                                   ExternalSecret  │  │
│  │                                   Operator (sync) │  │
│  └───────────────────────────────────────│─────────────┘  │
│                                            │                │
└────────────────────────────────────────────┼────────────────┘
                                             │
                                             ▼
                            ┌──────────────────────────────────┐
                            │   AWS Secrets Manager / Vault    │
                            │   (Encrypted at rest)            │
                            │   - Fine-grained access control  │
                            │   - Automatic rotation           │
                            │   - Audit logging                │
                            │   - Version history              │
                            └──────────────────────────────────┘
```

---

## 📚 Additional Resources

**Tools:**
- External Secrets Operator: https://external-secrets.io/
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/
- HashiCorp Vault: https://www.vaultproject.io/
- Mozilla SOPS: https://github.com/mozilla/sops/

**Documentation:**
- Kubernetes Secrets Encryption: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- External Secrets Operator Docs: https://external-secrets.io/v0.5.9/guides/aws-secrets-manager/
- AWS Secrets Manager Docs: https://docs.aws.amazon.com/secretsmanager/

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Maintained By:** Security Team

**Summary:** Use External Secrets Operator with AWS Secrets Manager (or Vault), enable etcd encryption, mount secrets as files, implement automated rotation, enable audit logging, and never commit secrets to git.

