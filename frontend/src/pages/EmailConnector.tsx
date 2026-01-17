// Email Connector Page - Email Integration, Communication Analytics, Connection Management
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const EmailConnector: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState<string>('gmail');
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');

  const emailProviders = [
    {
      id: 'gmail',
      name: 'Gmail',
      description: 'Google Gmail with OAuth2 authentication',
      icon: '📧',
      features: ['Real-time sync', 'Full access', 'OAuth2 secure'],
      difficulty: 'Easy'
    },
    {
      id: 'outlook',
      name: 'Microsoft Outlook',
      description: 'Outlook/Exchange Online integration',
      icon: '📨',
      features: ['Calendar integration', 'Full access', 'OAuth2 secure'],
      difficulty: 'Easy'
    },
    {
      id: 'exchange',
      name: 'Microsoft Exchange',
      description: 'On-premise Exchange server',
      icon: '🏢',
      features: ['Full access', 'Calendar', 'Advanced setup'],
      difficulty: 'Advanced'
    },
    {
      id: 'imap',
      name: 'Generic IMAP/POP3',
      description: 'Standard email protocol support',
      icon: '🔌',
      features: ['Read access', 'Basic features', 'Wide compatibility'],
      difficulty: 'Intermediate'
    }
  ];

  const analyticsFeatures = [
    'Communication pattern analysis',
    'Response time tracking',
    'Sentiment analysis',
    'Network analysis',
    'Topic extraction',
    'Collaboration patterns',
    'Engagement metrics',
    'Time-based patterns'
  ];

  const assessmentTypes = [
    { name: 'Communication Effectiveness', description: 'Analyze communication clarity and impact' },
    { name: 'Leadership Communication', description: 'Assess leadership communication style' },
    { name: 'Team Collaboration', description: 'Evaluate team collaboration patterns' },
    { name: 'Customer Service', description: 'Analyze customer service communication quality' },
    { name: 'Conflict Resolution', description: 'Identify conflict resolution patterns' }
  ];

  const syncOptions = [
    { option: 'Real-time sync', description: 'Immediate email processing' },
    { option: 'Hourly sync', description: 'Process emails every hour' },
    { option: 'Daily sync', description: 'Daily batch processing' },
    { option: 'Manual only', description: 'Sync only when triggered' }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Connector</h1>
        <p className="text-gray-600">
          Connect your email accounts for comprehensive communication analytics and behavioral insights.
        </p>
      </div>

      {/* Connection Status */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Connection Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' : 'bg-gray-400'
              }`}></div>
              <span className="font-medium">
                {connectionStatus === 'connected' ? 'Connected' : 'Not Connected'}
              </span>
            </div>
            <Button
              variant={connectionStatus === 'connected' ? 'outline' : 'primary'}
              onClick={() => setConnectionStatus(connectionStatus === 'connected' ? 'disconnected' : 'connected')}
            >
              {connectionStatus === 'connected' ? 'Disconnect' : 'Connect Email'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Email Provider Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Supported Email Providers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {emailProviders.map((provider) => (
            <Card
              key={provider.id}
              className={`cursor-pointer transition-all ${
                selectedProvider === provider.id
                  ? 'ring-2 ring-blue-500 bg-blue-50'
                  : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedProvider(provider.id)}
            >
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{provider.icon}</span>
                    <span>{provider.name}</span>
                  </div>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {provider.difficulty}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3">{provider.description}</p>
                <div className="flex flex-wrap gap-2">
                  {provider.features.map((feature, index) => (
                    <span key={index} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {feature}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Communication Analytics */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Communication Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {analyticsFeatures.map((feature, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="text-blue-500">✓</span>
              <span className="text-gray-700">{feature}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Behavioral Assessment Types */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Email-Based Assessments</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {assessmentTypes.map((assessment, index) => (
            <Card key={index} className="bg-gray-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{assessment.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{assessment.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Sync Options */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Synchronization Options</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {syncOptions.map((option, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <h3 className="font-medium mb-1">{option.option}</h3>
                <p className="text-sm text-gray-600">{option.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <Button variant="primary" onClick={() => console.log('Setup Connection')}>
          Setup Connection
        </Button>
        <Button variant="secondary" onClick={() => console.log('Start Analytics')}>
          Start Analytics
        </Button>
        <Button variant="outline" onClick={() => console.log('View Dashboard')}>
          View Dashboard
        </Button>
        <Button variant="outline" onClick={() => console.log('Sync Settings')}>
          Sync Settings
        </Button>
      </div>

      {/* Security Notice */}
      <Card className="mt-8 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-blue-800">Security & Privacy</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-blue-700">
            All email connections use secure OAuth2 authentication where available. Your email content
            is processed locally and encrypted. We never store email passwords or share your data with
            third parties. You maintain full control over what data is analyzed and can disconnect at any time.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default EmailConnector;
