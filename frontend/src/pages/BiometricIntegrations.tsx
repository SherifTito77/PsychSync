/**
 * Biometric Integrations Page
 * Connect and manage wearable devices for health & stress monitoring
 */

import React, { useState, useEffect } from 'react';
import { biometricService } from '@/services/biometricService';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Progress from '@/components/ui/progress';
import {
  Heart,
  Activity,
  Moon,
  Zap,
  Watch,
  Smartphone,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  AlertTriangle,
  Settings,
} from 'lucide-react';

interface WearableDevice {
  id: string;
  name: string;
  provider: string;
  icon: string;
  connected: boolean;
  lastSync: string | null;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  metricsAvailable: string[];
  dataPoints: number;
  description: string;
}

interface BiometricSnapshot {
  label: string;
  value: string;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  status: 'good' | 'warning' | 'critical';
  source: string;
}

const DEVICES: WearableDevice[] = [
  {
    id: 'apple_health',
    name: 'Apple Health',
    provider: 'Apple',
    icon: '🍎',
    connected: false,
    lastSync: null,
    status: 'disconnected',
    metricsAvailable: ['Heart Rate', 'HRV', 'Sleep', 'Steps', 'Blood Oxygen', 'Respiratory Rate'],
    dataPoints: 0,
    description: 'iPhone & Apple Watch health data via HealthKit',
  },
  {
    id: 'google_fit',
    name: 'Google Fit',
    provider: 'Google',
    icon: '💚',
    connected: false,
    lastSync: null,
    status: 'disconnected',
    metricsAvailable: ['Heart Rate', 'Steps', 'Sleep', 'Activity Minutes', 'Calories'],
    dataPoints: 0,
    description: 'Android & Wear OS health and fitness data',
  },
  {
    id: 'fitbit',
    name: 'Fitbit',
    provider: 'Fitbit',
    icon: '💙',
    connected: false,
    lastSync: null,
    status: 'disconnected',
    metricsAvailable: ['Heart Rate', 'HRV', 'Sleep Stages', 'Steps', 'Stress Score', 'SpO2'],
    dataPoints: 0,
    description: 'Fitbit trackers and smartwatches via Web API',
  },
  {
    id: 'garmin',
    name: 'Garmin Connect',
    provider: 'Garmin',
    icon: '🔵',
    connected: false,
    lastSync: null,
    status: 'disconnected',
    metricsAvailable: ['Heart Rate', 'HRV', 'Sleep', 'Body Battery', 'Stress Level', 'SpO2'],
    dataPoints: 0,
    description: 'Garmin wearables with advanced stress & body battery',
  },
  {
    id: 'whoop',
    name: 'WHOOP',
    provider: 'WHOOP',
    icon: '🟢',
    connected: false,
    lastSync: null,
    status: 'disconnected',
    metricsAvailable: ['HRV', 'Recovery Score', 'Strain', 'Sleep Performance', 'Respiratory Rate'],
    dataPoints: 0,
    description: 'WHOOP band recovery, strain, and sleep coaching',
  },
  {
    id: 'oura',
    name: 'Oura Ring',
    provider: 'Oura',
    icon: '⭕',
    connected: false,
    lastSync: null,
    status: 'disconnected',
    metricsAvailable: ['HRV', 'Readiness Score', 'Sleep Score', 'Body Temperature', 'SpO2'],
    dataPoints: 0,
    description: 'Oura Ring sleep, readiness, and activity insights',
  },
];

const MOCK_SNAPSHOTS: BiometricSnapshot[] = [
  { label: 'Resting Heart Rate', value: '--', unit: 'bpm', trend: 'stable', status: 'good', source: 'No device' },
  { label: 'Heart Rate Variability', value: '--', unit: 'ms', trend: 'stable', status: 'good', source: 'No device' },
  { label: 'Sleep Quality', value: '--', unit: 'score', trend: 'stable', status: 'good', source: 'No device' },
  { label: 'Stress Level', value: '--', unit: '', trend: 'stable', status: 'good', source: 'No device' },
  { label: 'Recovery Score', value: '--', unit: '%', trend: 'stable', status: 'good', source: 'No device' },
  { label: 'Activity Level', value: '--', unit: 'min', trend: 'stable', status: 'good', source: 'No device' },
];

const statusConfig = {
  connected: { color: 'bg-green-500', text: 'Connected', icon: CheckCircle },
  disconnected: { color: 'bg-gray-500', text: 'Not Connected', icon: XCircle },
  syncing: { color: 'bg-blue-500', text: 'Syncing...', icon: RefreshCw },
  error: { color: 'bg-red-500', text: 'Error', icon: AlertTriangle },
};

async function connectDevice(deviceId: string): Promise<{ success: boolean; authUrl?: string; requiresMobile?: boolean; message?: string }> {
  const result = await biometricService.connectProvider(deviceId);
  return {
    success: result.success,
    authUrl: result.auth_url,
    requiresMobile: result.requires_mobile,
    message: result.message,
  };
}

const BiometricIntegrations: React.FC = () => {
  const [devices, setDevices] = useState<WearableDevice[]>(DEVICES);
  const [snapshots] = useState<BiometricSnapshot[]>(MOCK_SNAPSHOTS);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'devices' | 'metrics' | 'settings'>('devices');

  const connectedCount = devices.filter(d => d.connected).length;
  const totalDataPoints = devices.reduce((sum, d) => sum + d.dataPoints, 0);

  const handleConnect = async (deviceId: string) => {
    setConnecting(deviceId);
    try {
      const result = await connectDevice(deviceId);

      if (result.requiresMobile) {
        alert(result.message || 'This device requires the PsychSync mobile app.');
        return;
      }

      if (result.authUrl) {
        window.open(result.authUrl, '_blank', 'width=600,height=700');
      }

      if (result.success) {
        setDevices(prev =>
          prev.map(d =>
            d.id === deviceId
              ? { ...d, connected: true, status: 'connected' as const, lastSync: 'Just now' }
              : d
          )
        );
      }
    } catch {
      // API unavailable — show device as errored
      setDevices(prev =>
        prev.map(d =>
          d.id === deviceId ? { ...d, status: 'error' as const } : d
        )
      );
    } finally {
      setConnecting(null);
    }
  };

  const handleDisconnect = async (deviceId: string) => {
    try {
      await biometricService.disconnectProvider(deviceId);
    } catch {
      // Continue with local state update even if API fails
    }
    setDevices(prev =>
      prev.map(d =>
        d.id === deviceId
          ? { ...d, connected: false, status: 'disconnected' as const, lastSync: null, dataPoints: 0 }
          : d
      )
    );
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (trend === 'down') return <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Watch className="w-8 h-8 text-emerald-400" />
          <h1 className="text-3xl font-bold">Biometric Integrations</h1>
        </div>
        <p className="text-gray-400">
          Connect wearable devices to monitor health, stress, and recovery signals in real-time
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Devices Connected</p>
                <p className="text-2xl font-bold text-emerald-400">{connectedCount}</p>
              </div>
              <Smartphone className="w-8 h-8 text-emerald-400/30" />
            </div>
            <p className="text-xs text-gray-500 mt-1">of {devices.length} available</p>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Data Points</p>
                <p className="text-2xl font-bold text-blue-400">{totalDataPoints.toLocaleString()}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-400/30" />
            </div>
            <p className="text-xs text-gray-500 mt-1">collected this month</p>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Sync Status</p>
                <p className="text-2xl font-bold text-gray-400">
                  {connectedCount > 0 ? 'Active' : 'Inactive'}
                </p>
              </div>
              <RefreshCw className="w-8 h-8 text-gray-400/30" />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {connectedCount > 0 ? 'Auto-sync every 15 min' : 'Connect a device to start'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Health Score</p>
                <p className="text-2xl font-bold text-gray-500">--</p>
              </div>
              <Heart className="w-8 h-8 text-red-400/30" />
            </div>
            <p className="text-xs text-gray-500 mt-1">Connect devices to calculate</p>
          </CardContent>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-gray-800 pb-2">
        {(['devices', 'metrics', 'settings'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-gray-800 text-white border-b-2 border-emerald-400'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            {tab === 'devices' && 'Device Connections'}
            {tab === 'metrics' && 'Live Metrics'}
            {tab === 'settings' && 'Sync Settings'}
          </button>
        ))}
      </div>

      {/* Devices Tab */}
      {activeTab === 'devices' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map(device => {
            const config = statusConfig[device.status];
            const StatusIcon = config.icon;

            return (
              <Card key={device.id} className={`bg-gray-900 border-gray-800 ${device.connected ? 'border-emerald-500/30' : ''}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{device.icon}</span>
                      <div>
                        <CardTitle className="text-lg">{device.name}</CardTitle>
                        <CardDescription className="text-xs">{device.provider}</CardDescription>
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={`${device.connected ? 'border-emerald-500 text-emerald-400' : 'border-gray-600 text-gray-400'}`}
                    >
                      <StatusIcon className="w-3 h-3 mr-1" />
                      {config.text}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-400 mb-3">{device.description}</p>

                  <div className="mb-3">
                    <p className="text-xs text-gray-500 mb-1.5">Available Metrics:</p>
                    <div className="flex flex-wrap gap-1">
                      {device.metricsAvailable.map(metric => (
                        <Badge key={metric} variant="secondary" className="text-xs bg-gray-800 text-gray-300">
                          {metric}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {device.lastSync && (
                    <div className="flex items-center gap-1 text-xs text-gray-500 mb-3">
                      <Clock className="w-3 h-3" />
                      Last sync: {device.lastSync}
                    </div>
                  )}

                  {device.connected ? (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
                        onClick={() => handleConnect(device.id)}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" /> Sync Now
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                        onClick={() => handleDisconnect(device.id)}
                      >
                        Disconnect
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                      onClick={() => handleConnect(device.id)}
                      disabled={connecting === device.id}
                    >
                      {connecting === device.id ? (
                        <>
                          <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> Connecting...
                        </>
                      ) : (
                        'Connect Device'
                      )}
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Metrics Tab */}
      {activeTab === 'metrics' && (
        <div>
          {connectedCount === 0 ? (
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-12 text-center">
                <Watch className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-300 mb-2">No Devices Connected</h3>
                <p className="text-gray-500 mb-4">Connect a wearable device to see live biometric metrics</p>
                <Button
                  className="bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => setActiveTab('devices')}
                >
                  Connect a Device
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {snapshots.map((metric, i) => (
                <Card key={i} className="bg-gray-900 border-gray-800">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-gray-400">{metric.label}</p>
                      {getTrendIcon(metric.trend)}
                    </div>
                    <p className="text-3xl font-bold">
                      {metric.value}
                      <span className="text-sm text-gray-500 ml-1">{metric.unit}</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Source: {metric.source}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" /> Sync Settings
            </CardTitle>
            <CardDescription>Configure how biometric data is collected and processed</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="text-sm font-medium text-gray-300 block mb-2">Sync Frequency</label>
                <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white">
                  <option value="5">Every 5 minutes</option>
                  <option value="15" selected>Every 15 minutes</option>
                  <option value="30">Every 30 minutes</option>
                  <option value="60">Every hour</option>
                  <option value="manual">Manual only</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-300 block mb-2">Data Retention</label>
                <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white">
                  <option value="30">30 days</option>
                  <option value="90" selected>90 days</option>
                  <option value="180">6 months</option>
                  <option value="365">1 year</option>
                </select>
              </div>
            </div>

            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Privacy Controls</h4>
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="w-4 h-4 rounded bg-gray-800 border-gray-600" />
                  <span className="text-sm text-gray-400">Share anonymized data with team health analytics</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="w-4 h-4 rounded bg-gray-800 border-gray-600" />
                  <span className="text-sm text-gray-400">Enable stress level alerts for burnout prevention</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded bg-gray-800 border-gray-600" />
                  <span className="text-sm text-gray-400">Allow manager to view aggregated wellness score</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end">
              <Button className="bg-emerald-600 hover:bg-emerald-700">Save Settings</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BiometricIntegrations;
