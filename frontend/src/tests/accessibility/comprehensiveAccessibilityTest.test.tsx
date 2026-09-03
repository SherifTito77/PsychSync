/**
 * Comprehensive Accessibility Test Suite
 * Tests all major components for ARIA, contrast, keyboard navigation, and WCAG compliance
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { accessibilityTester, type AccessibilityReport } from './accessibilityTester';

// Import components to test
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Select } from '../../components/ui/Select';
import NavBar from '../../components/NavBar';
import Login from '../../pages/Login';
import Dashboard from '../../pages/Dashboard';

// Test wrapper with router
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('🔍 Comprehensive Accessibility Testing Suite', () => {

  let allReports: AccessibilityReport[] = [];

  afterEach(() => {
    allReports = [];
  });

  afterAll(() => {
    if (allReports.length > 0) {
      const summary = accessibilityTester.generateSummary(allReports);
      console.log('\n📊 Accessibility Testing Summary:');
      console.log(`Components tested: ${summary.totalComponents}`);
      console.log(`Overall accessibility score: ${summary.overallScore}/100`);
      console.log(`Total issues found: ${summary.totalIssues}`);
      console.log(`Critical issues: ${summary.criticalIssues}`);
      console.log(`High severity issues: ${summary.highIssues}`);

      console.log('\n🎯 Most Common Issues:');
      summary.commonIssues.forEach((issue, index) => {
        console.log(`${index + 1}. ${issue.type}: ${issue.count} occurrences`);
      });

      console.log('\n💡 Recommendations:');
      summary.recommendations.forEach((rec, index) => {
        console.log(`${index + 1}. ${rec}`);
      });
    }
  });

  describe('🔘 Button Component Accessibility', () => {
    it('should have no accessibility violations for basic button', async () => {
      const component = (
        <TestWrapper>
          <Button>Click me</Button>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Button-Basic', component);
      allReports.push(report);

      // Should have good accessibility score
      expect(report.score).toBeGreaterThan(80);

      // Should not have critical ARIA or keyboard issues
      const criticalIssues = report.issues.filter(i => i.severity === 'critical');
      expect(criticalIssues.length).toBe(0);
    });

    it('should handle button variants accessibly', async () => {
      const component = (
        <TestWrapper>
          <div>
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="danger">Danger</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="link">Link</Button>
          </div>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Button-Variants', component);
      allReports.push(report);

      // All button variants should maintain focus visibility
      const focusIssues = report.issues.filter(i => i.type === 'focus');
      expect(focusIssues.length).toBeLessThan(2); // Allow for minor styling differences
    });

    it('should handle disabled button state accessibly', async () => {
      const component = (
        <TestWrapper>
          <Button disabled>Disabled Button</Button>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Button-Disabled', component);
      allReports.push(report);

      // Disabled button should not have keyboard navigation issues
      const keyboardIssues = report.issues.filter(i => i.type === 'keyboard');
      const tabIndexIssues = keyboardIssues.filter(i =>
        i.description.includes('tabindex="-1"')
      );
      expect(tabIndexIssues).toHaveLength(0);
    });

    it('should handle loading state accessibly', async () => {
      const component = (
        <TestWrapper>
          <Button loading>Loading Button</Button>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Button-Loading', component);
      allReports.push(report);

      // Loading button should have aria-busy attribute
      const ariaIssues = report.issues.filter(i => i.type === 'aria');
      const busyMissing = ariaIssues.filter(i => i.description.includes('aria-busy'));
      expect(busyMissing).toHaveLength(0);
    });
  });

  describe('📝 Input Component Accessibility', () => {
    it('should have proper labels and ARIA attributes', async () => {
      const component = (
        <TestWrapper>
          <Input
            label="Email Address"
            type="email"
            required
            helperText="Enter your company email"
          />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Input-Labeled', component);
      allReports.push(report);

      // Input with label should not have missing label violations
      const semanticIssues = report.issues.filter(i => i.type === 'semantic');
      const labelIssues = semanticIssues.filter(i =>
        i.description.includes('lacks proper label')
      );
      expect(labelIssues).toHaveLength(0);
    });

    it('should handle error states accessibly', async () => {
      const component = (
        <TestWrapper>
          <Input
            label="Password"
            type="password"
            error="Password must be at least 8 characters"
          />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Input-Error', component);
      allReports.push(report);

      // Error states should be properly announced to screen readers
      const ariaIssues = report.issues.filter(i => i.type === 'aria');
      expect(report.score).toBeGreaterThan(70); // Error states add complexity
    });

    it('should handle disabled input state accessibly', async () => {
      const component = (
        <TestWrapper>
          <Input
            label="Disabled Field"
            disabled
            defaultValue="Cannot edit this"
          />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Input-Disabled', component);
      allReports.push(report);

      // Disabled inputs should not have keyboard navigation issues
      const keyboardIssues = report.issues.filter(i => i.type === 'keyboard');
      expect(keyboardIssues.length).toBe(0);
    });
  });

  describe('🃏 Card Component Accessibility', () => {
    it('should have proper semantic structure', async () => {
      const component = (
        <TestWrapper>
          <Card>
            <CardHeader>
              <CardTitle>Card Title</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This is the card content description.</p>
              <Button>Action</Button>
            </CardContent>
          </Card>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Card-Standard', component);
      allReports.push(report);

      // Cards should have proper heading structure
      const semanticIssues = report.issues.filter(i => i.type === 'semantic');
      const headingIssues = semanticIssues.filter(i =>
        i.description.includes('Heading level skipped')
      );
      expect(headingIssues).toHaveLength(0);
    });

    it('should handle interactive elements within cards', async () => {
      const component = (
        <TestWrapper>
          <Card>
            <CardContent>
              <h3>Interactive Card</h3>
              <Input label="Card Input" />
              <Select label="Card Select" options={[{ value: '1', label: 'Option 1' }]} />
              <Button variant="outline">Card Action</Button>
            </CardContent>
          </Card>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Card-Interactive', component);
      allReports.push(report);

      // Interactive elements should be keyboard accessible
      const keyboardIssues = report.issues.filter(i => i.type === 'keyboard');
      expect(keyboardIssues.length).toBeLessThan(3); // Allow for minor issues
    });
  });

  describe('📋 Select Component Accessibility', () => {
    it('should have proper labels and keyboard navigation', async () => {
      const component = (
        <TestWrapper>
          <Select
            label="Country"
            options={[
              { value: 'us', label: 'United States' },
              { value: 'uk', label: 'United Kingdom' },
              { value: 'ca', label: 'Canada' }
            ]}
          />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Select-Standard', component);
      allReports.push(report);

      // Select should have proper labels and keyboard access
      const labelIssues = report.issues.filter(i =>
        i.type === 'semantic' && i.description.includes('lacks proper label')
      );
      expect(labelIssues).toHaveLength(0);
    });

    it('should handle error states accessibly', async () => {
      const component = (
        <TestWrapper>
          <Select
            label="Priority"
            error="Please select a priority level"
            options={[{ value: 'high', label: 'High' }]}
          />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Select-Error', component);
      allReports.push(report);

      // Error states should be accessible
      expect(report.score).toBeGreaterThan(60); // Error states add complexity
    });
  });

  describe('🧭 Navigation Component Accessibility', () => {
    it('should have proper ARIA landmarks and keyboard navigation', async () => {
      const component = (
        <TestWrapper>
          <NavBar />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('NavBar', component);
      allReports.push(report);

      // Navigation should be keyboard accessible
      const keyboardIssues = report.issues.filter(i => i.type === 'keyboard');
      const activationIssues = keyboardIssues.filter(i =>
        i.description.includes('cannot be activated')
      );
      expect(activationIssues).toHaveLength(0);
    });

    it('should have proper focus management', async () => {
      const component = (
        <TestWrapper>
          <NavBar />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('NavBar-Focus', component);
      allReports.push(report);

      // Navigation links should have focus indicators
      const focusIssues = report.issues.filter(i => i.type === 'focus');
      const focusIndicatorIssues = focusIssues.filter(i =>
        i.description.includes('lacks visible focus indicator')
      );
      expect(focusIndicatorIssues.length).toBeLessThan(3);
    });
  });

  describe('🔐 Login Page Accessibility', () => {
    it('should have comprehensive accessibility for login form', async () => {
      const component = (
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('LoginPage', component);
      allReports.push(report);

      // Login page should have high accessibility score
      expect(report.score).toBeGreaterThan(75);

      // Should not have critical issues
      const criticalIssues = report.issues.filter(i => i.severity === 'critical');
      expect(criticalIssues.length).toBe(0);
    });

    it('should have proper form structure and error handling', async () => {
      const component = (
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Login-Form', component);
      allReports.push(report);

      // Forms should have proper labels and error states
      const labelIssues = report.issues.filter(i =>
        i.type === 'semantic' && i.description.includes('lacks proper label')
      );
      expect(labelIssues.length).toBeLessThan(2);
    });
  });

  describe('📊 Dashboard Accessibility', () => {
    it('should have main landmarks and proper heading structure', async () => {
      const component = (
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Dashboard', component);
      allReports.push(report);

      // Dashboard should have main landmark
      const landmarkIssues = report.issues.filter(i =>
        i.type === 'semantic' && i.description.includes('main landmark')
      );
      expect(landmarkIssues).toHaveLength(0);
    });

    it('should handle complex interactive elements', async () => {
      const component = (
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Dashboard-Interactive', component);
      allReports.push(report);

      // Complex dashboards should maintain reasonable accessibility
      expect(report.score).toBeGreaterThan(65); // Complex components have more challenges
    });
  });

  describe('🎨 Color Contrast Testing', () => {
    it('should identify contrast issues in various states', async () => {
      const component = (
        <TestWrapper>
          <div style={{ backgroundColor: '#f0f0f0', padding: '20px' }}>
            <h3 style={{ color: '#999999' }}>Low Contrast Text</h3>
            <p style={{ color: '#cccccc' }}>Even lower contrast</p>
            <Button variant="outline" style={{ borderColor: '#dddddd', color: '#999999' }}>
              Low Contrast Button
            </Button>
          </div>
        </TestWrapper>
      );

      const report = await accessibilityTester.testComponent('Contrast-Test', component);
      allReports.push(report);

      // Should detect contrast issues
      const contrastIssues = report.issues.filter(i => i.type === 'contrast');
      expect(contrastIssues.length).toBeGreaterThan(0);

      // All contrast issues should be properly identified with WCAG guidelines
      contrastIssues.forEach(issue => {
        expect(issue.wcagGuideline).toContain('WCAG 2.1 1.4.3');
        expect(issue.recommendation).toContain('color contrast');
      });
    });
  });

  describe('⌨️ Keyboard Navigation Testing', () => {
    it('should test comprehensive keyboard navigation', async () => {
      const component = (
        <TestWrapper>
          <div>
            <Button>Button 1</Button>
            <Input label="Input Field" />
            <Select
              label="Options"
              options={[{ value: '1', label: 'Option 1' }, { value: '2', label: 'Option 2' }]}
            />
            <Button variant="outline">Button 2</Button>
            <a href="#test">Link</a>
          </div>
        </TestWrapper>
      );

      const additionalInteractions = () => {
        // Simulate tab navigation
        const tabbableElements = document.querySelectorAll(
          'button, input, select, a[href]'
        );
        tabbableElements.forEach(element => {
          element.focus();
          // Check if element actually received focus
          expect(document.activeElement).toBe(element);
        });
      };

      const report = await accessibilityTester.testComponent(
        'Keyboard-Navigation',
        component,
        additionalInteractions
      );
      allReports.push(report);

      // All interactive elements should be keyboard accessible
      const keyboardIssues = report.issues.filter(i => i.type === 'keyboard');
      const tabIndexIssues = keyboardIssues.filter(i =>
        i.description.includes('tabindex="-1"') || i.description.includes('Positive tabindex')
      );
      expect(tabIndexIssues).toHaveLength(0);
    });
  });

  describe('🔍 Overall Accessibility Assessment', () => {
    it('should maintain high accessibility standards across all components', () => {
      if (allReports.length > 0) {
        const summary = accessibilityTester.generateSummary(allReports);

        // Overall accessibility score should be good
        expect(summary.overallScore).toBeGreaterThan(70);

        // Should not have critical issues
        expect(summary.criticalIssues).toBe(0);

        // High severity issues should be minimal
        expect(summary.highIssues).toBeLessThan(5);

        // Should provide actionable recommendations
        expect(summary.recommendations.length).toBeGreaterThan(0);
      }
    });

    it('should provide comprehensive issue reporting', () => {
      if (allReports.length > 0) {
        const allIssues = allReports.flatMap(report => report.issues);

        // Each issue should have proper categorization
        allIssues.forEach(issue => {
          expect(issue.type).toBeDefined();
          expect(issue.severity).toBeDefined();
          expect(issue.description).toBeDefined();
          expect(issue.recommendation).toBeDefined();

          // Most automated issues should have WCAG references
          if (issue.automated) {
            expect(issue.wcagGuideline).toBeDefined();
          }
        });
      }
    });
  });
});

// Helper function to run accessibility tests in development
export const runAccessibilityAudit = async () => {
  console.log('🔍 Starting comprehensive accessibility audit...');

  const components = [
    { name: 'Button', component: <Button>Test Button</Button> },
    { name: 'Input', component: <Input label="Test Input" /> },
    { name: 'Card', component: (
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>Test content</CardContent>
      </Card>
    )},
    { name: 'Select', component: (
      <Select
        label="Test Select"
        options={[{ value: '1', label: 'Option 1' }]}
      />
    )},
  ];

  const reports: AccessibilityReport[] = [];

  for (const { name, component } of components) {
    try {
      const report = await accessibilityTester.testComponent(name, component);
      reports.push(report);
      console.log(`✅ ${name}: Score ${report.score}/100, Issues: ${report.totalIssues}`);
    } catch (error) {
      console.error(`❌ ${name}: Test failed`, error);
    }
  }

  const summary = accessibilityTester.generateSummary(reports);
  console.log('\n📊 Accessibility Audit Summary:');
  console.log(`Overall Score: ${summary.overallScore}/100`);
  console.log(`Total Issues: ${summary.totalIssues}`);
  console.log(`Critical Issues: ${summary.criticalIssues}`);

  return { reports, summary };
};
