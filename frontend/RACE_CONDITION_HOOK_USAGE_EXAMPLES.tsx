/**
 * 📚 Safe Hooks Usage Examples
 *
 * This file demonstrates how to use the custom safe hooks
 * to prevent race conditions in your components.
 *
 * Import from: @/hooks/useAsyncEffect
 */

import { useAsyncEffect, useSafeFetch, useSafeInterval, useSafeTimeout } from '@/hooks/useAsyncEffect';
import { useState, useEffect } from 'react';

// ============================================================================
// Example 1: useAsyncEffect - Safe Async Operations
// ============================================================================

export function UserProfile({ userId }: { userId: string }) {
  const [profile, setProfile] = useState(null);

  // ✅ SAFE: Auto-cleanup on unmount, no state updates after unmount
  useAsyncEffect(async (signal, isMounted) => {
    // signal: AbortSignal for cancelling fetch
    // isMounted: Function to check if component is still mounted

    try {
      const response = await fetch(`/api/users/${userId}`, {
        signal  // ✅ Pass signal to enable cancellation
      });

      // ✅ Check if still mounted before processing response
      if (!isMounted()) {
        return; // Component unmounted, abort
      }

      if (response.ok) {
        const data = await response.json();

        // ✅ Check again before state update
        if (isMounted()) {
          setProfile(data);
        }
      }
    } catch (error) {
      // ✅ Ignore abort errors (normal cancellation)
      if (error.name !== 'AbortError' && isMounted()) {
        console.error('Failed to load profile:', error);
      }
    }
  }, [userId]); // Dependency array - effect reruns when userId changes

  return (
    <div>
      {profile ? <h1>{profile.name}</h1> : <p>Loading...</p>}
    </div>
  );
}

// ============================================================================
// Example 2: useSafeFetch - Automatic Fetch with Loading States
// ============================================================================

export function Dashboard() {
  // ✅ SAFE: Automatic fetch with data, loading, error states
  const { data: stats, loading, error } = useSafeFetch(
    '/api/dashboard/stats',
    {}, // fetch options
    []  // dependencies
  );

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Dashboard Stats</h2>
      <pre>{JSON.stringify(stats, null, 2)}</pre>
    </div>
  );
}

// ============================================================================
// Example 3: useSafeInterval - Periodic Data Refresh
// ============================================================================

export function LiveFeed() {
  const [posts, setPosts] = useState([]);

  // ✅ SAFE: Auto-cleanup on unmount
  useSafeInterval(
    async () => {
      try {
        const response = await fetch('/api/posts/latest');
        const data = await response.json();
        setPosts(data);
      } catch (error) {
        console.error('Failed to fetch posts:', error);
      }
    },
    5000,  // Run every 5 seconds
    { runOnMount: true }  // ✅ Also run immediately on mount
  );

  return (
    <div>
      <h2>Live Feed</h2>
      {posts.map(post => (
        <div key={post.id}>{post.title}</div>
      ))}
    </div>
  );
}

// ============================================================================
// Example 4: useSafeTimeout - Delayed Actions
// ============================================================================

export function Notification({ message, duration }: { message: string, duration: number }) {
  const [visible, setVisible] = useState(true);

  // ✅ SAFE: Auto-clear timeout on unmount
  useSafeTimeout(
    () => {
      setVisible(false);
    },
    duration  // Auto-dismiss after duration ms
  );

  if (!visible) return null;

  return (
    <div className="notification">
      {message}
    </div>
  );
}

// ============================================================================
// Example 5: Multiple Async Operations with Error Handling
// ============================================================================

export function ComplexComponent({ orderId }: { orderId: string }) {
  const [order, setOrder] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useAsyncEffect(async (signal, isMounted) => {
    try {
      // ✅ Fetch multiple resources concurrently
      const [orderRes, itemsRes] = await Promise.all([
        fetch(`/api/orders/${orderId}`, { signal }),
        fetch(`/api/orders/${orderId}/items`, { signal })
      ]);

      // ✅ Check mount status before processing
      if (!isMounted()) return;

      if (orderRes.ok && itemsRes.ok) {
        const orderData = await orderRes.json();
        const itemsData = await itemsRes.json();

        // ✅ Final check before state updates
        if (isMounted()) {
          setOrder(orderData);
          setItems(itemsData);
          setLoading(false);
        }
      }
    } catch (error) {
      // ✅ Handle abort vs real errors
      if (error.name === 'AbortError') {
        console.log('Request cancelled');
        return;
      }

      if (isMounted()) {
        console.error('Failed to load order:', error);
        setLoading(false);
      }
    }
  }, [orderId]);

  if (loading) return <div>Loading order...</div>;

  return (
    <div>
      <h2>Order #{order?.id}</h2>
      <ul>
        {items.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}

// ============================================================================
// Example 6: Polling with Conditional Execution
// ============================================================================

export function OrderStatus({ orderId }: { orderId: string }) {
  const [status, setStatus] = useState('pending');

  // ✅ SAFE: Poll for status updates
  useAsyncEffect(async (signal, isMounted) => {
    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/orders/${orderId}/status`, { signal });

        if (!isMounted()) return;

        if (response.ok) {
          const data = await response.json();

          if (isMounted()) {
            setStatus(data.status);

            // ✅ Stop polling if order is complete
            if (data.status === 'delivered') {
              return false; // Signal to stop polling
            }
          }
        }
      } catch (error) {
        if (error.name !== 'AbortError' && isMounted()) {
          console.error('Failed to check status:', error);
        }
        return false; // Stop polling on error
      }
      return true; // Continue polling
    };

    // Poll every 3 seconds
    while (await pollStatus()) {
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }, [orderId]);

  return (
    <div>
      <p>Order Status: <strong>{status}</strong></p>
    </div>
  );
}

// ============================================================================
// Example 7: Combining Multiple Safe Hooks
// ============================================================================

export function AnalyticsDashboard() {
  // ✅ SAFE: Initial data load
  const { data: overview, loading: overviewLoading } = useSafeFetch(
    '/api/analytics/overview'
  );

  // ✅ SAFE: Real-time updates
  const [liveStats, setLiveStats] = useState(null);

  useSafeInterval(
    async () => {
      try {
        const response = await fetch('/api/analytics/live');
        const data = await response.json();
        setLiveStats(data);
      } catch (error) {
        console.error('Failed to fetch live stats:', error);
      }
    },
    10000,  // Every 10 seconds
    { runOnMount: false }  // Don't run on mount (overview handles that)
  );

  // ✅ SAFE: Session timeout warning
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);

  useSafeTimeout(
    () => {
      setShowTimeoutWarning(true);
    },
    300000  // 5 minutes
  );

  if (overviewLoading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Analytics Dashboard</h2>
      <div>Overview: {JSON.stringify(overview)}</div>
      <div>Live: {JSON.stringify(liveStats)}</div>
      {showTimeoutWarning && (
        <div className="warning">Session expiring soon!</div>
      )}
    </div>
  );
}

// ============================================================================
// Comparison: OLD vs NEW (What We Fixed)
// ============================================================================

/**
 * ❌ OLD: Unsafe async effect (causes race conditions)
 */
export function UnsafeComponent_old() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/data');
      const result = await response.json();
      setData(result);  // ⚠️ May run after unmount!
    };

    fetchData();  // ⚠️ No cleanup!
  }, []);

  return <div>{data}</div>;
}

/**
 * ✅ NEW: Safe async effect (race condition free)
 */
export function SafeComponent_new() {
  const [data, setData] = useState(null);

  useAsyncEffect(async (signal, isMounted) => {
    const response = await fetch('/api/data', { signal });
    if (isMounted()) {  // ✅ Check before update
      const result = await response.json();
      if (isMounted()) {
        setData(result);  // ✅ Safe update
      }
    }
  }, []);

  return <div>{data}</div>;
}

// ============================================================================
// Quick Reference Card
// ============================================================================

/**
 * 📌 Hook Quick Reference:
 *
 * useAsyncEffect(effect, deps, options)
 *   - For: Custom async operations in useEffect
 *   - Provides: signal (AbortSignal), isMounted () => boolean
 *   - Cleanup: Automatic abort on unmount
 *
 * useSafeFetch(url, options, deps)
 *   - For: Simple data fetching
 *   - Returns: { data, loading, error }
 *   - Cleanup: Automatic abort and state protection
 *
 * useSafeInterval(callback, delay, options)
 *   - For: Periodic operations (polling, live updates)
 *   - Options: { runOnMount: boolean }
 *   - Cleanup: Automatic clearInterval on unmount
 *
 * useSafeTimeout(callback, delay)
 *   - For: Delayed operations, auto-dismiss, debouncing
 *   - Cleanup: Automatic clearTimeout on unmount
 */

export default {
  UserProfile,
  Dashboard,
  LiveFeed,
  Notification,
  ComplexComponent,
  OrderStatus,
  AnalyticsDashboard,
  SafeComponent_new
};
