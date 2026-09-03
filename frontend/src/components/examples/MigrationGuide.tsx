/**
 * 🔄 MIGRATION GUIDE: From Unsafe to Safe Hooks
 *
 * This file shows you EXACTLY how to migrate existing code
 * to use the safe hooks pattern.
 */

import { useState, useEffect } from 'react';
import { useAsyncEffect, useSafeFetch, useSafeInterval, useSafeTimeout } from '../../hooks/useAsyncEffect';

// ============================================================================
// EXAMPLE 1: Simple Data Fetching
// ============================================================================

// ❌ BEFORE: Unsafe (causes race conditions)
export function UnsafeExample1_Before() {
  const [data, setData] = useState(null);

  // ⚠️ PROBLEM: No cleanup, updates after unmount
  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/user');
      const json = await response.json();
      setData(json); // ⚠️ May run after component unmounts!
    };
    fetchData();
  }, []);

  return <div>{JSON.stringify(data)}</div>;
}

// ✅ AFTER: Safe (race-condition free)
export function SafeExample1_After() {
  const [data, setData] = useState(null);

  // ✅ FIXED: Auto-cleanup on unmount
  useAsyncEffect(async (signal, isMounted) => {
    try {
      const response = await fetch('/api/user', { signal });
      const json = await response.json();

      if (isMounted()) {
        setData(json);
      }
    } catch (error) {
      if (error.name !== 'AbortError' && isMounted()) {
        console.error('Fetch failed:', error);
      }
    }
  }, []);

  return <div>{JSON.stringify(data)}</div>;
}

// ============================================================================
// EXAMPLE 2: Auto-Refreshing Data
// ============================================================================

// ❌ BEFORE: Unsafe (leaks intervals)
export function UnsafeExample2_Before() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Initial fetch
    fetch('/api/stats').then(r => r.json()).then(setStats);

    // ⚠️ PROBLEM: Interval may not clean up properly
    const interval = setInterval(async () => {
      const data = await fetch('/api/stats').then(r => r.json());
      setStats(data); // ⚠️ May update after unmount!
    }, 5000);

    return () => clearInterval(interval); // ⚠️ But what if component unmounts during fetch?
  }, []);

  return <div>{JSON.stringify(stats)}</div>;
}

// ✅ AFTER: Safe (auto-cleanup)
export function SafeExample2_After() {
  const [stats, setStats] = useState(null);

  // ✅ FIXED: Use useSafeFetch for initial load
  const { data, loading } = useSafeFetch('/api/stats', {}, []);

  // ✅ FIXED: Use useSafeInterval for polling
  useSafeInterval(async () => {
    try {
      const response = await fetch('/api/stats');
      const json = await response.json();
      setStats(json);
    } catch (error) {
      console.error('Polling failed:', error);
    }
  }, 5000); // Every 5 seconds

  if (loading) return <div>Loading...</div>;
  return <div>{JSON.stringify(data)}</div>;
}

// ============================================================================
// EXAMPLE 3: Notification with Auto-Dismiss
// ============================================================================

// ❌ BEFORE: Unsafe (memory leak)
export function UnsafeExample3_Before({ message }: { message: string }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // ⚠️ PROBLEM: Timeout not cleaned up
    const timer = setTimeout(() => {
      setVisible(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;
  return <div>{message}</div>;
}

// ✅ AFTER: Safe (auto-cleanup)
export function SafeExample3_After({ message }: { message: string }) {
  const [visible, setVisible] = useState(true);

  // ✅ FIXED: useSafeTimeout auto-cleans
  useSafeTimeout(() => {
    setVisible(false);
  }, 3000);

  if (!visible) return null;
  return <div>{message}</div>;
}

// ============================================================================
// EXAMPLE 4: Search with Debounce
// ============================================================================

// ❌ BEFORE: Unsafe (race conditions + leaks)
export function UnsafeExample4_Before() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    // ⚠️ PROBLEM: Timeout not tracked, causes leaks
    setTimeout(async () => {
      const response = await fetch(`/api/search?q=${value}`);
      const data = await response.json();
      setResults(data); // ⚠️ Stale result may override newer result!
    }, 300);
  };

  return (
    <input
      type="text"
      value={query}
      onChange={handleChange}
      placeholder="Search..."
    />
  );
}

// ✅ AFTER: Safe (proper debounce pattern)
export function SafeExample4_After() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [timeoutId, setTimeoutId] = useState<number | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    // ✅ Clear previous timeout
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    // ✅ Set new timeout
    const newTimeoutId = window.setTimeout(async () => {
      try {
        const response = await fetch(`/api/search?q=${value}`);
        const data = await response.json();

        // ✅ Check if this is still the latest request
        if (newTimeoutId === timeoutId) {
          setResults(data);
        }
      } catch (error) {
        console.error('Search failed:', error);
      }
    }, 300);

    setTimeoutId(newTimeoutId);
  };

  // ✅ Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [timeoutId]);

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={handleChange}
        placeholder="Search..."
      />
      <ul>
        {results.map((r: any) => <li key={r.id}>{r.name}</li>)}
      </ul>
    </div>
  );
}

// ============================================================================
// QUICK REFERENCE CARD
// ============================================================================

export const MigrationCheatsheet = () => (
  <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
    <h2>🔄 Migration Cheat Sheet</h2>

    <h3>Pattern 1: Simple Fetch</h3>
    <pre>
      {`// ❌ OLD
useEffect(() => {
  fetch('/api/data').then(r => r.json()).then(setData);
}, []);

// ✅ NEW
useAsyncEffect(async (signal, isMounted) => {
  const res = await fetch('/api/data', { signal });
  if (isMounted()) setData(await res.json());
}, []);`}
    </pre>

    <h3>Pattern 2: Polling</h3>
    <pre>
      {`// ❌ OLD
useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 5000);
  return () => clearInterval(interval);
}, []);

// ✅ NEW
useSafeInterval(fetchData, 5000, { runOnMount: true });`}
    </pre>

    <h3>Pattern 3: Timeout</h3>
    <pre>
      {`// ❌ OLD
useEffect(() => {
  const timer = setTimeout(callback, 3000);
  return () => clearTimeout(timer);
}, []);

// ✅ NEW
useSafeTimeout(callback, 3000);`}
    </pre>

    <h3>Pattern 4: Functional Updates</h3>
    <pre>
      {`// ❌ OLD (stale closure)
setState(count + 1);

// ✅ NEW (fresh state)
setState(prev => prev + 1);`}
    </pre>
  </div>
);

// ============================================================================
// EXPORT ALL EXAMPLES
// ============================================================================

export default {
  UnsafeExample1_Before,
  SafeExample1_After,
  UnsafeExample2_Before,
  SafeExample2_After,
  UnsafeExample3_Before,
  SafeExample3_After,
  UnsafeExample4_Before,
  SafeExample4_After,
  MigrationCheatsheet
};
