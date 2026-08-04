// src/routes/ProtectedRoutes.tsx - Examples of protected route configurations
// This file demonstrates how to use ProtectedRoute in your routing setup

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import RequireAuth from '../components/RequireAuth';
import DashboardLayout from '../components/layout/DashboardLayout';
import { ProtectedRoute, UnauthorizedPage } from '../components/auth/ProtectedRoute';

// Example: Import your page components
import Dashboard from '../pages/Dashboard';
import HRISConnector from '../pages/HRISConnector';
import BehavioralAnalytics from '../pages/BehavioralAnalytics';
import AdminPanel from '../pages/AdminPanel'; // Example admin page

/**
 * PROTECTED ROUTES EXAMPLE
 *
 * Copy these patterns into your App.tsx to implement role-based route protection
 */

export const ProtectedRoutesExample: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

      {/* Protected Routes - Require Authentication */}
      <Route element={<RequireAuth />}>
        <Route element={<DashboardLayout />}>
          {/* Routes accessible to ALL authenticated users */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/icon-gallery" element={<IconGallery />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/settings" element={<Settings />} />

          {/* Clinical Routes - All authenticated users */}
          <Route path="/clinical-assessments" element={<ClinicalAssessments />} />
          <Route path="/screening/phq9" element={<PHQ9Screening />} />
          <Route path="/screening/gad7" element={<GAD7Screening />} />
          <Route path="/my-responses" element={<MyResponses />} />

          {/* HR/Manager Only Routes */}
          <Route
            path="/hris-connector"
            element={
              <ProtectedRoute requireHR>
                <HRISConnector />
              </ProtectedRoute>
            }
          />

          <Route
            path="/behavioral-analytics"
            element={
              <ProtectedRoute requireHR>
                <BehavioralAnalytics />
              </ProtectedRoute>
            }
          />

          <Route
            path="/burnout-prevention"
            element={
              <ProtectedRoute requireHR>
                <BurnoutPrevention />
              </ProtectedRoute>
            }
          />

          <Route
            path="/email-connector"
            element={
              <ProtectedRoute allowedRoles={['hr', 'admin', 'super_admin', 'manager']}>
                <EmailConnector />
              </ProtectedRoute>
            }
          />

          {/* Admin Only Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <AdminPanel />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={['admin', 'super_admin']}>
                <UserManagement />
              </ProtectedRoute>
            }
          />

          {/* Super Admin Only Routes */}
          <Route
            path="/super-admin/system"
            element={
              <ProtectedRoute allowedRoles={['super_admin']}>
                <SystemConfiguration />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Route>
    </Routes>
  );
};

/**
 * USAGE GUIDE: Adding ProtectedRoute to your existing App.tsx
 *
 * Step 1: Import the component
 * import { ProtectedRoute } from './components/auth/ProtectedRoute';
 *
 * Step 2: Wrap protected routes
 * <Route
 *   path="/hris-analytics"
 *   element={
 *     <ProtectedRoute requireHR>
 *       <HRISAnalytics />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * Step 3: That's it! The route is now protected
 */

/**
 * COMMON PROTECTION PATTERNS
 *
 * Pattern 1: HR/Manager Only
 * <ProtectedRoute requireHR>
 *   <HROnlyComponent />
 * </ProtectedRoute>
 *
 * Pattern 2: Admin Only
 * <ProtectedRoute requireAdmin>
 *   <AdminOnlyComponent />
 * </ProtectedRoute>
 *
 * Pattern 3: Specific Roles
 * <ProtectedRoute allowedRoles={['admin', 'super_admin']}>
 *   <AdminOrSuperAdminComponent />
 * </ProtectedRoute>
 *
 * Pattern 4: Manager and above
 * <ProtectedRoute requireManager>
 *   <ManagerAndAboveComponent />
 * </ProtectedRoute>
 *
 * Pattern 5: Custom fallback path
 * <ProtectedRoute
 *   requireHR
 *   fallbackPath="/access-denied"
 * >
 *   <HRComponent />
 * </ProtectedRoute>
 */

/**
 * QUICK REFERENCE: ProtectedRoute Props
 *
 * @param children - The component to render if user has access
 * @param allowedRoles - Array of roles that can access (e.g., ['hr', 'admin'])
 * @param requireHR - If true, only HR/Manager/Admin can access
 * @param requireAdmin - If true, only Admin/Super Admin can access
 * @param requireManager - If true, only Manager/HR/Admin can access
 * @param fallbackPath - Where to redirect if no access (default: '/unauthorized')
 */

export default ProtectedRoutesExample;
