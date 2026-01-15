// HRIS Connector Page - HR System Integration, Workforce Analytics, Employee Data Management
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const HRISConnector: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState<string>('workday');
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');

  const hrisProviders = [
    {
      id: 'workday',
      name: 'Workday',
      description: 'Cloud-based human capital management',
      icon: '🏢',
      features: ['Real-time API', 'Complete suite', 'Advanced analytics'],
      freshness: 'Real-time',
      difficulty: 'Intermediate'
    },
    {
      id: 'bamboohr',
      name: 'BambooHR',
      description: 'Small to medium business HR platform',
      icon: '🎋',
      features: ['User-friendly', 'Affordable', 'Quick setup'],
      freshness: 'Near real-time',
      difficulty: 'Easy'
    },
    {
      id: 'adp',
      name: 'ADP Workforce Now',
      description: 'Enterprise payroll and HR solution',
      icon: '💼',
      features: ['Payroll focus', 'Time tracking', 'Benefits admin'],
      freshness: 'Daily',
      difficulty: 'Advanced'
    },
    {
      id: 'ukg',
      name: 'UKG (Ultimate Kronos Group)',
      description: 'Workforce management and HR solution',
      icon: '⏰',
      features: ['Time management', 'Scheduling', 'Labor analytics'],
      freshness: 'Real-time',
      difficulty: 'Intermediate'
    },
    {
      id: 'sap',
      name: 'SAP SuccessFactors',
      description: 'Enterprise talent management suite',
      icon: '🔷',
      features: ['Talent management', 'Learning', 'Succession planning'],
      freshness: 'Real-time',
      difficulty: 'Advanced'
    },
    {
      id: 'oracle',
      name: 'Oracle HCM Cloud',
      description: 'Comprehensive cloud HR solution',
      icon: '🟠',
      features: ['Complete suite', 'Global payroll', 'Workforce rewards'],
      freshness: 'Near real-time',
      difficulty: 'Advanced'
    }
  ];

  const analyticsTypes = [
    { name: 'Workforce Demographics', description: 'Employee composition and diversity analysis', icon: '👥' },
    { name: 'Performance Analytics', description: 'Performance metrics and trends', icon: '📊' },
    { name: 'Turnover Analysis', description: 'Employee turnover patterns and predictions', icon: '📈' },
    { name: 'Compensation Analysis', description: 'Pay equity and compensation benchmarking', icon: '💰' },
    { name: 'Engagement Analytics', description: 'Employee engagement and satisfaction metrics', icon: '😊' },
    { name: 'Learning & Development', description: 'Training effectiveness and skill development', icon: '📚' },
    { name: 'Succession Planning', description: 'Leadership pipeline and readiness analysis', icon: '🎯' }
  ];

  const integrationCapabilities = [
    'Employee data synchronization',
    'Performance metrics integration',
    'Compensation and benefits data',
    'Time and attendance tracking',
    'Organizational hierarchy mapping',
    'Compliance reporting',
    'Talent management analytics',
    'Workforce planning insights'
  ];

  const dataPermissions = [
    { level: 'Basic', description: 'Employee demographics and basic HR data' },
    { level: 'Standard', description: 'Performance, compensation, and engagement data' },
    { level: 'Advanced', description: 'All HR data including sensitive information' },
    { level: 'Custom', description: 'Tailored access based on specific needs' }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">HRIS Connector</h1>
        <p className="text-gray-600">
          Connect your Human Resources Information Systems for comprehensive workforce analytics and employee insights.
        </p>
      </div>

      {/* Connection Status */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>HRIS Connection Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' : 'bg-gray-400'
              }`}></div>
              <span className="font-medium">
                {connectionStatus === 'connected' ? 'Connected to HRIS' : 'No HRIS Connection'}
              </span>
            </div>
            <div className="flex space-x-2">
              <Button
                variant={connectionStatus === 'connected' ? 'outline' : 'primary'}
                onClick={() => setConnectionStatus(connectionStatus === 'connected' ? 'disconnected' : 'connected')}
              >
                {connectionStatus === 'connected' ? 'Manage Connection' : 'Connect HRIS'}
              </Button>
              {connectionStatus === 'connected' && (
                <Button variant="outline" onClick={() => console.log('Sync Now')}>
                  Sync Now
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* HRIS Provider Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Supported HRIS Providers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {hrisProviders.map((provider) => (
            <Card
              key={provider.id}
              className={`cursor-pointer transition-all ${
                selectedProvider === provider.id
                  ? 'ring-2 ring-indigo-500 bg-indigo-50'
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
                  <div className="text-right">
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded block mb-1">
                      {provider.difficulty}
                    </span>
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                      {provider.freshness}
                    </span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3">{provider.description}</p>
                <div className="flex flex-wrap gap-1">
                  {provider.features.slice(0, 2).map((feature, index) => (
                    <span key={index} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                      {feature}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Analytics Types */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Workforce Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {analyticsTypes.map((analytics, index) => (
            <Card key={index} className="bg-gray-50">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <span>{analytics.icon}</span>
                  <span>{analytics.name}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{analytics.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Integration Capabilities */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Integration Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {integrationCapabilities.map((capability, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="text-indigo-500">✓</span>
              <span className="text-gray-700">{capability}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Data Permissions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Access Levels</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {dataPermissions.map((permission, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <h3 className="font-medium mb-1">{permission.level}</h3>
                <p className="text-sm text-gray-600">{permission.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <Button variant="primary" onClick={() => console.log('Setup HRIS Connection')}>
          Setup Connection
        </Button>
        <Button variant="secondary" onClick={() => console.log('View Analytics')}>
          View Analytics
        </Button>
        <Button variant="outline" onClick={() => console.log('Employee Data')}>
          Employee Data
        </Button>
        <Button variant="outline" onClick={() => console.log('Sync Settings')}>
          Sync Settings
        </Button>
      </div>

      {/* Security & Compliance Notice */}
      <Card className="mt-8 bg-indigo-50">
        <CardHeader>
          <CardTitle className="text-indigo-800">Security & Compliance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-indigo-700">
            All HRIS connections use enterprise-grade security with encrypted data transmission and storage.
            We comply with GDPR, CCPA, and other data protection regulations. Role-based access control
            ensures appropriate data access levels, and comprehensive audit trails maintain data governance.
            Sensitive employee information is protected with additional security layers.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default HRISConnector;