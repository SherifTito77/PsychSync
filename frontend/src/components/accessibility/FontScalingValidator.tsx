/**
 * Font Scaling Validator - Real-time accessibility compliance checker
 * Validates WCAG 2.1 AA requirements for text resizing and reflow
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

interface ValidationResult {
  fontSize: number;
  passes: boolean;
  issues: FontScalingIssue[];
  score: number;
  recommendations: string[];
}

interface FontScalingIssue {
  type: 'horizontal-scroll' | 'text-overflow' | 'touch-target' | 'readability' | 'layout-break';
  severity: 'critical' | 'major' | 'minor';
  description: string;
  element?: string;
  wcagReference: string;
  fix: string;
}

interface FontScalingValidatorProps {
  onValidationComplete?: (results: ValidationResult[]) => void;
  autoRun?: boolean;
  testLevels?: number[];
}

export const FontScalingValidator: React.FC<FontScalingValidatorProps> = ({
  onValidationComplete,
  autoRun = false,
  testLevels = [100, 150, 200]
}) => {
  const [isValidating, setIsValidating] = useState(false);
  const [results, setResults] = useState<ValidationResult[]>([]);
  const [currentTest, setCurrentTest] = useState<number | null>(null);
  const originalFontSize = useRef<string>('');
  const containerRef = useRef<HTMLDivElement>(null);

  // Store original font size
  useEffect(() => {
    originalFontSize.current = getComputedStyle(document.documentElement).fontSize;
    return () => {
      // Restore original font size on cleanup
      document.documentElement.style.fontSize = originalFontSize.current;
    };
  }, []);

  // Auto-run validation if enabled
  useEffect(() => {
    if (autoRun) {
      runValidation();
    }
  }, [autoRun]);

  // Validate specific font size level
  const validateFontSize = useCallback(async (fontSizePercent: number): Promise<ValidationResult> => {
    return new Promise((resolve) => {
      // Apply font size
      document.documentElement.style.fontSize = `${fontSizePercent}%`;

      // Allow layout to settle
      setTimeout(() => {
        const issues: FontScalingIssue[] = [];
        let score = 100;

        // Check 1: Horizontal scrolling (WCAG 1.4.10 Reflow)
        const hasHorizontalScroll = document.documentElement.scrollWidth > document.documentElement.clientWidth;
        if (hasHorizontalScroll) {
          issues.push({
            type: 'horizontal-scroll',
            severity: 'critical',
            description: 'Horizontal scrolling is required to access content',
            wcagReference: 'WCAG 1.4.10 Reflow',
            fix: 'Ensure content reflows properly without horizontal scrolling at 200% zoom'
          });
          score -= 40;
        }

        // Check 2: Text overflow in specific elements
        const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, dt, dd');
        textElements.forEach((element) => {
          const el = element as HTMLElement;
          if (el.scrollWidth > el.clientWidth) {
            issues.push({
              type: 'text-overflow',
              severity: 'major',
              description: `Text overflow in ${el.tagName.toLowerCase()} element`,
              element: el.tagName.toLowerCase(),
              wcagReference: 'WCAG 1.4.10 Reflow',
              fix: 'Use responsive typography and proper text wrapping'
            });
            score -= 15;
          }
        });

        // Check 3: Touch target sizes (WCAG 2.5.5 Target Size)
        const touchTargets = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        touchTargets.forEach((target) => {
          const rect = (target as HTMLElement).getBoundingClientRect();
          const minSize = 44 * (fontSizePercent / 100); // Scale minimum with font size

          if (rect.width < minSize || rect.height < minSize) {
            issues.push({
              type: 'touch-target',
              severity: 'major',
              description: `Touch target too small: ${Math.round(rect.width)}x${Math.round(rect.height)}px`,
              element: target.tagName.toLowerCase(),
              wcagReference: 'WCAG 2.5.5 Target Size',
              fix: 'Ensure touch targets are at least 44x44px (scaled with font size)'
            });
            score -= 10;
          }
        });

        // Check 4: Readability at different sizes
        if (fontSizePercent < 75) {
          issues.push({
            type: 'readability',
            severity: 'minor',
            description: 'Font size may be too small for comfortable reading',
            wcagReference: 'WCAG 1.4.4 Resize text',
            fix: 'Ensure text remains readable at smaller sizes'
          });
          score -= 10;
        }

        // Check 5: Layout breaks
        const flexContainers = document.querySelectorAll('[style*="display: flex"], .flex, .flex-container');
        flexContainers.forEach((container) => {
          const el = container as HTMLElement;
          const computedStyle = getComputedStyle(el);

          // Check for forced wrapping or overlap
          if (fontSizePercent > 150) {
            const children = el.children;
            let overlapDetected = false;

            for (let i = 0; i < children.length - 1; i++) {
              const child1 = children[i] as HTMLElement;
              const child2 = children[i + 1] as HTMLElement;
              const rect1 = child1.getBoundingClientRect();
              const rect2 = child2.getBoundingClientRect();

              if (rect1.right > rect2.left && rect1.bottom > rect2.top) {
                overlapDetected = true;
                break;
              }
            }

            if (overlapDetected) {
              issues.push({
                type: 'layout-break',
                severity: 'major',
                description: 'Element overlap detected at large font sizes',
                element: 'flex container',
                wcagReference: 'WCAG 1.4.10 Reflow',
                fix: 'Use flexible layouts that adapt to font size changes'
              });
              score -= 20;
            }
          }
        });

        // Check 6: Spacing and line height
        const textBlocks = document.querySelectorAll('p, li, dd');
        textBlocks.forEach((block) => {
          const el = block as HTMLElement;
          const computedStyle = getComputedStyle(el);
          const lineHeight = parseFloat(computedStyle.lineHeight);
          const fontSize = parseFloat(computedStyle.fontSize);
          const lineHeightRatio = lineHeight / fontSize;

          if (lineHeightRatio < 1.3) {
            issues.push({
              type: 'readability',
              severity: 'minor',
              description: 'Line height too small for comfortable reading',
              element: el.tagName.toLowerCase(),
              wcagReference: 'WCAG 1.4.8 Visual Presentation',
              fix: 'Use line height of at least 1.3 for body text'
            });
            score -= 5;
          }
        });

        // Generate recommendations
        const recommendations: string[] = [];
        if (issues.some(i => i.type === 'horizontal-scroll')) {
          recommendations.push('Use max-width: 100% and flexible layouts');
        }
        if (issues.some(i => i.type === 'text-overflow')) {
          recommendations.push('Implement proper text wrapping and overflow handling');
        }
        if (issues.some(i => i.type === 'touch-target')) {
          recommendations.push('Increase touch target sizes or add padding');
        }
        if (issues.some(i => i.type === 'readability')) {
          recommendations.push('Optimize font sizes and line heights for better readability');
        }
        if (issues.some(i => i.type === 'layout-break')) {
          recommendations.push('Use CSS Grid or Flexbox with proper wrapping');
        }

        if (recommendations.length === 0) {
          recommendations.push('Great job! No major font scaling issues detected.');
        }

        resolve({
          fontSize: fontSizePercent,
          passes: score >= 80 && !hasHorizontalScroll,
          issues,
          score: Math.max(0, score),
          recommendations
        });
      }, 300);
    });
  }, []);

  // Run validation for all test levels
  const runValidation = useCallback(async () => {
    setIsValidating(true);
    setResults([]);

    const validationResults: ValidationResult[] = [];

    for (const fontSize of testLevels) {
      setCurrentTest(fontSize);
      const result = await validateFontSize(fontSize);
      validationResults.push(result);

      // Brief pause between tests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    setCurrentTest(null);
    setResults(validationResults);
    setIsValidating(false);

    // Restore original font size
    document.documentElement.style.fontSize = originalFontSize.current;

    if (onValidationComplete) {
      onValidationComplete(validationResults);
    }
  }, [testLevels, validateFontSize, onValidationComplete]);

  // Clear results
  const clearResults = () => {
    setResults([]);
    document.documentElement.style.fontSize = originalFontSize.current;
  };

  // Test specific font size
  const testSpecificSize = async (fontSize: number) => {
    setCurrentTest(fontSize);
    const result = await validateFontSize(fontSize);
    setResults([result]);
    setCurrentTest(null);
    document.documentElement.style.fontSize = originalFontSize.current;
  };

  return (
    <div className="font-scaling-validator" ref={containerRef}>
      <style>{`
        .font-scaling-validator {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .validator-header {
          text-align: center;
          margin-bottom: 24px;
        }

        .validator-title {
          font-size: 24px;
          font-weight: 600;
          margin-bottom: 8px;
          color: #2c3e50;
        }

        .validator-description {
          color: #7f8c8d;
          margin-bottom: 20px;
        }

        .validator-controls {
          display: flex;
          gap: 12px;
          justify-content: center;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .control-button {
          padding: 8px 16px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .control-button:hover {
          background: #f8f9fa;
        }

        .control-button.primary {
          background: #3498db;
          color: white;
          border-color: #3498db;
        }

        .control-button.primary:hover {
          background: #2980b9;
        }

        .control-button.danger {
          background: #e74c3c;
          color: white;
          border-color: #e74c3c;
        }

        .control-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .quick-test-sizes {
          display: flex;
          gap: 8px;
          justify-content: center;
          margin-top: 16px;
          flex-wrap: wrap;
        }

        .size-button {
          padding: 6px 12px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          min-width: 60px;
        }

        .size-button:hover {
          background: #f8f9fa;
        }

        .size-button.active {
          background: #e8f5e8;
          border-color: #27ae60;
        }

        .validation-status {
          text-align: center;
          margin-bottom: 20px;
          padding: 16px;
          border-radius: 8px;
          font-weight: 500;
        }

        .validation-status.validating {
          background: #fef9e7;
          color: #f39c12;
          border: 1px solid #f39c12;
        }

        .validation-status.idle {
          background: #f8f9fa;
          color: #6c757d;
          border: 1px solid #dee2e6;
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin-top: 20px;
        }

        .result-card {
          border: 1px solid #dee2e6;
          border-radius: 8px;
          overflow: hidden;
        }

        .result-header {
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #dee2e6;
        }

        .result-size {
          font-size: 18px;
          font-weight: 600;
        }

        .result-status {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .result-status.pass {
          background: #d5f4e6;
          color: #27ae60;
        }

        .result-status.fail {
          background: #fadbd8;
          color: #e74c3c;
        }

        .result-body {
          padding: 16px;
        }

        .score-display {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }

        .score-label {
          font-weight: 500;
        }

        .score-value {
          font-size: 24px;
          font-weight: bold;
        }

        .score-value.good {
          color: #27ae60;
        }

        .score-value.warning {
          color: #f39c12;
        }

        .score-value.poor {
          color: #e74c3c;
        }

        .issues-section {
          margin-bottom: 16px;
        }

        .issues-title {
          font-weight: 500;
          margin-bottom: 8px;
          color: #495057;
        }

        .issue-item {
          padding: 8px;
          margin-bottom: 4px;
          border-radius: 4px;
          font-size: 13px;
        }

        .issue-item.critical {
          background: #fadbd8;
          border-left: 3px solid #e74c3c;
        }

        .issue-item.major {
          background: #fef9e7;
          border-left: 3px solid #f39c12;
        }

        .issue-item.minor {
          background: #e8f5e8;
          border-left: 3px solid #27ae60;
        }

        .issue-description {
          font-weight: 500;
          margin-bottom: 2px;
        }

        .issue-fix {
          font-size: 11px;
          color: #6c757d;
        }

        .recommendations-section {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #dee2e6;
        }

        .recommendations-title {
          font-weight: 500;
          margin-bottom: 8px;
          color: #495057;
        }

        .recommendation-item {
          padding: 6px 0;
          font-size: 13px;
          color: #495057;
        }

        .recommendation-item::before {
          content: '• ';
          color: #3498db;
          font-weight: bold;
        }

        .summary-section {
          margin-top: 24px;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .summary-title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 12px;
          color: #2c3e50;
        }

        .summary-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .stat-item {
          text-align: center;
          padding: 16px;
          background: white;
          border-radius: 8px;
          border: 1px solid #dee2e6;
        }

        .stat-value {
          font-size: 24px;
          font-weight: bold;
          color: #3498db;
        }

        .stat-label {
          font-size: 14px;
          color: #6c757d;
          margin-top: 4px;
        }

        @media (max-width: 768px) {
          .font-scaling-validator {
            padding: 16px;
          }

          .validator-controls {
            flex-direction: column;
          }

          .control-button {
            width: 100%;
          }

          .quick-test-sizes {
            justify-content: center;
          }

          .results-grid {
            grid-template-columns: 1fr;
          }

          .summary-stats {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div className="validator-header">
        <h2 className="validator-title">♿ Font Scaling Validator</h2>
        <p className="validator-description">
          WCAG 2.1 AA compliance checker for text resizing and reflow requirements
        </p>
      </div>

      <div className="validator-controls">
        <button
          className="control-button primary"
          onClick={runValidation}
          disabled={isValidating}
        >
          {isValidating ? 'Validating...' : 'Run Full Validation'}
        </button>

        <button
          className="control-button danger"
          onClick={clearResults}
          disabled={isValidating}
        >
          Clear Results
        </button>
      </div>

      <div className="quick-test-sizes">
        <span>Quick test:</span>
        {[50, 75, 100, 125, 150, 175, 200].map(size => (
          <button
            key={size}
            className={`size-button ${currentTest === size ? 'active' : ''}`}
            onClick={() => testSpecificSize(size)}
            disabled={isValidating}
          >
            {size}%
          </button>
        ))}
      </div>

      <div className={`validation-status ${isValidating ? 'validating' : 'idle'}`}>
        {isValidating
          ? `Testing font size: ${currentTest}%...`
          : results.length === 0
            ? 'Ready to validate font scaling compliance'
            : `Validation complete - ${results.filter(r => r.passes).length}/${results.length} test levels passed`
        }
      </div>

      {results.length > 0 && (
        <>
          <div className="results-grid">
            {results.map((result, index) => (
              <div key={index} className="result-card">
                <div className="result-header">
                  <div className="result-size">{result.fontSize}% Font Size</div>
                  <div className={`result-status ${result.passes ? 'pass' : 'fail'}`}>
                    {result.passes ? '✅ Pass' : '❌ Fail'}
                  </div>
                </div>

                <div className="result-body">
                  <div className="score-display">
                    <span className="score-label">Accessibility Score:</span>
                    <span className={`score-value ${
                      result.score >= 80 ? 'good' : result.score >= 60 ? 'warning' : 'poor'
                    }`}>
                      {result.score}/100
                    </span>
                  </div>

                  {result.issues.length > 0 && (
                    <div className="issues-section">
                      <div className="issues-title">
                        Issues Found ({result.issues.length})
                      </div>
                      {result.issues.map((issue, issueIndex) => (
                        <div key={issueIndex} className={`issue-item ${issue.severity}`}>
                          <div className="issue-description">
                            {issue.description}
                          </div>
                          <div className="issue-fix">
                            <strong>Fix:</strong> {issue.fix}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="recommendations-section">
                    <div className="recommendations-title">Recommendations</div>
                    {result.recommendations.map((rec, recIndex) => (
                      <div key={recIndex} className="recommendation-item">
                        {rec}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="summary-section">
            <h3 className="summary-title">📊 Validation Summary</h3>

            <div className="summary-stats">
              <div className="stat-item">
                <div className="stat-value">
                  {results.filter(r => r.passes).length}/{results.length}
                </div>
                <div className="stat-label">Tests Passed</div>
              </div>

              <div className="stat-item">
                <div className="stat-value">
                  {Math.round(results.reduce((sum, r) => sum + r.score, 0) / results.length)}
                </div>
                <div className="stat-label">Average Score</div>
              </div>

              <div className="stat-item">
                <div className="stat-value">
                  {results.reduce((sum, r) => sum + r.issues.length, 0)}
                </div>
                <div className="stat-label">Total Issues</div>
              </div>

              <div className="stat-item">
                <div className="stat-value">
                  {results.some(r => r.passes && r.fontSize >= 200) ? '✅' : '❌'}
                </div>
                <div className="stat-label">WCAG 2.1 AA</div>
              </div>
            </div>

            <div style={{ marginTop: 16, fontSize: 14, color: '#6c757d' }}>
              <strong>WCAG 2.1 AA Requirements:</strong>
              <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                <li>Text can be resized up to 200% without loss of content or functionality</li>
                <li>No horizontal scrolling is required at 200% zoom</li>
                <li>Content reflows properly within the available space</li>
                <li>Touch targets remain accessible at all font sizes</li>
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default FontScalingValidator;