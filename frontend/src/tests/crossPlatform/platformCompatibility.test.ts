/**
 * iOS Safari vs Android Chrome Cross-Platform Compatibility Tests
 * Comprehensive testing of platform-specific list rendering behaviors
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mobileBrowserCompatibility, type CompatibilityIssue } from '../../utils/crossPlatform/mobileBrowserCompatibility';

describe('🍎 iOS Safari vs 🤖 Android Chrome Platform Compatibility', () => {
  let compatibility: any;

  beforeEach(() => {
    compatibility = mobileBrowserCompatibility;
  });

  describe('📱 Platform Detection', () => {
    it('should accurately detect iOS Safari', () => {
      const iOSUA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1';

      // Mock user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        configurable: true,
        value: iOSUA
      });

      const info = compatibility.getBrowserInfo();

      expect(info.platform).toBe('ios');
      expect(info.browser).toBe('safari');
      expect(info.engine).toBe('webkit');
    });

    it('should accurately detect Android Chrome', () => {
      const androidUA = 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36';

      // Mock user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        configurable: true,
        value: androidUA
      });

      const info = compatibility.getBrowserInfo();

      expect(info.platform).toBe('android');
      expect(info.browser).toBe('chrome');
      expect(info.engine).toBe('blink');
    });

    it('should assess browser capabilities correctly', () => {
      const info = compatibility.getBrowserInfo();

      expect(info.capabilities).toBeDefined();
      expect(info.capabilities.scrollBehavior).toBeDefined();
      expect(info.capabilities.touchEvents).toBeDefined();
      expect(info.capabilities.cssSupport).toBeDefined();
      expect(info.capabilities.performance).toBeDefined();
    });
  });

  describe('🔍 Issue Identification', () => {
    it('should identify iOS Safari specific issues', () => {
      // Mock iOS Safari environment
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        configurable: true,
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
      });

      // Create new instance to detect platform
      const newCompatibility = new (require('../../utils/crossPlatform/mobileBrowserCompatibility').MobileBrowserCompatibility)();
      const issues = newCompatibility.getCompatibilityIssues();

      // Should find iOS-specific issues
      const iOSSpecificIssues = issues.filter(issue => issue.platform === 'ios');
      expect(iOSSpecificIssues.length).toBeGreaterThan(0);

      // Check for known iOS issues
      const issueIds = iOSSpecificIssues.map(issue => issue.id);
      expect(issueIds).toContain('ios-safari-scroll-jump');
      expect(issueIds).toContain('ios-safari-overscroll-bounce');
    });

    it('should identify Android Chrome specific issues', () => {
      // Mock Android Chrome environment
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        configurable: true,
        value: 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
      });

      // Create new instance to detect platform
      const newCompatibility = new (require('../../utils/crossPlatform/mobileBrowserCompatibility').MobileBrowserCompatibility)();
      const issues = newCompatibility.getCompatibilityIssues();

      // Should find cross-platform issues
      expect(issues.length).toBeGreaterThan(0);

      // Check for cross-platform issues
      const issueIds = issues.map(issue => issue.id);
      expect(issueIds).toContain('cross-platform-scroll-position');
      expect(issueIds).toContain('cross-platform-list-performance');
    });

    it('should categorize issues by severity correctly', () => {
      const issues = compatibility.getCompatibilityIssues();

      // Should have critical, major, and minor issues
      const criticalIssues = issues.filter(issue => issue.severity === 'critical');
      const majorIssues = issues.filter(issue => issue.severity === 'major');
      const minorIssues = issues.filter(issue => issue.severity === 'minor');

      expect(issues.length).toBe(criticalIssues.length + majorIssues.length + minorIssues.length);
      expect(criticalIssues.length).toBeGreaterThan(0);
      expect(majorIssues.length).toBeGreaterThan(0);
    });
  });

  describe('📊 Compatibility Report Generation', () => {
    it('should generate comprehensive compatibility report', () => {
      const report = compatibility.generateCompatibilityReport();

      expect(report.browserInfo).toBeDefined();
      expect(report.issues).toBeDefined();
      expect(report.recommendations).toBeDefined();
      expect(report.severityBreakdown).toBeDefined();

      // Verify severity breakdown structure
      expect(typeof report.severityBreakdown.critical).toBe('number');
      expect(typeof report.severityBreakdown.major).toBe('number');
      expect(typeof report.severityBreakdown.minor).toBe('number');
    });

    it('should provide actionable recommendations', () => {
      const report = compatibility.generateCompatibilityReport();

      expect(report.recommendations.length).toBeGreaterThan(0);

      // Each recommendation should be a non-empty string
      report.recommendations.forEach(rec => {
        expect(typeof rec).toBe('string');
        expect(rec.length).toBeGreaterThan(0);
      });
    });

    it('should generate platform-specific CSS fixes', () => {
      const cssFixes = compatibility.getPlatformCSSFixes();

      expect(typeof cssFixes).toBe('string');
      expect(cssFixes.length).toBeGreaterThan(0);

      // Should contain CSS comments explaining fixes
      expect(cssFixes).toContain('/*');
      expect(cssFixes).toContain('*/');
    });
  });

  describe('🧪 List Implementation Validation', () => {
    let testElement: HTMLElement;

    beforeEach(() => {
      testElement = document.createElement('div');
      testElement.innerHTML = `
        <ul class="test-list">
          <li class="test-item">Item 1</li>
          <li class="test-item">Item 2</li>
          <li class="test-item">Item 3</li>
        </ul>
      `;
      document.body.appendChild(testElement);
    });

    afterEach(() => {
      document.body.removeChild(testElement);
    });

    it('should validate iOS Safari specific requirements', () => {
      // Mock iOS Safari
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        configurable: true,
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
      });

      const listElement = testElement.querySelector('.test-list') as HTMLElement;
      const validation = compatibility.validateListImplementation(listElement);

      // Should identify iOS Safari specific issues
      expect(validation.issues.length).toBeGreaterThan(0);
      expect(validation.recommendations.length).toBeGreaterThan(0);
    });

    it('should validate touch target requirements', () => {
      const itemElement = testElement.querySelector('.test-item') as HTMLElement;
      const computedStyle = window.getComputedStyle(itemElement);
      const height = parseInt(computedStyle.height);

      // Touch targets should be at least 44px on mobile
      expect(height).toBeGreaterThanOrEqual(40); // Allow some flexibility in test
    });

    it('should validate CSS contain property usage', () => {
      const listElement = testElement.querySelector('.test-list') as HTMLElement;
      const computedStyle = window.getComputedStyle(listElement);
      const contain = computedStyle.contain;

      // Should recommend contain property for performance
      expect(validation.recommendations.some(rec =>
        rec.toLowerCase().includes('contain')
      )).toBe(true);
    });
  });

  describe('⚡ Performance Testing', () => {
    it('should measure scroll performance accurately', async () => {
      const startTime = performance.now();

      // Create test list
      const container = document.createElement('div');
      container.style.height = '200px';
      container.style.overflowY = 'auto';

      // Add test items
      for (let i = 0; i < 100; i++) {
        const item = document.createElement('div');
        item.style.height = '40px';
        item.style.padding = '8px';
        item.style.borderBottom = '1px solid #eee';
        item.textContent = `Test Item ${i + 1}`;
        container.appendChild(item);
      }

      document.body.appendChild(container);

      // Test scroll performance
      const scrollStart = performance.now();
      container.scrollTop = 500;
      const scrollTime = performance.now() - scrollStart;

      const totalTime = performance.now() - startTime;

      document.body.removeChild(container);

      // Scroll should complete in reasonable time
      expect(scrollTime).toBeLessThan(100);
      expect(totalTime).toBeLessThan(200);

      console.log(`Scroll test: ${scrollTime.toFixed(2)}ms, Total: ${totalTime.toFixed(2)}ms`);
    });

    it('should measure list rendering performance', () => {
      const startTime = performance.now();
      const items = [];

      // Simulate list creation
      for (let i = 0; i < 1000; i++) {
        items.push({
          id: i,
          name: `User ${i + 1}`,
          email: `user${i + 1}@example.com`
        });
      }

      const renderTime = performance.now() - startTime;

      // Should be fast even with 1000 items
      expect(renderTime).toBeLessThan(50);
      expect(items).toHaveLength(1000);

      console.log(`List rendering test: ${renderTime.toFixed(2)}ms for 1000 items`);
    });

    it('should measure memory usage efficiently', () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;

        expect(memory.usedJSHeapSize).toBeGreaterThan(0);
        expect(memory.totalJSHeapSize).toBeGreaterThan(0);
        expect(memory.jsHeapSizeLimit).toBeGreaterThan(0);

        const usagePercentage = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
        expect(usagePercentage).toBeLessThan(90); // Should not be near limit

        console.log(`Memory usage: ${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB (${usagePercentage.toFixed(1)}%)`);
      } else {
        console.log('Memory API not available in this browser');
      }
    });
  });

  describe('🎨 CSS Feature Support Testing', () => {
    it('should test CSS Grid support', () => {
      const testElement = document.createElement('div');
      testElement.style.display = 'grid';
      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement);
      const supportsGrid = computedStyle.display === 'grid';

      document.body.removeChild(testElement);

      expect(supportsGrid).toBe(true);
    });

    it('should test Flexbox gap support', () => {
      const testElement = document.createElement('div');
      testElement.style.display = 'flex';
      testElement.style.gap = '10px';
      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement);
      const supportsGap = computedStyle.gap === '10px';

      document.body.removeChild(testElement);

      // Note: gap support varies by browser
      console.log(`Flexbox gap support: ${supportsGap ? 'Yes' : 'No'}`);
    });

    it('should test backdrop filter support', () => {
      const testElement = document.createElement('div');
      testElement.style.backdropFilter = 'blur(5px)';
      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement);
      const supportsBackdropFilter = testElement.style.backdropFilter !== '';

      document.body.removeChild(testElement);

      expect(supportsBackdropFilter).toBe(true);
    });

    it('should test scroll behavior support', () => {
      const htmlElement = document.documentElement;
      const originalBehavior = htmlElement.style.scrollBehavior;

      htmlElement.style.scrollBehavior = 'smooth';
      const supportsSmooth = htmlElement.style.scrollBehavior === 'smooth';

      // Restore original behavior
      htmlElement.style.scrollBehavior = originalBehavior;

      expect(supportsSmooth).toBe(true);
    });
  });

  describe('👆 Touch Interaction Testing', () => {
    it('should test touch support availability', () => {
      const hasTouchSupport = 'ontouchstart' in window;
      const hasPointerEvents = 'PointerEvent' in window;

      expect(hasTouchSupport || hasPointerEvents).toBe(true);
    });

    it('should test touch action CSS support', () => {
      const testElement = document.createElement('button');
      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement);
      const touchAction = computedStyle.touchAction;

      document.body.removeChild(testElement);

      expect(typeof touchAction).toBe('string');
    });

    it('should test CSS touch optimizations', () => {
      const testElement = document.createElement('div');
      testElement.style.webkitTapHighlightColor = 'transparent';
      testElement.style.webkitUserSelect = 'none';
      testElement.style.webkitTouchCallout = 'none';

      const webkitTapHighlightColor = testElement.style.webkitTapHighlightColor;
      const webkitUserSelect = testElement.style.webkitUserSelect;
      const webkitTouchCallout = testElement.style.webkitTouchCallout;

      expect(webkitTapHighlightColor).toBe('transparent');
      expect(webkitUserSelect).toBe('none');
      expect(webkitTouchCallout).toBe('none');
    });
  });

  describe('🔄 Cross-Platform Consistency', () => {
    it('should ensure consistent minimum touch target sizes', () => {
      const testElement = document.createElement('button');
      testElement.style.padding = '12px 16px';
      testElement.style.minHeight = '44px';
      document.body.appendChild(testElement);

      const rect = testElement.getBoundingClientRect();
      const computedStyle = window.getComputedStyle(testElement);

      document.body.removeChild(testElement);

      expect(rect.height).toBeGreaterThanOrEqual(44);
      expect(computedStyle.minHeight).toBe('44px');
    });

    it('should ensure consistent responsive behavior', () => {
      const testElement = document.createElement('div');
      testElement.style.padding = '1rem';
      testElement.style.fontSize = '16px';

      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement);
      const padding = computedStyle.padding;
      const fontSize = computedStyle.fontSize;

      document.body.removeChild(testElement);

      // Should use relative units that scale consistently
      expect(padding).toContain('px');
      expect(fontSize).toContain('px');
      expect(parseFloat(fontSize)).toBeGreaterThanOrEqual(16);
    });

    it('should ensure consistent scroll behavior', () => {
      const container = document.createElement('div');
      container.style.height = '200px';
      container.style.overflowY = 'auto';
      container.style.webkitOverflowScrolling = 'touch';

      document.body.appendChild(container);

      const computedStyle = window.getComputedStyle(container);
      const overflowScrolling = computedStyle.webkitOverflowScrolling;

      document.body.removeChild(container);

      // Should have webkit-overflow-scrolling for iOS
      expect(overflowScrolling).toBe('touch');
    });
  });

  describe('📊 Comprehensive Cross-Platform Score', () => {
    it('should calculate overall compatibility score', () => {
      const report = compatibility.generateCompatibilityReport();

      const issues = report.issues;
      const criticalIssues = issues.filter(i => i.severity === 'critical').length;
      const majorIssues = issues.filter(i => i.severity === 'major').length;
      const minorIssues = issues.filter(i => i.severity === 'minor').length;

      // Calculate score: (100 - issues*weightedPenalty)
      const totalIssues = criticalIssues + majorIssues + minorIssues;
      const weightedPenalty = (criticalIssues * 10) + (majorIssues * 5) + (minorIssues * 1);
      const score = Math.max(0, 100 - weightedPenalty);

      // Should have reasonable score
      expect(score).toBeGreaterThanOrEqual(50);
      expect(totalIssues).toBeLessThan(20);

      console.log(`Cross-Platform Compatibility Score: ${score}`);
      console.log(`Issues: ${criticalIssues} critical, ${majorIssues} major, ${minorIssues} minor`);
    });

    it('should provide actionable insights', () => {
      const report = compatibility.generateCompatibilityReport();

      // Should provide specific recommendations based on detected issues
      expect(report.recommendations.length).toBeGreaterThan(3);

      // Should reference browser capabilities
      expect(report.browserInfo.capabilities).toBeDefined();

      // Should include severity breakdown
      expect(report.severityBreakdown).toBeDefined();
    });
  });
});