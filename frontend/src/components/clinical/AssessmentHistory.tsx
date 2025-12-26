import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import RiskLevelIndicator from './RiskLevelIndicator';

interface AssessmentRecord {
  id: string;
  screening_type: string;
  completed_at: string;
  total_score: number;
  severity_level: string;
  risk_level: string;
  crisis_alert: boolean;
  response_data?: any;
  next_assessment_date?: string;
  provider_notified?: boolean;
  notes?: string;
}

interface AssessmentHistoryProps {
  userId?: string;
  maxItems?: number;
  showTrend?: boolean;
}

const AssessmentHistory: React.FC<AssessmentHistoryProps> = ({
  userId,
  maxItems = 10,
  showTrend = true,
}) => {
  const [loading, setLoading] = useState(true);
  const [assessments, setAssessments] = useState<AssessmentRecord[]>([]);

  useEffect(() => {
    fetchAssessmentHistory();
  }, [userId]);

  const fetchAssessmentHistory = async () => {
    try {
      const url = userId
        ? `/api/v1/clinical/screenings/user/${userId}?limit=${maxItems}`
        : `/api/v1/clinical/screenings/recent?limit=${maxItems}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAssessments(data.assessments || []);
      }
    } catch (error) {
      console.error('Error fetching assessment history:', error);
      // Mock data for demonstration
      setAssessments([
        {
          id: '1',
          screening_type: 'PHQ9',
          completed_at: '2024-01-15T10:30:00Z',
          total_score: 12,
          severity_level: 'Moderate',
          risk_level: 'low',
          crisis_alert: false,
          provider_notified: false,
          notes: 'Initial screening for depression symptoms',
          response_data: {
            duration: '5 minutes',
            questions_answered: 9,
            skipped_questions: 0
          }
        },
        {
          id: '2',
          screening_type: 'GAD7',
          completed_at: '2024-01-10T14:15:00Z',
          total_score: 8,
          severity_level: 'Mild',
          risk_level: 'low',
          crisis_alert: false,
          provider_notified: true,
          notes: 'Follow-up assessment for anxiety symptoms',
          response_data: {
            duration: '4 minutes',
            questions_answered: 7,
            skipped_questions: 0
          }
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getAssessmentTypeDisplay = (type: string) => {
    const types: Record<string, string> = {
      'PHQ9': 'Depression (PHQ-9)',
      'GAD7': 'Anxiety (GAD-7)',
      'STRESS': 'Stress Assessment',
      'WELLBEING': 'Wellbeing Check',
    };
    return types[type] || type;
  };

  const getTrendIcon = (current: AssessmentRecord[], previous: AssessmentRecord | null) => {
    if (!previous) return null;

    const currentScore = current[0]?.total_score || 0;
    const previousScore = previous.total_score;

    if (currentScore < previousScore) {
      return (
        <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      );
    } else if (currentScore > previousScore) {
      return (
        <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    } else {
      return (
        <svg className="h-5 w-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      );
    }
  };

  const getTrendText = (current: AssessmentRecord[], previous: AssessmentRecord | null) => {
    if (!previous) return '';

    const currentScore = current[0]?.total_score || 0;
    const previousScore = previous.total_score;
    const diff = Math.abs(currentScore - previousScore);

    if (currentScore < previousScore) {
      return `Improved by ${diff} points`;
    } else if (currentScore > previousScore) {
      return `Increased by ${diff} points`;
    } else {
      return 'No change';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-gray-600">Loading assessment history...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Assessment History</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.href = '/clinical-assessments'}
          >
            Take New Assessment
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {assessments.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No previous assessments found.</p>
            <Button onClick={() => window.location.href = '/clinical-assessments'}>
              Take Your First Assessment
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {showTrend && assessments.length > 1 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-700">Recent Trend:</span>
                    {getTrendIcon(assessments, assessments[1])}
                    <span className="text-sm text-gray-600">
                      {getTrendText(assessments, assessments[1])}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {assessments.map((assessment, index) => (
                <div
                  key={assessment.id}
                  className={`border rounded-lg p-4 ${
                    index === 0 ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="font-medium text-gray-900">
                          {getAssessmentTypeDisplay(assessment.screening_type)}
                        </span>
                        {index === 0 && (
                          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded">
                            Most Recent
                          </span>
                        )}
                        {assessment.crisis_alert && (
                          <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-0.5 rounded">
                            Crisis Alert
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-1 gap-2 text-sm text-gray-600">
                        <div className="flex items-center space-x-4">
                          <span className="font-medium">Score: {assessment.total_score}</span>
                          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                            {assessment.severity_level}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span>{new Date(assessment.completed_at).toLocaleDateString()}</span>
                          {assessment.response_data?.duration && (
                            <span className="text-gray-500">
                              Duration: {assessment.response_data.duration}
                            </span>
                          )}
                        </div>
                        {assessment.notes && (
                          <div className="text-xs text-gray-500 italic mt-1">
                            {assessment.notes}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center space-x-3">
                        <RiskLevelIndicator
                          level={assessment.risk_level as any}
                          showLabel={false}
                          size="sm"
                        />
                        {assessment.provider_notified && (
                          <div className="flex items-center text-xs text-green-600">
                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                            </svg>
                            Provider notified
                          </div>
                        )}
                        {assessment.next_assessment_date && (
                          <div className="text-xs text-blue-600">
                            Next: {new Date(assessment.next_assessment_date).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          // Store assessment data for the detailed view
                          const state = {
                            assessmentId: assessment.id,
                            assessmentType: assessment.screening_type.toLowerCase(),
                            completedAt: assessment.completed_at,
                            score: assessment.total_score,
                            severityLevel: assessment.severity_level,
                            riskLevel: assessment.risk_level,
                            crisisAlert: assessment.crisis_alert,
                            notes: assessment.notes,
                            responseData: assessment.response_data,
                            providerNotified: assessment.provider_notified
                          };

                          // Navigate to results with state data
                          window.location.href = `/clinical/assessment/${assessment.screening_type.toLowerCase()}/complete#${assessment.id}`;
                        }}
                      >
                        View Details
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 pt-4 border-t">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => window.location.href = '/clinical/dashboard'}
              >
                View Full Assessment Dashboard
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AssessmentHistory;