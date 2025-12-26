/**
 * Comprehensive Accessibility Testing Framework
 * Tests for ARIA properties, color contrast, keyboard navigation, and WCAG compliance
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axe from 'axe-core';
import type { AxeResults, Result } from 'axe-core';

export interface AccessibilityIssue {
  type: 'aria' | 'contrast' | 'keyboard' | 'wcag' | 'semantic' | 'focus';
  severity: 'critical' | 'high' | 'medium' | 'low';
  element: string;
  description: string;
  wcagGuideline?: string;
  recommendation: string;
  automated?: boolean;
}

export interface AccessibilityReport {
  component: string;
  timestamp: string;
  totalIssues: number;
  issuesByType: Record<string, number>;
  issuesBySeverity: Record<string, number>;
  issues: AccessibilityIssue[];
  axeResults?: AxeResults;
  score: number; // 0-100 accessibility score
}

export class AccessibilityTester {
  private contrastCache = new Map<string, number>();

  /**
   * Run axe-core accessibility testing
   */
  private async runAxe(container: HTMLElement): Promise<AxeResults> {
    return new Promise((resolve) => {
      axe.run(container, {
        reporter: 'v2',
        rules: {
          // Enable all rules by default
          'color-contrast': { enabled: true },
          'keyboard-navigation': { enabled: true },
          'aria-labels': { enabled: true },
          'focus-order-semantics': { enabled: true },
          'html-has-lang': { enabled: true },
          'landmark-one-main': { enabled: true },
          'page-has-heading-one': { enabled: true },
          'region': { enabled: true },
        },
        resultTypes: ['violations', 'passes', 'incomplete', 'inapplicable']
      }, (results) => {
        resolve(results);
      });
    });
  }

  /**
   * Perform comprehensive accessibility test on a component
   */
  async testComponent(
    componentName: string,
    Component: React.ReactElement,
    additionalInteractions?: () => void
  ): Promise<AccessibilityReport> {
    const issues: AccessibilityIssue[] = [];

    // Render component
    const { container } = render(Component);

    // 1. Run axe-core for automated accessibility testing
    const axeResults = await this.runAxe(container);

    // 2. Test ARIA properties and semantic HTML
    issues.push(...this.testARIAProperties(container));

    // 3. Test color contrast
    issues.push(...this.testColorContrast(container));

    // 4. Test keyboard navigation
    issues.push(...this.testKeyboardNavigation(container, additionalInteractions));

    // 5. Test focus management
    issues.push(...this.testFocusManagement(container));

    // 6. Test semantic structure
    issues.push(...this.testSemanticStructure(container));

    // Convert axe violations to our format
    const axeIssues = this.convertAxeViolations(axeResults);
    issues.push(...axeIssues);

    // Calculate metrics
    const report = this.generateReport(componentName, issues, axeResults);

    return report;
  }

  /**
   * Test ARIA properties and roles
   */
  private testARIAProperties(container: HTMLElement): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];

    // Check for missing ARIA labels on interactive elements
    const interactiveElements = container.querySelectorAll(
      'button, [role="button"], a, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    interactiveElements.forEach((element, index) => {
      const tagName = element.tagName.toLowerCase();
      const hasAriaLabel = element.hasAttribute('aria-label') ||
                          element.hasAttribute('aria-labelledby') ||
                          element.getAttribute('aria-describedby');

      // Check for accessible naming
      if (!this.getAccessibleName(element)) {
        issues.push({
          type: 'aria',
          severity: 'high',
          element: `${tagName}[${index}]`,
          description: 'Interactive element lacks accessible name',
          wcagGuideline: 'WCAG 2.1 1.3.1, 2.4.6',
          recommendation: 'Add aria-label, aria-labelledby, or visible text content',
          automated: true
        });
      }

      // Check for proper button roles
      if (tagName === 'button' && element.getAttribute('role') &&
          element.getAttribute('role') !== 'button') {
        issues.push({
          type: 'aria',
          severity: 'medium',
          element: `${tagName}[${index}]`,
          description: 'Button element has conflicting role attribute',
          wcagGuideline: 'WCAG 2.1 1.3.1',
          recommendation: 'Remove role attribute from native button elements',
          automated: true
        });
      }

      // Check for invalid ARIA attributes
      this.checkInvalidAriaAttributes(element, index, issues);
    });

    // Check for proper heading structure
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let lastLevel = 0;

    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.substring(1));

      if (level > lastLevel + 1) {
        issues.push({
          type: 'semantic',
          severity: 'medium',
          element: `h${level}[${index}]`,
          description: `Heading level skipped (from h${lastLevel} to h${level})`,
          wcagGuideline: 'WCAG 2.1 1.3.1',
          recommendation: 'Use proper heading hierarchy without skipping levels',
          automated: true
        });
      }
      lastLevel = level;
    });

    return issues;
  }

  /**
   * Test color contrast ratios
   */
  private testColorContrast(container: HTMLElement): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];
    const textElements = container.querySelectorAll(
      'p, h1, h2, h3, h4, h5, h6, span, a, label, button, input, select, textarea'
    );

    textElements.forEach((element, index) => {
      const styles = window.getComputedStyle(element);
      const backgroundColor = this.rgbToHex(styles.backgroundColor);
      const textColor = this.rgbToHex(styles.color);

      if (backgroundColor && textColor && backgroundColor !== 'transparent') {
        const contrast = this.calculateContrastRatio(textColor, backgroundColor);
        const fontSize = parseFloat(styles.fontSize);
        const isBold = styles.fontWeight === 'bold' || parseInt(styles.fontWeight) >= 700;

        // WCAG AA standards
        const minimumContrast = (fontSize >= 18 || (fontSize >= 14 && isBold)) ? 3 : 4.5;

        if (contrast < minimumContrast) {
          issues.push({
            type: 'contrast',
            severity: 'high',
            element: `${element.tagName.toLowerCase()}[${index}]`,
            description: `Insufficient color contrast ratio: ${contrast.toFixed(2)}:1 (minimum: ${minimumContrast}:1)`,
            wcagGuideline: 'WCAG 2.1 1.4.3',
            recommendation: 'Increase color contrast to meet WCAG AA standards',
            automated: true
          });
        }
      }
    });

    return issues;
  }

  /**
   * Test keyboard navigation
   */
  private testKeyboardNavigation(
    container: HTMLElement,
    additionalInteractions?: () => void
  ): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];

    // Get all focusable elements
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [role="button"]'
    );

    if (focusableElements.length === 0) {
      return issues;
    }

    // Test tab order
    let previousElement: Element | null = null;

    focusableElements.forEach((element, index) => {
      const tabIndex = element.getAttribute('tabindex');

      // Check for positive tabindex (bad practice)
      if (tabIndex && parseInt(tabIndex) > 0) {
        issues.push({
          type: 'keyboard',
          severity: 'medium',
          element: `${element.tagName.toLowerCase()}[${index}]`,
          description: `Positive tabindex value: ${tabIndex}`,
          wcagGuideline: 'WCAG 2.1 2.4.3',
          recommendation: 'Remove positive tabindex or use 0 for natural tab order',
          automated: true
        });
      }

      // Check for tabindex="-1" on interactive elements
      if (tabIndex === "-1" && this.isInteractiveElement(element)) {
        issues.push({
          type: 'keyboard',
          severity: 'high',
          element: `${element.tagName.toLowerCase()}[${index}]`,
          description: 'Interactive element has tabindex="-1" (removed from tab order)',
          wcagGuideline: 'WCAG 2.1 2.4.3',
          recommendation: 'Remove tabindex="-1" or ensure element is not interactive',
          automated: true
        });
      }
    });

    // Test keyboard accessibility
    focusableElements.forEach((element, index) => {
      if (element.tagName.toLowerCase() === 'button' ||
          element.getAttribute('role') === 'button') {
        // Simulate Enter key
        const keyDownEvent = new KeyboardEvent('keydown', {
          key: 'Enter',
          bubbles: true,
          cancelable: true
        });

        const canBeActivated = element.dispatchEvent(keyDownEvent);

        if (!canBeActivated && !(element as HTMLButtonElement).disabled) {
          issues.push({
            type: 'keyboard',
            severity: 'high',
            element: `button[${index}]`,
            description: 'Button cannot be activated via keyboard',
            wcagGuideline: 'WCAG 2.1 2.1.1',
            recommendation: 'Ensure buttons can be activated with Enter and Space keys',
            automated: true
          });
        }
      }
    });

    return issues;
  }

  /**
   * Test focus management
   */
  private testFocusManagement(container: HTMLElement): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];

    // Check for visible focus indicators
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    focusableElements.forEach((element, index) => {
      const styles = window.getComputedStyle(element, ':focus');
      const hasFocusIndicator = styles.outline !== 'none' ||
                               styles.outline !== '0px' ||
                               styles.boxShadow !== 'none';

      if (!hasFocusIndicator) {
        issues.push({
          type: 'focus',
          severity: 'medium',
          element: `${element.tagName.toLowerCase()}[${index}]`,
          description: 'Element lacks visible focus indicator',
          wcagGuideline: 'WCAG 2.1 2.4.7',
          recommendation: 'Add visible focus styles using :focus or :focus-visible',
          automated: false // Requires visual verification
        });
      }
    });

    // Check for skip links (for accessibility)
    const skipLinks = container.querySelectorAll('a[href^="#"], [role="navigation"] a');
    if (skipLinks.length === 0 && container.querySelectorAll('nav').length > 0) {
      issues.push({
        type: 'focus',
        severity: 'low',
        element: 'page',
        description: 'No skip links found for keyboard navigation',
        wcagGuideline: 'WCAG 2.1 2.4.1',
        recommendation: 'Add skip links to main content areas',
        automated: false
      });
    }

    return issues;
  }

  /**
   * Test semantic HTML structure
   */
  private testSemanticStructure(container: HTMLElement): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];

    // Check for proper use of landmark roles
    const hasMainLandmark = container.querySelector('main, [role="main"]');
    if (!hasMainLandmark && container.textContent && container.textContent.length > 500) {
      issues.push({
        type: 'semantic',
        severity: 'medium',
        element: 'page',
        description: 'No main landmark found',
        wcagGuideline: 'WCAG 2.1 1.3.1',
        recommendation: 'Add <main> element or role="main" for main content',
        automated: true
      });
    }

    // Check for proper form labels
    const formInputs = container.querySelectorAll('input, select, textarea');
    formInputs.forEach((input, index) => {
      const hasLabel = container.querySelector(`label[for="${input.id}"]`) ||
                      input.hasAttribute('aria-label') ||
                      input.hasAttribute('aria-labelledby') ||
                      input.getAttribute('placeholder')?.length;

      if (!hasLabel && input.type !== 'hidden') {
        issues.push({
          type: 'semantic',
          severity: 'high',
          element: `${input.tagName.toLowerCase()}[${index}]`,
          description: 'Form input lacks proper label',
          wcagGuideline: 'WCAG 2.1 1.3.1, 3.3.2',
          recommendation: 'Add associated label or ARIA attributes',
          automated: true
        });
      }
    });

    // Check for proper table structure
    const tables = container.querySelectorAll('table');
    tables.forEach((table, index) => {
      const hasHeaders = table.querySelector('thead, th[scope], th[abbr]');
      if (!hasHeaders) {
        issues.push({
          type: 'semantic',
          severity: 'high',
          element: `table[${index}]`,
          description: 'Table lacks proper headers',
          wcagGuideline: 'WCAG 2.1 1.3.1',
          recommendation: 'Add table headers using <th> with scope attributes',
          automated: true
        });
      }

      const hasCaption = table.querySelector('caption');
      if (!hasCaption) {
        issues.push({
          type: 'semantic',
          severity: 'medium',
          element: `table[${index}]`,
          description: 'Table lacks caption for context',
          wcagGuideline: 'WCAG 2.1 2.4.6',
          recommendation: 'Add caption to describe table content',
          automated: false
        });
      }
    });

    return issues;
  }

  /**
   * Check for invalid ARIA attributes
   */
  private checkInvalidAriaAttributes(element: Element, index: number, issues: AccessibilityIssue[]) {
    const attributes = Array.from(element.attributes);

    attributes.forEach(attr => {
      if (attr.name.startsWith('aria-')) {
        // Check for empty ARIA attributes
        if (!attr.value.trim()) {
          issues.push({
            type: 'aria',
            severity: 'medium',
            element: `${element.tagName.toLowerCase()}[${index}]`,
            description: `Empty ARIA attribute: ${attr.name}`,
            wcagGuideline: 'WCAG 2.1 1.3.1',
            recommendation: 'Remove empty ARIA attributes or provide meaningful values',
            automated: true
          });
        }
      }
    });
  }

  /**
   * Get accessible name for an element
   */
  private getAccessibleName(element: Element): string {
    // Check for aria-label
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel;

    // Check for aria-labelledby
    const ariaLabelledBy = element.getAttribute('aria-labelledby');
    if (ariaLabelledBy) {
      const labelElement = document.getElementById(ariaLabelledBy);
      if (labelElement) return labelElement.textContent || '';
    }

    // Check for button content
    if (element.tagName.toLowerCase() === 'button') {
      return element.textContent?.trim() || '';
    }

    // Check for input labels
    if (element.tagName.toLowerCase() === 'input') {
      const id = element.getAttribute('id');
      if (id) {
        const label = document.querySelector(`label[for="${id}"]`);
        if (label) return label.textContent?.trim() || '';
      }

      return element.getAttribute('placeholder')?.trim() || '';
    }

    return element.textContent?.trim() || '';
  }

  /**
   * Check if element is interactive
   */
  private isInteractiveElement(element: Element): boolean {
    const tagName = element.tagName.toLowerCase();
    const interactiveTags = ['button', 'a', 'input', 'select', 'textarea', 'details'];

    return interactiveTags.includes(tagName) ||
           element.hasAttribute('onclick') ||
           element.getAttribute('role') === 'button' ||
           element.getAttribute('role') === 'link';
  }

  /**
   * Convert RGB color to hex
   */
  private rgbToHex(rgb: string): string {
    if (rgb.startsWith('#')) return rgb;
    if (rgb === 'transparent') return 'transparent';

    const match = rgb.match(/\d+/g);
    if (!match || match.length < 3) return '';

    const r = parseInt(match[0]);
    const g = parseInt(match[1]);
    const b = parseInt(match[2]);

    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  }

  /**
   * Calculate relative luminance
   */
  private getRelativeLuminance(hex: string): number {
    const rgb = this.hexToRgb(hex);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(val => {
      val /= 255;
      return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Calculate contrast ratio between two colors
   */
  private calculateContrastRatio(color1: string, color2: string): number {
    const cacheKey = `${color1}-${color2}`;
    if (this.contrastCache.has(cacheKey)) {
      return this.contrastCache.get(cacheKey)!;
    }

    const lum1 = this.getRelativeLuminance(color1);
    const lum2 = this.getRelativeLuminance(color2);

    const contrast = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
    this.contrastCache.set(cacheKey, contrast);

    return contrast;
  }

  /**
   * Convert hex to RGB
   */
  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

  /**
   * Convert axe violations to our format
   */
  private convertAxeViolations(axeResults: AxeResults): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];

    axeResults.violations.forEach(violation => {
      violation.nodes.forEach(node => {
        issues.push({
          type: 'wcag',
          severity: this.mapImpactToSeverity(violation.impact),
          element: node.html.join(', '),
          description: violation.description,
          wcagGuideline: violation.tags.find(tag => tag.startsWith('wcag2')) || '',
          recommendation: violation.help,
          automated: true
        });
      });
    });

    return issues;
  }

  /**
   * Map axe impact to our severity
   */
  private mapImpactToSeverity(impact?: string): AccessibilityIssue['severity'] {
    switch (impact) {
      case 'critical': return 'critical';
      case 'serious': return 'high';
      case 'moderate': return 'medium';
      case 'minor': return 'low';
      default: return 'medium';
    }
  }

  /**
   * Generate accessibility report
   */
  private generateReport(
    componentName: string,
    issues: AccessibilityIssue[],
    axeResults?: AxeResults
  ): AccessibilityReport {
    const issuesByType: Record<string, number> = {};
    const issuesBySeverity: Record<string, number> = {};

    issues.forEach(issue => {
      issuesByType[issue.type] = (issuesByType[issue.type] || 0) + 1;
      issuesBySeverity[issue.severity] = (issuesBySeverity[issue.severity] || 0) + 1;
    });

    // Calculate accessibility score (0-100)
    const severityWeights = { critical: 10, high: 5, medium: 2, low: 1 };
    const totalDeductions = issues.reduce((sum, issue) =>
      sum + severityWeights[issue.severity], 0);

    const score = Math.max(0, 100 - totalDeductions);

    return {
      component: componentName,
      timestamp: new Date().toISOString(),
      totalIssues: issues.length,
      issuesByType,
      issuesBySeverity,
      issues,
      axeResults,
      score
    };
  }

  /**
   * Generate comprehensive accessibility report
   */
  generateSummary(reports: AccessibilityReport[]): {
    totalComponents: number;
    overallScore: number;
    totalIssues: number;
    criticalIssues: number;
    highIssues: number;
    commonIssues: Array<{ type: string; count: number }>;
    recommendations: string[];
  } {
    const totalComponents = reports.length;
    const overallScore = Math.round(
      reports.reduce((sum, report) => sum + report.score, 0) / totalComponents
    );
    const totalIssues = reports.reduce((sum, report) => sum + report.totalIssues, 0);

    const allIssues = reports.flatMap(report => report.issues);
    const criticalIssues = allIssues.filter(issue => issue.severity === 'critical').length;
    const highIssues = allIssues.filter(issue => issue.severity === 'high').length;

    // Find most common issues
    const issueTypes: Record<string, number> = {};
    allIssues.forEach(issue => {
      issueTypes[issue.type] = (issueTypes[issue.type] || 0) + 1;
    });

    const commonIssues = Object.entries(issueTypes)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Generate recommendations
    const recommendations = this.generateRecommendations(allIssues);

    return {
      totalComponents,
      overallScore,
      totalIssues,
      criticalIssues,
      highIssues,
      commonIssues,
      recommendations
    };
  }

  /**
   * Generate recommendations based on issues found
   */
  private generateRecommendations(issues: AccessibilityIssue[]): string[] {
    const recommendations = new Set<string>();

    if (issues.some(i => i.type === 'contrast')) {
      recommendations.add('Improve color contrast ratios to meet WCAG AA standards (4.5:1 for normal text)');
    }

    if (issues.some(i => i.type === 'aria')) {
      recommendations.add('Add proper ARIA labels and descriptions to interactive elements');
    }

    if (issues.some(i => i.type === 'keyboard')) {
      recommendations.add('Ensure all interactive elements are keyboard accessible');
    }

    if (issues.some(i => i.type === 'focus')) {
      recommendations.add('Implement visible focus indicators for keyboard navigation');
    }

    if (issues.some(i => i.type === 'semantic')) {
      recommendations.add('Use semantic HTML elements and proper heading structure');
    }

    return Array.from(recommendations);
  }
}

export const accessibilityTester = new AccessibilityTester();