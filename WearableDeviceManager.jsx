import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Watch, Heart, Activity, Moon, Smartphone, Wifi, Battery,
  Plus, Settings, Sync, CheckCircle, AlertCircle, XCircle,
  TrendingUp, Calendar, Download, Shield, Zap, Cloud,
  Bluetooth, Smartphone as Mobile, Monitor, Watch as Smartwatch
} from 'lucide-react';

const WearableDeviceManager = ({ onDataUpdate, userId }) => {
  const [connectedDevices, setConnectedDevices] = useState([]);
  const [availableDevices, setAvailableDevices] = useState([]);
  const [syncStatus, setSyncStatus] = useState({});
  const [healthData, setHealthData] = useState(null);
  const [insights, setInsights] = useState([]);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);

  const deviceTypes = [
    {
      id: 'apple_health',
      name: 'Apple Health',
      icon: Smartphone,
      color: '#000000',
      description: 'Connect with Apple HealthKit for comprehensive health data',
      capabilities: ['Heart Rate', 'Steps', 'Sleep', 'Workouts', 'Nutrition'],
      platforms: ['iOS'],
      popular: true
    },
    {
      id: 'fitbit',
      name: 'Fitbit',
      icon: Activity,
      color: '#00b0b9',
      description: 'Sync with Fitbit devices and apps',
      capabilities: ['Steps', 'Heart Rate', 'Sleep', 'Calories', 'Floors'],
      platforms: ['iOS', 'Android', 'Web'],
      popular: true
    },
    {
      id: 'garmin',
      name: 'Garmin Connect',
      icon: Smartwatch,
      color: '#007cc3',
      description: 'Connect Garmin watches and fitness devices',
      capabilities: ['GPS Activities', 'Heart Rate', 'Recovery', 'Training Load'],
      platforms: ['iOS', 'Android', 'Web'],
      popular: true
    },
    {
      id: 'oura',
      name: 'Oura Ring',
      icon: Heart,
      color: '#000000',
      description: 'Advanced sleep and recovery tracking',
      capabilities: ['Sleep Analysis', 'Readiness', 'HRV', 'Temperature'],
      platforms: ['iOS', 'Android'],
      popular: false
    },
    {
      id: 'whoop',
      name: 'Whoop',
      icon: Zap,
      color: '#000000',
      description: 'Strain, recovery, and sleep optimization',
      capabilities: ['Recovery Score', 'Strain', 'Sleep Performance', 'HRV'],
      platforms: ['iOS', 'Android'],
      popular: false
    },
    {
      id: 'polar',
      name: 'Polar',
      icon: Heart,
      color: '#ff0000',
      description: 'Heart rate and fitness tracking',
      capabilities: ['Heart Rate', 'Running Power', 'Sleep Plus'],
      platforms: ['iOS', 'Android', 'Web'],
      popular: false
    },
    {
      id: 'withings',
      name: 'Withings',
      icon: Monitor,
      color: '#34a85a',
      description: 'Smart scales and health monitors',
      capabilities: ['Weight', 'Body Composition', 'Blood Pressure', 'Sleep'],
      platforms: ['iOS', 'Android', 'Web'],
      popular: false
    }
  ];

  useEffect(() => {
    loadConnectedDevices();
    loadHealthData();
  }, []);

  const loadConnectedDevices = async () => {
    try {
      const response = await fetch(`/api/health-devices/${userId}/connections`);
      const data = await response.json();
      setConnectedDevices(data.devices || []);
    } catch (error) {
      console.error('Failed to load connected devices:', error);
    }
  };

  const loadHealthData = async () => {
    try {
      const response = await fetch(`/api/health-data/${userId}/summary`);
      const data = await response.json();
      setHealthData(data.summary);
      setInsights(data.insights || []);
    } catch (error) {
      console.error('Failed to load health data:', error);
    }
  };

  const handleConnectDevice = async (deviceType) => {
    try {
      // Initiate OAuth flow for device connection
      const authUrl = `/api/health-devices/${deviceType}/auth?user_id=${userId}`;
      window.open(authUrl, '_blank', 'width=500,height=600');

      // Poll for connection completion
      const checkConnection = setInterval(async () => {
        const response = await fetch(`/api/health-devices/${userId}/connections`);
        const data = await response.json();

        if (data.devices.some(d => d.type === deviceType)) {
          clearInterval(checkConnection);
          setShowConnectModal(false);
          loadConnectedDevices();
          loadHealthData();
        }
      }, 2000);

      // Timeout after 5 minutes
      setTimeout(() => clearInterval(checkConnection), 300000);
    } catch (error) {
      console.error('Failed to connect device:', error);
    }
  };

  const handleDisconnectDevice = async (deviceId) => {
    try {
      await fetch(`/api/health-devices/${userId}/disconnect/${deviceId}`, {
        method: 'DELETE'
      });
      loadConnectedDevices();
    } catch (error) {
      console.error('Failed to disconnect device:', error);
    }
  };

  const handleSyncDevice = async (deviceId) => {
    try {
      setSyncStatus(prev => ({ ...prev, [deviceId]: 'syncing' }));

      await fetch(`/api/health-devices/${userId}/sync/${deviceId}`, {
        method: 'POST'
      });

      setSyncStatus(prev => ({ ...prev, [deviceId]: 'success' }));
      loadHealthData();

      // Reset status after delay
      setTimeout(() => {
        setSyncStatus(prev => ({ ...prev, [deviceId]: null }));
      }, 2000);
    } catch (error) {
      console.error('Failed to sync device:', error);
      setSyncStatus(prev => ({ ...prev, [deviceId]: 'error' }));
    }
  };

  const renderHealthMetrics = () => {
    if (!healthData) return null;

    const metrics = [
      {
        label: 'Steps Today',
        value: healthData.steps?.value || 0,
        unit: healthData.steps?.unit || 'steps',
        icon: Activity,
        color: '#10b981',
        trend: '+12%'
      },
      {
        label: 'Heart Rate',
        value: healthData.heartRate?.value || 0,
        unit: healthData.heartRate?.unit || 'bpm',
        icon: Heart,
        color: '#ef4444',
        trend: 'Normal'
      },
      {
        label: 'Sleep Last Night',
        value: healthData.sleepDuration?.value || 0,
        unit: 'hours',
        icon: Moon,
        color: '#6366f1',
        trend: '+0.5h'
      },
      {
        label: 'Recovery Score',
        value: healthData.recoveryScore?.value || 0,
        unit: '%',
        icon: Zap,
        color: '#f59e0b',
        trend: 'Good'
      }
    ];

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
      >
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 rounded-lg" style={{ backgroundColor: `${metric.color}20` }}>
                <metric.icon className="h-5 w-5" style={{ color: metric.color }} />
              </div>
              <span className="text-sm text-green-600 font-medium">{metric.trend}</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(metric.value)}
              <span className="text-sm font-normal text-gray-500 ml-1">{metric.unit}</span>
            </div>
            <div className="text-sm text-gray-600 mt-1">{metric.label}</div>
          </motion.div>
        ))}
      </motion.div>
    );
  };

  const renderConnectedDevices = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="bg-white rounded-xl shadow-sm p-6 mb-8"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Connected Devices</h3>
        <button
          onClick={() => setShowConnectModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Connect Device</span>
        </button>
      </div>

      {connectedDevices.length === 0 ? (
        <div className="text-center py-12">
          <Bluetooth className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">No Connected Devices</h4>
          <p className="text-gray-600 mb-6">Connect your wearable devices to sync health data automatically</p>
          <button
            onClick={() => setShowConnectModal(true)}
            className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-5 w-5" />
            <span>Connect Your First Device</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {connectedDevices.map((device, index) => {
            const deviceType = deviceTypes.find(t => t.id === device.type);
            const Icon = deviceType?.icon || Smartphone;

            return (
              <motion.div
                key={device.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg" style={{ backgroundColor: `${deviceType?.color}20` }}>
                      <Icon className="h-5 w-5" style={{ color: deviceType?.color }} />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{deviceType?.name}</h4>
                      <p className="text-sm text-gray-600">
                        Last sync: {device.lastSync ? new Date(device.lastSync).toLocaleDateString() : 'Never'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      device.connected
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {device.connected ? (
                        <CheckCircle className="h-3 w-3 mr-1" />
                      ) : (
                        <XCircle className="h-3 w-3 mr-1" />
                      )}
                      {device.connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="text-sm text-gray-600 mb-2">Capabilities:</div>
                  <div className="flex flex-wrap gap-2">
                    {deviceType?.capabilities.map(cap => (
                      <span key={cap} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleSyncDevice(device.id)}
                    disabled={!device.connected}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      device.connected
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <Sync className={`h-4 w-4 ${syncStatus[device.id] === 'syncing' ? 'animate-spin' : ''}`} />
                    <span>
                      {syncStatus[device.id] === 'syncing'
                        ? 'Syncing...'
                        : syncStatus[device.id] === 'success'
                        ? 'Synced!'
                        : 'Sync Now'}
                    </span>
                  </button>

                  <button
                    onClick={() => handleDisconnectDevice(device.id)}
                    className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    <Settings className="h-4 w-4" />
                    <span>Settings</span>
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );

  const renderInsights = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.7 }}
      className="bg-white rounded-xl shadow-sm p-6 mb-8"
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Health Insights</h3>

      {insights.length === 0 ? (
        <div className="text-center py-8">
          <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Connect more devices to get personalized insights</p>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((insight, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + index * 0.1 }}
              className={`p-4 rounded-lg border-l-4 ${
                insight.level === 'warning'
                  ? 'bg-yellow-50 border-yellow-400'
                  : insight.level === 'error'
                  ? 'bg-red-50 border-red-400'
                  : 'bg-blue-50 border-blue-400'
              }`}
            >
              <div className="flex items-start space-x-3">
                {insight.level === 'warning' ? (
                  <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                ) : insight.level === 'error' ? (
                  <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                ) : (
                  <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                )}
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{insight.title}</h4>
                  <p className="text-gray-600 mt-1">{insight.message}</p>
                  {insight.recommendation && (
                    <p className="text-sm text-gray-500 mt-2">💡 {insight.recommendation}</p>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );

  const renderConnectModal = () => (
    <AnimatePresence>
      {showConnectModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setShowConnectModal(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto"
          >
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-900">Connect Health Device</h3>
                <button
                  onClick={() => setShowConnectModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {deviceTypes.map((device) => {
                  const isPopular = device.popular;
                  const Icon = device.icon;
                  const isConnected = connectedDevices.some(d => d.type === device.id);

                  return (
                    <motion.div
                      key={device.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => !isConnected && handleConnectDevice(device.id)}
                      className={`relative border rounded-lg p-4 cursor-pointer transition-all ${
                        isConnected
                          ? 'border-green-300 bg-green-50 cursor-not-allowed'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                      }`}
                    >
                      {isPopular && (
                        <div className="absolute -top-2 -right-2 px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
                          Popular
                        </div>
                      )}

                      {isConnected && (
                        <div className="absolute top-2 right-2">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        </div>
                      )}

                      <div className="flex items-start space-x-3">
                        <div className="p-2 rounded-lg" style={{ backgroundColor: `${device.color}20` }}>
                          <Icon className="h-6 w-6" style={{ color: device.color }} />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">{device.name}</h4>
                          <p className="text-sm text-gray-600 mt-1">{device.description}</p>

                          <div className="mt-3">
                            <div className="text-xs text-gray-500 mb-2">Connects via:</div>
                            <div className="flex flex-wrap gap-1 mb-3">
                              {device.platforms.map(platform => (
                                <span key={platform} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  {platform}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div className="mt-3">
                            <div className="text-xs text-gray-500 mb-2">Tracks:</div>
                            <div className="flex flex-wrap gap-1">
                              {device.capabilities.slice(0, 3).map(cap => (
                                <span key={cap} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  {cap}
                                </span>
                              ))}
                              {device.capabilities.length > 3 && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  +{device.capabilities.length - 3} more
                                </span>
                              )}
                            </div>
                          </div>

                          {!isConnected && (
                            <button className="mt-3 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
                              Connect
                            </button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Health Devices</h1>
              <p className="text-gray-600">Connect your wearables and sync health data</p>
            </div>
            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <Download className="h-4 w-4" />
                <span>Export Data</span>
              </button>
              <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <Shield className="h-4 w-4" />
                <span>Privacy Settings</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {healthData && renderHealthMetrics()}
        {renderConnectedDevices()}
        {renderInsights()}
        {renderConnectModal()}
      </div>
    </div>
  );
};

export default WearableDeviceManager;
