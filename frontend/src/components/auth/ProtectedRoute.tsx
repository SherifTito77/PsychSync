// src/components/auth/ProtectedRoute.tsx - Route-level role protection
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useRoleNavigation } from '../../hooks/useRoleNavigation';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
  requireHR?: boolean;
  requireAdmin?: boolean;
  requireManager?: boolean;
  fallbackPath?: string;
}

/**
 * ProtectedRoute Component
 *
 * Wraps routes to restrict access based on user roles.
 * Use this to protect pages that should only be accessible to certain roles.
 *
 * @example
 * // HR-only page
 * <ProtectedRoute requireHR>
 *   <HRISDashboard />
 * </ProtectedRoute>
 *
 * @example
 * // Multiple allowed roles
 * <ProtectedRoute allowedRoles={['admin', 'hr']}>
 *   <AdminPanel />
 * </ProtectedRoute>
 *
 * @example
 * // Custom fallback
 * <ProtectedRoute requireAdmin fallbackPath="/access-denied">
 *   <SuperAdminPanel />
 * </ProtectedRoute>
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  requireHR = false,
  requireAdmin = false,
  requireManager = false,
  fallbackPath = '/unauthorized',
}) => {
  const location = useLocation();
  const { isHR, isAdmin, userRole } = useRoleNavigation();

  // Check if user has access
  const hasAccess = React.useMemo(() => {
    // If no requirements, allow access
    if (!allowedRoles && !requireHR && !requireAdmin && !requireManager) {
      return true;
    }

    // Check explicit allowed roles
    if (allowedRoles && allowedRoles.length > 0) {
      return allowedRoles.includes(userRole);
    }

    // Check role requirements
    if (requireAdmin && !isAdmin) {
      return false;
    }

    if (requireHR && !isHR) {
      return false;
    }

    if (requireManager && !['hr', 'admin', 'super_admin', 'manager'].includes(userRole)) {
      return false;
    }

    return true;
  }, [allowedRoles, requireHR, requireAdmin, requireManager, userRole, isHR, isAdmin]);

  if (!hasAccess) {
    // Save the location they were trying to go to for redirect after login
    return (
      <Navigate
        to={fallbackPath}
        state={{ from: location, requiredRoles: allowedRoles }}
        replace
      />
    );
  }

  return <>{children}</>;
};

/**
 * Unauthorized Page Component
 *
 * Shown when a user tries to access a page they don't have permission for.
 */
export const UnauthorizedPage: React.FC = () => {
  const location = useLocation();
  const { userRole, isHR, isAdmin } = useRoleNavigation();

  const state = location.state as { from?: Location; requiredRoles?: string[] } | null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">🔒</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600 mb-6">
            You don't have permission to access this page.
          </p>

          {/* User's current role */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600 mb-2">Your current role:</p>
            <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
              isAdmin
                ? 'bg-orange-100 text-orange-700'
                : isHR
                ? 'bg-purple-100 text-purple-700'
                : 'bg-blue-100 text-blue-700'
            }`}>
              {userRole === 'super_admin'
                ? 'Super Admin'
                : userRole === 'admin'
                ? 'Administrator'
                : userRole === 'hr'
                ? 'HR Manager'
                : userRole === 'manager'
                ? 'Manager'
                : userRole === 'employee'
                ? 'Employee'
                : 'User'}
            </div>
          </div>

          {/* Required roles (if available) */}
          {state?.requiredRoles && (
            <div className="bg-red-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-red-700 mb-2">This page requires:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {state.requiredRoles.map((role) => (
                  <span
                    key={role}
                    className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium"
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="space-y-3">
            <a
              href="/dashboard"
              className="block w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Go to Dashboard
            </a>
            <button
              onClick={() => window.history.back()}
              className="block w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Go Back
            </button>
          </div>

          {/* Help text */}
          <p className="text-xs text-gray-500 mt-6">
            If you believe this is an error, please contact your administrator
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * RoleGate Component
 *
 * Conditionally renders children based on role, but doesn't redirect.
 * Useful for showing/hiding specific UI elements within a page.
 *
 * @example
 * <RoleGate requireHR>
 *   <HROnlyButton />
 * </RoleGate>
 */
export const RoleGate: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  requireHR = false,
  requireAdmin = false,
  requireManager = false,
}) => {
  const { isHR, isAdmin, userRole } = useRoleNavigation();

  const hasAccess = React.useMemo(() => {
    if (!allowedRoles && !requireHR && !requireAdmin && !requireManager) {
      return true;
    }

    if (allowedRoles && allowedRoles.length > 0) {
      return allowedRoles.includes(userRole);
    }

    if (requireAdmin && !isAdmin) return false;
    if (requireHR && !isHR) return false;
    if (requireManager && !['hr', 'admin', 'super_admin', 'manager'].includes(userRole)) {
      return false;
    }

    return true;
  }, [allowedRoles, requireHR, requireAdmin, requireManager, userRole, isHR, isAdmin]);

  if (!hasAccess) {
    return null;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
