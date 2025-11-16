// src/pages/Assessments.tsx - Assessments Page
import React, { useState } from 'react';
import Button from '../components/common/Button';
interface Assessment {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'available' | 'completed' | 'in_progress';
}
const Assessments: React.FC = () => {
  const [assessments] = useState<Assessment[]>([
    {
      id: 'mbti',
      name: 'MBTI Assessment',
      description: 'Myers-Briggs Type Indicator - Understand your personality preferences',
      icon: '🧭',
      status: 'available'
    },
    {
      id: 'big_five',
      name: 'Big Five Personality',
      description: 'Five-factor model of personality traits',
      icon: '📊',
      status: 'completed'
    },
    {
      id: 'enneagram',
      name: 'Enneagram',
      description: 'Nine personality types and their motivations',
      icon: '⭐',
      status: 'available'
    },
    {
      id: 'strengths',
      name: 'StrengthsFinder',
      description: 'Discover your top 5 strengths and talents',
      icon: '💪',
      status: 'in_progress'
    },
    {
      id: 'disc',
      name: 'DISC Assessment',
      description: 'Behavioral assessment for communication styles',
      icon: '🎯',
      status: 'available'
    },
    {
      id: 'predictive_index',
      name: 'Predictive Index',
      description: 'Behavioral drives and motivations',
      icon: '🔮',
      status: 'available'
    }
  ]);
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };
  const getButtonText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'View Results';
      case 'in_progress':
        return 'Continue';
      default:
        return 'Start Assessment';
    }
  };
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Personality Assessments</h1>
          <p className="text-gray-600 mt-2">
            Complete assessments to build your comprehensive personality profile
          </p>
        </div>
        <Button variant="secondary">View My Profile</Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {assessments.map((assessment) => (
          <div
            key={assessment.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="text-3xl">{assessment.icon}</div>
              <span
                className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                  assessment.status
                )}`}
              >
                {assessment.status === 'in_progress'
                  ? 'In Progress'
                  : assessment.status === 'completed'
                  ? 'Completed'
                  : 'Available'}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {assessment.name}
            </h3>
            <p className="text-gray-600 mb-6 text-sm">{assessment.description}</p>
            <div className="flex space-x-2">
              <Button
                size="small"
                variant={assessment.status === 'completed' ? 'secondary' : 'primary'}
                className="flex-1"
              >
                {getButtonText(assessment.status)}
              </Button>
              {assessment.status === 'completed' && (
                <Button size="small" variant="secondary">
                  Retake
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
        <div className="flex items-start">
          <div className="text-2xl mr-4">💡</div>
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              Complete Multiple Assessments
            </h3>
            <p className="text-blue-800 mb-4">
              Taking multiple assessments gives you a more comprehensive and accurate
              personality profile. Our AI combines insights from different frameworks
              to provide better team optimization recommendations.
            </p>
            <Button size="small">Learn More About Our Approach</Button>
          </div>
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Assessment Progress
        </h3>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">Overall Completion</span>
          <span className="text-sm font-medium text-gray-900">33% (2 of 6)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: '33%' }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Complete 4 more assessments to unlock advanced team insights
        </p>
      </div>
    </div>
  );
};
export default Assessments;
// export default function Assessments() {
//   return <h1>Assessments Page</h1>;
// }
// // import React from "react";
// // const Assessments: React.FC = () => {
// //   return <h1>Assessments Page</h1>;
// // };
// // export default Assessments;
