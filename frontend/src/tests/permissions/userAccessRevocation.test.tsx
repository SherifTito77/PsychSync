// frontend/src/tests/permissions/userAccessRevocation.test.tsx
/**
 * User Access Revocation Testing
 * Tests for account deactivation, permission removal, and access control
 * Business Impact: Security compliance, data protection, access management
 * ROI: 6x - Ensures immediate access control when needed
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';

// Mock user management service
const mockUserService = {
  deactivateUser: vi.fn(),
  revokeAccess: vi.fn(),
  suspendUser: vi.fn(),
  deleteUserData: vi.fn(),
  getUserAccess: vi.fn(),
  updateUserPermissions: vi.fn(),
};

// Test component for user access management
const UserAccessManager: React.FC<{ user: any; currentAdmin: any }> = ({ user, currentAdmin }) => {
  const [accessStatus, setAccessStatus] = React.useState(user.active ? 'active' : 'inactive');
  const [revocationReason, setRevocationReason] = React.useState('');
  const [effectiveDate, setEffectiveDate] = React.useState('immediate');

  const hasPermissionToRevoke = currentAdmin.permissions.includes('revoke_user_access');
  const canDeleteData = currentAdmin.permissions.includes('delete_user_data');

  const handleRevokeAccess = async () => {
    try {
      await mockUserService.revokeAccess({
        userId: user.id,
        reason: revocationReason,
        effectiveDate,
        revokedBy: currentAdmin.id
      });
      setAccessStatus('revoked');
    } catch (error) {
      console.error('Failed to revoke access:', error);
    }
  };

  const handleDeactivateUser = async () => {
    try {
      await mockUserService.deactivateUser({
        userId: user.id,
        reason: revocationReason,
        revokedBy: currentAdmin.id
      });
      setAccessStatus('deactivated');
    } catch (error) {
      console.error('Failed to deactivate user:', error);
    }
  };

  return (
    <div data-testid="user-access-manager">
      <h3>Access Management for {user.name}</h3>

      <div data-testid="current-access-status">
        <p>Current Status: <strong>{accessStatus}</strong></p>
        <p>Role: {user.role}</p>
        <p>Last Login: {user.lastLogin}</p>
      </div>

      {hasPermissionToRevoke && accessStatus === 'active' && (
        <div data-testid="revocation-controls">
          <h4>Revoke Access</h4>

          <div data-testid="revocation-reason">
            <label>Reason for revocation:</label>
            <select
              value={revocationReason}
              onChange={(e) => setRevocationReason(e.target.value)}
              data-testid="reason-select"
            >
              <option value="">Select reason...</option>
              <option value="policy_violation">Policy Violation</option>
              <option value="security_breach">Security Breach</option>
              <option value="contract_ended">Contract Ended</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div data-testid="effective-date">
            <label>Effective Date:</label>
            <select
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
              data-testid="effective-date-select"
            >
              <option value="immediate">Immediate</option>
              <option value="end_of_day">End of Day</option>
              <option value="custom">Custom Date</option>
            </select>
          </div>

          <button
            onClick={handleRevokeAccess}
            disabled={!revocationReason}
            data-testid="revoke-access-button"
          >
            Revoke Access
          </button>

          <button
            onClick={handleDeactivateUser}
            disabled={!revocationReason}
            data-testid="deactivate-user-button"
          >
            Deactivate User
          </button>
        </div>
      )}

      {canDeleteData && accessStatus !== 'active' && (
        <div data-testid="data-deletion">
          <h4>Data Management</h4>
          <button
            onClick={() => mockUserService.deleteUserData(user.id)}
            data-testid="delete-user-data"
          >
            Delete User Data
          </button>
        </div>
      )}

      {!hasPermissionToRevoke && (
        <div data-testid="permission-denied">
          <p>You don't have permission to manage this user's access.</p>
        </div>
      )}
    </div>
  );
};

describe('User Access Revocation Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should allow admin to revoke user access with reason', async () => {
    const testUser = {
      id: 'user-1',
      name: 'John Doe',
      role: 'user',
      active: true,
      lastLogin: '2024-12-15'
    };

    const adminUser = {
      id: 'admin-1',
      permissions: ['revoke_user_access', 'delete_user_data']
    };

    render(<UserAccessManager user={testUser} currentAdmin={adminUser} />);

    expect(screen.getByTestId('current-access-status')).toHaveTextContent('active');

    await userEvent.selectOptions(screen.getByTestId('reason-select'), 'policy_violation');
    await userEvent.click(screen.getByTestId('revoke-access-button'));

    await waitFor(() => {
      expect(mockUserService.revokeAccess).toHaveBeenCalledWith({
        userId: 'user-1',
        reason: 'policy_violation',
        effectiveDate: 'immediate',
        revokedBy: 'admin-1'
      });
    });
  });

  it('should restrict access revocation for users without permissions', () => {
    const testUser = {
      id: 'user-1',
      name: 'John Doe',
      role: 'user',
      active: true
    };

    const regularUser = {
      id: 'regular-1',
      permissions: ['view_data']
    };

    render(<UserAccessManager user={testUser} currentAdmin={regularUser} />);

    expect(screen.getByTestId('permission-denied')).toBeInTheDocument();
    expect(screen.queryByTestId('revocation-controls')).not.toBeInTheDocument();
  });

  it('should require reason for access revocation', async () => {
    const testUser = { id: 'user-1', name: 'John', active: true };
    const adminUser = { id: 'admin-1', permissions: ['revoke_user_access'] };

    render(<UserAccessManager user={testUser} currentAdmin={adminUser} />);

    const revokeButton = screen.getByTestId('revoke-access-button');
    expect(revokeButton).toBeDisabled();

    await userEvent.selectOptions(screen.getByTestId('reason-select'), 'security_breach');
    expect(revokeButton).not.toBeDisabled();
  });

  it('should handle immediate vs scheduled revocation', async () => {
    const testUser = { id: 'user-1', name: 'John', active: true };
    const adminUser = { id: 'admin-1', permissions: ['revoke_user_access'] };

    render(<UserAccessManager user={testUser} currentAdmin={adminUser} />);

    await userEvent.selectOptions(screen.getByTestId('reason-select'), 'contract_ended');
    await userEvent.selectOptions(screen.getByTestId('effective-date-select'), 'end_of_day');
    await userEvent.click(screen.getByTestId('revoke-access-button'));

    await waitFor(() => {
      expect(mockUserService.revokeAccess).toHaveBeenCalledWith(
        expect.objectContaining({
          effectiveDate: 'end_of_day'
        })
      );
    });
  });
});