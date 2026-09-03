/**
 * Real-World Example: Using Safe Hooks
 *
 * This component demonstrates the safe hooks in a practical scenario.
 * Replace your existing components with this pattern.
 */

import React, { useState } from 'react';
import { useAsyncEffect, useSafeFetch, useSafeInterval, useSafeTimeout } from '../../hooks/useAsyncEffect';

/**
 * Example 1: User Profile Component
 * Replaces: Any component that fetches user data on mount
 */
export function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ✅ OLD WAY (Unsafe - causes race conditions):
  // useEffect(() => {
  //   const fetchUser = async () => {
  //     const data = await fetch(`/api/users/${userId}`).then(r => r.json());
  //     setUser(data); // ⚠️ May update after unmount!
  //   };
  //   fetchUser();
  // }, [userId]);

  // ✅ NEW WAY (Safe - automatic cleanup):
  useAsyncEffect(async (signal, isMounted) => {
    try {
      const response = await fetch(`/api/users/${userId}`, { signal });
      const data = await response.json();

      // Only update if still mounted
      if (isMounted()) {
        setUser(data);
        setLoading(false);
      }
    } catch (err) {
      if (err.name !== 'AbortError' && isMounted()) {
        setError(err);
        setLoading(false);
      }
    }
  }, [userId]);

  if (loading) return <div className="p-4">Loading user...</div>;
  if (error) return <div className="p-4 text-red-500">Error loading user</div>;

  return (
    <div className="p-4 border rounded">
      <h2 className="text-xl font-bold">{user?.name}</h2>
      <p className="text-gray-600">{user?.email}</p>
    </div>
  );
}

/**
 * Example 2: Auto-Refreshing Dashboard
 * Replaces: Any dashboard component with polling/refresh
 */
export function LiveDashboard() {
  // ✅ Use useSafeFetch for simple data fetching
  const { data: stats, loading, error } = useSafeFetch(
    '/api/dashboard/stats',
    {},
    [] // Empty deps - fetch once on mount
  );

  // ✅ Use useSafeInterval for auto-refresh
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useSafeInterval(
    () => {
      setLastUpdate(new Date());
    },
    30000, // Refresh every 30 seconds
    { runOnMount: false } // Don't run immediately
  );

  if (loading) return <div>Loading dashboard...</div>;
  if (error) return <div>Error loading dashboard</div>;

  return (
    <div className="p-4 border rounded">
      <h2 className="text-xl font-bold mb-4">Dashboard Stats</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-3 rounded">
          <div className="text-2xl font-bold">{(stats as any)?.totalUsers || 0}</div>
          <div className="text-sm text-gray-600">Total Users</div>
        </div>
        <div className="bg-green-50 p-3 rounded">
          <div className="text-2xl font-bold">{(stats as any)?.activeSessions || 0}</div>
          <div className="text-sm text-gray-600">Active Sessions</div>
        </div>
      </div>
      <div className="mt-4 text-xs text-gray-500">
        Last updated: {lastUpdate.toLocaleTimeString()}
      </div>
    </div>
  );
}

/**
 * Example 3: Notification with Auto-Dismiss
 * Replaces: Any notification/alert component with setTimeout
 */
export function AutoNotification({ message, duration = 5000 }: { message: string; duration?: number }) {
  const [visible, setVisible] = useState(true);

  // ✅ Auto-dismiss after duration
  useSafeTimeout(
    () => {
      setVisible(false);
    },
    duration
  );

  if (!visible) return null;

  return (
    <div className="fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded shadow-lg">
      {message}
    </div>
  );
}

/**
 * Example 4: Real-Time Activity Feed
 * Replaces: Any component with polling/periodic updates
 */
export function ActivityFeed() {
  const [activities, setActivities] = useState([]);

  // ✅ Poll for new activities every 10 seconds
  useSafeInterval(
    async () => {
      try {
        const response = await fetch('/api/activities/latest');
        const data = await response.json();
        setActivities(data);
      } catch (error) {
        console.error('Failed to fetch activities:', error);
      }
    },
    10000, // 10 seconds
    { runOnMount: true } // Also run immediately on mount
  );

  return (
    <div className="p-4 border rounded">
      <h3 className="font-bold mb-2">Recent Activity</h3>
      {activities.length === 0 ? (
        <p className="text-gray-500">No recent activity</p>
      ) : (
        <ul className="space-y-2">
          {activities.map((activity: any) => (
            <li key={activity.id} className="text-sm p-2 bg-gray-50 rounded">
              <span className="font-medium">{activity.user}</span>: {activity.action}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * Example 5: Search with Debounce
 * Replaces: Any search component with manual setTimeout
 */
export function SearchWithDebounce() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searchTimeout, setSearchTimeout] = useState<number | null>(null);

  const handleSearch = (value: string) => {
    setQuery(value);

    // ✅ Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    // ✅ Set new timeout (debounce)
    const timeoutId = window.setTimeout(async () => {
      if (value.trim()) {
        const response = await fetch(`/api/search?q=${encodeURIComponent(value)}`);
        const data = await response.json();
        setResults(data);
      } else {
        setResults([]);
      }
    }, 300); // 300ms debounce

    setSearchTimeout(timeoutId);
  };

  // ✅ Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    };
  }, [searchTimeout]);

  return (
    <div className="p-4 border rounded">
      <input
        type="text"
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
        placeholder="Search..."
        className="w-full p-2 border rounded"
      />
      {results.length > 0 && (
        <ul className="mt-2 space-y-1">
          {results.map((result: any) => (
            <li key={result.id} className="p-2 bg-gray-50 rounded">
              {result.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * Example 6: Form with Auto-Save
 * Replaces: Any form with manual setTimeout for auto-save
 */
export function AutoSaveForm() {
  const [formData, setFormData] = useState({ title: '', content: '' });
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [saveTimeout, setSaveTimeout] = useState<number | null>(null);

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setSaveStatus('saving');

    // ✅ Clear previous timeout
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }

    // ✅ Auto-save after 2 seconds of no changes
    const timeoutId = window.setTimeout(async () => {
      try {
        await fetch('/api/drafts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        setSaveStatus('saved');
      } catch (error) {
        console.error('Auto-save failed:', error);
      }
    }, 2000);

    setSaveTimeout(timeoutId);
  };

  // ✅ Cleanup
  React.useEffect(() => {
    return () => {
      if (saveTimeout) {
        clearTimeout(saveTimeout);
      }
    };
  }, [saveTimeout]);

  return (
    <div className="p-4 border rounded">
      <h2 className="text-xl font-bold mb-4">Auto-Save Draft</h2>
      <div className="space-y-4">
        <input
          type="text"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="Title"
          className="w-full p-2 border rounded"
        />
        <textarea
          value={formData.content}
          onChange={(e) => handleChange('content', e.target.value)}
          placeholder="Content..."
          rows={5}
          className="w-full p-2 border rounded"
        />
        <div className="text-sm">
          Status:{' '}
          <span className={`font-medium ${
            saveStatus === 'saved' ? 'text-green-600' :
            saveStatus === 'saving' ? 'text-yellow-600' :
            'text-gray-600'
          }`}>
            {saveStatus === 'saved' ? '✓ Saved' :
             saveStatus === 'saving' ? 'Saving...' :
             'Idle'}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Export all examples
 */
export default {
  UserProfile,
  LiveDashboard,
  AutoNotification,
  ActivityFeed,
  SearchWithDebounce,
  AutoSaveForm
};
