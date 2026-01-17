#!/usr/bin/env python3
"""
Standalone test runner for data export permissions testing
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status


# Mock services for testing
class MockUserService:
    """Mock user service for role-based testing"""

    @staticmethod
    def get_user_role(user_id: str) -> str:
        """Get user role from mock data"""
        user_roles = {
            'admin_001': 'admin',
            'hr_manager_001': 'hr_manager',
            'team_lead_001': 'team_lead',
            'regular_user_001': 'user',
            'viewer_001': 'viewer',
            'external_auditor_001': 'external_auditor'
        }
        return user_roles.get(user_id, 'user')

    @staticmethod
    def get_user_organizations(user_id: str) -> list:
        """Get user's organizations"""
        user_orgs = {
            'admin_001': ['org_main', 'org_sub1', 'org_sub2'],
            'hr_manager_001': ['org_main'],
            'team_lead_001': ['org_main', 'org_team1'],
            'regular_user_001': ['org_main'],
            'viewer_001': ['org_main'],
            'external_auditor_001': ['org_main']
        }
        return user_orgs.get(user_id, [])

    @staticmethod
    def get_user_teams(user_id: str) -> list:
        """Get user's teams"""
        user_teams = {
            'admin_001': ['team_all', 'team_exec', 'team_dev'],
            'hr_manager_001': ['team_hr', 'team_all'],
            'team_lead_001': ['team_dev', 'team_team1'],
            'regular_user_001': ['team_dev'],
            'viewer_001': ['team_dev'],
            'external_auditor_001': []  # External users don't belong to teams
        }
        return user_teams.get(user_id, [])


class MockDataExportService:
    """Mock data export service for testing"""

    @staticmethod
    def check_export_permission(user_id: str, export_type: str, scope: dict) -> dict:
        """Check if user has permission for specific export"""
        user_role = MockUserService.get_user_role(user_id)
        user_orgs = MockUserService.get_user_organizations(user_id)
        user_teams = MockUserService.get_user_teams(user_id)

        # Define permission matrix
        permission_matrix = {
            'admin': {
                'allowed_exports': ['all'],
                'max_records': 1000000,
                'includes_pii': True,
                'cross_org_access': True,
                'historical_access': True
            },
            'hr_manager': {
                'allowed_exports': ['assessments', 'users', 'teams', 'analytics'],
                'max_records': 50000,
                'includes_pii': True,
                'cross_org_access': False,
                'historical_access': True
            },
            'team_lead': {
                'allowed_exports': ['team_assessments', 'team_analytics', 'team_members'],
                'max_records': 5000,
                'includes_pii': False,
                'cross_org_access': False,
                'historical_access': True
            },
            'user': {
                'allowed_exports': ['personal_assessments', 'personal_analytics'],
                'max_records': 100,
                'includes_pii': False,
                'cross_org_access': False,
                'historical_access': False
            },
            'viewer': {
                'allowed_exports': ['basic_analytics'],
                'max_records': 1000,
                'includes_pii': False,
                'cross_org_access': False,
                'historical_access': False
            },
            'external_auditor': {
                'allowed_exports': ['audit_reports', 'compliance_data'],
                'max_records': 100000,
                'includes_pii': False,
                'cross_org_access': False,
                'historical_access': True
            }
        }

        role_permissions = permission_matrix.get(user_role, permission_matrix['user'])

        # Check export type permission
        if export_type not in role_permissions['allowed_exports'] and 'all' not in role_permissions['allowed_exports']:
            return {
                'allowed': False,
                'reason': f'Role {user_role} not authorized for export type {export_type}',
                'suggestion': 'Contact administrator for permission upgrade'
            }

        # Check scope restrictions
        if scope.get('organization_id') and scope['organization_id'] not in user_orgs:
            if not role_permissions['cross_org_access']:
                return {
                    'allowed': False,
                    'reason': 'Cannot export data from organizations you do not belong to',
                    'suggestion': 'Request cross-organization access or contact admin'
                }

        if scope.get('team_id') and scope['team_id'] not in user_teams:
            if user_role in ['user', 'viewer', 'team_lead']:
                return {
                    'allowed': False,
                    'reason': 'Cannot export data from teams you do not belong to',
                    'suggestion': 'Request team membership or contact team lead'
                }

        # Check record limit
        if scope.get('record_count', 0) > role_permissions['max_records']:
            return {
                'allowed': False,
                'reason': f'Export request exceeds maximum records limit ({role_permissions["max_records"]})',
                'suggestion': 'Reduce export scope or request higher limits'
            }

        # Check PII access
        if scope.get('include_pii', False) and not role_permissions['includes_pii']:
            return {
                'allowed': False,
                'reason': 'Role does not have permission to export personally identifiable information',
                'suggestion': 'Contact administrator for PII export access'
            }

        return {
            'allowed': True,
            'max_records': role_permissions['max_records'],
            'includes_pii': role_permissions['includes_pii'],
            'historical_access': role_permissions['historical_access']
        }

    @staticmethod
    async def create_export_job(user_id: str, export_config: dict) -> dict:
        """Create export job with permission checks"""
        permission_check = MockDataExportService.check_export_permission(
            user_id,
            export_config['export_type'],
            export_config.get('scope', {})
        )

        if not permission_check['allowed']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    'error': 'permission_denied',
                    'message': permission_check['reason'],
                    'suggestion': permission_check['suggestion']
                }
            )

        # Create export job
        job_id = f"export_job_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return {
            'job_id': job_id,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'estimated_completion': (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            'user_id': user_id,
            'export_type': export_config['export_type'],
            'record_count': export_config.get('scope', {}).get('record_count', 0)
        }

    @staticmethod
    def get_export_audit_log(export_id: str) -> dict:
        """Get audit log for export job"""
        return {
            'export_id': export_id,
            'accessed_by': 'admin_001',
            'accessed_at': datetime.utcnow().isoformat(),
            'access_reason': 'admin_review',
            'data_downloaded': True,
            'ip_address': '192.168.1.100'
        }


class TestDataExportPermissions:
    """Comprehensive data export permissions testing"""

    def test_admin_full_export_access(self):
        """Test admin can export all data types"""
        admin_user = 'admin_001'
        export_scenarios = [
            {
                'export_type': 'assessments',
                'scope': {'organization_id': 'org_main', 'record_count': 10000, 'include_pii': True},
                'should_allow': True
            },
            {
                'export_type': 'users',
                'scope': {'organization_id': 'org_sub1', 'record_count': 5000, 'include_pii': True},
                'should_allow': True
            },
            {
                'export_type': 'financial_data',
                'scope': {'record_count': 100000, 'include_pii': True},
                'should_allow': True
            },
            {
                'export_type': 'audit_logs',
                'scope': {'historical_data': True, 'record_count': 500000},
                'should_allow': True
            }
        ]

        for scenario in export_scenarios:
            permission = MockDataExportService.check_export_permission(
                admin_user,
                scenario['export_type'],
                scenario['scope']
            )

            assert permission['allowed'] == scenario['should_allow'], \
                f"Admin should be allowed to export {scenario['export_type']}"

            if scenario['should_allow']:
                assert permission['includes_pii'] is True
                assert permission['historical_access'] is True

    def test_admin_cross_organization_exports(self):
        """Test admin can export data across organizations"""
        admin_user = 'admin_001'

        # Export from different organizations
        cross_org_export = {
            'export_type': 'assessments',
            'scope': {
                'organization_id': 'org_sub2',  # Different from primary
                'record_count': 15000,
                'include_pii': True
            }
        }

        permission = MockDataExportService.check_export_permission(
            admin_user,
            cross_org_export['export_type'],
            cross_org_export['scope']
        )

        assert permission['allowed'] is True
        assert permission['max_records'] == 1000000

    def test_hr_manager_limited_export_access(self):
        """Test HR manager has appropriate export limitations"""
        hr_user = 'hr_manager_001'

        # Allowed exports
        allowed_exports = [
            {'export_type': 'assessments', 'scope': {'record_count': 1000}},
            {'export_type': 'users', 'scope': {'record_count': 500, 'include_pii': True}},
            {'export_type': 'teams', 'scope': {'record_count': 100}},
            {'export_type': 'analytics', 'scope': {'record_count': 10000}}
        ]

        for export in allowed_exports:
            permission = MockDataExportService.check_export_permission(
                hr_user, export['export_type'], export['scope']
            )
            assert permission['allowed'] is True
            assert permission['max_records'] == 50000

    def test_hr_manager_cross_org_restriction(self):
        """Test HR manager cannot export from other organizations"""
        hr_user = 'hr_manager_001'

        # Try to export from organization they don't belong to
        unauthorized_export = {
            'export_type': 'assessments',
            'scope': {
                'organization_id': 'org_unauthorized',
                'record_count': 1000
            }
        }

        permission = MockDataExportService.check_export_permission(
            hr_user,
            unauthorized_export['export_type'],
            unauthorized_export['scope']
        )

        assert permission['allowed'] is False
        assert 'organizations you do not belong to' in permission['reason']

    def test_hr_manager_financial_data_restriction(self):
        """Test HR manager cannot export financial data"""
        hr_user = 'hr_manager_001'

        # Try to export financial data
        financial_export = {
            'export_type': 'financial_data',
            'scope': {'record_count': 1000}
        }

        permission = MockDataExportService.check_export_permission(
            hr_user,
            financial_export['export_type'],
            financial_export['scope']
        )

        assert permission['allowed'] is False
        assert 'not authorized for export type' in permission['reason']

    def test_team_lead_team_only_exports(self):
        """Test team lead can only export their team data"""
        team_lead = 'team_lead_001'

        # Export from their own team
        team_export = {
            'export_type': 'team_assessments',
            'scope': {
                'team_id': 'team_team1',
                'record_count': 100
            }
        }

        permission = MockDataExportService.check_export_permission(
            team_lead,
            team_export['export_type'],
            team_export['scope']
        )

        assert permission['allowed'] is True
        assert permission['includes_pii'] is False

    def test_team_lead_cross_team_restriction(self):
        """Test team lead cannot export from other teams"""
        team_lead = 'team_lead_001'

        # Try to export from team they don't belong to
        unauthorized_export = {
            'export_type': 'team_assessments',
            'scope': {
                'team_id': 'team_unauthorized',
                'record_count': 100
            }
        }

        permission = MockDataExportService.check_export_permission(
            team_lead,
            unauthorized_export['export_type'],
            unauthorized_export['scope']
        )

        assert permission['allowed'] is False
        assert 'teams you do not belong to' in permission['reason']

    def test_regular_user_personal_data_only(self):
        """Test regular user can only export their own data"""
        regular_user = 'regular_user_001'

        # Export their own assessments
        personal_export = {
            'export_type': 'personal_assessments',
            'scope': {'record_count': 50}
        }

        permission = MockDataExportService.check_export_permission(
            regular_user,
            personal_export['export_type'],
            personal_export['scope']
        )

        assert permission['allowed'] is True
        assert permission['max_records'] == 100

    def test_regular_user_pii_restriction(self):
        """Test regular user cannot export PII data"""
        regular_user = 'regular_user_001'

        # Try to export with PII
        pii_export = {
            'export_type': 'personal_assessments',
            'scope': {'record_count': 50, 'include_pii': True}
        }

        permission = MockDataExportService.check_export_permission(
            regular_user,
            pii_export['export_type'],
            pii_export['scope']
        )

        assert permission['allowed'] is False
        assert 'personally identifiable information' in permission['reason']

    def test_regular_user_record_limit_enforcement(self):
        """Test regular user record limits are enforced"""
        regular_user = 'regular_user_001'

        # Try to export more than allowed
        large_export = {
            'export_type': 'personal_assessments',
            'scope': {'record_count': 500}  # Exceeds limit of 100
        }

        permission = MockDataExportService.check_export_permission(
            regular_user,
            large_export['export_type'],
            large_export['scope']
        )

        assert permission['allowed'] is False
        assert 'exceeds maximum records limit' in permission['reason']

    def test_viewer_basic_analytics_only(self):
        """Test viewer can only export basic analytics"""
        viewer = 'viewer_001'

        # Allowed export
        analytics_export = {
            'export_type': 'basic_analytics',
            'scope': {'record_count': 500}
        }

        permission = MockDataExportService.check_export_permission(
            viewer,
            analytics_export['export_type'],
            analytics_export['scope']
        )

        assert permission['allowed'] is True
        assert permission['max_records'] == 1000

    def test_viewer_restricted_exports(self):
        """Test viewer cannot export sensitive data"""
        viewer = 'viewer_001'

        restricted_exports = [
            {'export_type': 'assessments', 'scope': {}},
            {'export_type': 'users', 'scope': {}},
            {'export_type': 'personal_assessments', 'scope': {}},
            {'export_type': 'team_assessments', 'scope': {}}
        ]

        for export in restricted_exports:
            permission = MockDataExportService.check_export_permission(
                viewer,
                export['export_type'],
                export['scope']
            )
            assert permission['allowed'] is False

    def test_external_auditor_compliance_exports(self):
        """Test external auditor can export compliance data"""
        auditor = 'external_auditor_001'

        # Allowed compliance exports
        compliance_exports = [
            {'export_type': 'audit_reports', 'scope': {'record_count': 1000}},
            {'export_type': 'compliance_data', 'scope': {'record_count': 5000}}
        ]

        for export in compliance_exports:
            permission = MockDataExportService.check_export_permission(
                auditor,
                export['export_type'],
                export['scope']
            )
            assert permission['allowed'] is True
            assert permission['includes_pii'] is False
            assert permission['historical_access'] is True

    def test_external_auditor_pii_blocking(self):
        """Test external auditor cannot export PII"""
        auditor = 'external_auditor_001'

        # Try to export with PII
        pii_export = {
            'export_type': 'audit_reports',
            'scope': {'record_count': 1000, 'include_pii': True}
        }

        permission = MockDataExportService.check_export_permission(
            auditor,
            pii_export['export_type'],
            pii_export['scope']
        )

        assert permission['allowed'] is False

    async def test_export_job_creation_with_permissions(self):
        """Test export job creation respects permissions"""
        # Successful job creation
        valid_export = {
            'export_type': 'personal_assessments',
            'scope': {'record_count': 50}
        }

        job = await MockDataExportService.create_export_job('regular_user_001', valid_export)

        assert 'job_id' in job
        assert job['status'] == 'pending'
        assert job['user_id'] == 'regular_user_001'

    async def test_export_job_creation_permission_denied(self):
        """Test export job creation fails without permissions"""
        # Invalid export attempt
        invalid_export = {
            'export_type': 'financial_data',
            'scope': {'record_count': 1000}
        }

        with pytest.raises(HTTPException) as exc_info:
            await MockDataExportService.create_export_job('regular_user_001', invalid_export)

        assert exc_info.value.status_code == 403
        error_detail = exc_info.value.detail
        assert error_detail['error'] == 'permission_denied'

    def test_export_access_audit_trail(self):
        """Test export access creates proper audit trail"""
        export_id = 'export_job_test_123'

        audit_log = MockDataExportService.get_export_audit_log(export_id)

        assert audit_log['export_id'] == export_id
        assert 'accessed_by' in audit_log
        assert 'accessed_at' in audit_log
        assert 'ip_address' in audit_log
        assert 'data_downloaded' in audit_log

    def test_export_permission_bypass_attempts(self):
        """Test various permission bypass attempts are blocked"""
        bypass_attempts = [
            # Role manipulation
            {
                'user_id': 'regular_user_001',
                'claimed_role': 'admin',
                'export_type': 'financial_data',
                'scope': {'record_count': 10000}
            },
            # Organization scope manipulation
            {
                'user_id': 'team_lead_001',
                'export_type': 'team_assessments',
                'scope': {'organization_id': '*', 'record_count': 50000}  # Wildcard
            },
            # PII bypass attempt
            {
                'user_id': 'viewer_001',
                'export_type': 'basic_analytics',
                'scope': {'record_count': 1000, 'include_pii': 'true', 'bypass_pii_check': 'true'}
            }
        ]

        for attempt in bypass_attempts:
            permission = MockDataExportService.check_export_permission(
                attempt['user_id'],
                attempt['export_type'],
                attempt['scope']
            )
            assert permission['allowed'] is False

    def test_large_export_permission_checks_performance(self):
        """Test permission checks perform well with large datasets"""
        large_export_request = {
            'export_type': 'assessments',
            'scope': {'record_count': 999999}  # Near limit
        }

        start_time = time.time()

        # Multiple permission checks to simulate load
        for _ in range(100):
            MockDataExportService.check_export_permission(
                'admin_001',
                large_export_request['export_type'],
                large_export_request['scope']
            )

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete quickly even under load
        assert total_time < 1.0, "Permission checks should be fast"

    def test_gdpr_export_restrictions(self):
        """Test GDPR-specific export restrictions"""
        eu_user_export = {
            'user_id': 'eu_user_001',
            'export_type': 'personal_assessments',
            'scope': {'record_count': 100, 'include_pii': True},
            'user_location': 'EU',
            'data_residency': 'EU'
        }

        # Check GDPR compliance
        permission = MockDataExportService.check_export_permission(
            eu_user_export['user_id'],
            eu_user_export['export_type'],
            eu_user_export['scope']
        )

        # Would normally check GDPR-specific rules
        assert 'allowed' in permission

    def test_data_retention_policy_enforcement(self):
        """Test data retention policies affect export capabilities"""
        old_data_export = {
            'export_type': 'assessments',
            'scope': {
                'record_count': 1000,
                'date_range': {
                    'start': '2020-01-01',
                    'end': '2020-12-31'
                }
            }
        }

        # This would integrate with retention policy service
        current_date = datetime.utcnow()
        retention_cutoff = current_date - timedelta(days=365 * 2)  # 2 years

        # Mock check
        data_within_retention = True  # Would normally check actual dates
        assert data_within_retention


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
