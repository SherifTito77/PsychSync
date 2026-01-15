// frontend/src/pages/admin/ExperimentManagementPage.tsx
/**
 * Experiment Management Page
 *
 * Admin page for product operations - A/B testing and feature request management
 */
import React from 'react';
import ExperimentManagementDashboard from '../../components/admin/ExperimentManagementDashboard';

const ExperimentManagementPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ExperimentManagementDashboard />
      </div>
    </div>
  );
};

export default ExperimentManagementPage;
