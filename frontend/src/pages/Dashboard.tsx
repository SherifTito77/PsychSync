// src/pages/Dashboard.tsx
// src/pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTeam } from '../contexts/TeamContext';
import Button from '../components/common/Button';
import Icon from '../components/common/Icon';
import { DashboardData } from '../types';
const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { teams, fetchTeams } = useTeam();
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    totalTeams: 0,
    totalAssessments: 0,
    avgCompatibility: 0.85,
    predictedVelocity: 42,
  });
  useEffect(() => {
    fetchTeams();
  }, []);
  useEffect(() => {
    setDashboardData({
      totalTeams: teams.length,
      totalAssessments: 12,
      avgCompatibility: 0.85,
      predictedVelocity: 42,
    });
  }, [teams]);
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
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
                <Icon size="lg" className={card.textColor}>{card.icon}</Icon>
              </div>
            </div>
          </div>
        ))}
      </div>
      {/* --- Quick Actions --- */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 mobile-text-responsive">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          <Button className="mobile-touch-target" mobileLarge>Create New Team</Button>
          <Button className="mobile-touch-target" variant="secondary" mobileLarge>
            Run Assessment
          </Button>
          <Button className="mobile-touch-target" variant="secondary" mobileLarge>
            Optimize Teams
          </Button>
        </div>
      </div>
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
