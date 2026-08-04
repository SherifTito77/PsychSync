.
├── AI_AGENTS_DEPLOYMENT_SUCCESS.md.bak
├── AI_AGENTS_SERVICE_README.md.bak
├── Dockerfile.prod -> infra/Dockerfile.prod
├── GEMINI.md
├── PROJECT_STRUCTURE.md
├── README.md
├── WellnessAssessment.css
├── agents
│   ├── AUTONOMOUS_AGENTS_SUMMARY.md
│   ├── README.md
│   ├── api_contract_agent.py
│   ├── auto_test_agent.py
│   ├── code_quality_scanner.py
│   ├── crash_log_analyzer.py
│   ├── dead_code_agent.py
│   ├── dependency_updater.py
│   ├── doc_completeness_agent.py
│   ├── doc_syncer.py
│   ├── log_anomaly_agent.py
│   ├── logs
│   └── pr_coverage_tester.py
├── ai_testing
│   ├── ai_hallucination_detection_results_20251213_084629.json
│   ├── ai_hallucination_detection_results_20251213_084810.json
│   ├── ai_hallucination_detection_results_20251213_084926.json
│   ├── ai_output_consistency_results_20251213_084418.json
│   ├── ai_output_consistency_results_20251213_084554.json
│   ├── ai_quality_dashboard_20251213_085128.txt
│   ├── ai_quality_monitoring_dashboard.py
│   ├── comprehensive_ai_testing_report_20251213_075836.json
│   ├── comprehensive_ai_testing_report_20251213_082516.json
│   ├── comprehensive_ai_testing_report_20251213_083219.json
│   ├── comprehensive_ai_testing_report_20251213_085005.json
│   ├── personality_analysis_validation_results_20251213_082446.json
│   ├── personality_analysis_validation_results_20251213_083157.json
│   ├── personality_analysis_validation_results_20251213_083239.json
│   ├── recommendation_data_reference_results_20251213_084139.json
│   ├── recommendation_data_reference_results_20251213_084237.json
│   ├── recommendation_data_reference_results_20251213_084331.json
│   ├── run_ai_testing_suite.py
│   ├── test_ai_bias_detection.py
│   ├── test_ai_hallucination_detection.py
│   ├── test_ai_output_consistency.py
│   ├── test_personality_analysis_validation.py
│   └── test_recommendation_data_reference.py
├── alembic
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   ├── versions
│   └── versions_backup
├── alembic.ini
├── alerts
│   └── psychsync_alerts.yml
├── all_models.txt
├── allowed-dependencies.txt
├── app
│   ├── __init__.py
│   ├── ai
│   ├── api
│   ├── application
│   ├── assessments
│   ├── backup.py
│   ├── core
│   ├── core_database_fix.py
│   ├── create_assessment_tables.py
│   ├── create_db.py
│   ├── create_scoring_tables.py
│   ├── create_team_tables.py
│   ├── create_template_tables.py
│   ├── crud
│   ├── data
│   ├── db
│   ├── dependency_injection
│   ├── domain
│   ├── etl
│   ├── events
│   ├── factory
│   ├── infrastructure
│   ├── init_db.py
│   ├── integrations
│   ├── interfaces
│   ├── main.py
│   ├── middleware
│   ├── migrate.py
│   ├── models
│   ├── monitoring
│   ├── performance
│   ├── presentation
│   ├── reports
│   ├── repositories
│   ├── schemas
│   ├── scripts
│   ├── security
│   ├── seed_scoring_templates.py
│   ├── seed_templates.py
│   ├── services
│   ├── static
│   ├── tasks
│   ├── templates
│   ├── testing
│   ├── update_response_tables.py
│   └── utils
├── architecture_refactor
│   ├── PHASE_1_REVIEW.md
│   ├── PHASE_1_REVIEW_SUMMARY.md
│   ├── docs
│   ├── examples
│   ├── plan
│   └── review
├── archived_services
│   ├── ARCHIVAL_MANIFEST.md
│   └── SERVICES_MANIFEST.csv
├── argocd
│   └── psychsync-rollout.yaml
├── artifacts
├── audit_logs
│   ├── credential-rotation
│   └── model_training
├── azure-devops-pipeline.yml
├── azure-pipelines.yml
├── backend
│   └── core
├── backups
│   ├── credentials
│   ├── pre_migration_backup.dump
│   └── pre_unification_state
├── build
│   └── logs
├── celery_app.py
├── certs
│   ├── openssl.cnf
│   ├── psychsync.crt
│   ├── psychsync.csr
│   └── psychsync.key
├── check_permission.py
├── checkpoints
│   └── secure_training
├── commented_lifespan.txt
├── commented_lifespan_final.txt
├── config
│   └── ir_tools
├── coverage.xml
├── coverage_reports
├── cypress
│   └── integration
├── data
│   ├── 01KFYK0C7XCCSG8AA7XV708035
│   ├── 01KFZHRZ2CT0FT8K5AHAKZ38PN
│   ├── 01KG1HDQG2RKRA4F31ZR48RND0
│   ├── 01KG41YZM7M8ENTDXP32MA4J88
│   ├── 01KG5EYMN7H4SRMF1D1NM0CPBC
│   ├── 01KG78ZBWJ34Q3QY6YMHGN8M4X
│   ├── 01KG910TEQDJDPFK3ZEPCPA7TJ
│   ├── 01KG97WKK67ZHKF5EA70P41NQ0
│   ├── 01KG97WQVFG6MWHT8DZRT1NA3K
│   ├── 01KG9DKZ7JQW4PQ5Q85TGWFBGB
│   ├── 01KG9MFQ7VZFW6T3PX1ZKGTY7K
│   ├── baselines
│   ├── chunks_head
│   ├── corpora
│   ├── db_local
│   ├── lock
│   ├── queries.active
│   └── wal
├── data_validation
│   ├── run_data_validation_tests.py
│   ├── test_large_scale_csv_export.py
│   ├── test_pdf_dashboard_consistency.py
│   ├── test_psychometric_scoring_consistency.py
│   ├── test_report_accuracy_midway_changes.py
│   └── test_rounding_error_validation.py
├── debug-screenshots
│   ├── 01-login-page.png
│   ├── 02-form-filled.png
│   ├── 03-after-submit.png
│   └── 04-final-state.png
├── deploy
│   ├── archive
│   ├── argocd
│   ├── cloudfront-cdn.yaml
│   ├── grafana
│   ├── k8s
│   ├── k8s-deployment.yaml
│   ├── kubernetes
│   ├── logging
│   ├── monitoring-stack.yml
│   ├── production-config.env
│   ├── production_deploy.sh
│   ├── prometheus
│   └── systemd
├── docker
│   └── Dockerfile
├── docker-compose.yml
├── docs
│   ├──  RATE_LIMITING_TEST_SCENARIOS.md
│   ├── 10_WEEK_LAUNCH_TIMELINE.md
│   ├── 2_YEAR_PRODUCT_VISION.md
│   ├── 404_TROUBLESHOOTING.md
│   ├── AB_TESTING_UI_SCRIPT.md
│   ├── AB_TESTING_VALIDATION.md
│   ├── ACCESSIBILITY_IMPROVEMENTS.md
│   ├── ACCOUNT_DELETION_IMPLEMENTATION.md
│   ├── ACTION_PLAN_EXECUTION_REPORT.md
│   ├── ACTIVATION_MILESTONES.md
│   ├── ADAPTIVE_ASSESSMENT_ENGINE.md
│   ├── ADMIN_MODULE_SECURITY_ANALYSIS.md
│   ├── ADVANCED_ANALYTICS_DEPLOYMENT.md
│   ├── ADVANCED_CLINICAL_FEATURES_IMPLEMENTATION.md
│   ├── ADVANCED_FUNCTIONS.md
│   ├── ADVANCED_THREAT_DETECTION_GUIDE.md
│   ├── AGENTS.md
│   ├── AGENT_DEPLOYMENT_DELIVERY.md
│   ├── AGENT_DEPLOYMENT_GUIDE.md
│   ├── AGENT_QUICK_REFERENCE.md
│   ├── AGENT_TOOL_POLICY.md
│   ├── AI_AGENTS_IMPLEMENTATION.md
│   ├── AI_AGENTS_QUICK_REFERENCE.md
│   ├── AI_AGENTS_SERVICE_README.md
│   ├── AI_AGENTS_USAGE_GUIDE.md
│   ├── AI_AGENTS_USAGE_GUIDE_CORRECTED.md
│   ├── AI_PRODUCTION_DEPLOYMENT_STRATEGY.md
│   ├── AI_QUALITY_IMPROVEMENT_PROGRESS.md
│   ├── AI_QUALITY_IMPROVEMENT_ROADMAP.md
│   ├── AI_RISK_DASHBOARD.html
│   ├── AI_RISK_MITIGATION_PLAYBOOKS.md
│   ├── AI_RISK_REGISTER.csv
│   ├── AI_RISK_REGISTER_Detailed.xlsx
│   ├── AI_RISK_REGISTER_EXECUTIVE_SUMMARY.md
│   ├── AI_RISK_REGISTER_Executive.csv
│   ├── AI_RISK_TRACKING_TEMPLATE.md
│   ├── AI_SECURITY_DEVELOPER_GUIDELINES.md
│   ├── AI_SECURITY_FINAL_SUMMARY.md
│   ├── AI_SECURITY_GUIDE.md
│   ├── AI_SECURITY_IMPLEMENTATION.md
│   ├── AI_SECURITY_SCAN_REPORT.md
│   ├── AI_SECURITY_SUMMARY.md
│   ├── AI_VULNERABILITY_REMEDIATION_GUIDE.md
│   ├── ALERTS_CENTER_FINAL_FIX.md
│   ├── ALERTS_SCHEMA_FIX.md
│   ├── ALL_5_AGENTS_WORKING.md
│   ├── ALL_CRITICAL_ISSUES_FIXED.md
│   ├── ALL_SEVEN_CLINICAL_ASSESSMENTS_ENHANCED.md
│   ├── ANALYTICS_BLOAT_QUICK_FIX.md
│   ├── ANALYTICS_EVENT_CATALOG.md
│   ├── ANALYTICS_ROLLUP_SYSTEM_ACTIVE.md
│   ├── ANONYMOUS_FEEDBACK_DEPLOYMENT.md
│   ├── API.md
│   ├── API_COMPLETE.md
│   ├── API_EXAMPLES.md
│   ├── API_REFERENCE.md
│   ├── API_RESILIENCE_COMPLETE.md
│   ├── API_RESILIENCE_MIGRATION_GUIDE.md
│   ├── API_RESPONSE_MISMATCHES.md
│   ├── API_VALIDATION_RULES.md
│   ├── ARCHITECTURAL_REFACTORING_INDEX.md
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_AUDIT_DELIVERABLES_SUMMARY.md
│   ├── ARCHITECTURE_AUDIT_ITEM6_10_SUMMARY.md
│   ├── ARCHITECTURE_AUDIT_REPORT.md
│   ├── ARCHITECTURE_RISK_ANALYSIS.md
│   ├── ASSESSMENT_ENGINE_REQUIREMENTS.md
│   ├── ASSESSMENT_MIGRATION_GUIDE.md
│   ├── ASSESSMENT_MODULE_SECURITY_ANALYSIS.md
│   ├── ASSESSMENT_SCHEMA_FIX.md
│   ├── ASYNC_AWAIT_BLOCKING_OPERATIONS_AUDIT.md
│   ├── ASYNC_CACHE_INDEX.md
│   ├── ASYNC_CACHE_MIGRATION_DEMO.md
│   ├── ASYNC_CACHE_MIGRATION_GUIDE.md
│   ├── ASYNC_CACHE_QUICKSTART.md
│   ├── ASYNC_DEPLOYMENT_GUIDE.md
│   ├── ASYNC_JOB_QUEUE_IMPROVEMENTS.md
│   ├── ASYNC_MIGRATION_GUIDE.md
│   ├── ASYNC_MONITORING_GUIDE.md
│   ├── AUTHENTICATION_DEBUG_TEST.md
│   ├── AUTH_REDIRECT_FIX.md
│   ├── B2B_RETENTION_LEVERS.md
│   ├── B904_EXCEPTION_CHAINING_GUIDE.md
│   ├── BACKEND_COMPLEXITY_ANALYSIS.md
│   ├── BACKUP_SLA_REQUIREMENTS.md
│   ├── BASESERVICE_PATTERNS_CHEAT_SHEET.md
│   ├── BEFORE_CI_CD_CHECKLIST.md
│   ├── BIOMETRIC_AUTHENTICATION.md
│   ├── BOARD_PRESENTATION_DECK.md
│   ├── BOUNDARY_CONDITIONS_FIXES.md
│   ├── BURNOUT_ANALYTICS_COMPARISON.md
│   ├── BUSINESS_ANALYTICS_EVENTS_IMPLEMENTATION.md
│   ├── BUTTON_EMERGENCY_DEBUG.md
│   ├── CACHE_LAYER_MIGRATION_GUIDE.md
│   ├── CEO_DASHBOARD_DESIGN.md
│   ├── CHANGELOG_SECURITY.md
│   ├── CHURN_PREDICTION_SIGNALS.md
│   ├── CICD_SECURITY_PIPELINE.md
│   ├── CISA_SBOM_VEX_2025_GUIDE.md
│   ├── CI_CD_MONITORING_QUICK_REFERENCE.md
│   ├── CI_CD_SETUP_GUIDE.md
│   ├── CI_CHECKS_INVESTIGATION.md
│   ├── CLEAR_TOKENS.md
│   ├── CLINICAL_ASSESSMENTS_IMPLEMENTATION.md
│   ├── CLINICAL_ASSESSMENT_REFACTORING_COMPLETE.md
│   ├── CLINICAL_TESTING_DASHBOARD.md
│   ├── CLINICIAN_JOB_POSTINGS.md
│   ├── CODEBASE_ANALYSIS_REPORT.md
│   ├── CODE_CONSOLIDATION_COMPLETE.md
│   ├── CODE_CONSOLIDATION_FINAL_REPORT.md
│   ├── CODE_CONSOLIDATION_TESTING_REPORT.md
│   ├── CODE_CONSULTATION_IMPROVEMENT_RECOMMENDATIONS.md
│   ├── CODE_QUALITY_IMPROVEMENTS.md
│   ├── CODE_QUALITY_OPTIMIZATION_DELIVERABLES.md
│   ├── CODE_QUALITY_STANDARDS.md
│   ├── CODE_QUALITY_START_HERE.md
│   ├── CODE_STYLE_IMPLEMENTATION.md
│   ├── COMPETITIVE_ADVANTAGES.md
│   ├── COMPLETE_DEPLOYMENT_GUIDE.md
│   ├── COMPLETE_OWASP_SECURITY_REVIEW_SUMMARY.md
│   ├── COMPONENT_SPLITTING_PLAN_CLINICALRESULTS.md
│   ├── COMPONENT_SPLITTING_ROADMAP.md
│   ├── COMPREHENSIVE_ANALYSIS_SUMMARY.md
│   ├── COMPREHENSIVE_IMPROVEMENT_PLAN.md
│   ├── COMPREHENSIVE_NETWORK_SECURITY_ASSESSMENT.md
│   ├── COMPREHENSIVE_SECURITY_IMPLEMENTATION_SUMMARY.md
│   ├── COMPREHENSIVE_SECURITY_PERFORMANCE_FIXES.md
│   ├── COMPREHENSIVE_SECURITY_REVIEW_FINAL_REPORT.md
│   ├── COMPREHENSIVE_SESSION_SUMMARY.md
│   ├── COMPREHENSIVE_SUPPLY_CHAIN_SECURITY.md
│   ├── COMPREHENSIVE_TESTING_REPORT.md
│   ├── CONTEXT_ASSEMBLY_SERVICE_GUIDE.md
│   ├── CORPORATE_DATA_INTEGRATION_GUIDE.md
│   ├── CORPORATE_INTEGRATIONS_ICONS.md
│   ├── CORPORATE_INTEGRATIONS_ICON_REFERENCE.md
│   ├── CORPORATE_INTEGRATIONS_IMPLEMENTATION.md
│   ├── CORPORATE_PSYCHOLOGY_IMPLEMENTATION.md
│   ├── CPU_MEMORY_OPTIMIZATION_GUIDE.md
│   ├── CREATE_FIGMA_IN_5_MINUTES.md
│   ├── CREATE_PR_INSTRUCTIONS.md
│   ├── CRITICAL_ISSUES_ACTION_PLAN.md
│   ├── CRITICAL_SECURITY_FIXES_APPLIED.md
│   ├── CRITICAL_SECURITY_ISSUES.md
│   ├── CRON_SETUP.md
│   ├── CROSS_TEAM_COLLABORATION_WORKFLOWS.md
│   ├── CSS_MIGRATION_PHASE_1_COMPLETE.md
│   ├── CSS_MIGRATION_PHASE_2_COMPLETE.md
│   ├── CSS_MIGRATION_PHASE_4_COMPLETE.md
│   ├── CSS_MIGRATION_PLAN.md
│   ├── CSS_MIGRATION_VALIDATION_COMPLETE.md
│   ├── CUSTOMER_PRODUCT_MANUAL.md
│   ├── CUSTOMER_SUCCESS_ONBOARDING_PROGRAM.md
│   ├── DASHBOARD_PERFORMANCE_FIX.md
│   ├── DATABASE_ENCRYPTION.md
│   ├── DATABASE_MIGRATIONS.md
│   ├── DATABASE_MIGRATION_COMPLETE.md
│   ├── DATABASE_MONITORING_GUIDE.md
│   ├── DATABASE_QUERY_OPTIMIZATION_COMPLETE.md
│   ├── DATABASE_QUERY_PATTERNS_ANALYSIS.md
│   ├── DATABASE_SCALING_EVOLUTION_PLAN.md
│   ├── DATABASE_SCALING_QUICKSTART.md
│   ├── DATABASE_SCHEMA.md
│   ├── DATABASE_SECURITY_README.md
│   ├── DATABASE_TEST_PROMPTS.md
│   ├── DATA_CORRUPTION_RISKS.md
│   ├── DATA_EXPORT_SECURITY_ANALYSIS.md
│   ├── DEBUG_INSTRUCTIONS.md
│   ├── DEFENSIVE_PATTERNS_QUICK_REFERENCE.md
│   ├── DEFINITIVE_ANSWERS.md
│   ├── DEPENDENCY_ALLOWLIST_POLICY.md
│   ├── DEPENDENCY_GOVERNANCE.md
│   ├── DEPENDENCY_INJECTION_GUIDE.md
│   ├── DEPENDENCY_SECURITY_AUDIT.md
│   ├── DEPENDENCY_SECURITY_AUDIT_UPDATED.md
│   ├── DEPLOYMENT.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── DEPLOYMENT_CHECKLIST_RESILIENCE.md
│   ├── DEPLOYMENT_FRONTEND.md
│   ├── DEPLOYMENT_GUIDE_LOCAL.md
│   ├── DEPRECATION_FIXES_APPLIED.md
│   ├── DESIGN_SYSTEM_FIXES.md
│   ├── DESIGN_SYSTEM_GUIDE.md
│   ├── DEVELOPER_ONBOARDING.md
│   ├── DEVELOPER_PERFORMANCE_GUIDELINES.md
│   ├── DEVELOPER_QUICK_REFERENCE.md
│   ├── DEVELOPMENT.md
│   ├── DEVELOPMENT_MIGRATED.md
│   ├── DEV_SCRIPTS.md
│   ├── DOCUMENTATION_INDEX.md
│   ├── DOCUMENTATION_QUALITY_HOOK.md
│   ├── EMAIL_ANALYSIS_README.md
│   ├── EMAIL_CONNECTOR_FIX.md
│   ├── EMAIL_SERVICE_SETUP.md
│   ├── EMAIL_SETUP.md
│   ├── END_TO_END_VERIFICATION_REPORT.md
│   ├── ENGINEERING_KPIS.md
│   ├── ENGINEERING_PIPELINE_DEMO.md
│   ├── ENTERPRISE_MATURITY_LEVEL_5_ACHIEVED.md
│   ├── ENTERPRISE_PRODUCT_FAQ.md
│   ├── ENTERPRISE_PRODUCT_STRATEGY.md
│   ├── ENTERPRISE_QUICK_START.md
│   ├── ENTERPRISE_SECURITY_DEPLOYMENT.md
│   ├── ENTERPRISE_TECHNICAL_IMPLEMENTATION_ROADMAP.md
│   ├── ERDs
│   ├── ESLint_RULES_PROPOSAL.md
│   ├── EVENT_HANDLER_TEST.md
│   ├── EXAMPLE_WORKFLOWS.md
│   ├── EXCEPTION_HANDLING_PROGRESS_REPORT.md
│   ├── EXCEPTION_HANDLING_ZERO_RISK_ACHIEVED.md
│   ├── EXECUTION_COMPLETION_REPORT.md
│   ├── EXECUTION_PLAN_SUMMARY.md
│   ├── EXECUTIVE_TEAM_REVIEW_AGENDA.md
│   ├── EXTENDED_SESSION_FINAL_SUMMARY.md
│   ├── FEATURES_TO_PSYCHOLOGICAL_OUTCOMES.md
│   ├── FEATURE_DISCOVERY_FLOW.md
│   ├── FEATURE_REQUEST_CLASSIFICATION.md
│   ├── FEATURE_SUNSET_PROCESS.md
│   ├── FIGMA_DESIGN_SYSTEM.md
│   ├── FIGMA_DESIGN_SYSTEM_PSYNCSYNC.md
│   ├── FIGMA_FRAMES_SETUP.md
│   ├── FIGMA_ICON_ASSETS.md
│   ├── FIGMA_QUICK_REFERENCE.md
│   ├── FILE_INDEX.md
│   ├── FINAL_ACTION_PLAN_COMPLETION_REPORT.md
│   ├── FINAL_DELIVERY_SUMMARY.md
│   ├── FINAL_OPTIMIZATION_PUSH.md
│   ├── FINAL_PRODUCTION_READINESS_REPORT.md
│   ├── FINAL_QUALITY_ASSURANCE.md
│   ├── FINAL_SECURITY_ASSESSMENT_CORRECTED.md
│   ├── FINAL_SECURITY_IMPLEMENTATION_SUMMARY.md
│   ├── FINAL_SESSION_COMPLETE_SUMMARY.md
│   ├── FINAL_SESSION_DELIVERY_SUMMARY.md
│   ├── FINAL_SOLUTION_TEST.md
│   ├── FIXES_APPLIED.md
│   ├── FIX_SYNTAX_ERRORS.md
│   ├── FOUR_BUTTON_DEBUG_TEST.md
│   ├── FRONTEND_ARCHITECTURE_EVALUATION_COMPLETE.md
│   ├── FRONTEND_ICON_REFERENCE.md
│   ├── FRONTEND_STATE_MANAGEMENT_AUDIT.md
│   ├── GDPR_COMPLIANCE_IMPLEMENTATION.md
│   ├── GETTING_STARTED.md
│   ├── GITHUB_ACTIONS_SECURITY_SUMMARY.md
│   ├── GITHUB_ISSUES_TO_CREATE.md
│   ├── HANDOFF_PACKAGE.md
│   ├── HEALTH_DASHBOARD_FIX.md
│   ├── HIPAA_TRAINING_DEPLOYMENT.md
│   ├── HIPAA_TRAINING_MANUAL.md
│   ├── HOW_TO_VIEW_BUSINESS_DASHBOARD.md
│   ├── HRIS_IMPLEMENTATION_STEPS.md
│   ├── ICON_GALLERY_PAGE.md
│   ├── IMMEDIATE_PERFORMANCE_FIXES.md
│   ├── IMMEDIATE_PROGRESS.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── IMPLEMENTATION_RATE_LIMITING_LOAD_TESTS.md
│   ├── IMPLEMENTATION_STATUS_REPORT.md
│   ├── IMPORT_TO_FIGMA.md
│   ├── IMPROVEMENT_ROADMAP.md
│   ├── INCIDENT_RESPONSE_PLAYBOOKS.md
│   ├── INLINE_ASSESSMENT_SOLUTION.md
│   ├── INSURANCE_INQUIRY_EMAILS.md
│   ├── INTEGRATION_GUIDE.md
│   ├── INTEGRATION_MONITORING_SIMPLE.md
│   ├── IR_AUTOMATION_TOOLS_GUIDE.md
│   ├── KUBERNETES_CLOUD_SECURITY_SUMMARY.md
│   ├── KUBERNETES_SECRETS_MANAGEMENT_GUIDE.md
│   ├── LAZY_LOADING_STRATEGY.md
│   ├── LEGAL_EQUITY_QUICK_START.md
│   ├── LEGAL_OUTREACH_EMAILS.md
│   ├── LEGAL_REVIEW_CHECKLIST.md
│   ├── LINTING_IMPLEMENTATION_SUMMARY.md
│   ├── LINTING_QUICKSTART.md
│   ├── LINTING_README.md
│   ├── LLM_SANITIZATION_POLICY.md
│   ├── LLM_SECURITY_IMPLEMENTATION_SUMMARY.md
│   ├── LLM_SECURITY_INTEGRATION_GUIDE.md
│   ├── LLM_SECURITY_POLICY.md
│   ├── LOCAL_DEVELOPMENT.md
│   ├── MANUAL_CLINICAL_TESTING.md
│   ├── MARKETING_CAMPAIGN_MATERIALS.md
│   ├── MASTER_SUITE_INDEX.md
│   ├── MFA_LIVE_TESTING_CHECKLIST.md
│   ├── MICROSERVICES_ARCHITECTURE_CORRECTED.md
│   ├── MIGRATION_PROGRESS.md
│   ├── MIGRATION_ROLLBACK_STRATEGY.md
│   ├── MIGRATION_v2.0.md
│   ├── MOBILE_NATIVE_INTERACTION_PATTERNS.md
│   ├── MOBILE_UX_OPTIMIZATION_ROADMAP.md
│   ├── MONITORING_BASELINE_20260118.md
│   ├── MONITORING_COST_OPTIMIZATION.md
│   ├── MONITORING_QUICKSTART.md
│   ├── MONITORING_QUICK_START.md
│   ├── MONITORING_SETUP.md
│   ├── MONITORING_SETUP_GUIDE.md
│   ├── MONTHLY_EXECUTIVE_PRODUCT_REPORTS.md
│   ├── NETWORK_ERROR_FIX.md
│   ├── NIST_SSDF_v1.1_PLAYBOOK.md
│   ├── OBSERVABILITY_IMPROVEMENT_RECOMMENDATIONS.md
│   ├── ONBOARDING_EXPERIMENTS.md
│   ├── ONBOARDING_MICROCOPY.md
│   ├── OPENAPI_DOCUMENTATION.md
│   ├── OPENAPI_ENHANCEMENT_GUIDE.md
│   ├── OPEN_GRAFANA_DASHBOARD.md
│   ├── OPERATIONAL_RUNBOOKS.md
│   ├── OPTIMIZATION_IMPLEMENTATION_PROGRESS.md
│   ├── ORGANIZATION_RELATIONSHIP_FIX.md
│   ├── OWASP_SECURITY_ANALYSIS.md
│   ├── OWASP_SECURITY_FINAL_REPORT.md
│   ├── OWASP_SECURITY_REVIEW_PROGRESS.md
│   ├── OWASP_SECURITY_REVIEW_SUMMARY.md
│   ├── PAGE_FREEZE_FINAL_FIX.md
│   ├── PAGE_NONRESPONSIVE_FIX.md
│   ├── PARTNERSHIP_PROGRAM_MATERIALS.md
│   ├── PERFORMANCE_COMPARISON_REPORT.md
│   ├── PERFORMANCE_FIXES_APPLIED.md
│   ├── PERFORMANCE_MONITORING_DEPLOYMENT.md
│   ├── PERFORMANCE_QUICKSTART.md
│   ├── PICKLE_VULNERABILITY_FIXES.md
│   ├── POPULATION_HEALTH_SETUP.md
│   ├── PRICING_EXPERIMENT_FRAMEWORK.md
│   ├── PRICING_STRATEGY_TIERS.md
│   ├── PROCEED_BUTTON_FIX_TEST.md
│   ├── PRODUCTION_DEPLOYMENT_CHECKLIST.md
│   ├── PRODUCTION_DEPLOYMENT_SECURITY_CHECKLIST.md
│   ├── PRODUCTION_OPTIMIZATION_FRAMEWORK.md
│   ├── PRODUCTION_OPTIMIZATION_IN_PROGRESS.md
│   ├── PRODUCTION_READINESS_CHECKLIST.md
│   ├── PRODUCTION_READINESS_FINAL_SUMMARY.md
│   ├── PRODUCTION_SECURITY_CHECKLIST.md
│   ├── PRODUCTION_SECURITY_MIDDLEWARE.md
│   ├── PRODUCT_ACTIVATION_THRESHOLDS.md
│   ├── PRODUCT_ANNOUNCEMENT_PLAYBOOK.md
│   ├── PRODUCT_DIFFERENTIATION_STRATEGY.md
│   ├── PRODUCT_MANAGEMENT_PROMPTS.md
│   ├── PRODUCT_MANAGEMENT_README.md
│   ├── PRODUCT_OPERATIONS_READY.md
│   ├── PRODUCT_RISK_ANALYSIS.md
│   ├── PROGRESS_UPDATE.md
│   ├── PROJECT_COMPLETION_CERTIFICATE.md
│   ├── PROJECT_STATUS.md
│   ├── PULL_REQUEST_DESCRIPTION.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── PULL_REQUEST_VALIDATION_RULES.md
│   ├── PUSH_NOTIFICATIONS.md
│   ├── PWA_DEPLOYMENT_PRODUCTION_GUIDE.md
│   ├── PWA_PERFORMANCE_OPTIMIZATION_GUIDE.md
│   ├── Q1_ENGINEERING_ROADMAP.md
│   ├── QA_ACCEPTANCE_CRITERIA.md
│   ├── QA_LOAD_TESTING_GUIDE.md
│   ├── QUARTERLY_INNOVATION_ROADMAP.md
│   ├── QUERY_OPTIMIZATION_FIXES.md
│   ├── QUERY_OPTIMIZATION_MASTER_INDEX.md
│   ├── QUICKSTART.md
│   ├── QUICKSTART_CRITICAL_FIXES.md
│   ├── QUICK_DEMO_STORYBOARD.md
│   ├── QUICK_JWT_TESTING.md
│   ├── QUICK_RATE_LIMITING_TEST.md
│   ├── QUICK_REFERENCE_DEPLOYMENT.md
│   ├── QUICK_START.md
│   ├── QUICK_START_CORPORATE.md
│   ├── QUICK_START_CORPORATE_MIGRATED.md
│   ├── QUICK_START_FREE.md
│   ├── QUICK_START_GUIDE.md
│   ├── QUICK_START_IMPLEMENTATION_COMPLETE.md
│   ├── QUICK_START_OPTIMIZATION.md
│   ├── QUICK_START_PERFORMANCE_FIXES.md
│   ├── QUICK_START_POPULATION_HEALTH.md
│   ├── QUICK_TEST_CHECKLIST.md
│   ├── RACE_CONDITIONS_FIXED.md
│   ├── RACE_CONDITION_FIXES.md
│   ├── RADAR_MVP_IMPLEMENTATION.md
│   ├── RADIO_BUTTON_DEBUG_TEST.md
│   ├── RATE_LIMITER_MIGRATION_GUIDE.md
│   ├── REACT_COMPONENT_OPTIMIZATION.md
│   ├── README.md
│   ├── README_ARCHITECTURE_AUDIT.md
│   ├── README_DEVELOPMENT.md
│   ├── README_DOCUMENTATION.md
│   ├── README_INDEX.md
│   ├── README_SCREENHOTS.md
│   ├── REDIS_MONITORING_GUIDE.md
│   ├── REFACTORED_SERVICES_QUICK_START.md
│   ├── REFACTORED_TESTS_QUICK_START.md
│   ├── REFACTORING_PLAN_assessments.py.md
│   ├── RESTART_BACKEND.md
│   ├── RETENTION_CLEANUP_IMPLEMENTATION.md
│   ├── RETENTION_IMPACT_ROADMAP.md
│   ├── RETRY_ENHANCEMENT_USAGE.md
│   ├── RETRY_LOGIC_IMPROVEMENTS.md
│   ├── RETRY_MONITORING_INTEGRATION.md
│   ├── RISK_MITIGATION_OWNER_ASSIGNMENTS.md
│   ├── ROLLBACK_PLAYBOOKS.md
│   ├── SALES_ENABLEMENT_NARRATIVE.md
│   ├── SALES_EXECUTION_MATERIALS.md
│   ├── SALES_TRAINING_PROGRAM.md
│   ├── SBOM_WORKFLOW_GUIDE.md
│   ├── SCHEMA_ALIGNMENT_FINAL_FIXES.md
│   ├── SECRET_LEAK_REMEDIATION_PLAYBOOK.md
│   ├── SECRET_MANAGEMENT_GUIDANCE.md
│   ├── SECURE_CONFIGURATION_GUIDE.md
│   ├── SECURE_CONFIG_README.md
│   ├── SECURE_SDLC_QUICK_START.md
│   ├── SECURITY_ARCHITECTURE.md
│   ├── SECURITY_AUDIT_2025-01-15.md
│   ├── SECURITY_BADGES.md
│   ├── SECURITY_HAEDENING_COMPLETE.md
│   ├── SECURITY_HEADERS_GUIDE.md
│   ├── SECURITY_IMPLEMENTATION_SUMMARY.md
│   ├── SECURITY_INDEX.md
│   ├── SECURITY_INTEGRATION_GUIDE.md
│   ├── SECURITY_LOGGING_EXAMPLES.md
│   ├── SECURITY_LOGGING_FINAL_SUMMARY.md
│   ├── SECURITY_LOGGING_GUIDE.md
│   ├── SECURITY_LOGGING_IMPLEMENTATION_SUMMARY.md
│   ├── SECURITY_MASTER_INDEX.md
│   ├── SECURITY_METRICS_DASHBOARD.md
│   ├── SECURITY_MIDDLEWARE_MIGRATION_GUIDE.md
│   ├── SECURITY_MONITORING_COMPLETE.md
│   ├── SECURITY_MONITORING_DEPLOYMENT_CHECKLIST.md
│   ├── SECURITY_MONITORING_GUIDE.md
│   ├── SECURITY_MONITORING_PRODUCTION_READY.md
│   ├── SECURITY_PIPELINE_QUICK_REF.md
│   ├── SECURITY_POLICY.md
│   ├── SECURITY_POLICY_EXECUTIVE_SUMMARY.md
│   ├── SECURITY_QUICK_REFERENCE.md
│   ├── SECURITY_QUICK_START.md
│   ├── SECURITY_QUICK_START_DEVELOPER.md
│   ├── SECURITY_README.md
│   ├── SECURITY_REVIEW_CHECKLIST.md
│   ├── SECURITY_SELF_ASSESSMENT_CHECKLIST.md
│   ├── SEMANTIC_UNCERTAINTY_DETECTION.md
│   ├── SEMANTIC_UNCERTAINTY_DETECTION_IMPLEMENTATION.md
│   ├── SERVER_SECURITY_AUDIT_CHECKLIST.md
│   ├── SERVER_SECURITY_DELIVERABLES_SUMMARY.md
│   ├── SERVER_STARTUP_ERRORS.md
│   ├── SERVICES_TO_DISABLE.md
│   ├── SERVICE_MIGRATION_PATTERNS.md
│   ├── SESSION_ACCOMPLISHMENTS.md
│   ├── SESSION_COMPLETE_SUMMARY.md
│   ├── SETUP.md
│   ├── SIDEBAR_VISUAL_MOCKUPS.md
│   ├── SLSA_GITHUB_ACTIONS_IMPLEMENTATION.md
│   ├── SLSA_VERIFICATION_GUIDE.md
│   ├── SMTP_QUICKSTART.md
│   ├── SOCIAL_ENGINEERING_SECURITY_ASSESSMENT.md
│   ├── SOLID_REMEDIATION_IMPLEMENTATION.md
│   ├── SPOTLIGHTING_SDK_GUIDE.md
│   ├── SSRF_SECURITY_ANALYSIS.md
│   ├── START_HERE.md
│   ├── STOP_ROGUE_PYTEST.md
│   ├── STRATEGY_EXECUTION_MASTER_INDEX.md
│   ├── SUPPLY_CHAIN_QUICKSTART.md
│   ├── SUPPLY_CHAIN_QUICK_START.md
│   ├── SUPPLY_CHAIN_SECURITY.md
│   ├── SUPPLY_CHAIN_SECURITY_V2.md
│   ├── SYNTAX_CORRUPTION_ANALYSIS.md
│   ├── TEAM_ANALYTICS_FEATURE_BRIEF.md
│   ├── TEAM_MEMBER_ADDITION_TEST_SCENARIOS.md
│   ├── TEAM_TRAINING_GUIDE.md
│   ├── TEAM_TRAINING_MEMORY_MANAGEMENT.md
│   ├── TESTING.md
│   ├── TESTING_ECOSYSTEM_DOCUMENTATION.md
│   ├── TESTING_GUIDELINES.md
│   ├── TESTING_QUICK_REFERENCE.md
│   ├── TESTING_REGRESSION_DELIVERY_SUMMARY.md
│   ├── TESTING_REGRESSION_SUITE_DESIGN.md
│   ├── TEST_COVERAGE_GAPS_ANALYSIS.md
│   ├── TEST_COVERAGE_MATRIX.md
│   ├── TEST_INFRASTRUCTURE_FIXES_SUMMARY.md
│   ├── TEST_REGRESSION_QUICKSTART.md
│   ├── THREAT_DETECTION_DASHBOARD_GUIDE.md
│   ├── TOXIC_BEHAVIOR_DETECTION_IMPLEMENTATION.md
│   ├── TRAINING_PRESENTATION.md
│   ├── TROUBLESHOOTING_PERFORMANCE.md
│   ├── TROUBLESHOOT_REFRESH_BUTTON.md
│   ├── UNIFIED_SECURITY_TESTING_FRAMEWORK.md
│   ├── UPSELL_OPPORTUNITIES.md
│   ├── USER_GUIDE.md
│   ├── USER_MODULE_SECURITY_ANALYSIS.md
│   ├── USER_ROLES_AND_PERSONAS.md
│   ├── UX_TO_BACKEND_MAPPING.md
│   ├── VALIDATION_SECURITY_ASSESSMENT_FINAL.md
│   ├── VALUE_VS_COMPLEXITY_ROADMAP.md
│   ├── VERIFICATION_QUICK_REFERENCE.md
│   ├── VIDEO_DEMO_SCRIPT.md
│   ├── VULNERABILITY_SEVERITY_REFERENCE.md
│   ├── WEARABLE_INTEGRATION_GUIDE.md
│   ├── WEB_SECURITY_README.md
│   ├── WEEK1_COMPLETION_REPORT.md
│   ├── WEEK2_FINAL_SUMMARY.md
│   ├── WEEK2_IMPROVEMENTS_COMPLETE.md
│   ├── WEEK_1_EXECUTION_CHECKLIST.md
│   ├── YOU_HAVE_NOW.md
│   ├── ZERO_DOWNTIME_DEPLOYMENT.md
│   ├── adr
│   ├── advanced_psychometrics_completion_report.md
│   ├── analytics_service_MIGRATION_CHECKLIST.md
│   ├── api
│   ├── architecture
│   ├── archive
│   ├── celery_setup_guide.md
│   ├── code-reviews
│   ├── code_quality
│   ├── complete_project_documentation.md
│   ├── cron_configuration.md
│   ├── developer
│   ├── email_service_MIGRATION_CHECKLIST.md
│   ├── engineering
│   ├── final_summary.md
│   ├── incidents
│   ├── internal
│   ├── irt_implementation_summary.md
│   ├── notifications_MIGRATION_CHECKLIST.md
│   ├── operations
│   ├── performance
│   ├── personality_MIGRATION_CHECKLIST.md
│   ├── product
│   ├── production_readiness.md
│   ├── push_notification_service_MIGRATION_CHECKLIST.md
│   ├── requirements_nlp.txt
│   ├── response_service_MIGRATION_CHECKLIST.md
│   ├── scoring_documentation.md
│   ├── scoring_service_MIGRATION_CHECKLIST.md
│   ├── security
│   ├── setup
│   ├── sops
│   ├── team_optimization_service_MIGRATION_CHECKLIST.md
│   ├── technical
│   ├── templates
│   ├── training
│   ├── week1
│   └── {architecture
├── examples
│   ├── optimized_queries_example.py
│   └── product_management_integrations.py
├── exports
├── fail2ban_log
│   └── fail2ban.log
├── frontend
│   ├── ACCESSIBILITY_CHECKLIST.md
│   ├── ACCESSIBILITY_FIXES_COMPLETE.md
│   ├── ACCESSIBILITY_IMPLEMENTATION_SUMMARY.md
│   ├── ACCESSIBILITY_VIOLATIONS_REPORT.md
│   ├── ANALYTICS_DOUBLE_COUNTING_ANALYSIS.md
│   ├── ANALYTICS_DOUBLE_COUNTING_FIXES.md
│   ├── ANALYTICS_PERFORMANCE_ANALYSIS.md
│   ├── ANALYTICS_TRACKING_IMPLEMENTATION.md
│   ├── API_TYPES_GUIDE.md
│   ├── AUTOMATED_SYSTEM_README.md
│   ├── AUTOMATION_COMPLETE_20260120_145348.md
│   ├── CLINICAL_SETUP.md
│   ├── CODE_REVIEW_CHECKLIST.md
│   ├── COMPLETE_ANALYTICS_TRACKING_GUIDE.md
│   ├── COMPLETE_IMPLEMENTATION_SUMMARY.md
│   ├── COMPLETE_MOBILE_OPTIMIZATION_GUIDE.md
│   ├── COMPLETE_OPTIMIZATION_SUMMARY.md
│   ├── COMPONENT_TREE_RENDERING_AUDIT.md
│   ├── CONTEXT_INTEGRITY_REVIEW.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── Dockerfile.free
│   ├── ERROR_BOUNDARY_TEST_RESULTS.md
│   ├── ERROR_HANDLING_IMPLEMENTATION_REPORT.md
│   ├── FULLY_AUTOMATED_SYSTEM_COMPLETE.md
│   ├── MEMORY_LEAK_AUDIT_REPORT.md
│   ├── MEMORY_LEAK_DASHBOARD_20260120.html
│   ├── MEMORY_LEAK_DETECTION_REPORT.html
│   ├── MEMORY_LEAK_DETECTION_REPORT.md
│   ├── MEMORY_LEAK_FIXES_COMPLETE.md
│   ├── MEMORY_LEAK_PREVENTION_COMPLETE.md
│   ├── MEMORY_LEAK_QUICKFIX_GUIDE.md
│   ├── MIGRATION_CHECKLIST.md
│   ├── MOBILE_OPTIMIZATION_FINAL_SUMMARY.md
│   ├── PERFORMANCE_MEASUREMENT.md
│   ├── PERFORMANCE_MONITORING_GUIDE.md
│   ├── PERFORMANCE_OPTIMIZATION_COMPLETE.md
│   ├── PERFORMANCE_OPTIMIZATION_IMPLEMENTATION.md
│   ├── PERFORMANCE_OPTIMIZATION_SUMMARY.md
│   ├── PERFORMANCE_TEST_REPORT.md
│   ├── QUICK_REFERENCE_CARD.md
│   ├── QUICK_START_CHECKLIST.md
│   ├── RACE_CONDITIONS_COMPLETE.md
│   ├── RACE_CONDITIONS_SUMMARY.md
│   ├── RACE_CONDITION_COMPLETE_PACKAGE.md
│   ├── RACE_CONDITION_FIXES.md
│   ├── RACE_CONDITION_FIX_GUIDE.md
│   ├── RACE_CONDITION_HOOK_USAGE_EXAMPLES.tsx
│   ├── REACT_EFFECT_CLEANUP_GUIDE.md
│   ├── REACT_PERFORMANCE_COMPLETE.md
│   ├── REACT_PERFORMANCE_FIXES.md
│   ├── REACT_QUERY_MIGRATION_GUIDE.md
│   ├── REACT_QUERY_SETUP.md
│   ├── README.md
│   ├── README_MOBILE_OPTIMIZATION.md
│   ├── REFACTORING_GUIDE.md
│   ├── ROLE_BASED_NAVIGATION.md
│   ├── SECURITY_RUNBOOK.md
│   ├── TAB_EXTRACTION_COMPLETE.md
│   ├── TEAMS_MIGRATION_EXAMPLE.md
│   ├── TEAM_EMAIL_TEMPLATE.md
│   ├── TEAM_HANDOFF.md
│   ├── TEAM_PRESENTATION.md
│   ├── TEAM_TRAINING_MEMORY_LEAKS.md
│   ├── TESTING_GUIDE.md
│   ├── TRAINING_SLIDES.md
│   ├── UI_STATE_SUMMARY.md
│   ├── UI_STATE_TRANSITIONS_ANALYSIS.md
│   ├── ULTIMATE_QUICK_START.md
│   ├── USEEXTP_RACE_CONDITIONS.md
│   ├── USEFFECT_DEPENDENCY_AUDIT.md
│   ├── USEFFECT_FIXES_SUMMARY.md
│   ├── VERIFICATION_COMPLETE.md
│   ├── WEEK_2_COMPLETE.md
│   ├── WEEK_3_FINAL_REPORT.md
│   ├── WORKSHOP_MEMORY_LEAKS.md
│   ├── allowed-dependencies.json
│   ├── components
│   ├── disabled-tests
│   ├── dist
│   ├── docs
│   ├── docs-frontend
│   ├── eslint-rules
│   ├── eslint.config.js
│   ├── find_unsafe_patterns.sh
│   ├── fix-error-types.sh
│   ├── frontend
│   ├── index.html
│   ├── logs
│   ├── models
│   ├── optimize_clinical_assessment.py
│   ├── package-lock.json
│   ├── package.json
│   ├── package.json.backup.enc
│   ├── package.json.backup.key
│   ├── playwright.config.ts
│   ├── postcss.config.js
│   ├── public
│   ├── run_manual_tests.sh
│   ├── scripts
│   ├── src
│   ├── tailwind.config.js
│   ├── team_optimizer.tsx
│   ├── temp_excluded
│   ├── test-performance.sh
│   ├── test-roles.html
│   ├── tests
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── verify-phase1-components.sh
│   ├── vite.config.ts
│   └── vitest.config.ts
├── github-actions-ci-cd.yml
├── imported_models.txt
├── integration
│   ├── ai_recommendations_test_results.json
│   ├── api_downtime_test_results.json
│   ├── integration_test_report_20251212_153518.html
│   ├── integration_test_report_20251212_153518.json
│   ├── integration_test_report_20251212_153725.html
│   ├── integration_test_report_20251212_153725.json
│   ├── integration_testing_suite.py
│   ├── optimized_api_downtime_handler.py
│   ├── optimized_api_downtime_results.json
│   ├── optimized_webhook_retry_results.json
│   ├── optimized_webhook_retry_system.py
│   ├── run_integration_tests.py
│   ├── sendgrid_email_integration_results_20251212_153518.json
│   ├── sendgrid_email_integration_results_20251212_153725.json
│   ├── sendgrid_integration_test_results.json
│   ├── sso_integration_results_20251212_153518.json
│   ├── sso_integration_results_20251212_153725.json
│   ├── sso_integration_test_results.json
│   ├── test_ai_recommendations_after_team_sync.py
│   ├── test_api_downtime_handling.py
│   ├── test_sendgrid_integration.py
│   ├── test_sso_integration.py
│   ├── test_webhook_retry_logic.py
│   ├── webhook_retry_logic_results_20251212_153518.json
│   ├── webhook_retry_logic_results_20251212_153725.json
│   └── webhook_retry_test_results.json
├── internal
│   └── persistence
├── isolated_artifacts
│   ├── api_sec_fix_backups
│   ├── comprehensive_sec_fix_backups
│   ├── fs_fix_backups
│   ├── htmlcov
│   ├── payment_fix_backups
│   ├── security_fix_backups
│   └── social_eng_fix_backups
├── lifespan_original.txt
├── load
│   └── locustfile.py
├── load_testing
│   ├── Dockerfile.locust
│   ├── QUICKSTART.md
│   ├── README.md
│   ├── TEST_SCENARIOS.md
│   ├── docker-compose.test.yml
│   ├── k6
│   ├── locust
│   ├── monitoring
│   ├── reports
│   ├── requirements.txt
│   ├── run_tests.sh
│   └── test_data
├── log_integrity_cron.conf
├── logging
│   ├── docker-compose-elk.yml
│   └── logstash.conf
├── logs
│   ├── app.log
│   ├── audit
│   ├── backend.log
│   ├── credential_rotations.json
│   ├── integrity.json
│   ├── locust_normal_load.log
│   ├── locust_smoke_simple.log
│   ├── locust_smoke_test.log
│   └── rotation.log
├── metrics_history
│   └── metrics_20260210.csv
├── migrations
│   ├── 010_add_critical_performance_indexes.py.bak.enc
│   └── 010_add_critical_performance_indexes.py.bak.key
├── ml
│   ├── security
│   └── training
├── mobile
│   ├── App.tsx
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── README.md
│   ├── app.json
│   ├── assets
│   ├── index.ts
│   ├── package-lock.json
│   ├── package.json
│   ├── src
│   └── tsconfig.json
├── models
│   ├── gradient_boosting_team_performance_20260413_144734.joblib
│   ├── linear_regression_team_performance_20260413_144829.joblib
│   ├── neural_network_team_performance_20260413_144820.joblib
│   ├── random_forest_team_performance_20260413_144634.joblib
│   └── svm_team_performance_20260413_144756.joblib
├── monitoring
│   ├── COST_BENEFIT_ANALYSIS.md
│   ├── ELK_AGGREGATION_DESIGN.md
│   ├── IMPLEMENTATION_TICKETS.md
│   ├── LOGGING_OBSERVABILITY_ANALYSIS.md
│   ├── LOG_ROTATION_DESIGN.md
│   ├── ML_ANOMALY_DETECTION_DESIGN.md
│   ├── ML_ARCHITECTURE_DEEP_DIVE.md
│   ├── MONITORING_BLIND_SPOTS_REPORT.md
│   ├── QUICKSTART.md
│   ├── REALTIME_DASHBOARD_DESIGN.md
│   ├── SAMPLE_LOGS_EXAMPLES.md
│   ├── advanced-observability.yaml
│   ├── alertmanager
│   ├── alerts
│   ├── alerts_integration.yml
│   ├── config
│   ├── dashboards
│   ├── datadog
│   ├── exporters
│   ├── grafana
│   ├── logging_config.json
│   ├── logs
│   ├── loki
│   ├── message_queue_alerts.yml
│   ├── metrics
│   ├── monitoring_config.json
│   ├── production-alerts.yml
│   ├── production-monitoring.yml
│   ├── prometheus
│   ├── prometheus.yml
│   ├── prometheus_integration.yml
│   ├── promtail
│   ├── scripts
│   ├── sentry
│   ├── services
│   ├── sla
│   ├── synthetic
│   └── webapp
├── monitoring_logs
│   ├── daily_20260220.log
│   ├── daily_20260407.log
│   ├── daily_20260506.log
│   ├── weekly_20260123.log
│   ├── weekly_20260213.log
│   ├── weekly_20260306.log
│   ├── weekly_20260313.log
│   ├── weekly_20260320.log
│   ├── weekly_20260327.log
│   └── weekly_20260501.log
├── monitoring_reports
│   ├── daily_report_2026-01-18.md
│   └── weekly_report_week_1_2026-01-18.md
├── new_imports.txt
├── nginx
│   ├── certbot
│   ├── nginx.conf
│   └── psychsync.conf
├── nginx.conf
├── package-lock.json
├── package.json
├── performance
│   ├── dashboard_performance_test.py
│   ├── load_testing_suite.py
│   └── stress_test_scenarios.py
├── product
│   ├── README.md
│   ├── experiments
│   ├── features
│   ├── go-to-market
│   ├── metrics
│   ├── operations
│   ├── pricing
│   ├── roadmap
│   ├── strategy
│   ├── user-journey-map.md
│   └── user-personas.md
├── product_management_prompts
│   ├── QUICKSTART.md
│   ├── README.md
│   ├── TEST_RESULTS.md
│   ├── product_management_prompts.json
│   ├── product_prompt_service.py
│   ├── requirements.txt
│   ├── start.sh
│   ├── static
│   └── templates
├── production
├── prometheus-2.47.2.darwin-amd64
├── psychsync.code-workspace
├── psychsync.egg-info
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   └── top_level.txt
├── psychsync_cron.conf
├── public
│   ├── assets
│   ├── manifest.json
│   ├── service-worker-optimized.js
│   └── service-worker.js
├── pyproject.toml
├── pyrightconfig.json
├── pytest.ini
├── pytest.refactored.ini
├── reports
│   ├── api_contract_drift.json
│   ├── dead_code.json
│   ├── doc_coverage.json
│   ├── poisoning-detection
│   ├── sbom-analysis
│   ├── security-metrics-20251227-115329.json
│   ├── security-metrics-20251227-115748.json
│   ├── security-metrics-20251227-122951.json
│   └── test_coverage_audit.json
├── requirements.txt
├── ruff.toml
├── sbom
│   └── backend-test-20251225_184416.json
├── screenshots
│   ├── 00-comparison.png
│   ├── 01-dashboard.png
│   ├── 02-burnout-prevention.png
│   ├── 03-behavioral-analytics.png
│   ├── 04-toxic-behavior-detection.png
│   ├── 05-employee-safety.png
│   ├── 06-anomaly-detection.png
│   ├── 07-predictive-analytics.png
│   ├── 08-teams.png
│   ├── 09-mobile-dashboard.png
│   ├── 09-team-dashboard-page.png
│   ├── 10-anomaly-detection-page.png
│   ├── 10-mobile-burnout.png
│   └── index.html
├── scripts
│   ├── GEMINI.md
│   ├── add_missing_indexes_simple.sql
│   ├── add_missing_performance_indexes.sql
│   ├── advanced_monitoring.py
│   ├── analyze_data_corruption_risks.py
│   ├── analyze_services_accurate.py
│   ├── analyze_unused_services.py
│   ├── api_excellence_optimizer.py
│   ├── apply_migrations_safe.sh
│   ├── apply_performance_indexes.sh
│   ├── architecture-validation.sh
│   ├── archive_old_data.py
│   ├── archive_old_data.sql
│   ├── archive_unused_services.py
│   ├── audit_test_coverage.py
│   ├── auto_fix_b904.py
│   ├── auto_fix_bare_exceptions.py
│   ├── backup-postgres-production.sh
│   ├── backup.sh
│   ├── benchmark_database.py
│   ├── build_monitoring_stack.sh
│   ├── cache-monitor.py
│   ├── check-allowlist.py
│   ├── check-allowlist.sh
│   ├── check-complexity.sh
│   ├── check-registry-policy.sh
│   ├── check_import_complexity.py
│   ├── check_no_bare_except.py
│   ├── check_user_status.py
│   ├── com.psychsync.emailmonitor.plist
│   ├── com.psychsync.scheduledreports.plist
│   ├── compliance-report.py
│   ├── comprehensive_security_health_check.py
│   ├── cors_security_audit_report.json
│   ├── create_composite_indexes.py
│   ├── create_enterprise_tables.sql
│   ├── create_indexes_smart.py
│   ├── create_mock_telehealth_session.py
│   ├── create_production_schema.py
│   ├── create_remaining_files_script.sh
│   ├── create_schema_from_models.py
│   ├── create_test_user.py
│   ├── create_user.py
│   ├── cron_maintenance.sh
│   ├── cve-monitor.py
│   ├── daily_monitoring_check.sh
│   ├── database_backup.py
│   ├── database_excellence_optimizer.py
│   ├── database_maintenance.py
│   ├── database_performance_test.py
│   ├── db-manage.sh
│   ├── db_healthcheck.py
│   ├── demo_agents.sh
│   ├── demo_llm_security.py
│   ├── demo_security_logging_complete.py
│   ├── demo_security_monitoring.py
│   ├── detect-unauthorized-logins.sh
│   ├── dev-start.sh
│   ├── dev.sh
│   ├── diagnose.sh
│   ├── diagnose_gad7_issue.py
│   ├── documentation_package_generator.py
│   ├── email_monitor.py
│   ├── email_monitor_simple.sh
│   ├── engineering_pipeline.py
│   ├── fallback_audit_report.json
│   ├── file_upload_security_tester.py
│   ├── fix_alembic_heads.py
│   ├── fix_alembic_script.sh
│   ├── fix_all_b904.py
│   ├── fix_api_authentication.py
│   ├── fix_auth_style.py
│   ├── fix_b904_120_percent.py
│   ├── fix_b904_automated.py
│   ├── fix_b904_comprehensive.py
│   ├── fix_b904_incremental.py
│   ├── fix_b904_manual.py
│   ├── fix_b904_manual_final.py
│   ├── fix_b904_safe.py
│   ├── fix_bare_exceptions.py
│   ├── fix_debug_bypasses.py
│   ├── fix_decorator_insertion.py
│   ├── fix_duplicate_fixtures.py
│   ├── fix_exception_chains.py
│   ├── fix_exception_handling_comprehensive.py
│   ├── fix_health_py.py
│   ├── fix_high_priority_bare_exceptions.py
│   ├── fix_indentation_errors.py
│   ├── fix_jsonb_imports.py
│   ├── fix_legacy_syntax.py
│   ├── fix_linting_incremental.py
│   ├── fix_pagination_limits.py
│   ├── fix_rate_limiter_signatures.py
│   ├── fix_syntax_and_b904.sh
│   ├── fix_syntax_corruption.py
│   ├── fix_syntax_corruption.sh
│   ├── fix_syntax_errors.py
│   ├── fix_technical_debt.py
│   ├── foo.py
│   ├── frontend-optimization-starter.sh
│   ├── frontend_excellence_optimizer.py
│   ├── gen_high_consistency_data.py
│   ├── generate-vex.py
│   ├── generate_migration_template.py
│   ├── generate_performance_graphs.py
│   ├── generate_predictive_data.py
│   ├── generate_provenance.py
│   ├── generate_pwa_icons.py
│   ├── generate_pwa_icons_simple.py
│   ├── generate_sbom.sh
│   ├── generate_secrets.py
│   ├── generate_ssl_certificates.sh
│   ├── generate_tests.py
│   ├── generate_weekly_report.py
│   ├── git-commit-push.sh
│   ├── git-setup-workflows.sh
│   ├── harden-ubuntu-server.sh
│   ├── health_check.sh
│   ├── hris_dev_server.py
│   ├── immutable_log.py
│   ├── implement_csp_hardening.sh
│   ├── infrastructure_security_scanner.py
│   ├── init-database.sh
│   ├── init_database.py
│   ├── init_database_sync.py
│   ├── init_db.py
│   ├── init_security_policies.py
│   ├── install_cron.sh
│   ├── install_email_monitor_service.sh
│   ├── install_log_integrity_cron.sh
│   ├── install_sbstools.sh
│   ├── list_app_routes.py
│   ├── load_test_async_cache.py
│   ├── master_production_optimizer.py
│   ├── measure_technical_debt.py
│   ├── migrate_rate_limiters.py
│   ├── migrate_security_imports.py
│   ├── minimal_app.py
│   ├── minimal_app_enhanced.py
│   ├── monitor_file_growth.py
│   ├── monitor_hsts_status.sh
│   ├── monitor_test_coverage.py
│   ├── monitoring_dashboard.py
│   ├── monitoring_observability_system.py
│   ├── optimize_database.py
│   ├── optimized_server_start.sh
│   ├── performance-optimization-starter.py
│   ├── pipeline_components
│   ├── pre-commit-security-check.sh
│   ├── pre_production_security_audit.py
│   ├── pre_production_validation.py
│   ├── prepare_test_db.sh
│   ├── product_prompts_cli.py
│   ├── production_monitoring_setup.py
│   ├── production_readiness_check.sh
│   ├── production_readiness_validation.py
│   ├── profile_api_endpoints.py
│   ├── profile_memory_usage.py
│   ├── push-to-all-repos.sh
│   ├── quick-login.sh
│   ├── quick_archive_unused.py
│   ├── quick_data_corruption_scan.py
│   ├── quick_fix_schema.sh
│   ├── quick_load_test.py
│   ├── quick_migrate.sh
│   ├── redis-memory-monitor.py
│   ├── remove_console_logs.py
│   ├── replace_print_with_logger.py
│   ├── repro_lsas_bug.py
│   ├── reproduce_telehealth_500.py
│   ├── reset-db.sh
│   ├── reset_alembic_safe.sh
│   ├── restore-postgres-production.sh
│   ├── restore_from_archive.py
│   ├── rollback_bad_migration.sh
│   ├── run-dast.sh
│   ├── run-sast.sh
│   ├── run_clinical_tests.sh
│   ├── run_comprehensive_security_tests.sh
│   ├── run_comprehensive_tests.py
│   ├── run_corporate_psychology_analysis.sh
│   ├── run_migrations.sh
│   ├── run_security_tests.sh
│   ├── run_tests.sh
│   ├── scan-dependencies.sh
│   ├── scan_dependencies.sh
│   ├── scheduled_reports.py
│   ├── secure-frontend-optimizer.sh
│   ├── secure-performance-optimizer.py
│   ├── secure_dns_configuration.sh
│   ├── security
│   ├── security-metrics.py
│   ├── security-quickstart.sh
│   ├── security_audit.py
│   ├── security_integration_manager.py
│   ├── security_release_tests.py
│   ├── security_test_suite.sh
│   ├── security_todo_tracker.py
│   ├── seed_engagement_survey.py
│   ├── seed_legal_equity_data.py
│   ├── session_security_tester.py
│   ├── setup-branch-protection.sh
│   ├── setup-kafka.sh
│   ├── setup-lean-dev.sh
│   ├── setup-linting.sh
│   ├── setup-localhost-ssl.sh
│   ├── setup-precommit.sh
│   ├── setup_data_retention.py
│   ├── setup_free.sh
│   ├── setup_monitoring_cron.sh
│   ├── setup_monitoring_stack.py
│   ├── setup_production_monitoring.py
│   ├── setup_redis.sh
│   ├── sign-container.sh
│   ├── sign_build_artifacts.sh
│   ├── simple_load_test.sh
│   ├── simple_optimized_server.sh
│   ├── simple_test_generator.py
│   ├── smoke_tests.py
│   ├── ssh_brute_force_tester.py
│   ├── ssl_init_script.sh
│   ├── stamp_alembic.py
│   ├── start-ai-agents.sh
│   ├── start-dev-https.sh
│   ├── start-dev.sh
│   ├── start-full-dev.sh
│   ├── start_all.sh
│   ├── start_backend.sh
│   ├── start_db_monitoring.py
│   ├── start_dev.sh
│   ├── start_dev_local.sh
│   ├── start_email_monitor.sh
│   ├── start_frontend.sh
│   ├── start_secure_network.sh
│   ├── start_secure_server.sh
│   ├── start_security_monitoring.sh
│   ├── stop-dev.sh
│   ├── stop_all.sh
│   ├── stop_dev.sh
│   ├── temp_imports.py
│   ├── test_analytics_dashboard.py
│   ├── test_async_cache_basic.py
│   ├── test_async_cache_performance.py
│   ├── test_auth_flow.sh
│   ├── test_auth_validation.sh
│   ├── test_authenticated_endpoints.sh
│   ├── test_cache_auth.py
│   ├── test_core_journey.py
│   ├── test_corporate_psychology.sh
│   ├── test_database_comprehensive.py
│   ├── test_dlq_components.py
│   ├── test_dlq_migration.sh
│   ├── test_endpoints.sh
│   ├── test_production_authentication.py
│   ├── test_programmatic_assessment_insert.py
│   ├── test_report_dashboard.py
│   ├── test_session_invalidation.sh
│   ├── testing_excellence_suite.py
│   ├── train_burnout_predictor.py
│   ├── uninstall_email_monitor_service.sh
│   ├── update_dependencies_security.sh
│   ├── update_telehealth_constraints.py
│   ├── validate_architecture.py
│   ├── validate_assessment_schema.sql
│   ├── validate_database.py
│   ├── validate_enterprise_maturity.sh
│   ├── validate_migration.py
│   ├── validate_monitoring_setup.sh
│   ├── validate_package_request.py
│   ├── validate_pwa_staging.py
│   ├── validate_query_optimization.py
│   ├── validate_response_schemas.py
│   ├── validate_security_fixes.sh
│   ├── verify-container.sh
│   ├── verify-cosign-signature.sh
│   ├── verify-production-ready.sh
│   ├── verify-quick.sh
│   ├── verify-supply-chain-security.sh
│   ├── verify_agents.sh
│   ├── verify_b904_setup.sh
│   ├── verify_build.sh
│   ├── verify_core_tables.py
│   ├── verify_critical_security_fixes.sh
│   ├── verify_dlq_system.sh
│   ├── verify_host_validation.sh
│   ├── verify_migration.py
│   ├── verify_monitoring.sh
│   ├── verify_performance_optimizations.py
│   ├── verify_predictive_data.py
│   ├── verify_production_ready.py
│   ├── verify_production_security.py
│   ├── verify_sbom.sh
│   ├── verify_security.sh
│   ├── verify_security_implementation.py
│   ├── verify_strict_host_validation.sh
│   ├── verify_user_model.py
│   ├── verify_week1_fixes.sh
│   ├── view_db_monitoring_stats.py
│   ├── visualize_dependencies.py
│   ├── warm_cache.py
│   └── watch_metrics.sh
├── security
│   └── credential_rotator.py
├── security_reports
├── semgrep_rules
│   ├── ai-introduced-security.yaml
│   ├── ai-security.yaml
│   ├── owasp-python.yaml
│   ├── owasp_auth_security.yaml
│   ├── owasp_path_traversal.yaml
│   ├── owasp_ssrf.yaml
│   └── web_security.yml
├── setup.py
├── src
│   └── components
├── static
│   ├── 503.html
│   ├── coming-soon.html
│   ├── css
│   ├── health.html
│   ├── js
│   ├── maintenance.html
│   └── status.html
├── supply_chain
│   └── sbom_analyzer.py
├── temp_commented.txt
├── templates
├── test_reports
│   ├── architecture_validation_20251114_182528.json
│   ├── architecture_validation_20251114_182559.json
│   ├── architecture_validation_20251114_183009.json
│   ├── architecture_validation_20251114_183814.json
│   ├── architecture_validation_20251114_184023.json
│   ├── architecture_validation_20251114_184735.json
│   ├── architecture_validation_20251114_185526.json
│   ├── architecture_validation_20251114_185755.json
│   ├── architecture_validation_20251115_082056.json
│   ├── coverage_report_20251122_045928.json
│   ├── coverage_report_20251122_045928.txt
│   └── test_summary_20251122_045928.json
└── tests
    ├── GEMINI.md
    ├── ONBOARDING_TESTING_GUIDE.md
    ├── README_team_assessment_tests.md
    ├── ai
    ├── api
    ├── app
    ├── app_services_user_service_test.py
    ├── assessment
    ├── authentication
    ├── business_logic_test_suite.py
    ├── chaos
    ├── clinical
    ├── comprehensive_tests.py
    ├── concurrency
    ├── conftest.py
    ├── conftest_fast.py
    ├── conftest_fix.py
    ├── coverage_requirements.md
    ├── crud
    ├── database_test_report.json
    ├── debug
    ├── devops_architecture_validation.py
    ├── devops_functional_testing.py
    ├── devops_master_test_orchestrator.py
    ├── devops_performance_testing.py
    ├── documentation
    ├── e2e
    ├── e2e_tests.py
    ├── enterprise_maturity_validation.py
    ├── fixtures
    ├── frontend
    ├── integration
    ├── integration_test_runner.py
    ├── integration_tests.py
    ├── integrations
    ├── load
    ├── load_test_async_endpoints.py
    ├── load_testing.py
    ├── models
    ├── oauth
    ├── payment
    ├── pdf
    ├── penetration_checklist.py
    ├── performance
    ├── permissions
    ├── production_readiness_test.py
    ├── pwa_comprehensive_test_suite.py
    ├── quick_test_runner.py
    ├── real_database_test_runner.py
    ├── real_device_pwa_testing.py
    ├── regression_strategy.md
    ├── schemas
    ├── scoring_tests.py
    ├── security
    ├── services
    ├── simple_database_test_runner.py
    ├── simple_real_db_test.py
    ├── smoke
    ├── test_account_deletion_cascade.py
    ├── test_advanced_functions.py
    ├── test_advanced_functions_boundary.py
    ├── test_analytics_service.py
    ├── test_api_endpoints.py
    ├── test_api_endpoints_comprehensive.py
    ├── test_api_integration.py
    ├── test_app_starts.py
    ├── test_assessment_integration.py
    ├── test_assessment_workflow_demo.py
    ├── test_assessments.py
    ├── test_audit_logging.py
    ├── test_auth_complete.py
    ├── test_auth_comprehensive.py
    ├── test_auth_rate_limiter.py
    ├── test_auth_security.py
    ├── test_backup.py
    ├── test_billing.py
    ├── test_cache_setup.py
    ├── test_cases
    ├── test_celery_setup.py
    ├── test_clinical_core.py
    ├── test_clinical_scoring.py
    ├── test_clinical_screening.py
    ├── test_core_fixes.py
    ├── test_coverage_validator.py
    ├── test_create_assessment_tables.py
    ├── test_create_assessment_tables_improved.py
    ├── test_create_db.py
    ├── test_create_scoring_tables.py
    ├── test_create_team_tables.py
    ├── test_create_template_tables.py
    ├── test_crisis_email.py
    ├── test_data
    ├── test_data_generators.py
    ├── test_database_integration.py
    ├── test_database_integrity.py
    ├── test_database_performance.py
    ├── test_database_simple.py
    ├── test_database_standalone.py
    ├── test_database_transactions.py
    ├── test_db_isolated.py
    ├── test_db_minimal.py
    ├── test_domain_entities.py
    ├── test_edge_cases_comprehensive.py
    ├── test_email_service.py
    ├── test_end_to_end.py
    ├── test_enhanced_ai_service.py
    ├── test_enhanced_backend.py
    ├── test_enterprise_security.py
    ├── test_error_handling.py
    ├── test_generated_functions.py
    ├── test_init_db.py
    ├── test_irt_validation.py
    ├── test_llm_sanitization_integration.py
    ├── test_llm_sanitization_sql.py
    ├── test_llm_sanitization_ssrf.py
    ├── test_llm_sanitization_xss.py
    ├── test_logging_improvements.py
    ├── test_logging_improvements_simple.py
    ├── test_main_clean.py
    ├── test_migrate.py
    ├── test_models.py
    ├── test_nlp_service.py
    ├── test_onboarding_fast.py
    ├── test_onboarding_functional.py
    ├── test_onboarding_service_layer.py
    ├── test_onboarding_test_runner.py
    ├── test_penetration_security.py
    ├── test_performance_optimizations.py
    ├── test_psychometric_service.py
    ├── test_race_conditions.py
    ├── test_race_conditions_standalone.py
    ├── test_rapid_submission_handling.py
    ├── test_rate_limiter.py
    ├── test_rate_limiter_improved.py
    ├── test_refactored_services.py
    ├── test_response_service.py
    ├── test_security.py
    ├── test_security_automated.py
    ├── test_security_comprehensive.py
    ├── test_security_headers.py
    ├── test_security_integration.py
    ├── test_security_validations.py
    ├── test_seed_scoring_templates.py
    ├── test_seed_templates.py
    ├── test_serialization.py
    ├── test_services_comprehensive.py
    ├── test_simple_team_assessment.py
    ├── test_suite.py
    ├── test_supply_chain_security.py
    ├── test_team_assessment_creation.py
    ├── test_team_assessment_creation_manual.py
    ├── test_team_optimization.py
    ├── test_team_optimization_fixed.py
    ├── test_team_personality_service.py
    ├── test_teams.py
    ├── test_template_service.py
    ├── test_transaction_rollback.py
    ├── test_update_response_tables.py
    ├── test_users_secure.py
    ├── timezone
    ├── unit
    └── verify_clinical_screening.py

259 directories, 1318 files
