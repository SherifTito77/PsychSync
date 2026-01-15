// Behavioral Analysis Page - Pattern Recognition, Anomaly Detection, Team Insights
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const BehavioralAnalysis: React.FC = () => {
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>('patterns');

  const analysisTypes = [
    { id: 'patterns', name: 'Pattern Recognition', description: 'Identify behavioral patterns and trends', icon: '🔍' },
    { id: 'anomalies', name: 'Anomaly Detection', description: 'Detect unusual behavioral changes', icon: '⚠️' },
    { id: 'team', name: 'Team Insights', description: 'Team dynamics and collaboration patterns', icon: '👥' },
    { id: 'trends', name: 'Trend Analysis', description: 'Long-term behavioral trend tracking', icon: '📈' },
    { id: 'organizational', name: 'Organizational', description: 'Organization-wide behavioral insights', icon: '🏢' }
  ];

  const capabilities = [
    '7 behavioral pattern types',
    'Advanced anomaly detection algorithms',
    'Real-time behavioral monitoring',
    'Team collaboration analysis',
    'Predictive behavioral modeling',
    'Multi-dimensional trend analysis',
    'Organizational benchmarking',
    'Risk identification and alerts'
  ];

  const patternTypes = [
    { name: 'Temporal Patterns', description: 'Time-based behavioral rhythms' },
    { name: 'Sequential Patterns', description: 'Decision flows and processes' },
    { name: 'Social Patterns', description: 'Interaction and collaboration behaviors' },
    { name: 'Learning Patterns', description: 'Skill acquisition and adaptation' },
    { name: 'Performance Patterns', description: 'Productivity and achievement patterns' },
    { name: 'Risk Patterns', description: 'Risk-taking and safety behaviors' },
    { name: 'Communication Patterns', description: 'Communication style and effectiveness' }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Behavioral Analysis</h1>
        <p className="text-gray-600">
          Advanced behavioral pattern recognition and analytics to understand workplace dynamics and individual behaviors.
        </p>
      </div>

      {/* Analysis Type Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {analysisTypes.map((type) => (
            <Card
              key={type.id}
              className={`cursor-pointer transition-all ${
                selectedAnalysis === type.id
                  ? 'ring-2 ring-purple-500 bg-purple-50'
                  : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedAnalysis(type.id)}
            >
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center space-x-3">
                  <span className="text-2xl">{type.icon}</span>
                  <span>{type.name}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{type.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Pattern Types */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Behavioral Pattern Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patternTypes.map((pattern, index) => (
            <Card key={index} className="bg-gray-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{pattern.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{pattern.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Capabilities */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {capabilities.map((capability, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="text-purple-500">✓</span>
              <span className="text-gray-700">{capability}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <Button variant="primary" onClick={() => console.log('Start Analysis')}>
          Start Analysis
        </Button>
        <Button variant="secondary" onClick={() => console.log('View Patterns')}>
          View Patterns
        </Button>
        <Button variant="outline" onClick={() => console.log('Team Insights')}>
          Team Insights
        </Button>
        <Button variant="outline" onClick={() => console.log('Anomaly Detection')}>
          Anomaly Detection
        </Button>
      </div>

      {/* Info Card */}
      <Card className="mt-8 bg-purple-50">
        <CardHeader>
          <CardTitle className="text-purple-800">About Behavioral Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-purple-700">
            Our behavioral analysis platform uses advanced pattern recognition algorithms to identify
            meaningful patterns in workplace behavior. Separate from personality assessments, this service
            focuses on observable behaviors, collaboration patterns, and performance trends to provide
            actionable insights for team optimization and organizational development.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default BehavioralAnalysis;