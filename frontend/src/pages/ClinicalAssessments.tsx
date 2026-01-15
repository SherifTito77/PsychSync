import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle } from '@/components/ui/alert';

interface ScreeningTool {
  id: string;
  name: string;
  description: string;
  estimatedTime: string;
  type: 'phq9' | 'gad7' | 'stress' | 'wellbeing' | 'dass21' | 'pcl5' | 'audit';
  severity?: 'low' | 'moderate' | 'high';
  reliability?: string;
}

const ClinicalAssessments: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [screenings, setScreenings] = useState<ScreeningTool[]>([]);
  const [crisisAlert, setCrisisAlert] = useState(false);

  const screeningTools: ScreeningTool[] = [
    {
      id: 'phq9',
      name: 'PHQ-9 Depression Screening',
      description: 'Assess symptoms of depression over the past 2 weeks',
      estimatedTime: '5-10 minutes',
      type: 'phq9',
    },
    {
      id: 'gad7',
      name: 'GAD-7 Anxiety Screening',
      description: 'Measure severity of anxiety symptoms',
      estimatedTime: '3-5 minutes',
      type: 'gad7',
    },
    {
      id: 'dass21',
      name: 'DASS-21 Depression, Anxiety, Stress Scales',
      description: 'Comprehensive assessment of depression, anxiety, and stress symptoms',
      estimatedTime: '5-10 minutes',
      type: 'dass21',
      reliability: 'Good reliability (α = 0.84-0.91)',
    },
    {
      id: 'pcl5',
      name: 'PCL-5 PTSD Assessment',
      description: 'PTSD symptom assessment for trauma-related symptoms',
      estimatedTime: '10-15 minutes',
      type: 'pcl5',
      reliability: 'Excellent reliability (α = 0.94)',
    },
    {
      id: 'audit',
      name: 'AUDIT Alcohol Use Screening',
      description: 'Alcohol use screening and assessment of drinking patterns',
      estimatedTime: '5-8 minutes',
      type: 'audit',
      reliability: 'Good reliability (α = 0.75-0.85)',
    },
    {
      id: 'stress',
      name: 'Perceived Stress Scale',
      description: 'Evaluate your perceived stress levels',
      estimatedTime: '5 minutes',
      type: 'stress',
    },
    {
      id: 'wellbeing',
      name: 'Wellbeing Assessment',
      description: 'Comprehensive mental health and wellbeing check',
      estimatedTime: '10-15 minutes',
      type: 'wellbeing',
    },
  ];

  useEffect(() => {
    // Simulate checking for any active crisis alerts
    setTimeout(() => {
      setLoading(false);
      setCrisisAlert(false); // Set to true to show crisis banner
    }, 1000);
  }, []);

  const handleStartAssessment = (toolId: string) => {
    // Use the correct route pattern that matches App.tsx routing
    navigate(`/clinical/assessment/${toolId}/start`);
  };

  const handleEmergencyClick = () => {
    navigate('/clinical/emergency');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading clinical assessments...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Crisis Alert Banner */}
      {crisisAlert && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                <strong>Immediate Support Available:</strong> If you're experiencing a mental health crisis, help is available 24/7.
              </p>
              <div className="mt-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleEmergencyClick}
                >
                  Get Immediate Help
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Mental Health Screening
          </h1>
          <p className="text-lg text-gray-600">
            Take evidence-based assessments to understand your mental health better.
            All screenings are confidential and free.
          </p>
        </div>

        {/* Emergency Banner */}
        <Alert variant="warning" className="mb-8">
          <AlertTitle>Need Immediate Help?</AlertTitle>
          <p className="mt-2">
            If you're having thoughts of harming yourself or others, please call emergency services
            or contact a crisis hotline immediately.
          </p>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleEmergencyClick}
              className="mr-4"
            >
              View Emergency Resources
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => window.open('tel:988')}
            >
              Call 988 (Crisis Line)
            </Button>
          </div>
        </Alert>

        {/* Screening Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {screeningTools.map((tool) => (
            <Card key={tool.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{tool.name}</span>
                  <span className="text-sm font-normal text-gray-500">
                    {tool.estimatedTime}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-3">{tool.description}</p>
                {tool.reliability && (
                  <div className="mb-3 p-2 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-800">
                      <span className="font-semibold">Reliability:</span> {tool.reliability}
                    </p>
                  </div>
                )}
                <Button
                  onClick={() => handleStartAssessment(tool.id)}
                  className="w-full"
                  size="lg"
                >
                  Start Assessment
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Information Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Confidential & Secure</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Your responses are encrypted and stored securely. Only you and authorized
                healthcare providers can access your results.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Evidence-Based</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                All assessments are clinically validated tools used by healthcare professionals
                worldwide.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Free Support</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Access to mental health resources and referrals to licensed professionals
                when needed.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Assessments */}
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Recent Assessments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500 text-center py-8">
                No previous assessments found. Take your first assessment above to get started.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ClinicalAssessments;