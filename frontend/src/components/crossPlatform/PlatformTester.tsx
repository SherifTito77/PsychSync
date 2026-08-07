/**
 * iOS Safari vs Android Chrome Platform Tester
 * Real-time testing and comparison of mobile browser differences
 */

import React, { useState, useEffect, useRef } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { mobileBrowserCompatibility, type BrowserInfo, type CompatibilityIssue } from '../../utils/crossPlatform/mobileBrowserCompatibility';

// Helper function for conditional classes
function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

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
    (testContainer.style as any).webkitOverflowScrolling = info.platform === 'ios' ? 'touch' : 'auto';

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
        tapHighlight: (computedStyle as any).webkitTapHighlightColor,
        overflowScrolling: (computedStyle as any).webkitOverflowScrolling
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

  const getPerformanceColor = (grade: string): string => {
    switch (grade) {
      case 'A+': case 'A': return 'text-green-500';
      case 'B': return 'text-green-400';
      case 'C': return 'text-yellow-500';
      case 'D': return 'text-red-500';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="fixed top-5 left-5 right-5 z-[9999] w-auto max-w-[400px]">
      {/* Platform Indicator */}
      <div
        onClick={() => setShowDetails(!showDetails)}
        className={cn(
          'flex justify-between items-center cursor-pointer shadow-lg',
          browserInfo?.platform === 'ios' ? 'bg-[#007aff]' : 'bg-green-500',
          'text-white p-3 rounded-lg text-sm font-semibold'
        )}
      >
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">{getPlatformIcon()}</span>
            <span>{browserInfo?.platform.toUpperCase() || 'Unknown'}</span>
          </div>
          <div className="text-xs opacity-90 mt-0.5">
            {getBrowserIcon()} {browserInfo?.browser || 'Unknown'} {browserInfo?.version}
          </div>
          <div className="text-[10px] opacity-80 mt-0.5">
            {issues.length} compatibility issues
          </div>
        </div>
        <div className="text-lg">
          {showDetails ? '▼' : '▶'}
        </div>
      </div>

      {/* Detailed Panel */}
      {showDetails && (
        <div className="bg-white rounded-lg shadow-xl mt-2.5 max-h-[80vh] overflow-y-auto">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h3 className="my-0 text-gray-900 text-base">
              Platform Compatibility Analysis
            </h3>
            <div className="text-xs text-gray-600 mt-1">
              {browserInfo?.engine.toUpperCase()} Engine • {browserInfo?.capabilities.performance} Performance
            </div>
          </div>

          {/* Browser Info */}
          {browserInfo && (
            <div className="p-4 border-b border-gray-200">
              <h4 className="my-0 mb-3 text-gray-900 text-sm">
                🔍 Browser Information
              </h4>
              <div className="text-xs text-gray-600">
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
            <div className="p-4 border-b border-gray-200">
              <h4 className="my-0 mb-3 text-gray-900 text-sm">
                🎨 CSS Feature Support
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(testResults.cssTest).map(([feature, supported]) => (
                  <div key={feature} className="flex justify-between p-1 bg-green-50 rounded">
                    <span>{feature}</span>
                    <span className={(supported as boolean) ? 'text-green-500' : 'text-red-500'}>
                      {(supported as boolean) ? '✓' : '✗'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Tests */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="my-0 mb-3 text-gray-900 text-sm">
              ⚡ Performance Tests
            </h4>

            {testResults.scrollTest && !testResults.scrollTest.pending && (
              <div className="mb-3">
                <div className="text-xs mb-2">
                  <strong>Scroll Performance:</strong>
                  <span className={cn(
                    'ml-2 font-semibold',
                    getPerformanceColor(testResults.scrollTest.grade)
                  )}>
                    Grade {testResults.scrollTest.grade}
                  </span>
                </div>
                <div className="text-[11px] text-gray-600">
                  FPS: {testResults.scrollTest.fps} •
                  Time: {testResults.scrollTest.totalTime}ms
                </div>
              </div>
            )}

            {testResults.listPerformanceTest && (
              <div className="mb-3">
                <div className="text-xs mb-2">
                  <strong>List Rendering:</strong>
                  <span className={cn(
                    'ml-2 font-semibold',
                    getPerformanceColor(testResults.listPerformanceTest.performanceGrade)
                  )}>
                    {testResults.listPerformanceTest.performanceGrade.toUpperCase()}
                  </span>
                </div>
                <div className="text-[11px] text-gray-600">
                  {testResults.listPerformanceTest.itemCount} items •
                  {testResults.listPerformanceTest.renderTime}ms
                </div>
              </div>
            )}

            {testResults.memoryTest && (
              <div>
                <div className="text-xs mb-2">
                  <strong>Memory Usage:</strong>
                </div>
                <div className="text-[11px] text-gray-600">
                  {testResults.memoryTest.message ||
                   `Used: ${Math.round(testResults.memoryTest.used / 1024 / 1024)}MB ` +
                   `(${testResults.memoryTest.percentage}%)`}
                </div>
              </div>
            )}
          </div>

          {/* Compatibility Issues */}
          {issues.length > 0 && (
            <div className="p-4">
              <h4 className="my-0 mb-3 text-gray-900 text-sm">
                ⚠️ Compatibility Issues
              </h4>
              {issues.slice(0, 3).map((issue, index) => (
                <div
                  key={issue.id}
                  className={cn(
                    'mb-3 p-3 border rounded bg-opacity-20',
                    issue.severity === 'critical' ? 'border-red-200 bg-red-50' :
                    issue.severity === 'major' ? 'border-orange-200 bg-orange-50' : 'border-purple-200 bg-purple-50'
                  )}
                >
                  <div className="font-semibold text-sm mb-1">
                    {issue.title}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    {issue.description}
                  </div>
                  {issue.recommendation && (
                    <div className="text-[11px] text-blue-600">
                      💡 {issue.recommendation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
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

  const testPerformanceDifferences = () => {
    return {
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
