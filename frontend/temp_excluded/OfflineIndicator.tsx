/**
 * Offline Indicator Component
 * 
 * Shows user's connection status and sync state
 * Provides manual sync button when offline
 */

import React from 'react';
import { useOfflineIndicator, useOffline } from '../hooks/useOffline';

const OfflineIndicator = () => {
  const { status, isOnline, isSyncing, pendingCount } = useOfflineIndicator();
  const { triggerSync } = useOffline();

  // Don't show indicator if online with nothing pending
  if (isOnline && pendingCount === 0 && !isSyncing) {
    return null;
  }

  const getIcon = () => {
    switch (status.type) {
      case 'syncing':
        return (
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
      case 'offline':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
          </svg>
        );
      case 'pending':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getBackgroundColor = () => {
    const colors: Record<string, string> = {
      blue: 'bg-blue-500',
      orange: 'bg-orange-500',
      yellow: 'bg-yellow-500',
      green: 'bg-green-500'
    };
    return colors[status.color] || 'bg-gray-500';
  };

  const handleSyncClick = async () => {
    if (isOnline && !isSyncing) {
      try {
        await triggerSync();
      } catch (error) {
        console.error('Manual sync failed:', error);
      }
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div
        className={`${getBackgroundColor()} text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-3 transition-all duration-300 hover:shadow-xl`}
      >
        <div className="flex items-center gap-2">
          {getIcon()}
          <span className="text-sm font-medium">{status.message}</span>
        </div>
        
        {isOnline && pendingCount > 0 && !isSyncing && (
          <button
            onClick={handleSyncClick}
            className="ml-2 px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-xs font-medium transition-colors"
          >
            Sync Now
          </button>
        )}
      </div>
    </div>
  );
};

export default OfflineIndicator;
