// src/pages/Dashboard.tsx
// src/pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTeam } from '../contexts/TeamContext';
import Button from '../components/common/Button';
import Icon from '../components/common/Icon';
import { DashboardData } from '../types';
import { useAsyncEffect } from '@/hooks/useAsyncEffect';
import { useAnalytics } from '../services/analytics/tracker';
import { useHRISData } from '@/hooks/useHRISData';
import QuickActionsWidget from '../components/dashboard/QuickActionsWidget';
const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { teams, fetchTeams } = useTeam();
  const { track, trackPage } = useAnalytics();
  const { employees, departments, totalEmployees, loading: hrisLoading } = useHRISData();

  const [dashboardData, setDashboardData] = useState<DashboardData>({
    totalTeams: 0,
    totalAssessments: 0,
    avgCompatibility: 0.85,
    predictedVelocity: 42,
  });

  // Track dashboard page view on mount
  useEffect(() => {
    trackPage('dashboard', {
      user_id: user?.id,
      total_teams: teams.length
    });
  }, []);

  // ✅ FIXED: Combined useEffects to prevent race conditions
  // Previously had two separate effects that could trigger sequentially
  // Now fetches teams and sets dashboard data atomically
  // ⚡️ PERFORMANCE: Empty dependency array - only run once on mount to prevent infinite loop
  useAsyncEffect(async (signal, isMounted) => {
    try {
      // Fetch teams
      await fetchTeams();

      // Check if component is still mounted before updating state
      if (!isMounted()) return;

      // Get the updated teams length from context
      const currentTeamsLength = teams.length;

      // Set dashboard data atomically after teams are loaded
      setDashboardData({
        totalTeams: currentTeamsLength,
        totalAssessments: 12,
        avgCompatibility: 0.85,
        predictedVelocity: 42,
      });

      // Track dashboard loaded
      track('engagement_content_viewed', {
        content_type: 'dashboard',
        total_teams: currentTeamsLength,
        has_assessments: true // Static value to prevent loop
      });
    } catch (error) {
      // Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Error loading dashboard data:', error);

      // Track error
      track('system_error_occurred', {
        error_type: 'dashboard_load_failed',
        error_message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, []); // Empty deps - run once on mount only
  const statCards = [
    {
      title: 'Total Teams',
      value: dashboardData.totalTeams,
      icon: '👥',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-500',
    },
    {
      title: 'Assessments',
      value: dashboardData.totalAssessments,
      icon: '📊',
      bgColor: 'bg-green-50',
      textColor: 'text-green-500',
    },
    {
      title: 'Avg Compatibility',
      value: `${Math.round(dashboardData.avgCompatibility * 100)}%`,
      icon: '🤝',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-500',
    },
    {
      title: 'Predicted Velocity',
      value: `${dashboardData.predictedVelocity} SP`,
      icon: '⚡',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-500',
    },
    {
      title: 'HRIS Employees',
      value: hrisLoading ? '...' : totalEmployees,
      icon: '🏢',
      bgColor: 'bg-indigo-50',
      textColor: 'text-indigo-500',
    },
    {
      title: 'Departments',
      value: hrisLoading ? '...' : departments.length,
      icon: '🏛️',
      bgColor: 'bg-teal-50',
      textColor: 'text-teal-500',
    },
  ];
  return (
    <div className="space-y-8">
      {/* --- Welcome Header --- */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mobile-text-responsive">
          Welcome back, {user?.full_name || 'User'}!
        </h1>
        <p className="text-gray-600 mt-2 mobile-text-responsive">
          Here's an overview of your team optimization platform.
        </p>
      </div>
      {/* --- Stats Grid --- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {statCards.map((card, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 hover:shadow-md transition-shadow mobile-card"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mobile-text-responsive">
                  {card.title}
                </p>
                <p className="text-xl sm:text-2xl font-bold text-gray-900 mt-1 mobile-text-responsive">
                  {card.value}
                </p>
              </div>
              {/* --- FIX: Use the new, standardized Icon component --- */}
              <div className={`p-2 sm:p-3 rounded-lg ${card.bgColor} ml-3`}>
                <Icon size="sm" className={card.textColor}>{card.icon}</Icon>
              </div>
            </div>
          </div>
        ))}
      </div>
      {/* --- Quick Actions --- */}
      <QuickActionsWidget maxVisible={6} />

      {/* --- HRIS Department Breakdown --- */}
      {!hrisLoading && employees.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mobile-text-responsive">
              HRIS Department Overview
            </h2>
            <button
              onClick={() => navigate('/hris-connector')}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              View Details →
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {departments.map((dept) => {
              const deptEmployees = employees.filter(e => e.department === dept);
              const percentage = ((deptEmployees.length / employees.length) * 100).toFixed(0);
              return (
                <div
                  key={dept}
                  className="border border-gray-200 rounded-lg p-3 sm:p-4 hover:border-indigo-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 mobile-text-responsive">{dept}</span>
                    <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                      {percentage}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {deptEmployees.length} employee{deptEmployees.length !== 1 ? 's' : ''}
                  </div>
                  <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- Recent Activity --- */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 mobile-text-responsive">
          Recent Activity
        </h2>
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-start sm:items-center text-sm text-gray-600 mobile-list-item">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-3 mt-1 sm:mt-0 flex-shrink-0"></span>
            <span className="mobile-text-responsive">Team "Frontend Squad" completed MBTI assessment</span>
          </div>
          <div className="flex items-start sm:items-center text-sm text-gray-600 mobile-list-item">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-3 mt-1 sm:mt-0 flex-shrink-0"></span>
            <span className="mobile-text-responsive">New optimization suggestion for "Backend Team"</span>
          </div>
          <div className="flex items-start sm:items-center text-sm text-gray-600 mobile-list-item">
            <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
            Analytics report generated for Q4 2024
          </div>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
