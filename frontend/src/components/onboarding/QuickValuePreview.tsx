// src/components/onboarding/QuickValuePreview.tsx
// Immediate value demonstration component
import React, { useState } from 'react';
import Button from '../common/Button';

interface TeamRole {
  role: string;
  teamSize: string;
  challenge: string;
}

interface PreviewInsight {
  title: string;
  description: string;
  impact: string;
  timeframe: string;
}

const QuickValuePreview: React.FC = () => {
  const [role, setRole] = useState<string>('');
  const [teamSize, setTeamSize] = useState<string>('');
  const [challenge, setChallenge] = useState<string>('');
  const [showInsight, setShowInsight] = useState<boolean>(false);

  const roles = [
    { value: 'manager', label: 'Team Manager', icon: '👔' },
    { value: 'hr', label: 'HR Professional', icon: '💼' },
    { value: 'lead', label: 'Team Lead', icon: '🎯' },
    { value: 'member', label: 'Team Member', icon: '👥' },
    { value: 'executive', label: 'Executive', icon: '🚀' }
  ];

  const challenges = [
    {
      value: 'communication',
      label: 'Communication Issues',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      value: 'productivity',
      label: 'Low Productivity',
      color: 'text-red-600',
      bgColor: 'bg-red-50'
    },
    {
      value: 'turnover',
      label: 'High Turnover',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      value: 'collaboration',
      label: 'Poor Collaboration',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50'
    },
    {
      value: 'conflict',
      label: 'Team Conflict',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ];

  const generateInsight = (userRole: string, teamChallenge: string): PreviewInsight => {
    const insights: Record<string, Record<string, PreviewInsight>> = {
      manager: {
        communication: {
          title: 'Communication Gap Identified',
          description: 'Your team shows a 34% mismatch in communication styles. This typically causes 2-3 hours of lost productivity per week.',
          impact: 'Recover 8+ hours of team productivity monthly',
          timeframe: 'First assessment results'
        },
        productivity: {
          title: 'Productivity Bottleneck Detected',
          description: 'Analysis suggests role misalignment could be costing your team 15-20% in output potential.',
          impact: 'Increase team output by 20-25%',
          timeframe: '2-3 weeks'
        },
        turnover: {
          title: 'Turnover Risk Pattern Found',
          description: 'Your team profile shows 3 high-risk indicators for voluntary turnover in the next 6 months.',
          impact: 'Reduce turnover risk by 40%',
          timeframe: 'First month'
        },
        collaboration: {
          title: 'Collaboration Friction Points',
          description: 'Team members show complementary strengths but current processes aren\'t leveraging them effectively.',
          impact: 'Improve project completion speed by 30%',
          timeframe: '2 weeks'
        },
        conflict: {
          title: 'Conflict Style Mismatch',
          description: 'Different conflict resolution approaches are creating unnecessary tension in decision-making.',
          impact: 'Reduce meeting conflicts by 60%',
          timeframe: '1-2 weeks'
        }
      },
      hr: {
        communication: {
          title: 'Organizational Communication Health',
          description: 'Cross-departmental communication shows patterns that typically indicate silo formation.',
          impact: 'Break down silos, improve knowledge sharing',
          timeframe: 'First quarter analysis'
        },
        productivity: {
          title: 'Team Productivity Variance',
          description: 'Some teams are 40% more productive than others - personality alignment explains most of this difference.',
          impact: 'Standardize high productivity across teams',
          timeframe: '3-6 months'
        },
        turnover: {
          title: 'Retention Risk Dashboard',
          description: 'Early indicators show which teams/departments are at highest risk for turnover.',
          impact: 'Save $200K+ in replacement costs',
          timeframe: '90 days'
        },
        collaboration: {
          title: 'Team Collaboration Index',
          description: 'Current collaboration patterns suggest opportunities for cross-functional team improvements.',
          impact: 'Create 25% more effective teams',
          timeframe: 'First team restructuring'
        },
        conflict: {
          title: 'Workplace Conflict Hotspots',
          description: 'Identify teams with conflict patterns that typically lead to HR complaints.',
          impact: 'Reduce HR complaints by 50%',
          timeframe: '60 days'
        }
      },
      lead: {
        communication: {
          title: 'Team Communication Flow',
          description: 'Your team communication shows opportunities for 25% improvement in information clarity.',
          impact: 'Reduce misunderstandings by 40%',
          timeframe: '2 weeks'
        },
        productivity: {
          title: 'Task Assignment Optimization',
          description: 'Team member strengths suggest better task allocation could increase output by 18%.',
          impact: 'Hit sprint goals 20% more consistently',
          timeframe: 'Next sprint'
        },
        collaboration: {
          title: 'Team Synergy Score',
          description: 'Current team dynamics show room for improvement in collaborative decision-making.',
          impact: 'Improve team satisfaction by 35%',
          timeframe: 'One month'
        }
      },
      member: {
        communication: {
          title: 'Personal Communication Style',
          description: 'Your communication style differs from 60% of your team - learn to bridge this gap.',
          impact: 'Improve personal effectiveness by 25%',
          timeframe: 'This week'
        },
        productivity: {
          title: 'Personal Productivity Insights',
          description: 'Your work style suggests specific environmental changes could boost your focus.',
          impact: 'Increase personal productivity by 30%',
          timeframe: 'Immediate application'
        },
        collaboration: {
          title: 'Team Compatibility Analysis',
          description: 'Discover how your personality complements (or clashes with) team members.',
          impact: 'Build stronger working relationships',
          timeframe: 'Next team project'
        }
      },
      executive: {
        communication: {
          title: 'Organizational Communication Health',
          description: 'Executive-team communication patterns indicate 22% improvement opportunity in strategic alignment.',
          impact: 'Accelerate strategic initiatives by 30%',
          timeframe: 'Q1 results'
        },
        productivity: {
          title: 'Team Performance Optimization',
          description: 'Cross-team personality data suggests $2-3M productivity improvement potential.',
          impact: 'Increase organizational productivity by 15%',
          timeframe: '12 months'
        },
        turnover: {
          title: 'Leadership Retention Intelligence',
          description: 'High-potential employee patterns show 35% improvement opportunity in retention.',
          impact: 'Retain key talent, reduce replacement costs',
          timeframe: '6-12 months'
        }
      }
    };

    return insights[userRole]?.[teamChallenge] || insights.manager.communication;
  };

  const handleShowInsight = () => {
    if (role && challenge) {
      setShowInsight(true);
    }
  };

  const insight = showInsight ? generateInsight(role, challenge) : null;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          See PsychSync in Action - No Registration Required
        </h2>
        <p className="text-xl text-gray-600">
          Answer 2 questions to see how behavioral intelligence could help your team
        </p>
      </div>

      {!showInsight ? (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          {/* Question 1: Your Role */}
          <div className="mb-8">
            <label className="block text-lg font-semibold text-gray-900 mb-4">
              What's your role in your organization?
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {roles.map((roleOption) => (
                <button
                  key={roleOption.value}
                  onClick={() => setRole(roleOption.value)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    role === roleOption.value
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="text-2xl mb-2">{roleOption.icon}</div>
                  <div className="text-sm font-medium">{roleOption.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Question 2: Biggest Challenge */}
          {role && (
            <div className="mb-8">
              <label className="block text-lg font-semibold text-gray-900 mb-4">
                What's your biggest team challenge right now?
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {challenges.map((challengeOption) => {
                  const ChallengeIcon = getChallengeIcon(challengeOption.value);
                  return (
                    <button
                      key={challengeOption.value}
                      onClick={() => setChallenge(challengeOption.value)}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        challenge === challengeOption.value
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center">
                        <div className={`p-2 rounded-lg mr-3 ${challengeOption.bgColor}`}>
                          <ChallengeIcon className={`w-5 h-5 ${challengeOption.color}`} />
                        </div>
                        <div>
                          <div className="font-medium">{challengeOption.label}</div>
                          <div className="text-sm text-gray-500">
                            {getChallengeDescription(challengeOption.value)}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Show Results Button */}
          {challenge && (
            <div className="text-center">
              <Button
                size="sm"
                onClick={handleShowInsight}
                className="px-8 py-3 text-lg"
              >
                <span className="mr-2">🚀</span>
                See My Team Insights Preview
              </Button>
              <p className="text-sm text-gray-500 mt-3">
                Get instant results - no email required
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Insights Results */
        <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl border border-indigo-200 p-8">
          <div className="max-w-3xl mx-auto">
            {/* Success Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {insight?.title}
              </h3>
              <p className="text-lg text-gray-600">
                Based on your role as a {roles.find(r => r.value === role)?.label}
              </p>
            </div>

            {/* Key Insight */}
            <div className="bg-white rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-3">What We Found:</h4>
              <p className="text-gray-700 leading-relaxed">
                {insight?.description}
              </p>
            </div>

            {/* Impact & Timeline */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-white rounded-lg p-6">
                <div className="flex items-center mb-2">
                  <div className="p-2 bg-green-100 rounded-lg mr-3">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <h4 className="font-semibold text-gray-900">Potential Impact</h4>
                </div>
                <p className="text-gray-700 font-medium">{insight?.impact}</p>
              </div>

              <div className="bg-white rounded-lg p-6">
                <div className="flex items-center mb-2">
                  <div className="p-2 bg-blue-100 rounded-lg mr-3">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h4 className="font-semibold text-gray-900">Time to See Results</h4>
                </div>
                <p className="text-gray-700 font-medium">{insight?.timeframe}</p>
              </div>
            </div>

            {/* Call to Action */}
            <div className="bg-white rounded-lg p-6 text-center">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">
                This is just a preview. Get your complete team analysis:
              </h4>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="sm" className="px-6">
                  Get Full Team Analysis
                </Button>
                <Button size="sm" variant="secondary" className="px-6" onClick={() => setShowInsight(false)}>
                  Try Different Scenario
                </Button>
              </div>
              <p className="text-sm text-gray-500 mt-4">
                Join 10,000+ teams using PsychSync to optimize performance
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Trust Indicators */}
      <div className="mt-12 text-center">
        <div className="flex flex-wrap justify-center items-center gap-8 text-gray-500">
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            No credit card required
          </div>
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Instant results
          </div>
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Used by 10,000+ teams
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper functions for icons
const getChallengeIcon = (challenge: string) => {
  const icons: Record<string, React.FC<{ className?: string }>> = {
    communication: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
    productivity: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    turnover: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
      </svg>
    ),
    collaboration: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
    conflict: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    )
  };
  return icons[challenge] || icons.communication;
};

const getChallengeDescription = (challenge: string): string => {
  const descriptions: Record<string, string> = {
    communication: 'Misunderstandings, information gaps',
    productivity: 'Missing deadlines, low output',
    turnover: 'Losing valuable team members',
    collaboration: 'Poor teamwork, silo mentality',
    conflict: 'Disagreements, tension in meetings'
  };
  return descriptions[challenge] || '';
};

export default QuickValuePreview;
