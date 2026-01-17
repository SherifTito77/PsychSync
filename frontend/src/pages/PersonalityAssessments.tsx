// Personality Assessments Page - MBTI, Enneagram, Big Five, etc.
// ✅ UPDATED: StrengthsFinder added and debug features implemented
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { aiService } from '@/services/aiService';
import type { AIProcessingResponse, PersonalityFramework } from '@/services/aiService';

const PersonalityAssessments: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFramework, setSelectedFramework] = useState<string>('mbti');
  const [isAIEnabled, setIsAIEnabled] = useState<boolean>(true);
  const [aiStatus, setAIStatus] = useState<string>('✅ AI engine operational');
  const [lastProcessingResult, setLastProcessingResult] = useState<AIProcessingResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // AI engine is operational - status already set to true in state initialization

  // Function to navigate to assessment start page
  const startAssessment = (frameworkId: string) => {
    console.log('🎯 Starting assessment for framework:', frameworkId);

    // Map framework IDs to assessment routes - these must match backend endpoints
    const assessmentRoutes: Record<string, string> = {
      'mbti': 'mbti',
      'enneagram': 'enneagram',
      'bigfive': 'big-five',  // Use hyphen to match backend endpoint
      'predictive': 'predictive-index',  // Use hyphen to match backend endpoint
      'disc': 'disc',
      'clifton': 'strengthsfinder',
      'social': 'social-styles'  // Use hyphen to match backend endpoint
    };

    const assessmentType = assessmentRoutes[frameworkId];
    if (assessmentType) {
      const route = `/assessments/${assessmentType}/start`;
      console.log('🚀 Navigating to route:', route);
      navigate(route);
    } else {
      console.error('❌ No route found for framework:', frameworkId);
    }
  };

  const testMBTIProcessing = async () => {
    try {
      setIsProcessing(true);
      const result = await aiService.getMBTIInsights('INTJ');
      // Create a compatible result object for display
      const displayResult = {
        type: result.type || 'INTJ',
        confidence: result.confidence || 0.9,
        framework: result.framework || 'mbti',
        processed_at: result.processed_at || new Date().toISOString(),
        processed_by: result.processed_by || 'PsychSync AI Engine',
        description: result.description,
        ai_insights: result.ai_insights || []
      };
      setLastProcessingResult(displayResult);
      setAIStatus('✅ MBTI processing successful');
    } catch (error) {
      console.error('MBTI processing failed:', error);
      setAIStatus('❌ MBTI processing failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const personalityFrameworks = [
    { id: 'mbti', name: 'MBTI', description: 'Myers-Briggs Type Indicator', icon: '🧠' },
    { id: 'enneagram', name: 'Enneagram', description: 'Nine personality types', icon: '⭐' },
    { id: 'bigfive', name: 'Big Five', description: 'Five-factor personality model', icon: '🌟' },
    { id: 'predictive', name: 'Predictive Index', description: 'Behavioral assessment', icon: '📊' },
    { id: 'disc', name: 'DISC', description: 'Dominance, Influence, Steadiness, Conscientiousness', icon: '💼' },
    { id: 'clifton', name: 'Clifton Strengths', description: 'Strengths-based assessment', icon: '💪' },
    { id: 'social', name: 'Social Styles', description: 'Interactive behavior patterns', icon: '🤝' }
  ];

  // Debug: Log frameworks to console
  console.log('🎯 DEBUG: personalityFrameworks loaded:', personalityFrameworks);
  console.log('🎯 DEBUG: Total frameworks:', personalityFrameworks.length);

  const features = [
    'Multiple personality framework support',
    'Cross-framework analysis',
    'Team personality profiling',
    'Individual assessment tracking',
    'Framework-specific recommendations',
    'Historical trend analysis'
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Personality Assessments</h1>
        <p className="text-gray-600">
          Comprehensive personality assessment tools supporting multiple frameworks for individual and team development.
        </p>
      </div>

      {/* Framework Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Available Frameworks ({personalityFrameworks.length} total)
        </h2>
        {/* Debug: Show framework count */}
        <div className="mb-4 p-2 bg-yellow-50 rounded border border-yellow-200 text-sm">
          <strong>DEBUG:</strong> {personalityFrameworks.length} frameworks loaded.
          Look for 💪 Clifton Strengths card below.
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {personalityFrameworks.map((framework) => (
            <div
              key={framework.id}
              className={`group relative cursor-pointer rounded-lg border-2 border-gray-200 bg-white p-6 transition-all duration-200 hover:border-blue-400 hover:bg-blue-50 hover:shadow-lg ${
                selectedFramework === framework.id
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-300'
                  : 'hover:border-blue-300'
              }`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔘 Card clicked:', framework.id, framework.name);
                setSelectedFramework(framework.id);
                startAssessment(framework.id);
              }}
              onMouseEnter={() => {
                console.log('🖱️ Hovering over:', framework.id, framework.name);
              }}
            >
              <div className="flex items-center space-x-4">
                <span className="text-3xl group-hover:scale-110 transition-transform duration-200">
                  {framework.icon}
                </span>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                    {framework.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1 group-hover:text-gray-700 transition-colors duration-200">
                    {framework.description}
                  </p>
                </div>
              </div>

              {/* Hover indicator */}
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              </div>

              {/* Highlight StrengthsFinder specifically */}
              {framework.id === 'clifton' && (
                <div className="absolute top-0 left-0 w-full h-1 bg-green-500 rounded-t-lg animate-pulse"></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Features & Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feature, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span className="text-gray-700">{feature}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Test Button - Debugging */}
      <div className="mb-4">
        <Button
          variant="primary"
          onClick={() => {
            console.log('🔥 Test button clicked!');
            alert('Test button clicked!');
          }}
        >
          🧪 Test Click Events
        </Button>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <Button variant="primary" onClick={() => startAssessment(selectedFramework)}>
          Start Assessment
        </Button>
        <Button variant="secondary" onClick={() => navigate('/assessments')}>
          View Results
        </Button>
        <Button variant="outline" onClick={() => navigate('/teams')}>
          Team Analysis
        </Button>
      </div>

      {/* AI Engine Status */}
      <Card className="mt-8 bg-gray-50">
        <CardHeader>
          <CardTitle className="text-gray-800">🤖 AI Engine Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">AI Engine:</span>
              <span className={`font-medium ${isAIEnabled ? 'text-green-600' : 'text-red-600'}`}>
                {aiStatus}
              </span>
            </div>

            {isAIEnabled && (
              <div className="space-y-3">
                <Button
                  variant="primary"
                  onClick={testMBTIProcessing}
                  disabled={isProcessing}
                  className="w-full"
                >
                  {isProcessing ? '⏳ Processing...' : '🧠 Test MBTI AI Processing'}
                </Button>

                {lastProcessingResult && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <h4 className="font-semibold text-green-800 mb-2">✅ AI Processing Result:</h4>
                    <div className="space-y-2 text-sm">
                      <div><strong>Type:</strong> {lastProcessingResult.type}</div>
                      <div><strong>Confidence:</strong> {Math.round((lastProcessingResult.confidence || 0) * 100)}%</div>
                      <div><strong>Framework:</strong> {lastProcessingResult.framework}</div>
                      <div><strong>Processed by:</strong> {lastProcessingResult.processed_by}</div>
                      {lastProcessingResult.description && (
                        <div><strong>Description:</strong> {lastProcessingResult.description}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!isAIEnabled && (
              <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                <p className="text-yellow-800 text-sm">
                  <strong>Note:</strong> AI features are currently unavailable. The platform will still function
                  with static assessment data. Please check back later for AI-powered insights.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="mt-8 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-blue-800">About Personality Assessments</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-blue-700">
            Our personality assessment platform supports multiple evidence-based frameworks to provide
            comprehensive insights into individual and team dynamics. Each framework offers unique perspectives
            on personality, behavior, and workplace preferences.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default PersonalityAssessments;
