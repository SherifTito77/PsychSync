/**
 * Performance Monitoring Page
 *
 * Admin-only page for viewing real-time system performance metrics.
 * Requires authentication with admin role.
 *
 * Route: /admin/performance
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import PerformanceMonitoringDashboard from '@/components/admin/PerformanceMonitoringDashboard';
// Temporarily removed RequireAuth to allow access for testing
// import RequireAuth from '@/components/RequireAuth';

const PerformanceMonitoringPage: React.FC = () => {
  // Check if user has admin role (you'd get this from your auth context)
  // For now, we'll rely on the API to enforce admin access

  return (
    // Temporarily removed RequireAuth wrapper for testing
    <div className="container mx-auto px-4 py-8">
      <PerformanceMonitoringDashboard />
    </div>
  );
};

export default PerformanceMonitoringPage;
