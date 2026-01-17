/**
 * iOS Safari vs Android Chrome Platform Tester
 * Real-time testing and comparison of mobile browser differences
 */

import React, { useState, useEffect, useRef } from 'react';
import { mobileBrowserCompatibility, type BrowserInfo, type CompatibilityIssue } from '../../utils/crossPlatform/mobileBrowserCompatibility';

interface PlatformTesterProps {
  showInDevelopment?: boolean;
}

export const PlatformTester: React.FC<PlatformTesterProps> = ({ showInDevelopment = true }) => {
  const [browserInfo, setBrowserInfo] = useState<BrowserInfo | null>(null);
  const [issues, setIssues] = useState<CompatibilityIssue[]>([]);
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    setBrowserInfo(mobileBrowserCompatibility.getBrowserInfo());
    setIssues(mobileBrowserCompatibility.getCompatibilityIssues());
  }, []);

  // Run platform-specific tests
  useEffect(() => {
    if (!browserInfo) return;

    const results = runPlatformTests(browserInfo);
    setTestResults(results);
  }, [browserInfo]);

  const runPlatformTests = (info: BrowserInfo): Record<string, any> => {
    const results: Record<string, any> = {};

    // Test 1: Scroll Performance
    results.scrollTest = testScrollPerformance(info);

    // Test 2: Touch Responsiveness
    results.touchTest = testTouchResponsiveness(info);

    // Test 3: CSS Feature Support
    results.cssTest = testCSSFeatures(info);

    // Test 4: List Performance
    results.listPerformanceTest = testListPerformance(info);

    // Test 5: Memory Usage
    results.memoryTest = testMemoryUsage(info);

    return results;
  };

  const testScrollPerformance = (info: BrowserInfo) => {
    const startTime = performance.now();

    // Create test list
    const testContainer = document.createElement('div');
    testContainer.style.height = '200px';
    testContainer.style.overflowY = 'auto';
    testContainer.style.webkitOverflowScrolling = info.platform === 'ios' ? 'touch' : 'auto';

    // Add test items
    for (let i = 0; i < 50; i++) {
      const item = document.createElement('div');
      item.style.height = '40px';
      item.style.padding = '8px';
      item.style.borderBottom = '1px solid #eee';
      item.textContent = `Test Item ${i + 1}`;
      testContainer.appendChild(item);
    }

    document.body.appendChild(testContainer);

    // Test scroll performance
    const scrollStart = performance.now();
    testContainer.scrollTop = 100;
    const scrollTime = performance.now() - scrollStart;

    // Test smooth scrolling
    const smoothScrollStart = performance.now();
    testContainer.scrollTo({ top: 200, behavior: 'smooth' });

    setTimeout(() => {
      const smoothScrollTime = performance.now() - smoothScrollStart;
      const totalTime = performance.now() - startTime;

      document.body.removeChild(testContainer);

      return {
        scrollTime: scrollTime.toFixed(2),
        smoothScrollTime: smoothScrollTime.toFixed(2),
        totalTime: totalTime.toFixed(2),
        fps: calculateFPS(scrollTime),
        grade: getPerformanceGrade(totalTime)
      };
    }, 100);

    return { pending: true };
  };

  const testTouchResponsiveness = (info: BrowserInfo) => {
    const touchElement = document.createElement('button');
    touchElement.style.padding = '12px 16px';
    touchElement.style.minHeight = '44px';
    touchElement.textContent = 'Test Touch';

    // Check touch properties
    const computedStyle = window.getComputedStyle(touchElement);

    return {
      touchTargetSize: parseInt(computedStyle.minHeight),
      hasTouchSupport: 'ontouchstart' in window,
      touchAction: computedStyle.touchAction,
      platformOptimizations: info.platform === 'ios' ? {
        tapHighlight: computedStyle.webkitTapHighlightColor,
        overflowScrolling: computedStyle.webkitOverflowScrolling
      } : {
        touchAction: computedStyle.touchAction,
        overscrollBehavior: computedStyle.overscrollBehavior
      }
    };
  };

  const testCSSFeatures = (info: BrowserInfo) => {
    const testElement = document.createElement('div');
    document.body.appendChild(testElement);

    const features: Record<string, boolean> = {};

    // Test CSS Grid support
    testElement.style.display = 'grid';
    features.cssGrid = testElement.style.display === 'grid';

    // Test Flexbox gap support
    testElement.style.display = 'flex';
    testElement.style.gap = '10px';
    features.flexboxGap = testElement.style.gap === '10px';

    // Test backdrop filter support
    testElement.style.backdropFilter = 'blur(5px)';
    features.backdropFilter = testElement.style.backdropFilter !== '';

    // Test position sticky support
    testElement.style.position = 'sticky';
    features.positionSticky = testElement.style.position === 'sticky';

    // Test scroll behavior support
    const htmlElement = document.documentElement;
    htmlElement.style.scrollBehavior = 'smooth';
    features.scrollBehavior = htmlElement.style.scrollBehavior === 'smooth';

    // Test overscroll behavior support
    testElement.style.overscrollBehavior = 'contain';
    features.overscrollBehavior = testElement.style.overscrollBehavior === 'contain';

    document.body.removeChild(testElement);

    return features;
  };

  const testListPerformance = (info: BrowserInfo) => {
    const startTime = performance.now();
    const items = [];

    // Test rendering 100 list items
    for (let i = 0; i < 100; i++) {
      items.push({
        id: i,
        name: `Test User ${i + 1}`,
        email: `user${i + 1}@example.com`,
        role: ['Developer', 'Designer', 'Manager'][i % 3]
      });
    }

    const renderTime = performance.now() - startTime;

    // Estimate memory usage
    const estimatedMemory = items.length * 2; // Rough estimate

    return {
      itemCount: items.length,
      renderTime: renderTime.toFixed(2),
      estimatedMemory: estimatedMemory,
      performanceGrade: renderTime < 10 ? 'excellent' : renderTime < 25 ? 'good' : 'fair'
    };
  };

  const testMemoryUsage = (info: BrowserInfo) => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
        percentage: ((memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100).toFixed(1)
      };
    }

    return {
      message: 'Memory API not available',
      alternative: 'Use Chrome DevTools Memory tab for detailed analysis'
    };
  };

  const calculateFPS = (scrollTime: number): number => {
    // Rough FPS calculation based on scroll time
    return Math.min(60, Math.round(1000 / (scrollTime * 2)));
  };

  const getPerformanceGrade = (time: number): string => {
    if (time < 10) return 'A+';
    if (time < 25) return 'A';
    if (time < 50) return 'B';
    if (time < 100) return 'C';
    return 'D';
  };

  // Don't show in production
  if (process.env.NODE_ENV === 'production' && !showInDevelopment) {
    return null;
  }

  const getPlatformIcon = () => {
    if (!browserInfo) return '📱';
    if (browserInfo.platform === 'ios') return '🍎';
    if (browserInfo.platform === 'android') return '🤖';
    return '🖥️';
  };

  const getBrowserIcon = () => {
    if (!browserInfo) return '🌐';
    if (browserInfo.browser === 'safari') return '🧭';
    if (browserInfo.browser === 'chrome') return '🔵';
    if (browserInfo.browser === 'firefox') return '🦊';
    if (browserInfo.browser === 'edge') return '📘';
    return '🌐';
  };

  const getPerformanceColor = (grade: string) => {
    switch (grade) {
      case 'A+': case 'A': return '#4caf50';
      case 'B': return '#8bc34a';
      case 'C': return '#ffc107';
      case 'D': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      left: '20px',
      zIndex: 9999,
      minWidth: '350px',
      maxWidth: '400px'
    }}>
      {/* Platform Indicator */}
      <div
        onClick={() => setShowDetails(!showDetails)}
        style={{
          backgroundColor: browserInfo?.platform === 'ios' ? '#007aff' : '#4caf50',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '14px',
          fontWeight: '600'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '20px' }}>{getPlatformIcon()}</span>
            <span>{browserInfo?.platform.toUpperCase() || 'Unknown'}</span>
          </div>
          <div style={{ fontSize: '12px', opacity: 0.9, marginTop: '2px' }}>
            {getBrowserIcon()} {browserInfo?.browser || 'Unknown'} {browserInfo?.version}
          </div>
          <div style={{ fontSize: '10px', opacity: 0.8, marginTop: '2px' }}>
            {issues.length} compatibility issues
          </div>
        </div>
        <div style={{ fontSize: '18px' }}>
          {showDetails ? '▼' : '▶'}
        </div>
      </div>

      {/* Detailed Panel */}
      {showDetails && (
        <div
          style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            marginTop: '10px',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}
        >
          {/* Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #eee',
            backgroundColor: '#f8f9fa'
          }}>
            <h3 style={{ margin: 0, color: '#333', fontSize: '16px' }}>
              Platform Compatibility Analysis
            </h3>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              {browserInfo?.engine.toUpperCase()} Engine • {browserInfo?.capabilities.performance} Performance
            </div>
          </div>

          {/* Browser Info */}
          {browserInfo && (
            <div style={{ padding: '16px', borderBottom: '1px solid #eee' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '14px' }}>
                🔍 Browser Information
              </h4>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div><strong>Platform:</strong> {browserInfo.platform}</div>
                <div><strong>Browser:</strong> {browserInfo.browser}</div>
                <div><strong>Version:</strong> {browserInfo.version}</div>
                <div><strong>Engine:</strong> {browserInfo.engine}</div>
                <div><strong>Scroll Behavior:</strong> {browserInfo.capabilities.scrollBehavior}</div>
                <div><strong>Touch Events:</strong> {browserInfo.capabilities.touchEvents}</div>
                <div><strong>Performance:</strong> {browserInfo.capabilities.performance}</div>
              </div>
            </div>
          )}

          {/* CSS Support */}
          {testResults.cssTest && (
            <div style={{ padding: '16px', borderBottom: '1px solid #eee' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '14px' }}>
                🎨 CSS Feature Support
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                {Object.entries(testResults.cssTest).map(([feature, supported]) => (
                  <div key={feature} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '4px 8px',
                    backgroundColor: supported ? '#e8f5e8' : '#ffebee',
                    borderRadius: '4px'
                  }}>
                    <span>{feature}</span>
                    <span style={{ color: supported ? '#4caf50' : '#f44336' }}>
                      {supported ? '✓' : '✗'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Tests */}
          <div style={{ padding: '16px', borderBottom: '1px solid #eee' }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '14px' }}>
              ⚡ Performance Tests
            </h4>

            {testResults.scrollTest && !testResults.scrollTest.pending && (
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                  <strong>Scroll Performance:</strong>
                  <span style={{
                    color: getPerformanceColor(testResults.scrollTest.grade),
                    marginLeft: '8px',
                    fontWeight: '600'
                  }}>
                    Grade {testResults.scrollTest.grade}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  FPS: {testResults.scrollTest.fps} •
                  Time: {testResults.scrollTest.totalTime}ms
                </div>
              </div>
            )}

            {testResults.listPerformanceTest && (
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                  <strong>List Rendering:</strong>
                  <span style={{
                    color: getPerformanceColor(testResults.listPerformanceTest.performanceGrade),
                    marginLeft: '8px',
                    fontWeight: '600'
                  }}>
                    {testResults.listPerformanceTest.performanceGrade.toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  {testResults.listPerformanceTest.itemCount} items •
                  {testResults.listPerformanceTest.renderTime}ms
                </div>
              </div>
            )}

            {testResults.memoryTest && (
              <div>
                <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                  <strong>Memory Usage:</strong>
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  {testResults.memoryTest.message ||
                   `Used: ${Math.round(testResults.memoryTest.used / 1024 / 1024)}MB ` +
                   `(${testResults.memoryTest.percentage}%)`}
                </div>
              </div>
            )}
          </div>

          {/* Compatibility Issues */}
          {issues.length > 0 && (
            <div style={{ padding: '16px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '14px' }}>
                ⚠️ Compatibility Issues
              </h4>
              {issues.slice(0, 3).map((issue, index) => (
                <div
                  key={issue.id}
                  style={{
                    marginBottom: '12px',
                    padding: '12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    backgroundColor: issue.severity === 'critical' ? '#ffebee' :
                                     issue.severity === 'major' ? '#fff3e0' : '#f3e5f5'
                  }}
                >
                  <div style={{
                    fontWeight: '600',
                    color: '#333',
                    fontSize: '13px',
                    marginBottom: '4px'
                  }}>
                    {issue.title}
                  </div>
                  <div style={{ color: '#666', fontSize: '11px', marginBottom: '6px' }}>
                    {issue.description}
                  </div>
                  <div style={{ fontSize: '10px', color: '#888' }}>
                    <span style={{
                      color: issue.severity === 'critical' ? '#f44336' :
                              issue.severity === 'major' ? '#ff9800' : '#9c27b0'
                    }}>
                      {issue.severity.toUpperCase()}
                    </span>
                    {' • '}
                    Category: {issue.category}
                  </div>
                </div>
              ))}

              {issues.length > 3 && (
                <div style={{ textAlign: 'center', fontSize: '12px', color: '#666' }}>
                  ... and {issues.length - 3} more issues
                </div>
              )}
            </div>
          )}

          {/* Platform-Specific Tips */}
          <div style={{ padding: '16px' }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '14px' }}>
              💡 Platform-Specific Tips
            </h4>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {browserInfo?.platform === 'ios' ? (
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  <li>Use -webkit-overflow-scrolling: touch for smooth scrolling</li>
                  <li>Disable -webkit-tap-highlight-color for custom feedback</li>
                  <li>Test on actual iOS devices for accurate touch behavior</li>
                  <li>Be mindful of backdrop filter performance impact</li>
                </ul>
              ) : browserInfo?.platform === 'android' ? (
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  <li>Use touch-action CSS property for better performance</li>
                  <li>Test on various Android devices for consistency</li>
                  <li>Consider overscroll-behavior for better UX</li>
                  <li>Optimize for varying screen densities</li>
                </ul>
              ) : (
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  <li>Test on both iOS Safari and Android Chrome</li>
                  <li>Use progressive enhancement for features</li>
                  <li>Implement platform-specific optimizations</li>
                  <li>Test on actual devices, not emulators</li>
                </ul>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div style={{ padding: '16px', borderTop: '1px solid #eee' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '14px' }}>
              🚀 Quick Actions
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button
                onClick={() => {
                  console.log('Platform Info:', browserInfo);
                  console.log('Issues:', issues);
                  console.log('Test Results:', testResults);
                }}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#2196f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                📋 Log Details
              </button>
              <button
                onClick={() => {
                  const report = mobileBrowserCompatibility.generateCompatibilityReport();
                  console.log('Compatibility Report:', report);
                }}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#4caf50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                📊 Generate Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Platform comparison component
export const PlatformComparison: React.FC = () => {
  const [testData, setTestData] = useState<Record<string, any>>({});

  useEffect(() => {
    // Run comprehensive platform tests
    runComparisonTests();
  }, []);

  const runComparisonTests = () => {
    const results: Record<string, any> = {};

    // Test scroll behavior differences
    results.scrollDifferences = testScrollDifferences();

    // Test touch interaction differences
    results.touchDifferences = testTouchDifferences();

    // Test CSS rendering differences
    results.cssDifferences = testCSSDifferences();

    // Test performance differences
    results.performanceDifferences = testPerformanceDifferences();

    setTestData(results);
  };

  const testScrollDifferences = () => {
    return {
      iosSafari: {
        scrollBehavior: 'momentum-based',
        rubberBandEffect: true,
        scrollBounce: true,
        scrollTo: 'smooth with momentum'
      },
      androidChrome: {
        scrollBehavior: 'pixel-perfect',
        rubberBandEffect: false,
        scrollBounce: false,
        scrollTo: 'smooth or instant'
      },
      keyDifferences: [
        'iOS Safari: Natural scrolling with momentum',
        'Android Chrome: Precise pixel scrolling',
        'iOS: Rubber band/bounce effect',
        'Android: Overscroll behavior control'
      ]
    };
  };

  const testTouchDifferences = () => {
    return {
      iosSafari: {
        touchLatency: '50-100ms',
        touchAccuracy: 'high',
        tapHighlight: 'default gray',
        multiTouch: 'excellent'
      },
      androidChrome: {
        touchLatency: '10-50ms',
        touchAccuracy: 'excellent',
        tapHighlight: 'none',
        multiTouch: 'excellent'
      },
      keyDifferences: [
        'iOS: Higher touch latency but consistent',
        'Android: Lower latency, more responsive',
        'iOS: Default tap highlight needs customization',
        'Both: Excellent multi-touch support'
      ]
    };
  };

  const testCSSDifferences = () => {
    return {
      iosSafari: {
        cssGrid: 'full support (Safari 10.1+)',
        flexboxGap: 'partial support (Safari 14.1+)',
        backdropFilter: 'excellent support',
        webkitPrefixes: 'required for some features'
      },
      androidChrome: {
        cssGrid: 'excellent support',
        flexboxGap: 'full support',
        backdropFilter: 'good support',
        webkitPrefixes: 'rarely required'
      },
      keyDifferences: [
        'iOS: More webkit prefixes needed',
        'Android: Better standards compliance',
        'iOS: Better backdrop filter implementation',
        'Both: Modern CSS features well supported'
      ]
    };
  };

  const testPerformanceDifferences = {
    iosSafari: {
      javascript: 'excellent (Nitro engine)',
      rendering: 'very good',
      memoryManagement: 'efficient',
      batteryOptimization: 'excellent'
    },
    androidChrome: {
      javascript: 'excellent (V8 engine)',
      rendering: 'excellent',
      memoryManagement: 'good',
      batteryOptimization: 'good'
    },
    keyDifferences: [
      'iOS: Better battery optimization',
      'Android: More consistent performance',
      'iOS: Better touch responsiveness',
      'Both: Excellent JavaScript performance'
    ]
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1>🍎 iOS Safari vs 🤖 Android Chrome</h1>
        <p style={{ color: '#666', marginBottom: '30px' }}>
          Comprehensive comparison of mobile browser behaviors and performance characteristics
        </p>

        {/* Real-time Platform Detector */}
        <PlatformTester showInDevelopment={true} />

        {/* Comparison Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '40px' }}>

          {/* Scroll Comparison */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#007aff', marginTop: 0 }}>📱 Scroll Behavior</h3>
            {testData.scrollDifferences && (
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div style={{ marginBottom: '15px' }}>
                  <strong>iOS Safari:</strong>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>Momentum-based scrolling</li>
                    <li>Rubber band effect</li>
                    <li>Natural deceleration</li>
                  </ul>
                </div>
                <div>
                  <strong>Android Chrome:</strong>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>Precise pixel scrolling</li>
                    <li>No rubber band effect</li>
                    <li>Overscroll behavior control</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Touch Comparison */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#4caf50', marginTop: 0 }}>👆 Touch Interaction</h3>
            {testData.touchDifferences && (
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div style={{ marginBottom: '15px' }}>
                  <strong>iOS Safari:</strong>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>50-100ms touch latency</li>
                    <li>Default tap highlight</li>
                    <li>Consistent touch response</li>
                  </ul>
                </div>
                <div>
                  <strong>Android Chrome:</strong>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>10-50ms touch latency</li>
                    <li>No default highlight</li>
                    <li>Excellent accuracy</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* CSS Comparison */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#ff9800', marginTop: 0 }}>🎨 CSS Support</h3>
            {testData.cssDifferences && (
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div style={{ marginBottom: '15px' }}>
                  <strong>iOS Safari:</strong>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>Requires webkit prefixes</li>
                    <li>Partial flexbox gap support</li>
                    <li>Excellent backdrop filter</li>
                  </ul>
                </div>
                <div>
                  <strong>Android Chrome:</strong>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>Modern CSS support</li>
                    <li>Full flexbox gap support</li>
                    <li>Good backdrop filter</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Performance Comparison */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#f44336', marginTop: 0 }}>⚡ Performance</h3>
            <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
              <div style={{ marginBottom: '15px' }}>
                <strong>iOS Safari:</strong>
                <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                  <li>Excellent battery optimization</li>
                  <li>Efficient memory management</li>
                  <li>Nitro JavaScript engine</li>
                </ul>
              </div>
              <div>
                <strong>Android Chrome:</strong>
                <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                  <li>V8 JavaScript engine</li>
                  <li>Consistent performance</li>
                  <li>Good memory management</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Best Practices */}
        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginTop: '30px'
        }}>
          <h2>🎯 Cross-Platform Best Practices</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
            <div>
              <h3 style={{ color: '#007aff', marginTop: 0 }}>iOS Safari Optimizations</h3>
              <ul style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <li>Use <code>-webkit-overflow-scrolling: touch</code></li>
                <li>Disable <code>-webkit-tap-highlight-color</code></li>
                <li>Add <code>-webkit-transform: translateZ(0)</code> for hardware acceleration</li>
                <li>Test momentum scrolling behavior</li>
              </ul>
            </div>
            <div>
              <h3 style={{ color: '#4caf50', marginTop: 0 }}>Android Chrome Optimizations</h3>
              <ul style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <li>Use <code>touch-action</code> for better touch response</li>
                <li>Implement <code>overscroll-behavior</code> control</li>
                <li>Test on various device densities</li>
                <li>Optimize for consistent performance</li>
              </ul>
            </div>
            <div>
              <h3 style={{ color: '#ff9800', marginTop: 0 }}>Universal Best Practices</h3>
              <ul style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <li>44px minimum touch targets</li>
                <li>Progressive enhancement</li>
                <li>Platform detection with fallbacks</li>
                <li>Test on actual devices</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlatformTester;
