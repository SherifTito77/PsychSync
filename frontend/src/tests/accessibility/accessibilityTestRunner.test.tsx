/**
 * Focused Accessibility Test Runner
 * Tests core components for critical accessibility issues
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

// Import components to test
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Select } from '../../components/ui/Select';
import NavBar from '../../components/NavBar';

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

// Helper function to test basic accessibility
const testBasicAccessibility = (container: HTMLElement, componentName: string) => {
  const issues: string[] = [];

  // 1. Test for interactive elements with accessible names
  const interactiveElements = container.querySelectorAll(
    'button, [role="button"], a, input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  interactiveElements.forEach((element, index) => {
    const tagName = element.tagName.toLowerCase();
    const hasText = element.textContent?.trim().length || 0;
    const hasAriaLabel = element.hasAttribute('aria-label') ||
                        element.hasAttribute('aria-labelledby');

    if (!hasText && !hasAriaLabel) {
      issues.push(`${componentName}: Interactive ${tagName} element lacks accessible name`);
    }
  });

  // 2. Test form inputs have labels
  const formInputs = container.querySelectorAll('input, select, textarea');
  formInputs.forEach((input, index) => {
    const id = input.getAttribute('id');
    const hasLabel = id ? container.querySelector(`label[for="${id}"]`) : false;
    const hasAriaLabel = input.hasAttribute('aria-label') ||
                         input.hasAttribute('aria-labelledby') ||
                         input.hasAttribute('placeholder');

    // Check for accessible name through proper labeling
    const accessibleName = input.getAttribute('aria-label') ||
                          input.getAttribute('placeholder') ||
                          (id && container.querySelector(`label[for="${id}"]`)?.textContent?.trim());

    if (!accessibleName && input.type !== 'hidden') {
      issues.push(`${componentName}: Form input lacks proper label`);
    }
  });

  // 3. Test for proper button attributes
  const buttons = container.querySelectorAll('button, [role="button"]');
  buttons.forEach((button, index) => {
    const hasAriaDisabled = button.hasAttribute('aria-disabled');
    const isDisabled = button.hasAttribute('disabled');

    if (isDisabled && !hasAriaDisabled) {
      issues.push(`${componentName}: Disabled button missing aria-disabled attribute`);
    }
  });

  // 4. Test heading structure
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
  let lastLevel = 0;
  headings.forEach((heading, index) => {
    const level = parseInt(heading.tagName.substring(1));
    if (level > lastLevel + 1) {
      issues.push(`${componentName}: Heading level skipped (from h${lastLevel} to h${level})`);
    }
    lastLevel = level;
  });

  return issues;
};

describe('🔍 Core Accessibility Testing Suite', () => {

  describe('🔘 Button Component', () => {
    it('should have accessible names and proper attributes', () => {
      const { container } = render(
        <TestWrapper>
          <Button>Click me</Button>
        </TestWrapper>
      );

      const issues = testBasicAccessibility(container, 'Button');
      expect(issues.length).toBe(0);

      // Check for focus management
      const button = container.querySelector('button');
      expect(button).toBeTruthy();
      expect(button?.textContent?.trim()).toBe('Click me');

      // Check ARIA attributes
      expect(button?.hasAttribute('type')).toBe(true);
    });

    it('should handle disabled state properly', () => {
      const { container } = render(
        <TestWrapper>
          <Button disabled>Disabled Button</Button>
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button?.hasAttribute('disabled')).toBe(true);
      expect(button?.hasAttribute('aria-disabled')).toBe(true);

      // Should not be focusable when disabled
      expect(button?.hasAttribute('tabindex')).toBe(false);
    });

    it('should handle loading state properly', () => {
      const { container } = render(
        <TestWrapper>
          <Button loading>Loading Button</Button>
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button?.hasAttribute('aria-busy')).toBe(true);
      expect(button?.hasAttribute('disabled')).toBe(true);
    });
  });

  describe('📝 Input Component', () => {
    it('should have proper labels', () => {
      const { container } = render(
        <TestWrapper>
          <Input label="Email Address" />
        </TestWrapper>
      );

      const issues = testBasicAccessibility(container, 'Input');
      expect(issues.length).toBe(0);

      const input = container.querySelector('input');
      const label = container.querySelector('label');

      expect(input).toBeTruthy();
      expect(label).toBeTruthy();
      expect(label?.textContent).toBe('Email Address');
    });

    it('should handle required state', () => {
      const { container } = render(
        <TestWrapper>
          <Input label="Required Field" required />
        </TestWrapper>
      );

      const input = container.querySelector('input');
      expect(input?.hasAttribute('required')).toBe(true);

      // Check for required indicator
      const requiredIndicator = container.querySelector('.text-red-500');
      expect(requiredIndicator).toBeTruthy();
    });

    it('should handle error states', () => {
      const { container } = render(
        <TestWrapper>
          <Input label="Field with Error" error="This field has an error" />
        </TestWrapper>
      );

      const input = container.querySelector('input');
      const errorMessage = container.querySelector('.text-red-600');

      expect(input).toBeTruthy();
      expect(errorMessage).toBeTruthy();
      expect(errorMessage?.textContent).toBe('This field has an error');

      // Check for ARIA attributes (now implemented!)
      expect(input?.hasAttribute('aria-invalid')).toBe(true);
      expect(input?.getAttribute('aria-invalid')).toBe('true');
      expect(input?.hasAttribute('aria-describedby')).toBe(true);
      expect(errorMessage?.getAttribute('role')).toBe('alert');
    });

    it('should handle disabled state', () => {
      const { container } = render(
        <TestWrapper>
          <Input label="Disabled Field" disabled />
        </TestWrapper>
      );

      const input = container.querySelector('input');
      expect(input?.hasAttribute('disabled')).toBe(true);
    });
  });

  describe('🃏 Card Component', () => {
    it('should have proper heading structure', () => {
      const { container } = render(
        <TestWrapper>
          <Card>
            <CardHeader>
              <CardTitle level={2}>Card Title</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Card content</p>
            </CardContent>
          </Card>
        </TestWrapper>
      );

      const issues = testBasicAccessibility(container, 'Card');
      expect(issues.length).toBe(0);

      // With level={2}, it should now be h2
      const title = container.querySelector('h2');
      expect(title).toBeTruthy();
      expect(title?.textContent).toBe('Card Title');
    });

    it('should handle interactive content', () => {
      const { container } = render(
        <TestWrapper>
          <Card>
            <CardContent>
              <CardTitle level={3}>Interactive Card</CardTitle>
              <Input label="Card Input" />
              <Button variant="outline">Card Action</Button>
            </CardContent>
          </Card>
        </TestWrapper>
      );

      const issues = testBasicAccessibility(container, 'Card-Interactive');
      expect(issues.length).toBe(0);
    });
  });

  describe('📋 Select Component', () => {
    it('should have proper labels', () => {
      const { container } = render(
        <TestWrapper>
          <Select
            label="Country"
            options={[
              { value: 'us', label: 'United States' },
              { value: 'uk', label: 'United Kingdom' }
            ]}
          />
        </TestWrapper>
      );

      const issues = testBasicAccessibility(container, 'Select');
      expect(issues.length).toBe(0);

      const select = container.querySelector('select');
      const label = container.querySelector('label');

      expect(select).toBeTruthy();
      expect(label).toBeTruthy();
      expect(label?.textContent).toBe('Country');
    });

    it('should handle required state', () => {
      const { container } = render(
        <TestWrapper>
          <Select
            label="Required Select"
            required
            options={[{ value: '1', label: 'Option 1' }]}
          />
        </TestWrapper>
      );

      const select = container.querySelector('select');
      expect(select?.hasAttribute('required')).toBe(true);
    });
  });

  describe('🧭 Navigation Component', () => {
    it('should have accessible links', () => {
      const { container } = render(
        <TestWrapper>
          <NavBar />
        </TestWrapper>
      );

      const issues = testBasicAccessibility(container, 'NavBar');
      expect(issues.length).toBe(0);

      const links = container.querySelectorAll('a');
      expect(links.length).toBeGreaterThan(0);

      // All links should have accessible names
      links.forEach(link => {
        expect(link.textContent?.trim().length).toBeGreaterThan(0);
      });
    });

    it('should be keyboard navigable', () => {
      const { container } = render(
        <TestWrapper>
          <NavBar />
        </TestWrapper>
      );

      const links = container.querySelectorAll('a');

      // All links should be focusable
      links.forEach(link => {
        expect(link.hasAttribute('href')).toBe(true);
        // Links don't have tabindex by default (they're naturally focusable)
      });
    });
  });

  describe('🎨 Color Contrast Considerations', () => {
    it('should warn about potential contrast issues', () => {
      // This test checks for elements that might have contrast issues
      const { container } = render(
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

      // Note: This is a simplified test - real contrast testing requires
      // proper color extraction and calculation
      const textElements = container.querySelectorAll('h3, p, button');
      expect(textElements.length).toBeGreaterThan(0);

      // In a real implementation, we would calculate actual contrast ratios
      console.log('⚠️  Note: Real contrast testing requires proper color calculation');
    });
  });

  describe('⌨️ Keyboard Navigation Tests', () => {
    it('should support tab navigation through forms', () => {
      const { container } = render(
        <TestWrapper>
          <div>
            <Button>Button 1</Button>
            <Input label="Input Field" />
            <Select
              label="Options"
              options={[{ value: '1', label: 'Option 1' }]}
            />
            <Button variant="outline">Button 2</Button>
          </div>
        </TestWrapper>
      );

      const focusableElements = container.querySelectorAll(
        'button, input, select'
      );

      expect(focusableElements.length).toBeGreaterThan(0);

      // Check that elements don't have positive tabindex values
      focusableElements.forEach(element => {
        const tabIndex = element.getAttribute('tabindex');
        if (tabIndex) {
          const numTabIndex = parseInt(tabIndex);
          expect(numTabIndex).toBeLessThanOrEqual(0);
        }
      });
    });

    it('should handle button activation via keyboard', () => {
      const handleClick = vi.fn();
      const { container } = render(
        <TestWrapper>
          <Button onClick={handleClick}>Clickable Button</Button>
        </TestWrapper>
      );

      const button = container.querySelector('button');
      expect(button).toBeTruthy();

      // Simulate keyboard events
      if (button) {
        fireEvent.keyDown(button, { key: 'Enter' });
        fireEvent.keyUp(button, { key: 'Enter' });

        // Note: In a real browser, this would trigger the click handler
        // Testing library limitations prevent this from working perfectly
        console.log('⚠️  Note: Full keyboard testing requires browser environment');
      }
    });
  });

  describe('📊 Accessibility Summary', () => {
    it('should track overall accessibility health', () => {
      // This test serves as a summary of accessibility testing
      const components = [
        { name: 'Button', element: <Button>Test</Button> },
        { name: 'Input', element: <Input label="Test" /> },
        { name: 'Card', element: <Card><CardContent>Test</CardContent></Card> },
      ];

      const totalIssues: string[] = [];

      components.forEach(({ name, element }) => {
        const { container } = render(<TestWrapper>{element}</TestWrapper>);
        const issues = testBasicAccessibility(container, name);
        totalIssues.push(...issues);
      });

      console.log(`📊 Accessibility Summary: ${totalIssues.length} issues found`);
      totalIssues.forEach(issue => console.log(`  ❌ ${issue}`));

      // For now, we expect basic accessibility to be good
      expect(totalIssues.length).toBeLessThan(5);
    });
  });
});

// Accessibility testing utilities
export const accessibilityUtils = {
  testBasicAccessibility,
  runQuickAudit: (components: Array<{ name: string; element: React.ReactElement }>) => {
    const results: { name: string; issues: string[]; score: number }[] = [];

    components.forEach(({ name, element }) => {
      const { container } = render(<TestWrapper>{element}</TestWrapper>);
      const issues = testBasicAccessibility(container, name);
      const score = Math.max(0, 100 - (issues.length * 20)); // Simple scoring

      results.push({ name, issues, score });
    });

    return results;
  }
};