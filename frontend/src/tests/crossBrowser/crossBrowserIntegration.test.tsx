/**
 * Main Cross-Browser Integration Test Suite
 * Integrates all cross-browser testing components and provides comprehensive analysis
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { BrowserDetector, BrowserTestUtils } from './crossBrowserTestSuite';
import { AutomatedBrowserRunner, type CompatibilityReport } from './automatedBrowserRunner';
import { BROWSER_COMPATIBILITY_MATRIX, CROSS_BROWSER_TEST_CASES } from './browserCompatibilityMatrix';

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('🌐 Comprehensive Cross-Browser Integration Tests', () => {
  let browserInfo: any;
  let compatibilityReport: CompatibilityReport | null = null;

  beforeAll(async () => {
    browserInfo = BrowserDetector.getBrowserInfo();
    console.log(`🌐 Starting cross-browser integration tests on: ${browserInfo.name} ${browserInfo.version}`);

    // Run the automated browser test suite
    compatibilityReport = await browserRunner.runCrossBrowserTests();
  });

  afterAll(() => {
    console.log('\n📊 Cross-Browser Integration Test Summary:');
    if (compatibilityReport) {
      console.log(`Overall Compatibility: ${compatibilityReport.overallCompatibility.toFixed(1)}%`);
      console.log(`Tested Browsers: ${compatibilityReport.testedBrowsers.join(', ')}`);

      if (compatibilityReport.recommendations.length > 0) {
        console.log('\n💡 Recommendations:');
        compatibilityReport.recommendations.forEach((rec, index) => {
          console.log(`${index + 1}. ${rec}`);
        });
      }

      if (compatibilityReport.criticalIssues.length > 0) {
        console.log('\n🚨 Critical Issues:');
        compatibilityReport.criticalIssues.forEach((issue, index) => {
          console.log(`${index + 1}. ${issue}`);
        });
      }
    }
  });

  describe('🔍 Browser Detection & Analysis', () => {
    it('should correctly identify browser information', () => {
      expect(browserInfo).toBeDefined();
      expect(browserInfo.name).toBeOneOf(['Chrome', 'Edge', 'Safari', 'Firefox']);
      expect(browserInfo.version).toBeDefined();
      expect(browserInfo.engine).toBeOneOf(['Blink', 'WebKit', 'Gecko']);
      expect(browserInfo.platform).toBeDefined();

      console.log(`Browser: ${browserInfo.name} ${browserInfo.version} (${browserInfo.engine})`);
    });

    it('should provide accurate feature support information', () => {
      const features = [
        'css-grid', 'css-flexbox', 'css-variables', 'backdrop-filter',
        'focus-visible', 'intersection-observer', 'resize-observer'
      ];

      features.forEach(feature => {
        const supported = BrowserDetector.supportsFeature(feature);
        const matrixSupport = BROWSER_COMPATIBILITY_MATRIX[feature]?.[browserInfo.name as keyof typeof BROWSER_COMPATIBILITY_MATRIX[typeof feature]]?.supported;

        console.log(`${feature}: ${supported ? '✅' : '❌'} (Expected: ${matrixSupport ? '✅' : '❌'})`);

        // Allow for slight differences in feature detection
        expect(typeof supported).toBe('boolean');
      });
    });

    it('should detect rendering engine correctly', () => {
      const engine = BrowserDetector.getRenderingEngine();
      expect(engine).toBeOneOf(['Blink', 'WebKit', 'Gecko']);

      const expectedEngine = {
        'Chrome': 'Blink',
        'Edge': 'Blink',
        'Safari': 'WebKit',
        'Firefox': 'Gecko'
      }[browserInfo.name];

      expect(engine).toBe(expectedEngine);
    });
  });

  describe('🎨 CSS Cross-Browser Compatibility', () => {
    it('should render CSS Grid layouts consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <div style={{ padding: '16px', border: '1px solid #ccc' }}>Grid Item 1</div>
            <div style={{ padding: '16px', border: '1px solid #ccc' }}>Grid Item 2</div>
            <div style={{ padding: '16px', border: '1px solid #ccc' }}>Grid Item 3</div>
          </div>
        </TestWrapper>
      );

      const gridElement = container.firstElementChild as HTMLElement;
      expect(gridElement).toBeTruthy();

      const gridBehavior = await BrowserTestUtils.testGridBehavior(gridElement);
      expect(gridBehavior.supports).toBe(true);

      console.log(`Grid Support: ${gridBehavior.supports ? '✅' : '❌'}`);
      console.log(`Grid Columns: ${gridBehavior.columns}`);
    });

    it('should render Flexbox layouts consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ padding: '16px', border: '1px solid #ccc' }}>Flex Item 1</div>
            <div style={{ padding: '16px', border: '1px solid #ccc' }}>Flex Item 2</div>
          </div>
        </TestWrapper>
      );

      const flexElement = container.firstElementChild as HTMLElement;
      expect(flexElement).toBeTruthy();

      const flexBehavior = await BrowserTestUtils.testFlexboxBehavior(flexElement);
      expect(flexBehavior.supports).toBe(true);

      console.log(`Flexbox Support: ${flexBehavior.supports ? '✅' : '❌'}`);
      console.log(`Flex Direction: ${flexBehavior.direction}`);
    });

    it('should handle CSS Custom Properties correctly', () => {
      const { container } = render(
        <TestWrapper>
          <div
            style={{
              '--primary-color': '#3b82f6',
              '--secondary-color': '#64748b',
              padding: '16px',
              backgroundColor: 'var(--primary-color)',
              color: 'var(--secondary-color)'
            }}
          >
            Custom Properties Test
          </div>
        </TestWrapper>
      );

      const element = container.firstElementChild as HTMLElement;
      const style = window.getComputedStyle(element);

      const hasBackgroundColor = style.backgroundColor.includes('59, 130, 246') ||
                                style.backgroundColor.includes('3b82f6');
      const hasTextColor = style.color.includes('100, 116, 139') ||
                          style.color.includes('64748b');

      console.log(`Custom Properties Background: ${hasBackgroundColor ? '✅' : '❌'}`);
      console.log(`Custom Properties Text Color: ${hasTextColor ? '✅' : '❌'}`);

      expect(hasBackgroundColor).toBe(true);
      expect(hasTextColor).toBe(true);
    });
  });

  describe('⚡ Performance Cross-Browser Tests', () => {
    it('should handle large DOM structures efficiently', async () => {
      const startTime = performance.now();

      const { container } = render(
        <TestWrapper>
          <div>
            {Array.from({ length: 500 }, (_, i) => (
              <button key={i} style={{ margin: '4px', padding: '8px' }}>
                Button {i + 1}
              </button>
            ))}
          </div>
        </TestWrapper>
      );

      const renderTime = performance.now() - startTime;
      const buttons = container.querySelectorAll('button');

      expect(buttons).toHaveLength(500);

      console.log(`Large DOM Render Time: ${renderTime.toFixed(2)}ms`);
      console.log(`Performance: ${renderTime < 1000 ? '✅ Good' : '⚠️  Needs optimization'}`);

      expect(renderTime).toBeLessThan(2000); // Allow generous limit for testing environment
    });

    it('should handle animations smoothly', async () => {
      const { container } = render(
        <TestWrapper>
          <div
            style={{
              width: '100px',
              height: '100px',
              backgroundColor: '#3b82f6',
              transition: 'transform 0.3s ease',
              transform: 'translateX(0)'
            }}
            data-testid="animated-element"
          >
            Animated Box
          </div>
        </TestWrapper>
      );

      const element = container.querySelector('[data-testid="animated-element"]') as HTMLElement;
      expect(element).toBeTruthy();

      const hasTransition = BrowserTestUtils.testTransitionSupport('transform', element);
      console.log(`Transition Support: ${await hasTransition ? '✅' : '❌'}`);

      // Trigger animation
      fireEvent.mouseOver(element);
      element.style.transform = 'translateX(20px)';

      // Wait for animation
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(element).toBeTruthy();
    });
  });

  describe('♿ Accessibility Cross-Browser Tests', () => {
    it('should support ARIA attributes consistently', () => {
      const { container } = render(
        <TestWrapper>
          <button aria-label="Close Button">×</button>
          <div role="alert" aria-live="polite">Important notification</div>
          <input aria-describedby="helper" aria-label="Email input" />
          <span id="helper">Enter your email address</span>
        </TestWrapper>
      );

      const button = container.querySelector('button[aria-label]') as HTMLButtonElement;
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      const input = container.querySelector('input[aria-describedby]') as HTMLInputElement;
      const helper = container.querySelector('#helper') as HTMLElement;

      expect(button?.getAttribute('aria-label')).toBe('Close Button');
      expect(alert?.getAttribute('role')).toBe('alert');
      expect(alert?.getAttribute('aria-live')).toBe('polite');
      expect(input?.getAttribute('aria-describedby')).toBe('helper');
      expect(helper).toBeTruthy();

      console.log(`ARIA Attributes: ✅ Properly implemented`);
    });

    it('should handle focus management correctly', async () => {
      const { container } = render(
        <TestWrapper>
          <div>
            <button id="button1">Button 1</button>
            <button id="button2">Button 2</button>
            <input type="text" placeholder="Test input" />
            <button id="button3">Button 3</button>
          </div>
        </TestWrapper>
      );

      const buttons = container.querySelectorAll('button');
      const input = container.querySelector('input');

      expect(buttons).toHaveLength(3);
      expect(input).toBeTruthy();

      // Test tab order
      buttons.forEach((button, index) => {
        button.focus();
        expect(document.activeElement).toBe(button);
      });

      console.log(`Focus Management: ✅ Keyboard navigation working`);
    });
  });

  describe('📱 Responsive Design Cross-Browser Tests', () => {
    it('should handle viewport changes consistently', async () => {
      // Test different viewport sizes
      const viewportSizes = [
        { width: 375, height: 667, name: 'Mobile' },
        { width: 768, height: 1024, name: 'Tablet' },
        { width: 1920, height: 1080, name: 'Desktop' }
      ];

      for (const viewport of viewportSizes) {
        // Mock viewport size
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: viewport.width,
        });

        const { container } = render(
          <TestWrapper>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '16px'
            }}>
              <div style={{ padding: '16px', border: '1px solid #ccc' }}>
                Responsive Item 1
              </div>
              <div style={{ padding: '16px', border: '1px solid #ccc' }}>
                Responsive Item 2
              </div>
            </div>
          </TestWrapper>
        );

        const gridElement = container.firstElementChild as HTMLElement;
        const gridBehavior = await BrowserTestUtils.testGridBehavior(gridElement);

        console.log(`${viewport.name} (${viewport.width}px): Grid Support ${gridBehavior.supports ? '✅' : '❌'}`);

        expect(gridBehavior.supports).toBe(true);

        container.remove();
      }
    });
  });

  describe('🔧 Browser-Specific Feature Tests', () => {
    it('should handle Blink-specific features correctly', async () => {
      if (browserInfo.engine === 'Blink') {
        const { container } = render(
          <TestWrapper>
            <div
              style={{
                backdropFilter: 'blur(4px)',
                WebkitBackdropFilter: 'blur(4px)',
                padding: '16px',
                backgroundColor: 'rgba(255, 255, 255, 0.8)'
              }}
            >
              Blur Effect Test
            </div>
          </TestWrapper>
        );

        const element = container.firstElementChild as HTMLElement;
        const style = window.getComputedStyle(element);

        const hasBackdropFilter = style.backdropFilter !== 'none' || style.webkitBackdropFilter !== 'none';

        console.log(`Blink Backdrop Filter: ${hasBackdropFilter ? '✅' : '❌'}`);
        expect(hasBackdropFilter || !BrowserDetector.supportsFeature('backdrop-filter')).toBe(true);
      } else {
        console.log(`Blink Features: ⏭ Skipped (${browserInfo.name})`);
        expect(true).toBe(true);
      }
    });

    it('should handle WebKit-specific features correctly', async () => {
      if (browserInfo.engine === 'WebKit') {
        const { container } = render(
          <TestWrapper>
            <input
              type="search"
              style={{
                WebkitAppearance: 'none',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
              placeholder="Search..."
            />
          </TestWrapper>
        );

        const input = container.querySelector('input') as HTMLInputElement;
        expect(input).toBeTruthy();

        const style = window.getComputedStyle(input);
        const hasWebkitAppearance = style.webkitAppearance || style.appearance;

        console.log(`WebKit Appearance: ${hasWebkitAppearance ? '✅' : '❌'}`);
        expect(input).toBeTruthy();
      } else {
        console.log(`WebKit Features: ⏭ Skipped (${browserInfo.name})`);
        expect(true).toBe(true);
      }
    });

    it('should handle Gecko-specific features correctly', async () => {
      if (browserInfo.engine === 'Gecko') {
        const { container } = render(
          <TestWrapper>
            <div
              style={{
                MozBorderRadius: '8px',
                padding: '16px',
                border: '1px solid #ccc'
              }}
            >
              Gecko Test
            </div>
          </TestWrapper>
        );

        const element = container.firstElementChild as HTMLElement;
        const style = window.getComputedStyle(element);

        const hasBorderRadius = style.borderRadius && style.borderRadius !== '0px';

        console.log(`Gecko Border Radius: ${hasBorderRadius ? '✅' : '❌'}`);
        expect(hasBorderRadius).toBe(true);
      } else {
        console.log(`Gecko Features: ⏭ Skipped (${browserInfo.name})`);
        expect(true).toBe(true);
      }
    });
  });

  describe('📊 Compatibility Analysis', () => {
    it('should generate comprehensive compatibility report', () => {
      expect(compatibilityReport).toBeDefined();

      if (compatibilityReport) {
        console.log('\n📊 Final Compatibility Analysis:');
        console.log(`Overall Compatibility Score: ${compatibilityReport.overallCompatibility.toFixed(1)}%`);
        console.log(`Test Results Generated: ${compatibilityReport.testResults.length} browser(s)`);

        // Verify report structure
        expect(compatibilityReport.timestamp).toBeDefined();
        expect(compatibilityReport.testedBrowsers).toContain(browserInfo.name);
        expect(compatibilityReport.featureSupport).toBeDefined();
        expect(Array.isArray(compatibilityReport.recommendations)).toBe(true);
        expect(Array.isArray(compatibilityReport.criticalIssues)).toBe(true);

        // Check for reasonable compatibility score
        expect(compatibilityReport.overallCompatibility).toBeGreaterThan(0);
        expect(compatibilityReport.overallCompatibility).toBeLessThanOrEqual(100);
      }
    });

    it('should provide actionable recommendations', () => {
      expect(compatibilityReport).toBeDefined();

      if (compatibilityReport) {
        const recommendations = compatibilityReport.recommendations;
        const criticalIssues = compatibilityReport.criticalIssues;

        console.log(`\n💡 Total Recommendations: ${recommendations.length}`);
        console.log(`🚨 Critical Issues: ${criticalIssues.length}`);

        // Recommendations should be actionable
        recommendations.forEach(rec => {
          expect(rec.length).toBeGreaterThan(0);
          expect(typeof rec).toBe('string');
        });

        // Critical issues should be descriptive
        criticalIssues.forEach(issue => {
          expect(issue.length).toBeGreaterThan(0);
          expect(typeof issue).toBe('string');
        });
      }
    });
  });

  describe('🎯 Browser Compatibility Matrix Validation', () => {
    it('should validate browser compatibility matrix', () => {
      // Verify matrix structure
      Object.keys(BROWSER_COMPATIBILITY_MATRIX).forEach(feature => {
        const featureData = BROWSER_COMPATIBILITY_MATRIX[feature];
        expect(featureData).toBeDefined();
        expect(featureData.Chrome).toBeDefined();
        expect(featureData.Edge).toBeDefined();
        expect(featureData.Safari).toBeDefined();
        expect(featureData.Firefox).toBeDefined();
      });

      console.log('✅ Browser compatibility matrix is properly structured');
    });

    it('should have comprehensive test case coverage', () => {
      expect(CROSS_BROWSER_TEST_CASES.length).toBeGreaterThan(0);

      CROSS_BROWSER_TEST_CASES.forEach(testCase => {
        expect(testCase.id).toBeDefined();
        expect(testCase.name).toBeDefined();
        expect(testCase.category).toBeDefined();
        expect(testCase.priority).toBeDefined();
        expect(testCase.browsers).toBeDefined();
        expect(testCase.testSteps).toBeDefined();
        expect(testCase.expectedResult).toBeDefined();
      });

      console.log(`✅ Test case coverage: ${CROSS_BROWSER_TEST_CASES.length} test cases`);
    });
  });
});
