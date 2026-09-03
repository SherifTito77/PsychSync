import React, { useState, useEffect } from 'react';
import { pwaManager, OfflineStatus } from '../utils/pwaManager';

interface OfflineStatusProps {
  className?: string;
  showDetailedInfo?: boolean;
}

/**
 * 📱 Offline Status Indicator Component
 *
 * Displays real-time network status and connection information
 * Provides visual feedback for offline/online state transitions
 */
const OfflineStatusIndicator: React.FC<OfflineStatusProps> = ({
  className = '',
  showDetailedInfo = false
}) => {
  const [offlineStatus, setOfflineStatus] = useState<OfflineStatus | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    const updateStatus = () => {
      const status = pwaManager.getOfflineStatus();
      setOfflineStatus(status);

      if (status.isOnline) {
        setStatusMessage('You\'re online');
        setTimeout(() => setShowDetails(false), 3000);
      } else {
        setStatusMessage('You\'re offline - working in limited mode');
        setShowDetails(true);
      }
    };

    // Initial status
    updateStatus();

    // Set up status change listeners
    pwaManager.setOnNetworkStatusChange((isOnline) => {
      updateStatus();
    });

    // Update status every 10 seconds
    const interval = setInterval(updateStatus, 10000);

    return () => clearInterval(interval);
  }, []);

  if (!offlineStatus) {
    return null;
  }

  const getConnectionQuality = () => {
    if (!offlineStatus.isOnline) return 'offline';

    switch (offlineStatus.effectiveType) {
      case 'slow-2g':
      case '2g':
        return 'poor';
      case '3g':
        return 'fair';
      case '4g':
        return 'good';
      default:
        return 'unknown';
    }
  };

  const getConnectionColor = () => {
    const quality = getConnectionQuality();

    switch (quality) {
      case 'offline':
        return 'bg-yellow-500';
      case 'poor':
        return 'bg-orange-500';
      case 'fair':
        return 'bg-blue-500';
      case 'good':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getConnectionIcon = () => {
    const quality = getConnectionQuality();

    switch (quality) {
      case 'offline':
        return '📱';
      case 'poor':
        return '📶';
      case 'fair':
        return '📡';
      case 'good':
        return '📡';
      default:
        return '❓';
    }
  };

  const formatSpeed = (downlink: number) => {
    if (downlink === 0) return 'Unknown';
    return `${downlink.toFixed(1)} Mbps`;
  };

  return (
    <div className={`offline-status-indicator ${className}`}>
      {/* Status Bar */}
      <div
        className={`fixed top-0 left-0 right-0 ${getConnectionColor()} text-white text-center py-2 px-4 z-50 transition-all duration-300 ${
          offlineStatus.isOnline ? 'opacity-0 -translate-y-full' : 'opacity-100 translate-y-0'
        }`}
      >
        <div className="flex items-center justify-center space-x-2">
          <span className="text-lg">{getConnectionIcon()}</span>
          <span className="font-medium text-sm">{statusMessage}</span>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="ml-2 text-white/80 hover:text-white transition-colors"
          >
            {showDetails ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* Detailed Status Panel */}
      {showDetailedInfo && showDetails && (
        <div className="fixed top-12 left-4 right-4 md:left-auto md:right-4 md:w-80 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-40">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="mr-2">{getConnectionIcon()}</span>
            Network Status
          </h3>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`text-sm font-medium ${
                offlineStatus.isOnline ? 'text-green-600' : 'text-yellow-600'
              }`}>
                {offlineStatus.isOnline ? 'Online' : 'Offline'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Connection:</span>
              <span className="text-sm font-medium capitalize">
                {offlineStatus.connectionType || 'Unknown'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Quality:</span>
              <span className={`text-sm font-medium capitalize ${
                getConnectionQuality() === 'good' ? 'text-green-600' :
                getConnectionQuality() === 'fair' ? 'text-blue-600' :
                getConnectionQuality() === 'poor' ? 'text-orange-600' :
                'text-yellow-600'
              }`}>
                {getConnectionQuality()}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Speed:</span>
              <span className="text-sm font-medium">
                {formatSpeed(offlineStatus.downlink)}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Latency:</span>
              <span className="text-sm font-medium">
                {offlineStatus.rtt}ms
              </span>
            </div>

            {offlineStatus.saveData && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-2 mt-3">
                <div className="flex items-center">
                  <span className="text-yellow-600 mr-2">💾</span>
                  <span className="text-sm text-yellow-800">
                    Data saver mode is active
                  </span>
                </div>
              </div>
            )}

            {!offlineStatus.isOnline && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
                <div className="flex items-start">
                  <span className="text-blue-600 mr-2 text-lg">ℹ️</span>
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Offline Mode Active</p>
                    <p className="text-xs">
                      You can continue working with cached data. Changes will sync when you're back online.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => setShowDetails(false)}
            className="mt-4 w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
};

export default OfflineStatusIndicator;
