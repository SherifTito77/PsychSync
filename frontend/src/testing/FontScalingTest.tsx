/**
 * Font Scaling Test Suite - 50% to 200% Zoom Level Testing
 * Comprehensive validation of responsive behavior across accessibility font sizes
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  SimpleResponsiveList,
  VirtualizedList,
  useMobileResponsive
} from '../components/mobile';

// Test data for font scaling scenarios
const FONT_SCALING_TEST_DATA = [
  {
    id: 'text-scaling-1',
    title: 'Font Scaling Test Entry 1',
    description: 'This is a medium-length description that should scale properly at all zoom levels without breaking layout or causing horizontal scrolling.',
    metadata: ['Tag 1', 'Tag 2', 'Tag 3'],
    timestamp: '2024-01-15T10:30:00Z'
  },
  {
    id: 'text-scaling-2',
    title: 'Very Long Title That Extends Beyond Normal Container Width And Should Wrap Properly At All Font Sizes',
    description: 'This description contains extremely long content designed to test text wrapping and overflow behavior at 200% font size. It includes multiple sentences to ensure comprehensive testing of paragraph scaling and line height adjustments.',
    metadata: ['Very Long Metadata Tag That Extends', 'Another Long Tag', 'Short'],
    timestamp: '2024-01-14T15:45:00Z'
  },
  {
    id: 'text-scaling-3',
    title: 'Short',
    description: 'Brief.',
    metadata: ['A'],
    timestamp: '2024-01-13T09:15:00Z'
  },
  {
    id: 'text-scaling-4',
    title: 'Medium Length Title With Numbers (12345) and Symbols (@#$%)',
    description: 'This entry tests mixed content including numbers, symbols, and special characters. The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.',
    metadata: ['Numeric-123', 'Symbol-@#$', 'Mixed-Content'],
    timestamp: '2024-01-12T18:20:00Z'
  }
];

// Accessibility font size levels
const FONT_SIZE_LEVELS = [
  { level: 50, name: 'Very Small', description: '50% - Minimum practical size' },
  { level: 75, name: 'Small', description: '75% - Slightly reduced' },
  { level: 100, name: 'Normal', description: '100% - Default size' },
  { level: 125, name: 'Large', description: '125% - Common accessibility setting' },
  { level: 150, name: 'Extra Large', description: '150% - Moderate zoom' },
  { level: 175, name: 'Very Large', description: '175% - High zoom' },
  { level: 200, name: 'Maximum', description: '200% - WCAG 2.1 AA requirement' }
];

// Font scaling test metrics
interface FontScalingMetrics {
  fontSize: number;
  level: number;
  containerWidth: number;
  contentWidth: number;
  horizontalScroll: boolean;
  layoutBreaks: string[];
  accessibilityIssues: string[];
  readabilityScore: number;
}

export const FontScalingTest: React.FC = () => {
  const [currentZoomLevel, setCurrentZoomLevel] = useState(100);
  const [testMetrics, setTestMetrics] = useState<FontScalingMetrics[]>([]);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResults, setTestResults] = useState<any[]>([]);
  const testContainerRef = useRef<HTMLDivElement>(null);
  const { isMobile, breakpoints } = useMobileResponsive();

  // Apply font size zoom
  const applyFontZoom = (level: number) => {
    document.documentElement.style.fontSize = `${level}%`;
    setCurrentZoomLevel(level);
  };

  // Measure font scaling behavior
  const measureFontScaling = async (level: number): Promise<FontScalingMetrics> => {
    return new Promise((resolve) => {
      // Apply font size
      applyFontZoom(level);

      // Wait for layout to settle
      setTimeout(() => {
        if (!testContainerRef.current) {
          resolve({
            fontSize: level,
            level,
            containerWidth: 0,
            contentWidth: 0,
            horizontalScroll: false,
            layoutBreaks: [],
            accessibilityIssues: [],
            readabilityScore: 0
          });
          return;
        }

        const container = testContainerRef.current;
        const computedStyle = window.getComputedStyle(container);

        // Measure dimensions
        const containerWidth = container.clientWidth;
        const contentWidth = container.scrollWidth;
        const horizontalScroll = contentWidth > containerWidth;

        // Detect layout breaks
        const layoutBreaks: string[] = [];
        const accessibilityIssues: string[] = [];

        // Check for horizontal scrolling
        if (horizontalScroll) {
          layoutBreaks.push('Horizontal scrolling detected');
          accessibilityIssues.push('WCAG 1.4.10: Reflow violation - horizontal scrolling');
        }

        // Check text overflow
        const textElements = container.querySelectorAll('h1, h2, h3, h4, p, span');
        textElements.forEach((element) => {
          const el = element as HTMLElement;
          if (el.scrollWidth > el.clientWidth) {
            layoutBreaks.push(`Text overflow in ${el.tagName.toLowerCase()}`);
            accessibilityIssues.push('Text content overflow detected');
          }
        });

        // Check touch target sizes at different font sizes
        const touchTargets = container.querySelectorAll('button, a, [role="button"]');
        touchTargets.forEach((target) => {
          const rect = (target as HTMLElement).getBoundingClientRect();
          const minSize = 44; // WCAG minimum touch target
          if (rect.width < minSize || rect.height < minSize) {
            accessibilityIssues.push('WCAG 2.5.5: Touch target size too small');
          }
        });

        // Check readability based on font size
        let readabilityScore = 100;
        if (level < 75) readabilityScore -= 20; // Too small
        if (level > 175) readabilityScore -= 10; // Too large (might cause layout issues)
        if (horizontalScroll) readabilityScore -= 30; // Major accessibility issue
        if (layoutBreaks.length > 0) readabilityScore -= layoutBreaks.length * 10;

        resolve({
          fontSize: level,
          level,
          containerWidth,
          contentWidth,
          horizontalScroll,
          layoutBreaks,
          accessibilityIssues,
          readabilityScore: Math.max(0, readabilityScore)
        });
      }, 100); // Allow layout to settle
    });
  };

  // Run comprehensive font scaling test
  const runFontScalingTest = async () => {
    setIsTestRunning(true);
    const results: FontScalingMetrics[] = [];

    for (const { level } of FONT_SIZE_LEVELS) {
      const metrics = await measureFontScaling(level);
      results.push(metrics);

      // Brief pause between measurements
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    setTestMetrics(results);
    setIsTestRunning(false);

    // Return to normal size
    applyFontZoom(100);
  };

  // Real-time font scaling adjustment
  const handleZoomChange = (level: number) => {
    setCurrentZoomLevel(level);
    applyFontZoom(level);
  };

  // Test item renderer for font scaling
  const renderTestItem = (item: any) => (
    <div className="font-scaling-test-item">
      <div className="test-item-header">
        <h3 className="test-item-title">{item.title}</h3>
        <span className="test-item-timestamp">
          {new Date(item.timestamp).toLocaleDateString()}
        </span>
      </div>

      <p className="test-item-description">{item.description}</p>

      <div className="test-item-metadata">
        {item.metadata.map((tag: string, index: number) => (
          <span key={index} className="metadata-tag">
            {tag}
          </span>
        ))}
      </div>

      <div className="test-item-actions">
        <button className="action-button primary">Primary Action</button>
        <button className="action-button secondary">Secondary Action</button>
        <button className="action-button icon">⋮</button>
      </div>
    </div>
  );

  // Text samples for different content types
  const TextSamples = () => (
    <div className="text-samples">
      <h2>Typography Samples</h2>

      <div className="text-sample-section">
        <h3>Headings H1-H6</h3>
        <h1>Heading 1 - Main Page Title</h1>
        <h2>Heading 2 - Section Title</h2>
        <h3>Heading 3 - Subsection Title</h3>
        <h4>Heading 4 - Component Title</h4>
        <h5>Heading 5 - Minor Title</h5>
        <h6>Heading 6 - Smallest Title</h6>
      </div>

      <div className="text-sample-section">
        <h3>Body Text Variations</h3>
        <p className="large-text">Large body text for emphasis and better readability at smaller font sizes.</p>
        <p>Regular body text that should scale proportionally and maintain readability across all zoom levels.</p>
        <p className="small-text">Small text for captions and metadata that should remain readable even at 50% zoom.</p>
      </div>

      <div className="text-sample-section">
        <h3>Mixed Content</h3>
        <p>This paragraph contains <strong>bold text</strong>, <em>italic text</em>, and
          <a href="#" className="inline-link">inline links</a> that should all scale proportionally
          while maintaining visual hierarchy and accessibility.</p>

        <blockquote className="quote">
          "Block quotes should maintain proper indentation and spacing at all font sizes while preserving readability and visual distinction."
        </blockquote>
      </div>

      <div className="text-sample-section">
        <h3>Form Elements</h3>
        <div className="form-sample">
          <label className="form-label">Email Address</label>
          <input
            type="email"
            className="form-input"
            placeholder="user@example.com"
            defaultValue="test@example.com"
          />

          <label className="form-label">Message</label>
          <textarea
            className="form-textarea"
            rows={3}
            defaultValue="This is a sample message that should scale properly at all font sizes."
          />

          <div className="form-actions">
            <button className="form-button primary">Submit</button>
            <button className="form-button secondary">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="font-scaling-test">
      <style jsx>{`
        .font-scaling-test {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .test-header {
          text-align: center;
          margin-bottom: 30px;
          background: #f8f9fa;
          padding: 24px;
          border-radius: 12px;
        }

        .test-title {
          font-size: 28px;
          margin-bottom: 8px;
          color: #2c3e50;
        }

        .test-description {
          font-size: 16px;
          color: #7f8c8d;
          margin-bottom: 20px;
        }

        .current-zoom-indicator {
          display: inline-block;
          padding: 12px 24px;
          background: #3498db;
          color: white;
          border-radius: 8px;
          font-weight: 600;
          font-size: 18px;
          margin-bottom: 16px;
        }

        .zoom-controls {
          display: flex;
          gap: 8px;
          justify-content: center;
          flex-wrap: wrap;
          margin-bottom: 20px;
        }

        .zoom-button {
          padding: 8px 16px;
          border: 2px solid #ddd;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          min-width: 80px;
        }

        .zoom-button:hover {
          border-color: #3498db;
        }

        .zoom-button.active {
          border-color: #3498db;
          background: #3498db;
          color: white;
        }

        .test-actions {
          text-align: center;
          margin-bottom: 30px;
        }

        .run-test-button {
          padding: 12px 32px;
          background: #27ae60;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .run-test-button:hover {
          background: #229954;
        }

        .run-test-button:disabled {
          background: #95a5a6;
          cursor: not-allowed;
        }

        .test-container {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin-bottom: 30px;
        }

        .test-section {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .section-title {
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 16px;
          color: #2c3e50;
        }

        .font-scaling-test-item {
          padding: 16px;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          margin-bottom: 16px;
          transition: transform 0.2s ease;
        }

        .font-scaling-test-item:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .test-item-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .test-item-title {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          line-height: 1.3;
          flex: 1;
          margin-right: 12px;
        }

        .test-item-timestamp {
          font-size: 12px;
          color: #7f8c8d;
          white-space: nowrap;
        }

        .test-item-description {
          margin: 0 0 12px 0;
          line-height: 1.5;
          color: #34495e;
        }

        .test-item-metadata {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
          flex-wrap: wrap;
        }

        .metadata-tag {
          padding: 4px 8px;
          background: #ecf0f1;
          border-radius: 4px;
          font-size: 12px;
          color: #2c3e50;
        }

        .test-item-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .action-button {
          padding: 8px 16px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
          min-width: 44px;
          min-height: 44px;
        }

        .action-button:hover {
          background: #f8f9fa;
        }

        .action-button.primary {
          background: #3498db;
          color: white;
          border-color: #3498db;
        }

        .action-button.primary:hover {
          background: #2980b9;
        }

        .action-button.secondary {
          background: #95a5a6;
          color: white;
          border-color: #95a5a6;
        }

        .action-button.icon {
          font-size: 16px;
          padding: 8px 12px;
        }

        .text-samples {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .text-sample-section {
          margin-bottom: 24px;
          padding-bottom: 16px;
          border-bottom: 1px solid #f0f0f0;
        }

        .text-sample-section:last-child {
          border-bottom: none;
          margin-bottom: 0;
        }

        .large-text {
          font-size: 1.2em;
          line-height: 1.4;
        }

        .small-text {
          font-size: 0.9em;
          line-height: 1.4;
          color: #7f8c8d;
        }

        .inline-link {
          color: #3498db;
          text-decoration: none;
        }

        .inline-link:hover {
          text-decoration: underline;
        }

        .quote {
          border-left: 4px solid #3498db;
          padding-left: 16px;
          margin: 16px 0;
          font-style: italic;
          color: #5d6d7e;
        }

        .form-sample {
          max-width: 400px;
        }

        .form-label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
        }

        .form-input, .form-textarea {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          margin-bottom: 16px;
          min-height: 44px;
          box-sizing: border-box;
        }

        .form-actions {
          display: flex;
          gap: 12px;
        }

        .form-button {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          min-height: 44px;
          transition: background 0.2s ease;
        }

        .form-button.primary {
          background: #27ae60;
          color: white;
        }

        .form-button.secondary {
          background: #95a5a6;
          color: white;
        }

        .form-button:hover {
          opacity: 0.9;
        }

        .test-results {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-top: 16px;
        }

        .result-card {
          padding: 16px;
          border-radius: 8px;
          text-align: center;
        }

        .result-card.good {
          background: #d5f4e6;
          border: 1px solid #27ae60;
        }

        .result-card.warning {
          background: #fef9e7;
          border: 1px solid #f39c12;
        }

        .result-card.error {
          background: #fadbd8;
          border: 1px solid #e74c3c;
        }

        .result-score {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 8px;
        }

        .result-details {
          font-size: 12px;
          color: #666;
        }

        @media (max-width: 768px) {
          .font-scaling-test {
            padding: 12px;
          }

          .test-container {
            grid-template-columns: 1fr;
            gap: 16px;
          }

          .zoom-controls {
            gap: 4px;
          }

          .zoom-button {
            font-size: 12px;
            padding: 6px 12px;
            min-width: 60px;
          }

          .test-item-header {
            flex-direction: column;
            gap: 8px;
          }

          .form-actions {
            flex-direction: column;
          }
        }
      `}</style>

      <div className="test-header">
        <h1 className="test-title">🔍 Font Scaling Test Suite</h1>
        <p className="test-description">
          Comprehensive testing of responsive behavior from 50% to 200% font zoom levels
        </p>

        <div className="current-zoom-indicator">
          Current Zoom: {currentZoomLevel}%
        </div>

        <div className="zoom-controls">
          {FONT_SIZE_LEVELS.map(({ level, name }) => (
            <button
              key={level}
              className={`zoom-button ${currentZoomLevel === level ? 'active' : ''}`}
              onClick={() => handleZoomChange(level)}
              disabled={isTestRunning}
            >
              {level}%<br />
              <small>{name}</small>
            </button>
          ))}
        </div>

        <div className="test-actions">
          <button
            className="run-test-button"
            onClick={runFontScalingTest}
            disabled={isTestRunning}
          >
            {isTestRunning ? 'Running Tests...' : 'Run Comprehensive Test'}
          </button>
        </div>
      </div>

      <div className="test-container" ref={testContainerRef}>
        <div className="test-section">
          <h2 className="section-title">📝 List Rendering Test</h2>
          <SimpleResponsiveList
            items={FONT_SCALING_TEST_DATA}
            renderItem={renderTestItem}
            className="font-scaling-list"
          />
        </div>

        <div className="test-section">
          <h2 className="section-title">📄 Typography Samples</h2>
          <TextSamples />
        </div>
      </div>

      {testMetrics.length > 0 && (
        <div className="test-results">
          <h2 className="section-title">📊 Test Results</h2>

          <div className="results-grid">
            {testMetrics.map((metrics, index) => (
              <div
                key={index}
                className={`result-card ${
                  metrics.readabilityScore >= 80 ? 'good' :
                  metrics.readabilityScore >= 60 ? 'warning' : 'error'
                }`}
              >
                <div className="result-score">{metrics.fontSize}%</div>
                <div className="result-details">
                  Score: {metrics.readabilityScore}/100<br />
                  {metrics.horizontalScroll && '⚠️ Horizontal Scroll<br />'}
                  {metrics.layoutBreaks.length > 0 && `${metrics.layoutBreaks.length} Issues<br />`}
                  {metrics.accessibilityIssues.length > 0 && `${metrics.accessibilityIssues.length} A11y Issues`}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 20 }}>
            <h3>Summary</h3>
            <ul>
              <li>Average Readability Score: {
                Math.round(testMetrics.reduce((sum, m) => sum + m.readabilityScore, 0) / testMetrics.length)
              }/100</li>
              <li>Levels with Horizontal Scroll: {
                testMetrics.filter(m => m.horizontalScroll).map(m => `${m.fontSize}%`).join(', ') || 'None'
              }</li>
              <li>Total Accessibility Issues: {
                testMetrics.reduce((sum, m) => sum + m.accessibilityIssues.length, 0)
              }</li>
              <li>WCAG 2.1 AA Compliance: {
                testMetrics.filter(m => m.fontSize >= 100 && !m.horizontalScroll && m.accessibilityIssues.length === 0).length >= 4
                  ? '✅ Compliant' : '❌ Issues Found'
              }</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default FontScalingTest;