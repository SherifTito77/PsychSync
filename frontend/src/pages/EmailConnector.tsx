// Email Connector Page - Email Integration, Communication Analytics, Connection Management
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  getAvailableProviders,
  getEmailConnections,
  setupEmailConnection,
  disconnectEmail,
  getOAuthUrl,
  triggerManualSync,
} from '../services/emailConnectorService';
import IMAPConnectionModal from '../components/email/IMAPConnectionModal';

const EmailConnector: React.FC = () => {
  const navigate = useNavigate();
  const [selectedProvider, setSelectedProvider] = useState<string>('gmail');
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showIMAPModal, setShowIMAPModal] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<Record<string, 'connected' | 'disconnected'>>({});

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

  // Load existing connections on mount
  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      const result = await getEmailConnections();
      if (result.success) {
        setConnections(result.connections);
        const statusMap: Record<string, 'connected' | 'disconnected'> = {};
        result.connections.forEach((conn: any) => {
          statusMap[conn.provider] = conn.connection_status;
        });
        setConnectionStatus(statusMap);
      }
    } catch (error) {
      console.error('Failed to load connections:', error);
    }
  };

  const handleConnectEmail = async () => {
    if (selectedProvider === 'imap') {
      setShowIMAPModal(true);
      return;
    }

    // OAuth providers (Gmail, Outlook, Exchange)
    setLoading(true);
    try {
      const result = await getOAuthUrl(selectedProvider);
      if (result.success) {
        // Redirect to OAuth provider
        window.location.href = result.auth_url;
      } else {
        alert('Failed to get authorization URL. Please try again.');
      }
    } catch (error: any) {
      console.error('OAuth error:', error);

      // Extract error details from backend response
      let errorMessage = 'Failed to initiate OAuth flow. Please try again.';

      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail;

        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail?.message) {
          errorMessage = detail.message;
          if (detail.instructions) {
            errorMessage += '\n\n' + detail.instructions;
          }
        }
      } else if (error?.message) {
        errorMessage = error.message;
      }

      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    if (!confirm('Are you sure you want to disconnect this email account?')) {
      return;
    }

    setLoading(true);
    try {
      const result = await disconnectEmail(connectionId);
      if (result.success) {
        await loadConnections(); // Reload connections
        alert('Email account disconnected successfully.');
      } else {
        alert('Failed to disconnect. Please try again.');
      }
    } catch (error) {
      console.error('Disconnect error:', error);
      alert('Failed to disconnect. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleIMAPConnect = async (credentials: {
    email_address: string;
    server: string;
    port: number;
    use_ssl: boolean;
    username?: string;
    password: string;
  }) => {
    setLoading(true);
    try {
      const result = await setupEmailConnection({
        provider: 'imap',
        email_address: credentials.email_address,
        connection_parameters: {
          server: credentials.server,
          port: credentials.port,
          use_ssl: credentials.use_ssl,
          username: credentials.username || credentials.email_address,
          password: credentials.password,
        },
        permissions: ['read'],
        sync_settings: {
          frequency: 'manual',
        },
        auto_sync_enabled: false,
      });

      if (result.success) {
        setShowIMAPModal(false);
        await loadConnections();
        alert('IMAP connection successful!');
      } else {
        alert(`Connection failed: ${result.error_message || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('IMAP connection error:', error);

      // Show detailed error information
      let errorDetails = 'Failed to connect. Please check your credentials and try again.';

      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        if (data && data.detail) {
          errorDetails = `Connection failed (${status}): ${typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)}`;
        } else {
          errorDetails = `Connection failed (${status}): ${error.response.statusText}`;
        }
      } else if (error.message) {
        errorDetails = `Connection failed: ${error.message}`;
      }

      alert(errorDetails);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAnalytics = () => {
    // Navigate to email analytics dashboard
    navigate('/email-analytics');
  };

  const isProviderConnected = (providerId: string) => {
    return connections.some((conn: any) => conn.provider === providerId && conn.connection_status === 'connected');
  };

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
          <div className="space-y-3">
            {connections.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No email accounts connected yet.</p>
            ) : (
              connections.map((connection: any) => (
                <div key={connection.connection_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      connection.connection_status === 'connected' ? 'bg-green-500' : 'bg-gray-400'
                    }`}></div>
                    <div>
                      <p className="font-medium">{connection.email_address}</p>
                      <p className="text-sm text-gray-500 capitalize">{connection.provider}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDisconnect(connection.connection_id)}
                    disabled={loading}
                  >
                    Disconnect
                  </Button>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* OAuth Configuration Notice */}
      <Card className="mb-8 bg-yellow-50 border-yellow-200">
        <CardHeader>
          <CardTitle className="text-yellow-800">⚠️ OAuth Setup Required for Gmail/Outlook</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-yellow-700 mb-3">
            To use Gmail or Outlook OAuth connections, you need to configure OAuth credentials in your backend environment.
          </p>
          <div className="space-y-2 text-sm">
            <p className="font-medium">For Gmail:</p>
            <ol className="list-decimal list-inside space-y-1 text-yellow-700">
              <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline font-medium">Google Cloud Console</a></li>
              <li>Create a new project or select existing one</li>
              <li>Enable Gmail API</li>
              <li>Create OAuth 2.0 credentials (Web application)</li>
              <li>Add <code className="bg-yellow-100 px-1 rounded">http://localhost:5004/email-oauth-callback</code> to authorized redirect URIs</li>
              <li>Set <code className="bg-yellow-100 px-1 rounded">GMAIL_CLIENT_ID</code> and <code className="bg-yellow-100 px-1 rounded">GMAIL_CLIENT_SECRET</code> in your .env file</li>
            </ol>
          </div>
          <div className="mt-4 p-2 bg-white rounded border border-yellow-300">
            <p className="text-sm font-medium text-gray-800">
              💡 <strong>Alternative:</strong> Use <strong>Generic IMAP/POP3</strong> connection below - it works without OAuth setup using your email password or app-specific password!
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Email Provider Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Supported Email Providers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {emailProviders.map((provider) => {
            const isConnected = isProviderConnected(provider.id);
            return (
              <Card
                key={provider.id}
                className={`cursor-pointer transition-all ${
                  selectedProvider === provider.id && !isConnected
                    ? 'ring-2 ring-blue-500 bg-blue-50'
                    : isConnected
                    ? 'ring-2 ring-green-500 bg-green-50'
                    : 'hover:shadow-md'
                }`}
                onClick={() => !isConnected && setSelectedProvider(provider.id)}
              >
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{provider.icon}</span>
                      <span>{provider.name}</span>
                      {isConnected && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Connected</span>
                      )}
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
            );
          })}
        </div>

        {/* Connect Button */}
        <div className="mt-6">
          <Button
            variant="primary"
            onClick={handleConnectEmail}
            disabled={loading || isProviderConnected(selectedProvider)}
            className="w-full md:w-auto"
          >
            {loading ? 'Connecting...' : isProviderConnected(selectedProvider) ? 'Already Connected' : `Connect ${selectedProvider === 'gmail' ? 'Gmail' : selectedProvider === 'outlook' ? 'Outlook' : selectedProvider === 'imap' ? 'IMAP Account' : selectedProvider}`}
          </Button>
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
      <div className="flex flex-wrap gap-4">
        <Button
          variant="primary"
          onClick={handleConnectEmail}
          disabled={loading || isProviderConnected(selectedProvider)}
        >
          Setup Connection
        </Button>
        <Button
          variant="secondary"
          onClick={handleStartAnalytics}
          disabled={connections.length === 0}
        >
          Start Analytics
        </Button>
        <Button
          variant="outline"
          onClick={() => navigate('/email-analytics')}
          disabled={connections.length === 0}
        >
          View Dashboard
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

      {/* IMAP Connection Modal */}
      <IMAPConnectionModal
        isOpen={showIMAPModal}
        onClose={() => setShowIMAPModal(false)}
        onConnect={handleIMAPConnect}
        loading={loading}
      />
    </div>
  );
};

export default EmailConnector;
