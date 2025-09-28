
// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTeam } from '../contexts/TeamContext';
import { DashboardData } from '../types';
import Button from '../components/Button';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { teams, fetchTeams } = useTeam();
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    totalTeams: 0,
    totalAssessments: 0,
    avgCompatibility: 0.85,
    predictedVelocity: 42
  });

  useEffect(() => {
    fetchTeams();
  }, []);

  useEffect(() => {
    setDashboardData({
      totalTeams: teams.length,
      totalAssessments: 12,
      avgCompatibility: 0.85,
      predictedVelocity: 42
    });
  }, [teams]);

  const statCards = [
    {
      title: 'Total Teams',
      value: dashboardData.totalTeams,
      icon: '👥',
      color: 'bg-blue-500'
    },
    {
      title: 'Assessments',
      value: dashboardData.totalAssessments,
      icon: '📊',
      color: 'bg-green-500'
    },
    {
      title: 'Avg Compatibility',
      value: `${Math.round(dashboardData.avgCompatibility * 100)}%`,
      icon: '🤝',
      color: 'bg-purple-500'
    },
    {
      title: 'Predicted Velocity',
      value: `${dashboardData.predictedVelocity} SP`,
      icon: '⚡',
      color: 'bg-yellow-500'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's an overview of your team optimization platform.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{card.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${card.color} bg-opacity-10`}>
                <span className="text-2xl">{card.icon}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button className="justify-center">Create New Team</Button>
          <Button className="justify-center" variant="secondary">Run Assessment</Button>
          <Button className="justify-center" variant="secondary">Optimize Teams</Button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          <div className="flex items-center text-sm text-gray-600">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
            Team "Frontend Squad" completed MBTI assessment
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
            New optimization suggestion for "Backend Team"
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
            Analytics report generated for Q4 2024
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;