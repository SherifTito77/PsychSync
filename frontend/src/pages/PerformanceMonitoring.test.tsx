/**
 * Simple test page to verify the route works
 *
 * Temporarily use this simplified page to test if routing works
 * Access at: http://localhost:5173/admin/performance-test
 */

import React from 'react';

const PerformanceMonitoringTestPage: React.FC = () => {
  return (
    <div style={{ padding: '2rem', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: '#333' }}>✅ Performance Monitoring Test Page</h1>
      <p style={{ fontSize: '1.2rem', color: '#666' }}>
        If you can see this page, the routing works!
      </p>
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#fff', border: '2px solid #4CAF50' }}>
        <h2>Next Steps:</h2>
        <ol style={{ lineHeight: '1.8' }}>
          <li>Check browser console for errors (F12)</li>
          <li>Check Network tab for failed requests</li>
          <li>Verify the PerformanceMonitoringDashboard component loads</li>
        </ol>
      </div>
      <div style={{ marginTop: '2rem', fontFamily: 'monospace', backgroundColor: '#fff', padding: '1rem' }}>
        <h3>Debug Info:</h3>
        <p>Current URL: {window.location.href}</p>
        <p>Current Path: {window.location.pathname}</p>
      </div>
    </div>
  );
};

export default PerformanceMonitoringTestPage;
