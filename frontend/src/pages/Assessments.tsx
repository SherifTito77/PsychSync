// src/pages/Assessments.tsx - Assessments Page
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/common/Button';
interface Assessment {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'available' | 'completed' | 'in_progress';
}
const Assessments: React.FC = () => {
  const navigate = useNavigate();
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
      id: 'disc',
      name: 'DISC Assessment',
      description: 'Behavioral assessment for communication styles',
      icon: '🎯',
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

  const handleAssessmentAction = (assessmentId: string, status: string) => {
    switch (status) {
      case 'completed':
        // Navigate to results page
        navigate(`/responses/my-responses?assessment=${assessmentId}`);
        break;
      case 'in_progress':
        // Navigate to continue assessment
        navigate(`/assessments/${assessmentId}/continue`);
        break;
      default:
        // Start new assessment
        navigate(`/assessments/${assessmentId}/start`);
        break;
    }
  };
  return (
    <div className="space-y-6 mobile-container">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mobile-text-responsive">Personality Assessments</h1>
          <p className="text-gray-600 mt-2 mobile-text-responsive">
            Complete assessments to build your comprehensive personality profile
          </p>
        </div>
        <Button variant="secondary" onClick={() => navigate('/profile')} className="w-full sm:w-auto mobile-touch-target">
          View My Profile
        </Button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {assessments.map((assessment) => (
          <div
            key={assessment.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 hover:shadow-md transition-shadow mobile-card"
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
            <p className="text-gray-600 mb-4 sm:mb-6 text-sm mobile-text-responsive">{assessment.description}</p>
            <div className="flex flex-col sm:flex-row gap-2 sm:space-x-2 sm:space-y-0">
              <Button
                size="small"
                variant={assessment.status === 'completed' ? 'secondary' : 'primary'}
                className="flex-1 mobile-touch-target"
                onClick={() => handleAssessmentAction(assessment.id, assessment.status)}
                mobileLarge
              >
                {getButtonText(assessment.status)}
              </Button>
              {assessment.status === 'completed' && (
                <Button size="small" variant="secondary" onClick={() => handleAssessmentAction(assessment.id, 'available')} className="mobile-touch-target" mobileLarge>
                  Retake
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="bg-blue-50 rounded-lg p-4 sm:p-6 border border-blue-200 mobile-card">
        <div className="flex items-start">
          <div className="text-2xl mr-4">💡</div>
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-blue-900 mb-2 mobile-text-responsive">
              Complete Multiple Assessments
            </h3>
            <p className="text-blue-800 mb-4 mobile-text-responsive">
              Taking multiple assessments gives you a more comprehensive and accurate
              personality profile. Our AI combines insights from different frameworks
              to provide better team optimization recommendations.
            </p>
            <Button size="small" onClick={() => navigate('/help')} className="mobile-touch-target" mobileLarge>
                Learn More About Our Approach
              </Button>
          </div>
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4 mobile-text-responsive">
          Assessment Progress
        </h3>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600 mobile-text-responsive">Overall Completion</span>
          <span className="text-sm font-medium text-gray-900 mobile-text-responsive">50% (2 of 4)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 sm:h-2">
          <div
            className="bg-blue-600 h-3 sm:h-2 rounded-full transition-all duration-300"
            style={{ width: '50%' }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 mt-2 mobile-text-responsive">
          Complete 2 more assessments to unlock advanced team insights
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
