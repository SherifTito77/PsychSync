// src/components/assessment/AssessmentOrchestrator.tsx
// AI Assessment Orchestrator UI - Personalized assessment recommendations
import React, { useState, useEffect, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { orchestratorService } from '../../services/orchestratorService';
import {
  UserContext,
  Recommendation,
  OrchestratorResponse,
  OrchestratorInsight,
} from '../../types/orchestrator';

interface AssessmentOrchestratorProps {
  userContext: UserContext;
}

const RecommendationCard: React.FC<{
  recommendation: Recommendation;
  onStart: () => void;
}> = memo(({ recommendation, onStart }) => {
  const priorityColors = {
    high: 'bg-green-100 text-green-800 border-green-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-bold text-gray-900">{recommendation.name}</h3>
            <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${priorityColors[recommendation.priority]}`}>
              {recommendation.priority} priority
            </span>
          </div>
          <p className="text-gray-600 text-sm mb-3">{recommendation.description}</p>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {recommendation.estimatedTime} min
            </span>
            <span className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {Math.round(recommendation.confidence * 100)}% match
            </span>
          </div>
        </div>
      </div>

      {recommendation.reasoning && recommendation.reasoning.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-700 mb-2">Why this assessment?</p>
          <ul className="text-sm text-gray-600 space-y-1">
            {recommendation.reasoning.map((reason, idx) => (
              <li key={idx} className="flex items-start">
                <svg className="w-4 h-4 mr-2 text-indigo-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {recommendation.benefits && recommendation.benefits.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-700 mb-2">You'll gain:</p>
          <div className="flex flex-wrap gap-2">
            {recommendation.benefits.map((benefit, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-2 py-1 bg-indigo-50 text-indigo-700 text-xs rounded"
              >
                ✓ {benefit}
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={onStart}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
      >
        Start Assessment →
      </button>
    </div>
  );
});

const InsightCard: React.FC<{ insight: OrchestratorInsight }> = memo(({ insight }) => {
  const typeIcons = {
    opportunity: '💡',
    gap: '🎯',
    next_step: '🚀',
    trend: '📈',
  };

  const typeColors = {
    opportunity: 'bg-yellow-50 border-yellow-200',
    gap: 'bg-blue-50 border-blue-200',
    next_step: 'bg-green-50 border-green-200',
    trend: 'bg-purple-50 border-purple-200',
  };

  return (
    <div className={`p-4 rounded-lg border ${typeColors[insight.type]}`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{typeIcons[insight.type]}</span>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 mb-1">{insight.title}</h4>
          <p className="text-sm text-gray-700 mb-3">{insight.description}</p>
          {insight.actionable && insight.recommendations.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-2">Suggested actions:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {insight.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-2 text-indigo-500">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

const AssessmentOrchestrator: React.FC<AssessmentOrchestratorProps> = ({ userContext }) => {
  const navigate = useNavigate();
  const [response, setResponse] = useState<OrchestratorResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'recommendations' | 'path' | 'insights'>('recommendations');

  useEffect(() => {
    loadRecommendations();
  }, [userContext]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const data = await orchestratorService.getRecommendations(userContext, {
        maxRecommendations: 6,
        includeClinicalTools: true,
        prioritizeTeamFeatures: userContext.role === 'hr_manager' || userContext.role === 'team_lead',
      });
      setResponse(data);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAssessment = (recommendation: Recommendation) => {
    // Navigate to assessment
    const frameworkMap: Record<string, string> = {
      big_five: '/assessments/big-five',
      mbti: '/assessments/mbti',
      enneagram: '/assessments/enneagram',
      disc: '/assessments/disc',
      predictive_index: '/assessments/predictive_index',
      strengthsfinder: '/assessments/strengthsfinder',
      social_styles: '/assessments/social',
      phq9: '/clinical/assessment/phq9/take',
      gad7: '/clinical/assessment/gad7/take',
    };

    const path = frameworkMap[recommendation.framework];
    if (path) {
      navigate(path);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">AI is analyzing your profile...</p>
        </div>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800">Failed to load recommendations. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🤖 AI-Powered Assessment Recommendations
        </h2>
        <p className="text-gray-600">
          Based on your profile, goals, and assessment history, here's what we recommend for you next.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setSelectedTab('recommendations')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'recommendations'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Top Recommendations ({response.topRecommendations.length})
          </button>
          {response.personalizedPath && (
            <button
              onClick={() => setSelectedTab('path')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'path'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Personalized Path
            </button>
          )}
          <button
            onClick={() => setSelectedTab('insights')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'insights'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Insights ({response.insights.length})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'recommendations' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {response.topRecommendations.map((rec) => (
            <RecommendationCard
              key={rec.assessmentId}
              recommendation={rec}
              onStart={() => handleStartAssessment(rec)}
            />
          ))}
        </div>
      )}

      {selectedTab === 'path' && response.personalizedPath && (
        <div className="bg-white rounded-lg border border-gray-200 p-8">
          <div className="mb-6">
            <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-800 text-sm font-semibold rounded-full mb-4">
              {response.personalizedPath.difficulty}
            </span>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {response.personalizedPath.name}
            </h3>
            <p className="text-gray-600 mb-4">{response.personalizedPath.description}</p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {response.personalizedPath.duration} minutes total
              </span>
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
                {response.personalizedPath.assessments.length} assessments
              </span>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">What you'll achieve:</h4>
            <p className="text-gray-600">{response.personalizedPath.expectedOutcome}</p>
          </div>

          <div className="space-y-4">
            {response.personalizedPath.assessments.map((assessment, index) => (
              <div key={assessment.assessmentId} className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 text-indigo-800 rounded-full flex items-center justify-center font-bold">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <h5 className="font-semibold text-gray-900">{assessment.name}</h5>
                  <p className="text-sm text-gray-600">{assessment.description}</p>
                </div>
                <span className="text-sm text-gray-500">{assessment.estimatedTime} min</span>
              </div>
            ))}
          </div>

          <button
            onClick={() => handleStartAssessment(response.personalizedPath!.assessments[0])}
            className="mt-8 w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
          >
            Start Your Journey →
          </button>
        </div>
      )}

      {selectedTab === 'insights' && (
        <div className="space-y-4">
          {response.insights.map((insight, index) => (
            <InsightCard key={index} insight={insight} />
          ))}
        </div>
      )}
    </div>
  );
};

AssessmentOrchestrator.displayName = 'AssessmentOrchestrator';

export default AssessmentOrchestrator;
