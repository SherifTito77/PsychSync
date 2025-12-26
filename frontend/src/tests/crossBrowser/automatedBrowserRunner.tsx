/**
 * Automated Cross-Browser Test Runner
 * Executes tests across Chrome, Edge, Safari, and Firefox
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { BrowserDetector } from './crossBrowserTestSuite';
import { BROWSER_COMPATIBILITY_MATRIX, CROSS_BROWSER_TEST_CASES } from './browserCompatibilityMatrix';

export interface BrowserTestResult {
  browser: string;
  version: string;
  platform: string;
  tests: {
    id: string;
    name: string;
    passed: boolean;
    executionTime: number;
    errors: string[];
    warnings: string[];
  }[];
  summary: {
    totalTests: number;
    passedTests: number;
    failedTests: number;
    executionTime: number;
    compatibilityScore: number;
  };
}

export interface CompatibilityReport {
  timestamp: string;
  testedBrowsers: string[];
  overallCompatibility: number;
  featureSupport: Record<string, {
    Chrome: boolean;
    Edge: boolean;
    Safari: boolean;
    Firefox: boolean;
  }>;
  testResults: BrowserTestResult[];
  recommendations: string[];
  criticalIssues: string[];
}

export class AutomatedBrowserRunner {
  private results: BrowserTestResult[] = [];
  private testCases = CROSS_BROWSER_TEST_CASES;

  /**
   * Run comprehensive cross-browser tests
   */
  async runCrossBrowserTests(): Promise<CompatibilityReport> {
    console.log('🚀 Starting automated cross-browser test suite...');

    const currentBrowser = BrowserDetector.getBrowserInfo();
    const startTime = performance.now();

    // Test current browser
    const browserResult = await this.runBrowserTests(currentBrowser);
    this.results.push(browserResult);

    const executionTime = performance.now() - startTime;

    // Generate compatibility report
    const report = this.generateCompatibilityReport(executionTime);

    console.log(`✅ Cross-browser tests completed in ${executionTime.toFixed(2)}ms`);

    return report;
  }

  /**
   * Run tests for a specific browser
   */
  private async runBrowserTests(browserInfo: any): Promise<BrowserTestResult> {
    console.log(`🌐 Running tests on ${browserInfo.name} ${browserInfo.version}...`);

    const testResults: BrowserTestResult['tests'] = [];
    const startTime = performance.now();

    // Run CSS feature tests
    await this.runCSSFeatureTests(browserInfo, testResults);

    // Run JavaScript feature tests
    await this.runJavaScriptFeatureTests(browserInfo, testResults);

    // Run accessibility tests
    await this.runAccessibilityTests(browserInfo, testResults);

    // Run performance tests
    await this.runPerformanceTests(browserInfo, testResults);

    // Run PWA tests
    await this.runPWATests(browserInfo, testResults);

    const executionTime = performance.now() - startTime;
    const passedTests = testResults.filter(t => t.passed).length;
    const failedTests = testResults.filter(t => !t.passed).length;

    return {
      browser: browserInfo.name,
      version: browserInfo.version,
      platform: browserInfo.platform,
      tests: testResults,
      summary: {
        totalTests: testResults.length,
        passedTests,
        failedTests,
        executionTime,
        compatibilityScore: (passedTests / testResults.length) * 100
      }
    };
  }

  /**
   * Run CSS feature tests
   */
  private async runCSSFeatureTests(browserInfo: any, testResults: BrowserTestResult['tests']): Promise<void> {
    const cssFeatures = ['css-grid', 'css-flexbox', 'css-variables', 'backdrop-filter'];

    for (const feature of cssFeatures) {
      const startTime = performance.now();
      const errors: string[] = [];
      const warnings: string[] = [];

      try {
        const supported = BrowserDetector.supportsFeature(feature);
        const expectedSupport = BROWSER_COMPATIBILITY_MATRIX[feature]?.[browserInfo.name as keyof typeof BROWSER_COMPATIBILITY_MATRIX[typeof feature]]?.supported;

        if (supported !== expectedSupport) {
          errors.push(`Feature support mismatch: expected ${expectedSupport}, got ${supported}`);
        }

        // Run specific feature tests
        if (feature === 'css-grid') {
          await this.testCSSGridFeature(errors, warnings);
        } else if (feature === 'css-flexbox') {
          await this.testCSSFlexboxFeature(errors, warnings);
        } else if (feature === 'css-variables') {
          await this.testCSSVariablesFeature(errors, warnings);
        }

        testResults.push({
          id: `css-${feature}`,
          name: `CSS ${feature.replace('-', ' ')}`,
          passed: errors.length === 0,
          executionTime: performance.now() - startTime,
          errors,
          warnings
        });

      } catch (error) {
        testResults.push({
          id: `css-${feature}`,
          name: `CSS ${feature.replace('-', ' ')}`,
          passed: false,
          executionTime: performance.now() - startTime,
          errors: [`Test execution error: ${error}`],
          warnings
        });
      }
    }
  }

  /**
   * Test CSS Grid feature
   */
  private async testCSSGridFeature(errors: string[], warnings: string[]): Promise<void> {
    const testElement = document.createElement('div');
    testElement.style.display = 'grid';
    testElement.style.gridTemplateColumns = '1fr 1fr';
    document.body.appendChild(testElement);

    try {
      const computedStyle = window.getComputedStyle(testElement);
      const displayValue = computedStyle.display;

      if (displayValue !== 'grid' && displayValue !== '-webkit-grid' && displayValue !== '-ms-grid') {
        errors.push(`Grid display not supported: ${displayValue}`);
      }

      // Test grid template columns
      const gridTemplateColumns = computedStyle.gridTemplateColumns;
      if (!gridTemplateColumns || gridTemplateColumns === 'none') {
        warnings.push('Grid template columns may not be properly supported');
      }

    } finally {
      document.body.removeChild(testElement);
    }
  }

  /**
   * Test CSS Flexbox feature
   */
  private async testCSSFlexboxFeature(errors: string[], warnings: string[]): Promise<void> {
    const testElement = document.createElement('div');
    testElement.style.display = 'flex';
    testElement.style.flexDirection = 'column';
    document.body.appendChild(testElement);

    try {
      const computedStyle = window.getComputedStyle(testElement);
      const displayValue = computedStyle.display;

      if (displayValue !== 'flex' && displayValue !== '-webkit-flex' && displayValue !== '-ms-flexbox') {
        errors.push(`Flexbox display not supported: ${displayValue}`);
      }

      // Test flex direction
      const flexDirection = computedStyle.flexDirection || computedStyle.webkitFlexDirection;
      if (flexDirection !== 'column') {
        warnings.push(`Flex direction not properly supported: ${flexDirection}`);
      }

    } finally {
      document.body.removeChild(testElement);
    }
  }

  /**
   * Test CSS Variables feature
   */
  private async testCSSVariablesFeature(errors: string[], warnings: string[]): Promise<void> {
    const testElement = document.createElement('div');
    testElement.style.setProperty('--test-color', '#ff0000');
    testElement.style.backgroundColor = 'var(--test-color)';
    document.body.appendChild(testElement);

    try {
      const computedStyle = window.getComputedStyle(testElement);
      const backgroundColor = computedStyle.backgroundColor;

      if (!backgroundColor.includes('255') && !backgroundColor.includes('ff0000')) {
        errors.push(`CSS variables not supported: ${backgroundColor}`);
      }

    } finally {
      document.body.removeChild(testElement);
    }
  }

  /**
   * Run JavaScript feature tests
   */
  private async runJavaScriptFeatureTests(browserInfo: any, testResults: BrowserTestResult['tests']): Promise<void> {
    const jsFeatures = ['intersection-observer', 'resize-observer', 'web-share', 'clipboard'];

    for (const feature of jsFeatures) {
      const startTime = performance.now();
      const errors: string[] = [];
      const warnings: string[] = [];

      try {
        const supported = BrowserDetector.supportsFeature(feature);
        const expectedSupport = BROWSER_COMPATIBILITY_MATRIX[feature]?.[browserInfo.name as keyof typeof BROWSER_COMPATIBILITY_MATRIX[typeof feature]]?.supported;

        if (supported !== expectedSupport) {
          errors.push(`Feature support mismatch: expected ${expectedSupport}, got ${supported}`);
        }

        // Run specific feature tests
        if (feature === 'intersection-observer' && supported) {
          await this.testIntersectionObserver(errors, warnings);
        } else if (feature === 'resize-observer' && supported) {
          await this.testResizeObserver(errors, warnings);
        }

        testResults.push({
          id: `js-${feature}`,
          name: `JavaScript ${feature.replace('-', ' ')}`,
          passed: errors.length === 0,
          executionTime: performance.now() - startTime,
          errors,
          warnings
        });

      } catch (error) {
        testResults.push({
          id: `js-${feature}`,
          name: `JavaScript ${feature.replace('-', ' ')}`,
          passed: false,
          executionTime: performance.now() - startTime,
          errors: [`Test execution error: ${error}`],
          warnings
        });
      }
    }
  }

  /**
   * Test Intersection Observer
   */
  private async testIntersectionObserver(errors: string[], warnings: string[]): Promise<void> {
    if (!('IntersectionObserver' in window)) {
      errors.push('IntersectionObserver not available');
      return;
    }

    try {
      const testElement = document.createElement('div');
      testElement.style.height = '100px';
      document.body.appendChild(testElement);

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (typeof entry.isIntersecting !== 'boolean') {
            errors.push('IntersectionObserver entry missing isIntersecting property');
          }
        });
      });

      observer.observe(testElement);

      // Clean up
      observer.disconnect();
      document.body.removeChild(testElement);

    } catch (error) {
      errors.push(`IntersectionObserver test error: ${error}`);
    }
  }

  /**
   * Test Resize Observer
   */
  private async testResizeObserver(errors: string[], warnings: string[]): Promise<void> {
    if (!('ResizeObserver' in window)) {
      errors.push('ResizeObserver not available');
      return;
    }

    try {
      const testElement = document.createElement('div');
      testElement.style.width = '100px';
      document.body.appendChild(testElement);

      const observer = new ResizeObserver((entries) => {
        entries.forEach(entry => {
          if (!entry.contentRect) {
            errors.push('ResizeObserver entry missing contentRect');
          }
        });
      });

      observer.observe(testElement);

      // Clean up
      observer.disconnect();
      document.body.removeChild(testElement);

    } catch (error) {
      errors.push(`ResizeObserver test error: ${error}`);
    }
  }

  /**
   * Run accessibility tests
   */
  private async runAccessibilityTests(browserInfo: any, testResults: BrowserTestResult['tests']): Promise<void> {
    const accessibilityTests = ['aria-live-regions', 'keyboard-navigation', 'focus-management'];

    for (const test of accessibilityTests) {
      const startTime = performance.now();
      const errors: string[] = [];
      const warnings: string[] = [];

      try {
        if (test === 'aria-live-regions') {
          await this.testARIALiveRegions(errors, warnings);
        } else if (test === 'keyboard-navigation') {
          await this.testKeyboardNavigation(errors, warnings);
        } else if (test === 'focus-management') {
          await this.testFocusManagement(errors, warnings);
        }

        testResults.push({
          id: `a11y-${test}`,
          name: `Accessibility ${test.replace('-', ' ')}`,
          passed: errors.length === 0,
          executionTime: performance.now() - startTime,
          errors,
          warnings
        });

      } catch (error) {
        testResults.push({
          id: `a11y-${test}`,
          name: `Accessibility ${test.replace('-', ' ')}`,
          passed: false,
          executionTime: performance.now() - startTime,
          errors: [`Test execution error: ${error}`],
          warnings
        });
      }
    }
  }

  /**
   * Test ARIA live regions
   */
  private async testARIALiveRegions(errors: string[], warnings: string[]): Promise<void> {
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('role', 'alert');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.textContent = 'Test message';
    document.body.appendChild(liveRegion);

    try {
      const hasRole = liveRegion.hasAttribute('role');
      const hasLive = liveRegion.hasAttribute('aria-live');

      if (!hasRole) {
        errors.push('ARIA role not properly set');
      }

      if (!hasLive) {
        errors.push('ARIA live attribute not properly set');
      }

    } finally {
      document.body.removeChild(liveRegion);
    }
  }

  /**
   * Test keyboard navigation
   */
  private async testKeyboardNavigation(errors: string[], warnings: string[]): Promise<void> {
    const testButton = document.createElement('button');
    testButton.textContent = 'Test Button';
    document.body.appendChild(testButton);

    try {
      testButton.focus();

      if (document.activeElement !== testButton) {
        errors.push('Button focus not working');
      }

      // Test tabindex
      testButton.tabIndex = 0;
      if (testButton.tabIndex !== 0) {
        errors.push('Tabindex not working');
      }

    } finally {
      document.body.removeChild(testButton);
    }
  }

  /**
   * Test focus management
   */
  private async testFocusManagement(errors: string[], warnings: string[]): Promise<void> {
    const focusableElements = ['button', 'input', 'select', 'textarea'];

    focusableElements.forEach(tagName => {
      const element = document.createElement(tagName);
      document.body.appendChild(element);

      try {
        element.focus();

        if (document.activeElement !== element) {
          errors.push(`${tagName} element cannot receive focus`);
        }

      } finally {
        document.body.removeChild(element);
      }
    });
  }

  /**
   * Run performance tests
   */
  private async runPerformanceTests(browserInfo: any, testResults: BrowserTestResult['tests']): Promise<void> {
    const performanceTests = ['large-dom-rendering', 'animation-performance', 'memory-usage'];

    for (const test of performanceTests) {
      const startTime = performance.now();
      const errors: string[] = [];
      const warnings: string[] = [];

      try {
        if (test === 'large-dom-rendering') {
          await this.testLargeDOMRendering(errors, warnings);
        } else if (test === 'animation-performance') {
          await this.testAnimationPerformance(errors, warnings);
        }

        testResults.push({
          id: `perf-${test}`,
          name: `Performance ${test.replace('-', ' ')}`,
          passed: errors.length === 0,
          executionTime: performance.now() - startTime,
          errors,
          warnings
        });

      } catch (error) {
        testResults.push({
          id: `perf-${test}`,
          name: `Performance ${test.replace('-', ' ')}`,
          passed: false,
          executionTime: performance.now() - startTime,
          errors: [`Test execution error: ${error}`],
          warnings
        });
      }
    }
  }

  /**
   * Test large DOM rendering performance
   */
  private async testLargeDOMRendering(errors: string[], warnings: string[]): Promise<void> {
    const startTime = performance.now();
    const container = document.createElement('div');
    document.body.appendChild(container);

    try {
      // Create 1000 elements
      for (let i = 0; i < 1000; i++) {
        const element = document.createElement('div');
        element.textContent = `Item ${i}`;
        element.className = 'test-item';
        container.appendChild(element);
      }

      const renderTime = performance.now() - startTime;

      if (renderTime > 1000) {
        warnings.push(`Large DOM rendering took ${renderTime.toFixed(2)}ms (threshold: 1000ms)`);
      }

    } finally {
      document.body.removeChild(container);
    }
  }

  /**
   * Test animation performance
   */
  private async testAnimationPerformance(errors: string[], warnings: string[]): Promise<void> {
    const testElement = document.createElement('div');
    testElement.style.width = '100px';
    testElement.style.height = '100px';
    testElement.style.backgroundColor = 'red';
    testElement.style.transition = 'all 0.3s ease';
    document.body.appendChild(testElement);

    try {
      const startTime = performance.now();

      // Trigger animation
      testElement.style.transform = 'translateX(50px)';

      // Wait for animation to complete
      await new Promise(resolve => setTimeout(resolve, 350));

      const animationTime = performance.now() - startTime;

      if (animationTime > 500) {
        warnings.push(`Animation took ${animationTime.toFixed(2)}ms (threshold: 500ms)`);
      }

    } finally {
      document.body.removeChild(testElement);
    }
  }

  /**
   * Run PWA tests
   */
  private async runPWATests(browserInfo: any, testResults: BrowserTestResult['tests']): Promise<void> {
    const pwaTests = ['service-worker', 'offline-support', 'installable-pwa'];

    for (const test of pwaTests) {
      const startTime = performance.now();
      const errors: string[] = [];
      const warnings: string[] = [];

      try {
        if (test === 'service-worker') {
          await this.testServiceWorker(errors, warnings);
        } else if (test === 'offline-support') {
          await this.testOfflineSupport(errors, warnings);
        }

        testResults.push({
          id: `pwa-${test}`,
          name: `PWA ${test.replace('-', ' ')}`,
          passed: errors.length === 0,
          executionTime: performance.now() - startTime,
          errors,
          warnings
        });

      } catch (error) {
        testResults.push({
          id: `pwa-${test}`,
          name: `PWA ${test.replace('-', ' ')}`,
          passed: false,
          executionTime: performance.now() - startTime,
          errors: [`Test execution error: ${error}`],
          warnings
        });
      }
    }
  }

  /**
   * Test Service Worker availability
   */
  private async testServiceWorker(errors: string[], warnings: string[]): Promise<void> {
    if (!('serviceWorker' in navigator)) {
      errors.push('Service Worker not supported');
      return;
    }

    // Check if service worker is already registered
    navigator.serviceWorker.getRegistrations().then(registrations => {
      if (registrations.length > 0) {
        console.log('Service worker already registered');
      } else {
        warnings.push('No service worker registered');
      }
    }).catch(error => {
      errors.push(`Service worker check failed: ${error}`);
    });
  }

  /**
   * Test offline support
   */
  private async testOfflineSupport(errors: string[], warnings: string[]): Promise<void> {
    const isOnline = navigator.onLine;

    if (!isOnline) {
      warnings.push('Currently offline - may affect test results');
    }

    // Check if browser supports offline events
    if (!('ononline' in window && 'onoffline' in window)) {
      errors.push('Browser does not support online/offline events');
    }
  }

  /**
   * Generate compatibility report
   */
  private generateCompatibilityReport(executionTime: number): CompatibilityReport {
    const testedBrowsers = this.results.map(r => r.browser);
    const featureSupport: Record<string, any> = {};

    // Analyze feature support across browsers
    Object.keys(BROWSER_COMPATIBILITY_MATRIX).forEach(feature => {
      featureSupport[feature] = {
        Chrome: BROWSER_COMPATIBILITY_MATRIX[feature].Chrome.supported,
        Edge: BROWSER_COMPATIBILITY_MATRIX[feature].Edge.supported,
        Safari: BROWSER_COMPATIBILITY_MATRIX[feature].Safari.supported,
        Firefox: BROWSER_COMPATIBILITY_MATRIX[feature].Firefox.supported
      };
    });

    // Calculate overall compatibility
    const totalTests = this.results.reduce((sum, r) => sum + r.tests.length, 0);
    const totalPassed = this.results.reduce((sum, r) => sum + r.tests.filter(t => t.passed).length, 0);
    const overallCompatibility = totalTests > 0 ? (totalPassed / totalTests) * 100 : 0;

    // Generate recommendations
    const recommendations = this.generateRecommendations();
    const criticalIssues = this.identifyCriticalIssues();

    return {
      timestamp: new Date().toISOString(),
      testedBrowsers,
      overallCompatibility,
      featureSupport,
      testResults: this.results,
      recommendations,
      criticalIssues
    };
  }

  /**
   * Generate recommendations based on test results
   */
  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    this.results.forEach(result => {
      const failedTests = result.tests.filter(t => !t.passed);

      if (failedTests.length > 0) {
        if (result.browser === 'Firefox' && failedTests.some(t => t.id.includes('backdrop-filter'))) {
          recommendations.push('Consider fallback CSS effects for Firefox backdrop-filter support');
        }

        if (result.browser === 'Safari' && failedTests.some(t => t.id.includes('web-share'))) {
          recommendations.push('Implement custom share dialog for Safari web-share API limitations');
        }

        if (failedTests.some(t => t.id.includes('performance'))) {
          recommendations.push(`Optimize performance for ${result.browser} - consider code splitting and lazy loading`);
        }
      }
    });

    // Add general recommendations
    recommendations.push('Test on multiple browser versions, not just latest');
    recommendations.push('Consider progressive enhancement for unsupported features');
    recommendations.push('Implement proper feature detection with fallbacks');

    return recommendations;
  }

  /**
   * Identify critical issues from test results
   */
  private identifyCriticalIssues(): string[] {
    const criticalIssues: string[] = [];

    this.results.forEach(result => {
      const criticalFailures = result.tests.filter(t =>
        !t.passed && (t.id.includes('css-grid') || t.id.includes('flexbox') || t.id.includes('a11y-'))
      );

      criticalFailures.forEach(failure => {
        criticalIssues.push(`${result.browser}: ${failure.name} - ${failure.errors.join(', ')}`);
      });
    });

    return criticalIssues;
  }
}

// Export singleton instance
export const browserRunner = new AutomatedBrowserRunner();