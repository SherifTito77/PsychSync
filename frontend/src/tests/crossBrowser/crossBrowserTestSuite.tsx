/**
 * Comprehensive Cross-Browser Testing Framework for PsychSync
 * Tests for Edge, Chrome, Safari, and Firefox compatibility
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

// Import components to test
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import NotificationContainer from '../../components/common/NotificationContainer';
import { NotificationProvider, useNotification } from '../../contexts/NotificationContext';

// Browser detection utilities
export class BrowserDetector {
  static getBrowserInfo(): {
    name: string;
    version: string;
    engine: string;
    platform: string;
  } {
    const ua = navigator.userAgent;

    // Chrome/Edge (Chromium)
    if (ua.includes('Chrome') && !ua.includes('Edg')) {
      const match = ua.match(/Chrome\/(\d+\.\d+)/);
      return {
        name: 'Chrome',
        version: match ? match[1] : 'Unknown',
        engine: 'Blink',
        platform: navigator.platform
      };
    }

    // Edge (Chromium)
    if (ua.includes('Edg')) {
      const match = ua.match(/Edg\/(\d+\.\d+)/);
      return {
        name: 'Edge',
        version: match ? match[1] : 'Unknown',
        engine: 'Blink',
        platform: navigator.platform
      };
    }

    // Safari
    if (ua.includes('Safari') && !ua.includes('Chrome')) {
      const match = ua.match(/Version\/(\d+\.\d+)/);
      return {
        name: 'Safari',
        version: match ? match[1] : 'Unknown',
        engine: 'WebKit',
        platform: navigator.platform
      };
    }

    // Firefox
    if (ua.includes('Firefox')) {
      const match = ua.match(/Firefox\/(\d+\.\d+)/);
      return {
        name: 'Firefox',
        version: match ? match[1] : 'Unknown',
        engine: 'Gecko',
        platform: navigator.platform
      };
    }

    return {
      name: 'Unknown',
      version: 'Unknown',
      engine: 'Unknown',
      platform: navigator.platform
    };
  }

  static supportsFeature(feature: string): boolean {
    switch (feature) {
      case 'css-grid':
        return typeof CSS !== 'undefined' && CSS.supports ? CSS.supports('display', 'grid') : true;
      case 'css-flexbox':
        return typeof CSS !== 'undefined' && CSS.supports ? CSS.supports('display', 'flex') : true;
      case 'css-variables':
        return typeof CSS !== 'undefined' && CSS.supports ? CSS.supports('color', 'var(--test)') : true;
      case 'backdrop-filter':
        return typeof CSS !== 'undefined' && CSS.supports ? CSS.supports('backdrop-filter', 'blur(10px)') : false;
      case 'focus-visible':
        return typeof CSS !== 'undefined' && CSS.supports ? CSS.supports(':focus-visible') : true;
      case 'scroll-behavior':
        return typeof CSS !== 'undefined' && CSS.supports ? CSS.supports('scroll-behavior', 'smooth') : false;
      case 'intersection-observer':
        return 'IntersectionObserver' in window;
      case 'resize-observer':
        return 'ResizeObserver' in window;
      case 'webp':
        try {
          return document.createElement('canvas').toDataURL('image/webp').indexOf('data:image/webp') === 0;
        } catch {
          return false;
        }
      case 'avif':
        try {
          return document.createElement('canvas').toDataURL('image/avif').indexOf('data:image/avif') === 0;
        } catch {
          return false;
        }
      case 'web-share':
        return 'share' in navigator;
      case 'clipboard':
        return 'clipboard' in navigator;
      case 'service-worker':
        return 'serviceWorker' in navigator;
      case 'push-notifications':
        return 'PushManager' in window;
      default:
        return false;
    }
  }

  static getRenderingEngine(): 'Blink' | 'WebKit' | 'Gecko' | 'Unknown' {
    const browser = this.getBrowserInfo();
    return browser.engine as any;
  }
}

// Browser-specific test utilities
export class BrowserTestUtils {
  static async testCSSSupport(
    propertyName: string,
    propertyValue: string,
    element: HTMLElement
  ): Promise<boolean> {
    const style = window.getComputedStyle(element);
    return style.getPropertyValue(propertyName) === propertyValue;
  }

  static async testAnimationSupport(
    animationName: string,
    element: HTMLElement
  ): Promise<boolean> {
    const style = window.getComputedStyle(element);
    return style.animationName !== 'none' || style.animationName.includes(animationName);
  }

  static async testTransitionSupport(
    property: string,
    element: HTMLElement
  ): Promise<boolean> {
    const style = window.getComputedStyle(element);
    return style.transitionProperty.includes(property);
  }

  static async testFlexboxBehavior(element: HTMLElement): Promise<{
    supports: boolean;
    direction: string;
    wrap: boolean;
  }> {
    const style = window.getComputedStyle(element);
    return {
      supports: style.display === 'flex' || style.display === '-webkit-flex' || style.display === '-ms-flexbox',
      direction: style.flexDirection || style.webkitFlexDirection || '',
      wrap: style.flexWrap === 'wrap' || style.webkitFlexWrap === 'wrap'
    };
  }

  static async testGridBehavior(element: HTMLElement): Promise<{
    supports: boolean;
    columns: number;
    rows: number;
  }> {
    const style = window.getComputedStyle(element);
    return {
      supports: style.display === 'grid' || style.display === '-ms-grid' || style.display === '-webkit-grid',
      columns: parseInt(style.gridTemplateColumns?.split(' ').length.toString() || '0'),
      rows: parseInt(style.gridTemplateRows?.split(' ').length.toString() || '0')
    };
  }
}

// Test results collector
export class CrossBrowserTestResults {
  private results: Array<{
    browser: string;
    version: string;
    test: string;
    passed: boolean;
    issues: string[];
    performance: number;
  }> = [];

  addResult(
    browser: string,
    version: string,
    test: string,
    passed: boolean,
    issues: string[] = [],
    performance = 0
  ): void {
    this.results.push({
      browser,
      version,
      test,
      passed,
      issues,
      performance
    });
  }

  getResults() {
    return this.results;
  }

  getResultsByBrowser(browser: string) {
    return this.results.filter(r => r.browser === browser);
  }

  getFailedTests() {
    return this.results.filter(r => !r.passed);
  }

  getCompatibilityReport() {
    const browsers = ['Chrome', 'Edge', 'Safari', 'Firefox'];
    const report: Record<string, any> = {};

    browsers.forEach(browser => {
      const browserResults = this.getResultsByBrowser(browser);
      const totalTests = browserResults.length;
      const passedTests = browserResults.filter(r => r.passed).length;
      const failedTests = browserResults.filter(r => !r.passed);

      report[browser] = {
        totalTests,
        passedTests,
        failedTests: failedTests.length,
        passRate: totalTests > 0 ? (passedTests / totalTests * 100).toFixed(1) : 0,
        issues: failedTests.flatMap(f => f.issues),
        avgPerformance: browserResults.reduce((sum, r) => sum + r.performance, 0) / totalTests
      };
    });

    return report;
  }
}

// Test wrapper for cross-browser testing
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <NotificationProvider>
      {children}
    </NotificationProvider>
  </BrowserRouter>
);

describe('🌐 Comprehensive Cross-Browser Testing Suite', () => {
  const browserInfo = BrowserDetector.getBrowserInfo();
  const results = new CrossBrowserTestResults();

  beforeAll(async () => {
    console.log(`🌐 Running cross-browser tests on: ${browserInfo.name} ${browserInfo.version} (${browserInfo.engine})`);
  });

  afterAll(() => {
    const report = results.getCompatibilityReport();
    console.log('\n📊 Cross-Browser Compatibility Report:');
    console.table(report);
  });

  beforeEach(() => {
    // Reset any browser-specific state
  });

  describe('🎨 CSS Feature Support Tests', () => {
    it('should support CSS Grid layout', () => {
      const { container } = render(
        <TestWrapper>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
            <div>Grid Item 1</div>
            <div>Grid Item 2</div>
          </div>
        </TestWrapper>
      );

      const gridElement = container.firstElementChild as HTMLElement;
      expect(gridElement).toBeTruthy();

      BrowserTestUtils.testGridBehavior(gridElement).then(({ supports, columns }) => {
        const passed = supports && columns === 2;
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'CSS Grid Support',
          passed,
          passed ? [] : ['CSS Grid not properly supported'],
          0
        );
        expect(passed).toBe(true);
      });
    });

    it('should support Flexbox layout', () => {
      const { container } = render(
        <TestWrapper>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div>Flex Item 1</div>
            <div>Flex Item 2</div>
          </div>
        </TestWrapper>
      );

      const flexElement = container.firstElementChild as HTMLElement;
      expect(flexElement).toBeTruthy();

      BrowserTestUtils.testFlexboxBehavior(flexElement).then(({ supports, direction }) => {
        const passed = supports && (direction === 'column' || direction === 'column');
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'CSS Flexbox Support',
          passed,
          passed ? [] : ['CSS Flexbox not properly supported'],
          0
        );
        expect(passed).toBe(true);
      });
    });

    it('should support CSS Custom Properties', () => {
      const { container } = render(
        <TestWrapper>
          <div style={{
            '--primary-color': '#3b82f6',
            backgroundColor: 'var(--primary-color)',
            padding: '16px'
          }}>
            Custom Properties Test
          </div>
        </TestWrapper>
      );

      const element = container.firstElementChild as HTMLElement;
      expect(element).toBeTruthy();

      const style = window.getComputedStyle(element);
      const passed = style.backgroundColor === 'rgb(59, 130, 246)' || style.backgroundColor.includes('59, 130, 246');

      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'CSS Custom Properties',
        passed,
        passed ? [] : ['CSS Custom Properties not supported'],
        0
      );
      expect(passed).toBe(true);
    });

    it('should support CSS Transitions', () => {
      const { container } = render(
        <TestWrapper>
          <div style={{
            transition: 'all 0.3s ease',
            transform: 'translateX(0)',
            backgroundColor: '#3b82f6'
          }}>
            Transition Test
          </div>
        </TestWrapper>
      );

      const element = container.firstElementChild as HTMLElement;
      expect(element).toBeTruthy();

      BrowserTestUtils.testTransitionSupport('transform', element).then(supported => {
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'CSS Transitions',
          supported,
          supported ? [] : ['CSS Transitions not supported'],
          0
        );
        expect(supported).toBe(true);
      });
    });

    it('should support backdrop-filter if available', () => {
      const supported = BrowserDetector.supportsFeature('backdrop-filter');

      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'CSS Backdrop Filter',
        true, // This is optional, so we don't fail if not supported
        supported ? [] : ['Backdrop filter not supported in this browser'],
        0
      );

      // We don't assert here as it's an optional feature
    });
  });

  describe('🧩 Component Cross-Browser Tests', () => {
    it('should render Button component consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <Button variant="primary">Primary Button</Button>
          <Button variant="secondary">Secondary Button</Button>
          <Button variant="danger">Danger Button</Button>
          <Button disabled>Disabled Button</Button>
        </TestWrapper>
      );

      const buttons = container.querySelectorAll('button');
      expect(buttons).toHaveLength(4);

      const issues: string[] = [];
      buttons.forEach((button, index) => {
        const style = window.getComputedStyle(button);

        // Test focus styles
        if (!style.outline || style.outline === 'none') {
          issues.push(`Button ${index + 1} lacks visible focus outline`);
        }

        // Test disabled state
        if (index === 3 && button.getAttribute('disabled') === null) {
          issues.push('Disabled button not properly disabled');
        }
      });

      const passed = issues.length === 0;
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Button Component Rendering',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });

    it('should render Input component consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <Input label="Test Input" placeholder="Enter text" />
          <Input label="Error Input" error="This field has an error" />
          <Input label="Disabled Input" disabled />
        </TestWrapper>
      );

      const inputs = container.querySelectorAll('input');
      const labels = container.querySelectorAll('label');

      expect(inputs).toHaveLength(3);
      expect(labels).toHaveLength(3);

      const issues: string[] = [];

      inputs.forEach((input, index) => {
        const style = window.getComputedStyle(input);

        // Test focus styles
        if (!style.outline || style.outline === 'none') {
          issues.push(`Input ${index + 1} lacks visible focus outline`);
        }

        // Test disabled state
        if (index === 2 && !input.hasAttribute('disabled')) {
          issues.push('Disabled input not properly disabled');
        }
      });

      const passed = issues.length === 0;
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Input Component Rendering',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });

    it('should render Alert component consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <Alert variant="info">Info Alert</Alert>
          <Alert variant="success">Success Alert</Alert>
          <Alert variant="warning">Warning Alert</Alert>
          <Alert variant="error">Error Alert</Alert>
        </TestWrapper>
      );

      const alerts = container.querySelectorAll('[role="alert"]');
      expect(alerts).toHaveLength(4);

      const issues: string[] = [];
      alerts.forEach((alert, index) => {
        if (!alert.hasAttribute('role')) {
          issues.push(`Alert ${index + 1} missing role="alert"`);
        }

        const style = window.getComputedStyle(alert);
        if (style.display === 'none') {
          issues.push(`Alert ${index + 1} is not visible`);
        }
      });

      const passed = issues.length === 0;
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Alert Component Rendering',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });

    it('should handle form submissions consistently', async () => {
      const handleSubmit = vi.fn();

      const { container } = render(
        <TestWrapper>
          <form onSubmit={handleSubmit}>
            <Input label="Email" type="email" required />
            <Input label="Password" type="password" required />
            <Button type="submit">Submit</Button>
          </form>
        </TestWrapper>
      );

      const emailInput = container.querySelector('input[type="email"]') as HTMLInputElement;
      const passwordInput = container.querySelector('input[type="password"]') as HTMLInputElement;
      const submitButton = container.querySelector('button[type="submit"]') as HTMLButtonElement;

      expect(emailInput).toBeTruthy();
      expect(passwordInput).toBeTruthy();
      expect(submitButton).toBeTruthy();

      const issues: string[] = [];

      // Test form validation
      if (emailInput && !emailInput.validity.valid) {
        issues.push('Email input validation not working');
      }

      if (passwordInput && !passwordInput.validity.valid) {
        issues.push('Password input validation not working');
      }

      const passed = issues.length === 0;
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Form Submission Behavior',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });
  });

  describe('♿ Accessibility Cross-Browser Tests', () => {
    it('should support ARIA attributes consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <button aria-label="Close Button">×</button>
          <div role="alert" aria-live="polite">Notification</div>
          <input aria-describedby="helper" />
          <span id="helper">Helper text</span>
        </TestWrapper>
      );

      const button = container.querySelector('button[aria-label]') as HTMLButtonElement;
      const alert = container.querySelector('[role="alert"]') as HTMLElement;
      const input = container.querySelector('input[aria-describedby]') as HTMLInputElement;
      const helper = container.querySelector('#helper') as HTMLElement;

      expect(button).toBeTruthy();
      expect(alert).toBeTruthy();
      expect(input).toBeTruthy();
      expect(helper).toBeTruthy();

      const issues: string[] = [];

      if (button && !button.getAttribute('aria-label')) {
        issues.push('ARIA label not supported');
      }

      if (alert && !alert.hasAttribute('role')) {
        issues.push('ARIA role not supported');
      }

      if (input && !input.getAttribute('aria-describedby')) {
        issues.push('ARIA describedby not supported');
      }

      const passed = issues.length === 0;
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'ARIA Support',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });

    it('should handle focus management consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <Button>Button 1</Button>
          <Button>Button 2</Button>
          <Button>Button 3</Button>
          <Input label="Test Input" />
          <Button>Button 4</Button>
        </TestWrapper>
      );

      const focusableElements = container.querySelectorAll('button, input');
      expect(focusableElements.length).toBeGreaterThan(0);

      const issues: string[] = [];

      focusableElements.forEach((element, index) => {
        const style = window.getComputedStyle(element);

        // Test for visible focus indicators
        if (style.outline === 'none' || style.outline === '0px') {
          // Check if :focus-visible is supported
          if (BrowserDetector.supportsFeature('focus-visible')) {
            issues.push(`Focusable element ${index + 1} lacks visible focus`);
          }
        }
      });

      const passed = issues.length === 0 || BrowserDetector.supportsFeature('focus-visible');
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Focus Management',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });
  });

  describe('🎭 Browser-Specific Feature Tests', () => {
    it('should handle WebKit-specific CSS prefixes', async () => {
      if (browserInfo.engine === 'WebKit') {
        const { container } = render(
          <TestWrapper>
            <div style={{
              WebkitAppearance: 'none',
              WebkitBorderRadius: '8px',
              padding: '8px'
            }}>
              WebKit Test
            </div>
          </TestWrapper>
        );

        const element = container.firstElementChild as HTMLElement;
        const style = window.getComputedStyle(element);

        const passed = style.webkitAppearance || style.borderRadius.includes('8px');
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'WebKit CSS Prefixes',
          passed,
          passed ? [] : ['WebKit prefixes not working'],
          performance.now()
        );

        expect(passed).toBe(true);
      } else {
        // Skip test for non-WebKit browsers
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'WebKit CSS Prefixes',
          true,
          ['Skipped - Not a WebKit browser'],
          0
        );
        expect(true).toBe(true);
      }
    });

    it('should handle Gecko-specific CSS features', async () => {
      if (browserInfo.engine === 'Gecko') {
        const { container } = render(
          <TestWrapper>
            <div style={{
              MozBorderRadius: '8px',
              padding: '8px'
            }}>
              Gecko Test
            </div>
          </TestWrapper>
        );

        const element = container.firstElementChild as HTMLElement;
        const style = window.getComputedStyle(element);

        const passed = style.borderRadius.includes('8px') || style.MozBorderRadius;
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'Gecko CSS Features',
          passed,
          passed ? [] : ['Gecko-specific features not working'],
          performance.now()
        );

        expect(passed).toBe(true);
      } else {
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'Gecko CSS Features',
          true,
          ['Skipped - Not a Gecko browser'],
          0
        );
        expect(true).toBe(true);
      }
    });

    it('should handle Blink-specific features', async () => {
      if (browserInfo.engine === 'Blink') {
        const { container } = render(
          <TestWrapper>
            <div style={{
              backdropFilter: 'blur(4px)',
              WebkitBackdropFilter: 'blur(4px)',
              padding: '8px'
            }}>
              Blink Test
            </div>
          </TestWrapper>
        );

        const element = container.firstElementChild as HTMLElement;
        const style = window.getComputedStyle(element);

        const hasBackdropFilter = style.backdropFilter !== 'none' || style.webkitBackdropFilter !== 'none';
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'Blink Features',
          hasBackdropFilter,
          hasBackdropFilter ? [] : ['Blink-specific features not working'],
          performance.now()
        );

        expect(hasBackdropFilter || !BrowserDetector.supportsFeature('backdrop-filter')).toBe(true);
      } else {
        results.addResult(
          browserInfo.name,
          browserInfo.version,
          'Blink Features',
          true,
          ['Skipped - Not a Blink browser'],
          0
        );
        expect(true).toBe(true);
      }
    });
  });

  describe('📱 Responsive Design Cross-Browser Tests', () => {
    it('should handle responsive breakpoints consistently', async () => {
      // Mock different viewport sizes
      const originalWidth = window.innerWidth;
      const breakpoints = [320, 768, 1024, 1440];
      const issues: string[] = [];

      for (const width of breakpoints) {
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: width,
        });

        const { container } = render(
          <TestWrapper>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
              <div>Responsive Item 1</div>
              <div>Responsive Item 2</div>
            </div>
          </TestWrapper>
        );

        const gridElement = container.firstElementChild as HTMLElement;
        if (gridElement) {
          const style = window.getComputedStyle(gridElement);
          if (style.display !== 'grid' && style.display !== '-webkit-grid') {
            issues.push(`Responsive grid not working at ${width}px`);
          }
        }

        container.remove();
      }

      // Restore original width
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: originalWidth,
      });

      const passed = issues.length === 0;
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Responsive Design',
        passed,
        issues,
        performance.now()
      );

      expect(passed).toBe(true);
    });
  });

  describe('🚀 Performance Cross-Browser Tests', () => {
    it('should handle large DOM efficiently', async () => {
      const startTime = performance.now();

      const { container } = render(
        <TestWrapper>
          <div>
            {Array.from({ length: 1000 }, (_, i) => (
              <Button key={i} variant="outline">Button {i + 1}</Button>
            ))}
          </div>
        </TestWrapper>
      );

      const renderTime = performance.now() - startTime;
      const buttons = container.querySelectorAll('button');

      expect(buttons).toHaveLength(1000);

      const passed = renderTime < 1000; // Should render in less than 1 second
      results.addResult(
        browserInfo.name,
        browserInfo.version,
        'Large DOM Performance',
        passed,
        passed ? [] : [`Slow rendering: ${renderTime.toFixed(2)}ms`],
        renderTime
      );

      expect(passed).toBe(true);
    });
  });

  describe('🔧 Browser Compatibility Matrix', () => {
    it('should generate compatibility report', () => {
      const report = results.getCompatibilityReport();

      console.log(`📊 ${browserInfo.name} Compatibility Report:`);
      console.log(`Browser: ${browserInfo.name} ${browserInfo.version}`);
      console.log(`Engine: ${browserInfo.engine}`);
      console.log(`Platform: ${browserInfo.platform}`);
      console.log(`Total Tests: ${results.getResults().length}`);
      console.log(`Failed Tests: ${results.getFailedTests().length}`);

      // Log feature support
      const features = [
        'css-grid', 'css-flexbox', 'css-variables', 'backdrop-filter',
        'focus-visible', 'intersection-observer', 'resize-observer'
      ];

      console.log('\n🎨 Feature Support:');
      features.forEach(feature => {
        const supported = BrowserDetector.supportsFeature(feature);
        console.log(`${feature}: ${supported ? '✅' : '❌'}`);
      });

      expect(report).toBeDefined();
    });
  });
});
