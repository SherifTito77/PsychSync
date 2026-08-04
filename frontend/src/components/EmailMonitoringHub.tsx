import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  CalendarDays,
  AlertTriangle,
  Users,
  Smile
} from 'lucide-react';

/**
 * EmailMonitoringHub - Landing page for Email Monitoring section
 * Provides navigation to all 4 email monitoring enhancement features
 */
const EmailMonitoringHub: React.FC = () => {
  console.log('📧 EmailMonitoringHub component rendering!');

  const features = [
    {
      name: 'Scheduled Reports',
      path: '/scheduled-reports',
      icon: CalendarDays,
      description: 'Automated weekly and monthly email reports with customizable recipients and formats.',
      color: 'blue'
    },
    {
      name: 'Anomaly Detection',
      path: '/anomaly-detection',
      icon: AlertTriangle,
      description: 'ML-powered pattern detection identifying unusual email behaviors and potential issues.',
      color: 'yellow'
    },
    {
      name: 'Team Dashboard',
      path: '/team-dashboard',
      icon: Users,
      description: 'Comprehensive team analytics with performance metrics and member comparisons.',
      color: 'green'
    },
    {
      name: 'Sentiment Analysis',
      path: '/sentiment-analysis',
      icon: Smile,
      description: 'Email tone and emotion analysis to understand communication patterns.',
      color: 'purple'
    }
  ];

  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 hover:bg-yellow-500/20',
    green: 'bg-green-500/10 border-green-500/20 hover:bg-green-500/20',
    purple: 'bg-purple-500/10 border-purple-500/20 hover:bg-purple-500/20'
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">📧 Email Monitoring</h1>
        <p className="text-indigo-100 text-lg">
          Advanced analytics and monitoring tools for your email integration
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <NavLink
              key={feature.path}
              to={feature.path}
              className={`block p-6 rounded-lg border-2 transition-all duration-200 ${colorClasses[feature.color as keyof typeof colorClasses]}`}
            >
              <div className="flex items-start space-x-4">
                <div className={`p-3 rounded-lg bg-${feature.color}-500/20`}>
                  <Icon className="w-8 h-8 text-${feature.color}-500" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.name}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
              </div>
            </NavLink>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-3xl font-bold text-indigo-400 mb-1">4</div>
          <div className="text-gray-400">Active Features</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-3xl font-bold text-green-400 mb-1">Real-time</div>
          <div className="text-gray-400">Monitoring</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-3xl font-bold text-purple-400 mb-1">ML-Powered</div>
          <div className="text-gray-400">Analytics</div>
        </div>
      </div>
    </div>
  );
};

export default EmailMonitoringHub;
