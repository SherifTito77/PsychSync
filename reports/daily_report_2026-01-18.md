# Daily Monitoring Report - 2026-01-18

**Day of Monitoring:** 365
**Date:** 2026-01-18
**Status:** Monitoring Active

## Validation Status


================================================================================
DATABASE QUERY OPTIMIZATION VALIDATION
================================================================================
Database: localhost:5432/psychsync_db

================================================================================
Checking Composite Indexes...
================================================================================
  ✅ team_members.idx_team_members_team_user
  ✅ team_members.idx_team_members_user_created
  ✅ team_members.idx_team_members_team_role
  ✅ responses.idx_responses_user_assessment
  ✅ assessments.idx_assessments_org_created
  ✅ teams.idx_teams_org_created

Summary: 6/6 indexes found

================================================================================
Checking Index Usage...
================================================================================

Top 20 indexes by usage:
  build_failures.idx_build_failures_resolved:
    - Scans: 50
    - Tuples read: 0
    - Tuples fetched: 0
  breaking_changes.idx_breaking_changes_approved:
    - Scans: 15
    - Tuples read: 0
    - Tuples fetched: 0
  churn_risk_scores.idx_churn_risk_overall:
    - Scans: 2
    - Tuples read: 0
    - Tuples fetched: 0
  teams.idx_teams_org:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  assessments.idx_assessments_org:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  assessment_responses.idx_assessment_responses_user:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  team_members.idx_team_members_user:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  users.idx_users_two_factor_enabled:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  email_metadata.idx_email_metadata_thread_date:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  email_metadata.idx_email_metadata_subject_hash:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  email_metadata.idx_email_metadata_sender_date:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  email_metadata.idx_email_metadata_folder:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  communication_analyses.idx_comm_analysis_conflict:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  communication_analyses.idx_comm_analysis_style:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  communication_analyses.idx_comm_analysis_urgency:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  communication_analyses.idx_comm_analysis_sentiment:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  communication_analyses.idx_comm_analysis_user_date:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  email_metadata.idx_email_metadata_connection_sent:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  ab_experiments.idx_ab_experiments_name:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0
  assessment_responses.idx_assessment_responses_assessment:
    - Scans: 0
    - Tuples read: 0
    - Tuples fetched: 0

❌ Error checking index usage: dictionary update sequence element #0 has length 6; 2 is required

================================================================================
Checking Query Performance...
================================================================================

  Testing: Team member lookup
    ⚠️  Expected Index Scan not found
    ⏱️  Execution Time: 0.052 ms

  Testing: User's teams
    ✅ Using Nested Loop
    ⏱️  Execution Time: 0.033 ms

  Testing: Team members count
    ✅ Using Aggregate
    ⏱️  Execution Time: 0.191 ms

================================================================================
Checking Pagination Limits...
================================================================================
  ✅ All pagination limits are within acceptable range

================================================================================
VALIDATION SUMMARY
================================================================================
✅ Indexes: All 6 indexes present
✅ Pagination: All limits acceptable

Overall Status: ✅ PASS

## Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Indexes Created | 6 | ✅ |
| Validation | PASS | ✅ |
| Tests | 8/8 | ✅ |

## Observations

<!-- Add your observations here -->

## Issues Found

<!-- Document any issues found during monitoring -->

## Next Actions

<!-- Add any follow-up actions needed -->
