# Incident Response Runbook: Poisoned RAG/Fine-Tuning Corpora

**Runbook ID**: IR-ML-002
**Version**: 1.0.0
**Last Updated**: 2025-12-26
**Owner**: ML Security Team
**Classification**: CRITICAL

---

## Executive Summary

This runbook provides procedures for responding to confirmed or suspected poisoning of Retrieval-Augmented Generation (RAG) corpora or fine-tuning datasets. Data poisoning can introduce backdoors, biased outputs, or malicious behavior into ML models.

**Key Success Metrics**:
- **Time to Quarantine**: < 30 minutes
- **Time to Provenance Analysis**: < 4 hours
- **Time to Retrain**: < 72 hours
- **Model Integrity Restoration**: 100%

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

Automated systems may detect data poisoning via:

1. **Model Drift Monitoring**
   - Sudden accuracy degradation
   - Unexpected prediction shifts
   - Bias metrics anomalies

2. **Output Anomaly Detection**
   - Toxic/harmful outputs
   - Unexpected responses to specific inputs
   - Backdoor triggers activated

3. **Data Pipeline Monitoring**
   - Unusual data source connections
   - Data checksum mismatches
   - Supplier access anomalies

4. **External Reports**
   - User reports of biased/inappropriate outputs
   - Researcher disclosure of vulnerabilities
   - Security researcher reports

### Initial Validation

**Step 1**: Confirm poisoning suspicion (15 minutes)

```python
from ml.security.data_poisoning_detector import PoisoningDetector

detector = PoisoningDetector()

# Quick validation check
validation = detector.quick_validate(
    model_id=<MODEL_ID>,
    corpus_id=<CORPUS_ID>,
    suspicious_outputs=<USER_REPORTS>
)

# Validation checks:
# - Model performance vs baseline
# - Output distribution analysis
# - Known poison pattern matching
# - Backdoor trigger testing
```

**Step 2**: Classify poisoning type

| Type | Description | Severity | Response Time |
|------|-------------|----------|---------------|
| **Label Flipping** | Training labels changed | CRITICAL | < 30 min |
| **Backdoor Injection** | Trigger-based malicious behavior | CRITICAL | < 30 min |
| **Clean-Label Poison** | Subtle bias injection | HIGH | < 2 hours |
| **Availability Poison** | Model degradation | MEDIUM | < 4 hours |
| **Privacy Poison** | Membership inference aids | HIGH | < 2 hours |

**Step 3**: Activate ML Security Response Team

```bash
python -m incident_response.activate \
  --runbook IR-ML-002 \
  --severity <SEVERITY> \
  --alert-id <ALERT_ID> \
  --teams "ml-security,data-engineering,legal,compliance"
```

---

## Immediate Containment

### Phase 1: Quarantine Poisoned Data (0-30 minutes)

#### Action 1.1: Disable Affected Models

**Priority**: CRITICAL
**Timeline**: < 10 minutes

```bash
# 1. Identify all models using the poisoned corpus
python -m ml.security.model_dependency_tracker \
  --corpus-id <CORPUS_ID> \
  --list-dependent-models

# Output:
# Model: clinical-assessment-v3, Corpus: medical-knowledge-base
# Model: team-optimizer-v2, Corpus: team-dynamics-research
# Model: personality-analyzer-v5, Corpus: psychology-research-papers

# 2. Disable all dependent models
for MODEL_ID in clinical-assessment-v3 team-optimizer-v2 personality-analyzer-v5; do
  curl -X POST https://api.psychsync.com/api/v1/admin/models/$MODEL_ID/disable \
    -H "Authorization: Bearer <ADMIN_TOKEN>" \
    -H "X-Reason: Data-Poisoning-Incident"

  # Update model registry
  kubectl patch configmap model-registry -n production \
    --type=json \
    -p='[{"op": "replace", "path": "/models/'$MODEL_ID'/status", "value": "quarantined"}]'
done

# 3. Verify models are disabled
curl https://api.psychsync.com/api/v1/models/status | jq '.models[] | select(.status=="quarantined")'
```

#### Action 1.2: Quarantine Affected Corpora

**Priority**: CRITICAL
**Timeline**: < 20 minutes

```python
from ml.security.corpora_quarantine import CorporaQuarantine

quarantine = CorporaQuarantine()

# 1. Create quarantine snapshot
snapshot = quarantine.create_snapshot(
    corpus_id=<CORPUS_ID>,
    quarantine_reason="suspected-poisoning",
    incident_id=<INCIDENT_ID>
)

# 2. Move to quarantine storage
import boto3

s3 = boto3.client('s3')

# List all corpus files
corpus_files = s3.list_objects_v2(
    Bucket='psychsync-ml-corpora',
    Prefix=<CORPUS_ID>
)

# Move to quarantine bucket
for obj in corpus_files['Contents']:
    source_key = obj['Key']
    dest_key = f"quarantine/incident-<INCIDENT_ID>/{source_key}"

    # Copy with metadata
    s3.copy_object(
        CopySource={'Bucket': 'psychsync-ml-corpora', 'Key': source_key},
        Bucket='psychsync-ml-quarantine',
        Key=dest_key,
        Metadata={
            'original-bucket': 'psychsync-ml-corpora',
            'original-key': source_key,
            'quarantine-date': datetime.utcnow().isoformat(),
            'incident-id': <INCIDENT_ID>,
            'quarantine-reason': 'data-poisoning'
        },
        MetadataDirective='REPLACE'
    )

    # Delete from production
    s3.delete_object(
        Bucket='psychsync-ml-corpora',
        Key=source_key
    )

# 3. Update corpus metadata in database
UPDATE ml_corpora
SET status = 'quarantined',
    quarantine_id = '<INCIDENT_ID>',
    quarantined_at = NOW(),
    quarantined_by = CURRENT_USER,
    checksum_quarantine = <SNAPSHOT_CHECKSUM>
WHERE corpus_id = '<CORPUS_ID>';

# 4. Log quarantine event
INSERT INTO data_quarantine_events (
  incident_id,
  corpus_id,
  file_count,
  total_size_gb,
  quarantine_type,
  timestamp
) VALUES (
  '<INCIDENT_ID>',
  '<CORPUS_ID>',
  <FILE_COUNT>,
  <SIZE_GB>,
  'data-poisoning',
  NOW()
);
```

#### Action 1.3: Preserve Evidence

**Priority**: HIGH
**Timeline**: < 30 minutes

```python
from ml.security.forensics import EvidencePreserver

preserver = EvidencePreserver()

# 1. Create forensic image of poisoned corpus
forensic_image = preserver.create_forensic_image(
    corpus_id=<CORPUS_ID>,
    output_path=f"s3://psychsync-forensics/incidents/<INCIDENT_ID>/",
    preserve_metadata=True,
    calculate_checksums=True
)

# 2. Capture model state
model_state = preserver.capture_model_state(
    model_id=<MODEL_ID>,
    include_weights=True,
    include_config=True,
    include_training_history=True
)

# 3. Record pipeline provenance
provenance = preserver.record_provenance(
    corpus_id=<CORPUS_ID>,
    model_id=<MODEL_ID>,
    include_upstream_sources=True,
    include_processing_steps=True,
    include_access_logs=True
)

# 4. Generate evidence chain of custody
chain_of_custody = preserver.generate_custody_log(
    incident_id=<INCIDENT_ID>,
    evidence_items=[forensic_image, model_state, provenance],
    collectors=[<INVESTIGATOR_NAMES>],
    storage_location="s3://psychsync-forensics/incidents/<INCIDENT_ID>/"
)
```

### Phase 2: Prevent Spread (30-60 minutes)

#### Action 2.1: Disable Data Pipelines

**Priority**: HIGH
**Timeline**: < 40 minutes

```bash
# 1. Stop all ETL jobs processing the poisoned corpus
airflow dags pause -o process_corpora_to_rag

# 2. Disable fine-tuning pipelines
kubectl scale deployment fine-tuning-pipeline --replicas=0 -n ml-training

# 3. Disable vector database updates
curl -X POST https://vector-db.psychsync.com/admin/disable-ingest \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"corpus_ids": ["<CORPUS_ID>"], "reason": "poisoning-incident"}'

# 4. Lock down data lake access
aws s3api put-bucket-policy \
  --bucket psychsync-ml-corpora \
  --policy file://policies/quarantine-access.json

# quarantine-access.json:
# {
#   "Version": "2012-10-17",
#   "Statement": [{
#     "Effect": "Deny",
#     "Principal": "*",
#     "Action": "s3:*",
#     "Resource": [
#       "arn:aws:s3:::psychsync-ml-corpora/<CORPUS_ID>/*",
#       "arn:aws:s3:::psychsync-ml-corpora/<CORPUS_ID>"
#     ]
#   }]
# }
```

#### Action 2.2: Deploy Backup Models

**Priority**: HIGH
**Timeline**: < 60 minutes

```python
from ml.deployment.model_deployer import ModelDeployer

deployer = ModelDeployer()

# 1. Identify last known good model version
last_good_version = deployer.get_last_safe_version(
    model_id=<MODEL_ID>,
    exclude_corpora=<CORPUS_ID>
)

# 2. Deploy backup model
deployment = deployer.deploy_model(
    model_id=last_good_version,
    environment="production",
    strategy="canary",
    canary_percentage=10,  # Start with 10% traffic
    monitoring_enabled=True
)

# 3. Validate backup model performance
validation = deployer.validate_deployment(
    deployment_id=deployment.id,
    test_set="golden",
    threshold=0.95  # 95% of baseline performance
)

if validation.passed:
    # Gradually increase traffic
    deployer.update_canary_percentage(
        deployment_id=deployment.id,
        percentage=50
    )

    # Monitor for 1 hour
    time.sleep(3600)

    if deployment.healthy:
        deployer.promote_to_production(deployment_id=deployment.id)
else:
    # Rollback and investigate
    deployer.rollback(deployment_id=deployment.id)
    logger.error("Backup model validation failed")
```

---

## Investigation & Analysis

### Phase 3: Provenance Analysis (1-4 hours)

#### Action 3.1: Trace Data Lineage

**Priority**: CRITICAL
**Timeline**: < 2 hours

```python
from ml.security.provenance_analyzer import ProvenanceAnalyzer

analyzer = ProvenanceAnalyzer()

# 1. Build complete data lineage graph
lineage = analyzer.build_lineage(
    target_corpus_id=<CORPUS_ID>,
    depth=5,  # Go back 5 hops
    include_processing=True,
    include_access=True
)

# 2. Identify all data sources
sources = analyzer.get_sources(lineage)

# 3. Check for unauthorized sources
unauthorized = analyzer.check_authorization(
    sources=sources,
    approved_sources_list="s3://psychsync-ml/approved-sources.json"
)

# 4. Identify access during critical window
access_logs = analyzer.get_access_logs(
    corpus_id=<CORPUS_ID>,
    time_window=(<WINDOW_START>, <WINDOW_END>),
    include_who=True,
    include_what=True,
    include_when=True
)

# 5. Find anomalous access patterns
anomalies = analyzer.detect_anomalies(
    logs=access_logs,
    baseline_period="30d",
    anomaly_types=["unusual_time", "unusual_location", "unusual_volume"]
)
```

#### Action 3.2: Identify Poisoning Technique

**Priority**: CRITICAL
**Timeline**: < 3 hours

```python
from ml.security.poisoning_technique_classifier import PoisoningClassifier

classifier = PoisoningClassifier()

# 1. Analyze poisoned samples
technique = classifier.classify(
    poisoned_corpus=<CORPUS_ID>,
    known_patterns="ml/security/poisoning-patterns.db"
)

# Common techniques:
# - Label flipping: Change training labels
# - Backdoor: Inject trigger-response pairs
# - Gradient ascent: Maximize loss on specific inputs
# - Clean-label: Poison with correct labels but malicious features
# - Model inversion: Extract training data

# 2. Characterize the poison
characteristics = classifier.analyze_characteristics(
    corpus_id=<CORPUS_ID>,
    technique=technique
)

# 3. Estimate poison extent
extent = classifier.estimate_poisoned_fraction(
    corpus_id=<CORPUS_ID>,
    confidence=0.95
)

# 4. Identify trigger patterns (if backdoor)
if technique == "backdoor":
    triggers = classifier.extract_triggers(
        corpus_id=<CORPUS_ID>,
        model_id=<MODEL_ID>
    )

    # Test triggers
    trigger_results = classifier.test_triggers(
        triggers=triggers,
        model_id=<MODEL_ID>,
        safety_checks=True  # Test in sandbox
    )
```

#### Action 3.3: Assess Model Impact

**Priority**: HIGH
**Timeline**: < 4 hours

```python
from ml.security.impact_assessor import ImpactAssessor

assessor = ImpactAssessor()

# 1. Evaluate model on clean test set
clean_performance = assessor.evaluate_on_clean_data(
    model_id=<MODEL_ID>,
    test_set="validation-clean"
)

# 2. Test for backdoor activation
backdoor_assessment = assessor.test_backdoors(
    model_id=<MODEL_ID>,
    trigger_candidates=<TRIGGER_PATTERNS>,
    safety_checks=True
)

# 3. Analyze output drift
drift_analysis = assessor.analyze_output_distribution(
    model_id=<MODEL_ID>,
    baseline_period="30d",
    current_outputs=<RECENT_OUTPUTS>
)

# 4. Check for bias injection
bias_assessment = assessor.measure_bias(
    model_id=<MODEL_ID>,
    protected_attributes=["race", "gender", "age"],
    bias_metrics=["demographic_parity", "equalized_odds"]
)

# 5. Generate impact report
impact_report = assessor.generate_report(
    clean_performance=clean_performance,
    backdoor_assessment=backdoor_assessment,
    drift_analysis=drift_analysis,
    bias_assessment=bias_assessment
)

impact_report.save("s3://psychsync-security/incidents/<INCIDENT_ID>/impact-report.pdf")
```

---

## Eradication & Recovery

### Phase 4: Clean and Retrain (4-72 hours)

#### Action 4.1: Clean Poisoned Data

**Priority**: CRITICAL
**Timeline**: < 12 hours

```python
from ml.security.data_cleaner import DataCleaner

cleaner = DataCleaner()

# 1. Create whitelist of known-good sources
whitelist = cleaner.create_whitelist(
    trusted_sources=[
        "s3://psychsync-ml/corpora/pubmed/",
        "s3://psychsync-ml/corpora/peer-reviewed/",
        "s3://psychsync-ml/corpora/internal-validated/"
    ],
    require_checksum=True,
    require_signature=True
)

# 2. Scan corpus for poisoned samples
poisoned_samples = cleaner.scan_corpus(
    corpus_id=<CORPUS_ID>,
    poison_signature=<TECHNIQUE_SIGNATURE>,
    confidence_threshold=0.9
)

# 3. Remove poisoned samples
clean_corpus = cleaner.remove_samples(
    corpus_id=<CORPUS_ID>,
    sample_ids=poisoned_samples,
    create_backup=True
)

# 4. Validate cleaned corpus
validation = cleaner.validate_clean_corpus(
    clean_corpus=clean_corpus,
    checks=["poison_scan", "distribution_check", "quality_check"]
)

if not validation.passed:
    # Alternative: Rebuild from trusted sources
    logger.warning("Cleaning insufficient, rebuilding from trusted sources")

    clean_corpus = cleaner.rebuild_from_trusted_sources(
        corpus_id=<CORPUS_ID>,
        trusted_sources=whitelist,
        verify_checksums=True,
        verify_signatures=True
    )
```

#### Action 4.2: Retrain Models

**Priority**: CRITICAL
**Timeline**: < 48 hours

```python
from ml.training.secure_trainer import SecureTrainer

trainer = SecureTrainer()

# 1. Prepare clean training data
training_data = trainer.prepare_data(
    corpus_id=<CLEAN_CORPUS_ID>,
    validation_split=0.2,
    test_split=0.1,
    stratify=True,
    shuffle_seed=42  # Fixed seed for reproducibility
)

# 2. Configure training with security monitoring
training_config = {
    "model_id": <MODEL_ID>,
    "model_type": "clinical-assessment",
    "training_data": training_data,
    "epochs": 100,
    "early_stopping": True,
    "security_monitoring": {
        "gradient_monitoring": True,
        "loss_monitoring": True,
        "output_monitoring": True,
        "backdoor_detection": True,
        "anomaly_detection": True
    },
    "provenance_tracking": {
        "enable": True,
        "log_all_inputs": True,
        "log_all_hyperparameters": True,
        "log_all_random_seeds": True,
        "checkpoint_interval": "5min"
    }
}

# 3. Train with security controls
training_job = trainer.train_secure(
    config=training_config,
    environment="isolated",  # Isolated training environment
    resource_limits={
        "gpu_count": 4,
        "max_duration": "48h"
    }
)

# 4. Monitor training for anomalies
while not training_job.complete:
    status = trainer.get_status(training_job.id)

    if status.anomaly_detected:
        # Investigate anomaly
        investigation = trainer.investigate_anomaly(
            job_id=training_job.id,
            anomaly_id=status.anomaly_id
        )

        if investigation.severity == "CRITICAL":
            # Stop training
            trainer.stop_training(training_job.id)
            logger.error(f"Critical anomaly detected: {investigation.reason}")
            break

    time.sleep(300)  # Check every 5 minutes

# 5. Validate trained model
validation = trainer.validate_model(
    model_id=training_job.model_id,
    validation_sets=["test", "golden", "adversarial"],
    performance_threshold=0.95,
    bias_threshold=0.05,
    backdoor_threshold=0.01
)

if validation.passed:
    # Model is safe to deploy
    trained_model = training_job.model_id
else:
    logger.error("Model validation failed after retraining")
```

#### Action 4.3: Deploy Clean Models

**Priority**: HIGH
**Timeline**: < 72 hours

```bash
# 1. Create deployment package
python -m ml.deployment.package_model \
  --model-id <TRAINED_MODEL_ID> \
  --include-provenance \
  --include-signature \
  --output deployment-package.tar.gz

# 2. Sign model package
gpg --detach-sign --local-user <SIGNING_KEY> deployment-package.tar.gz

# 3. Upload to model registry
aws s3 cp deployment-package.tar.gz \
  s3://psychsync-models/registry/<TRAINED_MODEL_ID>/model.tar.gz

aws s3 cp deployment-package.tar.gz.sig \
  s3://psychsync-models/registry/<TRAINED_MODEL_ID>/model.tar.gz.sig

# 4. Deploy to staging first
kubectl apply -f k8s/model-deployment-staging.yaml

# 5. Run comprehensive tests in staging
python -m tests.e2e.model_validation \
  --environment staging \
  --model-id <TRAINED_MODEL_ID> \
  --test-suite "comprehensive"

# 6. Monitor staging deployment
python -m monitoring.watch_deployment \
  --environment staging \
  --duration 3600 \
  --metrics ["accuracy", "latency", "error_rate", "output_distribution"]

# 7. If staging passes, deploy to production (canary)
kubectl apply -f k8s/model-deployment-production-canary.yaml

# 8. Gradual rollout (canary → 50% → 100%)
python -m ml.deployment.gradual_rollout \
  --model-id <TRAINED_MODEL_ID> \
  --strategy canary \
  --steps [10, 25, 50, 75, 100] \
  --monitor-duration-each-step 3600

# 9. Final validation
python -m ml.deployment.final_validation \
  --model-id <TRAINED_MODEL_ID> \
  --environment production \
  --duration 86400  # 24 hours
```

---

## Post-Incident Activities

### Phase 5: Hardening (7-14 days)

#### Action 5.1: Enhance Data Pipeline Security

**Priority**: HIGH
**Timeline**: < 10 days

```python
# 1. Implement data source validation
from ml.security.data_validator import DataValidator

validator = DataValidator()

# Require cryptographic signatures
validator.require_signature(
    sources="all",
    signature_algorithm="ed25519",
    public_key_trust_store="ml/security/trusted-keys.db"
)

# Require checksums
validator.require_checksum(
    algorithm="sha256",
    verify_against="s3://psychsync-ml/checksums/"
)

# 2. Add content-based anomaly detection
validator.enable_content_scanning(
    scan_types=["poison", "backdoor", "bias"],
    threshold=0.8,
    auto_quarantine=True
)

# 3. Implement data provenance tracking
from ml.security.provenance import ProvenanceTracker

tracker = ProvenanceTracker()

tracker.enable_tracking(
    corpus_ids="all",
    log_all_access=True,
    log_all_transformations=True,
    immutable_logs=True,
    retention_years=7
)

# 4. Add supplier monitoring
from ml.security.supplier_monitor import SupplierMonitor

monitor = SupplierMonitor()

monitor.watch_suppliers(
    suppliers=[<DATA_SUPPLIERS>],
    check_interval="hourly",
    alerts=["unusual_access", "data_change", "credential_compromise"]
)
```

#### Action 5.2: Implement Adversarial Training

**Priority**: MEDIUM
**Timeline**: < 14 days

```python
from ml.training.adversarial import AdversarialTrainer

adv_trainer = AdversarialTrainer()

# 1. Generate adversarial examples for robustness
adversarial_examples = adv_trainer.generate_examples(
    clean_corpus=<CLEAN_CORPUS>,
    attack_types=["label_flipping", "backdoor", "gradient_ascent"],
    num_examples_per_class=1000
)

# 2. Augment training data with adversarial examples
augmented_data = adv_trainer.augment_data(
    clean_data=<TRAINING_DATA>,
    adversarial_data=adversarial_examples,
    mix_ratio=0.2  # 20% adversarial
)

# 3. Train with adversarial robustness
robust_model = adv_trainer.train_robust(
    data=augmented_data,
    architecture=<MODEL_ARCHITECTURE>,
    adversarial_loss_weight=0.1,
    robustness_objective="min_max"  # Minimize worst-case loss
)

# 4. Validate robustness
robustness_validation = adv_trainer.validate_robustness(
    model=robust_model,
    test_attacks=["fgsm", "pgd", "backdoor_injection"],
    success_threshold=0.95  # 95% defense success rate
)
```

#### Action 5.3: Update Monitoring

**Priority**: HIGH
**Timeline**: < 7 days

```python
from ml.security.comprehensive_monitoring import ComprehensiveMonitoring

monitoring = ComprehensiveMonitoring()

# 1. Enable real-time output monitoring
monitoring.enable_output_monitoring(
    models="all",
    checks=["toxicity", "bias", "hallucination", "backdoor"],
    sample_rate=1.0,  # 100% sampling
    alert_threshold=0.7
)

# 2. Enable model drift detection
monitoring.enable_drift_detection(
    models="all",
    baseline_period="30d",
    detection_method="adwin",  # Adaptive Windowing
    alert_threshold=0.05
)

# 3. Enable data pipeline monitoring
monitoring.enable_pipeline_monitoring(
    pipelines="all",
    checks=["source_authorization", "checksum_verification", "signature_validation"],
    log_all_transformations=True
)

# 4. Create dashboards
monitoring.create_dashboard(
    name="ML Security Monitoring",
    panels=[
        "model_drift",
        "output_distribution",
        "adversarial_inputs",
        "data_pipeline_status",
        "poisoning_detection_confidence"
    ]
)
```

---

## Communications Plan

### Internal Communications

#### Detection Phase (0-2 hours)

```
TO: ML Team, Security, Legal, Executives
SUBJECT: 🔴 CRITICAL: Potential Data Poisoning Detected - ML Systems

EXECUTIVE SUMMARY:
- Incident ID: INC-2025-<ID>
- Type: Potential Data Poisoning
- Affected: <MODELS_AFFECTED>
- Corpus: <CORPUS_ID>
- Status: INVESTIGATION UNDERWAY

IMMEDIATE ACTIONS:
✅ Affected models disabled
✅ Corpora quarantined
✅ Backup models deploying

INVESTIGATION:
- Provenance analysis in progress
- Poisoning technique identification underway
- ETA for initial findings: <TIME>

NEXT UPDATE: <TIME>
```

#### Investigation Update (2-8 hours)

```
TO: ML Team, Security, Legal, Executives
SUBJECT: 🟡 UPDATE: Data Poisoning Investigation

INVESTIGATION FINDINGS:
- Poisoning Technique: <TECHNIQUE>
- Source: <SOURCE_IDENTIFIED>
- Extent: <PERCENTAGE>% of data affected
- Impact: <IMPACT_SUMMARY>

ROOT CAUSE:
<Summary of how poison was introduced>

MITIGATION PLAN:
- [ ] Data cleaning in progress
- [ ] Retraining planned (ETA: <TIME>)
- [ ] Enhanced controls being implemented

NEXT UPDATE: <TIME>
```

#### Resolution (48-72 hours)

```
TO: All Staff
SUBJECT: ✅ RESOLVED: Data Poisoning Incident

INCIDENT SUMMARY:
- Incident ID: INC-2025-<ID>
- Duration: <X> hours
- Status: RESOLVED

WHAT HAPPENED:
<Summary for non-technical audience>

ACTIONS TAKEN:
✅ Poisoned data removed
✅ Models retrained with clean data
✅ Enhanced security controls implemented
✅ Monitoring upgraded

PREVENTIVE MEASURES:
<Summary of improvements>

BUSINESS IMPACT:
<Service availability during incident>
<Performance impact, if any>

QUESTIONS: Contact <INCIDENT_COMMANDER>
```

### External Communications (If Required)

#### Regulatory Notification (If Model Impacts Protected Data)

```markdown
# Data Processing Incident Notification

[Date]

To: [Regulatory Authority]

Subject: Notification of Data Processing Incident - AI Model Training

## Incident Description

On [Date], [Company] detected a security incident affecting our machine learning model training data.

## Type of Incident

Data poisoning attack affecting [number] models used for [purpose].

## Timeline

- **Detection**: [Date/Time]
- **Containment**: [Date/Time]
- **Notification**: [Date/Time] (within [X] hours of detection)

## Data Categories Affected

[List categories of data involved]

## Potential Impact

[Assessment of impact on individuals]

## Mitigation Actions Taken

[Steps taken to address the incident]

## Preventive Measures

[Measures implemented to prevent recurrence]

## Contact Person

[Name]
[Title]
[Email]
[Phone]
```

#### Customer Communication (If B2B)

```markdown
# Security Incident Notification - AI Model Update

Dear [Customer],

We are writing to inform you of a security incident affecting some of our AI-powered services.

## What Happened

We detected potential data poisoning in the training data used for [Service Name].

## What We're Doing

- We have quarantined the affected data
- We are retraining models with verified clean data
- We are deploying backup models in the interim

## Impact to You

[Specific impact assessment]

## What You Need to Do

[Specific actions, if any]

## Timeline

We expect to restore full service by [Date].

## Questions

[Contact information]
```

---

## Checklist & Quick Reference

### Immediate Response Checklist (First 30 Minutes)

- [ ] Validate poisoning suspicion
- [ ] Classify poisoning type
- [ ] Activate ML Security Response Team
- [ ] Disable affected models
- [ ] Quarantine affected corpora
- [ ] Preserve forensic evidence
- [ ] Disable data pipelines
- [ ] Begin deploying backup models

### Investigation Checklist (1-4 Hours)

- [ ] Trace data lineage
- [ ] Identify unauthorized sources
- [ ] Analyze access logs
- [ ] Classify poisoning technique
- [ ] Identify trigger patterns (if backdoor)
- [ ] Estimate poison extent
- [ ] Assess model impact
- [ ] Test for backdoors
- [ ] Analyze output drift
- [ ] Measure bias injection

### Recovery Checklist (4-72 Hours)

- [ ] Clean poisoned data
- [ ] Rebuild from trusted sources (if needed)
- [ ] Retrain models with monitoring
- [ ] Validate trained models
- [ ] Deploy to staging
- [ ] Run comprehensive tests
- [ ] Deploy to production (canary)
- [ ] Monitor gradual rollout
- [ ] Final validation
- [ ] Remove from quarantine (when safe)

### Hardening Checklist (7-14 Days)

- [ ] Enhance data source validation
- [ ] Implement content scanning
- [ ] Add provenance tracking
- [ ] Enable supplier monitoring
- [ ] Implement adversarial training
- [ ] Update monitoring dashboards
- [ ] Update runbooks
- [ ] Train team on lessons learned

### Quick Commands

```bash
# Disable model
curl -X POST https://api.psychsync.com/api/v1/admin/models/<ID>/disable

# Quarantine corpus
python -m ml.security.quarantine_corpus --corpus-id <ID>

# Train new model
python -m ml.training.secure_trainer --config config.yaml

# Deploy model
kubectl apply -f k8s/model-deployment.yaml

# Check model status
kubectl get pods -n ml-training -l app=model-training
```

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **ML Security Lead** | [Name] | [Phone] | [Email] |
| **Data Engineering Lead** | [Name] | [Phone] | [Email] |
| **MLOps Lead** | [Name] | [Phone] | [Email] |
| **Legal Counsel** | [Name] | [Phone] | [Email] |
| **Incident Commander** | [Name] | [Phone] | [Email] |

---

## Appendix: Tools and Resources

### Detection Tools

```bash
# Poisoning detection
python -m ml.security.detect_poisoning

# Provenance analysis
python -m ml.security.analyze_provenance

# Model impact assessment
python -m ml.security.assess_impact
```

### Recovery Tools

```bash
# Data cleaning
python -m ml.security.clean_corpora

# Secure training
python -m ml.training.secure_trainer

# Model deployment
python -m ml.deployment.deploy_model
```

### References

- [Poisoning Attacks and Defenses](https://arxiv.org/abs/2006.07670)
- [Backdoor Attacks on Deep Learning Systems](https://arxiv.org/abs/1908.01708)
- [Data Provenance in ML Systems](https://www.usenix.org/conference/usenixsecurity20/presentation/gkountolas)
- [ML Security Best Practices](https://www.nist.gov/itl/applied-cybersecurity/topics/machine-learning-security)

---

**Document Control**:
- **Owner**: ML Security Team
- **Review Frequency**: Quarterly
- **Next Review**: 2026-03-26
- **Change History**:
  - 2025-12-26: Initial version (v1.0.0)

---

**END OF RUNBOOK**
