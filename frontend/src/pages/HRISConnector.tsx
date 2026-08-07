// HRIS Connector Page - HR System Integration, Workforce Analytics, Employee Data Management
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const HRISConnector: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [providerData, setProviderData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<string | null>(null); // 'analytics', 'employees', 'sync'

  // Fetch demo data when orangehrm-demo is selected
  const fetchDemoData = async (providerId: string) => {
    if (providerId === 'orangehrm-demo') {
      setLoading(true);
      try {
        // In a real app, this would call your API
        // For now, we'll show the demo data directly
        const demoData = {
          employees: [
            { id: 'EMP001', name: 'Admin User', department: 'Administration', position: 'Administrator' },
            { id: 'EMP002', name: 'John Dickens', department: 'IT', position: 'Software Engineer' },
            { id: 'EMP003', name: 'Jane Doe', department: 'Sales', position: 'Sales Manager' },
            { id: 'EMP004', name: 'Bob Smith', department: 'HR', position: 'HR Manager' },
            { id: 'EMP005', name: 'Alice Williams', department: 'Finance', position: 'Accountant' }
          ],
          total_records: 11,
          attendance: 2,
          leave: 2,
          performance: 2
        };
        setProviderData(demoData);
        setConnectionStatus('connected');
      } catch (error) {
        console.error('Error fetching demo data:', error);
      } finally {
        setLoading(false);
      }
    } else {
      setProviderData(null);
    }
  };

  const handleProviderSelect = (providerId: string) => {
    setSelectedProvider(providerId);
    fetchDemoData(providerId);
  };

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
    },
    {
      id: 'orangehrm',
      name: 'OrangeHRM',
      description: 'Open-source HR management system',
      icon: '🍊',
      features: ['Employee data', 'Performance', 'Time attendance', 'Leave management'],
      freshness: 'Real-time',
      difficulty: 'Intermediate'
    },
    {
      id: 'orangehrm-demo',
      name: 'OrangeHRM Demo',
      description: 'Demo connector with sample data - Perfect for testing!',
      icon: '🎯',
      features: ['Demo data', '5 employees', 'Attendance', 'Leave tracking'],
      freshness: 'Demo Data',
      difficulty: 'Easy'
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
              onClick={() => handleProviderSelect(provider.id)}
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

      {/* Selected Provider Details */}
      {selectedProvider && (
        <Card className="mb-8 bg-gradient-to-r from-indigo-50 to-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-3xl">
                  {hrisProviders.find(p => p.id === selectedProvider)?.icon}
                </span>
                <div>
                  <div className="text-xl font-bold">
                    {hrisProviders.find(p => p.id === selectedProvider)?.name}
                  </div>
                  <div className="text-sm text-gray-600">
                    {selectedProvider === 'orangehrm-demo' ? '✅ Demo Data Loaded' : 'Selected'}
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedProvider(null);
                  setProviderData(null);
                  setConnectionStatus('disconnected');
                }}
              >
                Clear Selection
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">
              {hrisProviders.find(p => p.id === selectedProvider)?.description}
            </p>

            {selectedProvider === 'orangehrm-demo' && (
              <div className="space-y-4">
                {loading ? (
                  <div className="text-center py-8">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    <p className="mt-2 text-gray-600">Loading demo data...</p>
                  </div>
                ) : providerData ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card className="bg-white">
                        <CardContent className="p-4 text-center">
                          <div className="text-3xl font-bold text-indigo-600">
                            {providerData.employees.length}
                          </div>
                          <div className="text-sm text-gray-600">Employees</div>
                        </CardContent>
                      </Card>
                      <Card className="bg-white">
                        <CardContent className="p-4 text-center">
                          <div className="text-3xl font-bold text-green-600">
                            {providerData.attendance}
                          </div>
                          <div className="text-sm text-gray-600">Attendance Records</div>
                        </CardContent>
                      </Card>
                      <Card className="bg-white">
                        <CardContent className="p-4 text-center">
                          <div className="text-3xl font-bold text-blue-600">
                            {providerData.leave}
                          </div>
                          <div className="text-sm text-gray-600">Leave Records</div>
                        </CardContent>
                      </Card>
                      <Card className="bg-white">
                        <CardContent className="p-4 text-center">
                          <div className="text-3xl font-bold text-yellow-600">
                            {providerData.performance}
                          </div>
                          <div className="text-sm text-gray-600">Performance Reviews</div>
                        </CardContent>
                      </Card>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold mb-3">📊 Demo Employees</h3>
                      <div className="grid grid-cols-1 gap-2">
                        {providerData.employees.map((emp: any) => (
                          <Card key={emp.id} className="bg-white p-3">
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="font-medium">{emp.name}</div>
                                <div className="text-sm text-gray-600">
                                  {emp.position} • {emp.department}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-gray-500">ID: {emp.id}</div>
                                <div className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded mt-1">
                                  Active
                                </div>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>

                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <span className="text-2xl">✅</span>
                        <div>
                          <div className="font-medium text-green-800">Demo Connection Active</div>
                          <div className="text-sm text-green-700 mt-1">
                            You're viewing demo data from OrangeHRM Demo connector.
                            This data is ready for testing and development.
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-600">Click "Connect Demo" to load sample data</p>
                    <Button
                      className="mt-4"
                      onClick={() => fetchDemoData(selectedProvider)}
                    >
                      Connect Demo
                    </Button>
                  </div>
                )}
              </div>
            )}

            {selectedProvider !== 'orangehrm-demo' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">ℹ️</span>
                  <div>
                    <div className="font-medium text-blue-800">Connection Setup Required</div>
                    <div className="text-sm text-blue-700 mt-1">
                      To connect to {hrisProviders.find(p => p.id === selectedProvider)?.name},
                      you'll need to provide your API credentials and configure OAuth authentication.
                      Contact your HR administrator for access.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
      <div className="flex flex-wrap gap-4 mb-8">
        <Button
          variant={activeView === 'setup' ? 'primary' : 'outline'}
          onClick={() => setActiveView(activeView === 'setup' ? null : 'setup')}
        >
          {activeView === 'setup' ? '✅ ' : ''}Setup Connection
        </Button>
        <Button
          variant={activeView === 'analytics' ? 'primary' : 'outline'}
          onClick={() => {
            if (!selectedProvider) {
              alert('Please select a provider first');
              return;
            }
            setActiveView(activeView === 'analytics' ? null : 'analytics');
          }}
          disabled={!selectedProvider}
        >
          {activeView === 'analytics' ? '✅ ' : ''}View Analytics
        </Button>
        <Button
          variant={activeView === 'employees' ? 'primary' : 'outline'}
          onClick={() => {
            if (!selectedProvider) {
              alert('Please select a provider first');
              return;
            }
            setActiveView(activeView === 'employees' ? null : 'employees');
          }}
          disabled={!selectedProvider}
        >
          {activeView === 'employees' ? '✅ ' : ''}Employee Data
        </Button>
        <Button
          variant={activeView === 'sync' ? 'primary' : 'outline'}
          onClick={() => {
            if (!selectedProvider) {
              alert('Please select a provider first');
              return;
            }
            setActiveView(activeView === 'sync' ? null : 'sync');
          }}
          disabled={!selectedProvider}
        >
          {activeView === 'sync' ? '✅ ' : ''}Sync Settings
        </Button>
      </div>

      {/* Expandable Views */}
      {activeView === 'analytics' && selectedProvider === 'orangehrm-demo' && providerData && (
        <Card className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50">
          <CardHeader>
            <CardTitle>📊 Workforce Analytics Dashboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Department Distribution */}
              <div>
                <h3 className="text-lg font-semibold mb-3">🏢 Department Distribution</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {['Administration', 'IT', 'Sales', 'HR', 'Finance'].map((dept) => {
                    const count = providerData.employees.filter((e: any) => e.department === dept).length;
                    const percentage = (count / providerData.employees.length) * 100;
                    return (
                      <Card key={dept} className="bg-white">
                        <CardContent className="p-4 text-center">
                          <div className="text-2xl font-bold text-purple-600">{count}</div>
                          <div className="text-xs text-gray-600">{dept}</div>
                          <div className="text-xs text-gray-500">{percentage.toFixed(0)}%</div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>

              {/* Key Metrics */}
              <div>
                <h3 className="text-lg font-semibold mb-3">📈 Key Performance Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="bg-white">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-gray-600">Avg Hours/Day</div>
                          <div className="text-2xl font-bold text-green-600">8.25</div>
                        </div>
                        <span className="text-3xl">⏰</span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-white">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-gray-600">Avg Rating</div>
                          <div className="text-2xl font-bold text-yellow-600">4.25/5</div>
                        </div>
                        <span className="text-3xl">⭐</span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-white">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-gray-600">Total Leave Days</div>
                          <div className="text-2xl font-bold text-blue-600">8</div>
                        </div>
                        <span className="text-3xl">🏖️</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {/* Employment Overview */}
              <div>
                <h3 className="text-lg font-semibold mb-3">👥 Employment Overview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="bg-white">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-indigo-600">5</div>
                      <div className="text-sm text-gray-600">Total Employees</div>
                      <div className="text-xs text-green-600 mt-1">100% Active</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-white">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-blue-600">5</div>
                      <div className="text-sm text-gray-600">Departments</div>
                      <div className="text-xs text-gray-500 mt-1">1 per dept</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-white">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-purple-600">2</div>
                      <div className="text-sm text-gray-600">Locations</div>
                      <div className="text-xs text-gray-500 mt-1">HQ + Branch</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-white">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-green-600">4</div>
                      <div className="text-sm text-gray-600">Avg Tenure</div>
                      <div className="text-xs text-gray-500 mt-1">years</div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeView === 'employees' && selectedProvider === 'orangehrm-demo' && providerData && (
        <Card className="mb-8 bg-gradient-to-r from-blue-50 to-cyan-50">
          <CardHeader>
            <CardTitle>👥 Complete Employee Directory</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {providerData.employees.map((emp: any) => (
                <Card key={emp.id} className="bg-white">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                            {emp.name.split(' ').map((n: string) => n[0]).join('')}
                          </div>
                          <div>
                            <div className="font-semibold text-lg">{emp.name}</div>
                            <div className="text-sm text-gray-600">{emp.position}</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <div className="text-xs text-gray-500">Employee ID</div>
                            <div className="text-sm font-medium">{emp.id}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Department</div>
                            <div className="text-sm font-medium">{emp.department}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Location</div>
                            <div className="text-sm font-medium">Headquarters</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Status</div>
                            <div className="text-sm font-medium text-green-600">Active</div>
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button variant="outline" size="sm">View Details</Button>
                        <Button variant="outline" size="sm">Edit</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeView === 'sync' && selectedProvider === 'orangehrm-demo' && (
        <Card className="mb-8 bg-gradient-to-r from-green-50 to-emerald-50">
          <CardHeader>
            <CardTitle>⚙️ Sync Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Sync Status */}
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="font-semibold">Last Sync</div>
                      <div className="text-sm text-gray-600">Today at 10:30 AM</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-green-600">✅ Successful</div>
                      <div className="text-xs text-gray-500">11 records synced</div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button size="sm" onClick={() => alert('Sync initiated!')}>
                      🔄 Sync Now
                    </Button>
                    <Button variant="outline" size="sm">
                      View History
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Sync Schedule */}
              <div>
                <h3 className="text-lg font-semibold mb-3">📅 Sync Schedule</h3>
                <Card className="bg-white">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">Auto-Sync Frequency</div>
                        <div className="text-sm text-gray-600">How often to fetch new data</div>
                      </div>
                      <select className="border rounded-lg px-3 py-2 text-sm">
                        <option>Real-time</option>
                        <option selected>Hourly</option>
                        <option>Daily</option>
                        <option>Weekly</option>
                        <option>Manual only</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">Data Types to Sync</div>
                        <div className="text-sm text-gray-600">Choose what to synchronize</div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded cursor-pointer hover:bg-indigo-200">
                          ✓ Employees
                        </span>
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded cursor-pointer hover:bg-indigo-200">
                          ✓ Attendance
                        </span>
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded cursor-pointer hover:bg-indigo-200">
                          ✓ Leave
                        </span>
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded cursor-pointer hover:bg-indigo-200">
                          ✓ Performance
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Data Mapping */}
              <div>
                <h3 className="text-lg font-semibold mb-3">🔗 Data Mapping</h3>
                <Card className="bg-white">
                  <CardContent className="p-4">
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="text-gray-600">Employee ID</span>
                        <span className="font-medium">→ employee_id</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="text-gray-600">Full Name</span>
                        <span className="font-medium">→ first_name + last_name</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="text-gray-600">Department</span>
                        <span className="font-medium">→ department</span>
                      </div>
                      <div className="flex items-center justify-between py-2">
                        <span className="text-gray-600">Job Title</span>
                        <span className="font-medium">→ position</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeView === 'setup' && (
        <Card className="mb-8 bg-gradient-to-r from-yellow-50 to-orange-50">
          <CardHeader>
            <CardTitle>🔌 Connection Setup</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">ℹ️</span>
                  <div>
                    <div className="font-medium text-blue-800">Quick Start with Demo</div>
                    <div className="text-sm text-blue-700 mt-1">
                      You're currently viewing the OrangeHRM Demo connector. No setup required!
                      Click "Connect Demo" above to start exploring the data.
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">To connect to a real HRIS system:</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
                  <li>Select your HRIS provider from the cards above</li>
                  <li>Contact your HR administrator for API credentials</li>
                  <li>Configure OAuth2 authentication settings</li>
                  <li>Specify data access permissions required</li>
                  <li>Test the connection before activating</li>
                </ol>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="bg-white">
                  <CardContent className="p-4">
                    <div className="font-medium mb-2">Required Information</div>
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>• API Key or OAuth Client ID</li>
                      <li>• API Secret or Client Secret</li>
                      <li>• Instance URL / Subdomain</li>
                      <li>• Admin email for verification</li>
                    </ul>
                  </CardContent>
                </Card>
                <Card className="bg-white">
                  <CardContent className="p-4">
                    <div className="font-medium mb-2">Supported Providers</div>
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>✓ Workday (OAuth2)</li>
                      <li>✓ BambooHR (API Key)</li>
                      <li>✓ ADP (OAuth2)</li>
                      <li>✓ UKG, SAP, Oracle, OrangeHRM</li>
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
