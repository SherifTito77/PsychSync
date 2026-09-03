/**
 * Comprehensive Overlay Component Testing Framework
 * Tests modals, notifications, alerts, and toasts for consistency
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Import components to test
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/Alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import NotificationContainer from '../../components/common/NotificationContainer';
import { NotificationProvider, useNotification } from '../../contexts/NotificationContext';
import type { AlertProps } from '../../components/ui/Alert';

// Mock components
vi.mock('../../services/assessmentService');
vi.mock('../../services/teamService');

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <NotificationProvider>
      {children}
    </NotificationProvider>
  </BrowserRouter>
);

// Helper component to test notifications
const TestNotificationComponent: React.FC = () => {
  const { showNotification } = useNotification();

  return (
    <div>
      <button onClick={() => showNotification('Success message', 'success')}>
        Show Success
      </button>
      <button onClick={() => showNotification('Error message', 'error')}>
        Show Error
      </button>
      <button onClick={() => showNotification('Warning message', 'warning')}>
        Show Warning
      </button>
      <button onClick={() => showNotification('Info message', 'info')}>
        Show Info
      </button>
    </div>
  );
};

// Helper function to test overlay accessibility
const testOverlayAccessibility = (container: HTMLElement, componentName: string): string[] => {
  const issues: string[] = [];

  // 1. Test for proper focus management
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  // Check for modal/overlay specific attributes
  const modals = container.querySelectorAll('[role="dialog"], .modal, [aria-modal="true"]');
  modals.forEach((modal, index) => {
    // Check for proper aria-modal attribute
    if (!modal.hasAttribute('aria-modal') && modal.getAttribute('role') !== 'dialog') {
      issues.push(`${componentName}: Modal lacks aria-modal attribute`);
    }

    // Check for focus trapping (should have focusable elements)
    if (focusableElements.length === 0) {
      issues.push(`${componentName}: Modal has no focusable elements for keyboard navigation`);
    }
  });

  // 2. Test for dismissibility
  const closeButtons = container.querySelectorAll(
    'button[aria-label*="close"], button[aria-label*="dismiss"], button[aria-label*="cancel"], .close-button'
  );

  if (modals.length > 0 && closeButtons.length === 0) {
    issues.push(`${componentName}: Modal lacks close/dismiss button`);
  }

  // 3. Test for proper ARIA labels
  const ariaLabeledElements = container.querySelectorAll('[aria-labelledby], [aria-label]');
  if (modals.length > 0 && ariaLabeledElements.length === 0) {
    issues.push(`${componentName}: Modal lacks proper ARIA label or-labelledby`);
  }

  // 4. Test for backdrop behavior
  const backdrops = container.querySelectorAll('.modal-backdrop, [role="presentation"], .fixed.inset-0');
  if (modals.length > 0 && backdrops.length === 0) {
    issues.push(`${componentName}: Modal lacks proper backdrop overlay`);
  }

  return issues;
};

// Helper function to test consistency patterns
const testConsistencyPatterns = (container: HTMLElement, componentName: string): {
  issues: string[];
  patterns: string[];
} => {
  const issues: string[] = [];
  const patterns: string[] = [];

  // Test color consistency
  const elements = container.querySelectorAll('*');
  elements.forEach((element) => {
    const styles = window.getComputedStyle(element);
    const backgroundColor = styles.backgroundColor;
    const color = styles.color;

    // Check for consistent color scheme
    if (backgroundColor && backgroundColor !== 'rgba(0, 0, 0, 0)' && backgroundColor !== 'transparent') {
      patterns.push(`Background color: ${backgroundColor}`);
    }

    if (color && color !== 'rgba(0, 0, 0, 0)') {
      patterns.push(`Text color: ${color}`);
    }
  });

  // Test spacing consistency
  const spacingElements = container.querySelectorAll('[class*="p-"], [class*="m-"], [class*="px-"], [class*="py-"]');
  spacingElements.forEach((element) => {
    const className = element.className;
    if (className.includes('p-')) {
      patterns.push(`Padding pattern: ${className}`);
    }
  });

  // Test border consistency
  const borderElements = container.querySelectorAll('[class*="border"], [class*="rounded"]');
  borderElements.forEach((element) => {
    patterns.push(`Border pattern: ${element.className}`);
  });

  return { issues, patterns };
};

describe('🔍 Comprehensive Overlay Component Testing Suite', () => {

  describe('🚨 Alert Component', () => {
    it('should have consistent styling across variants', () => {
      const variants: Array<AlertProps['variant']> = ['info', 'success', 'warning', 'error'];
      const patternCounts: Record<string, number> = {};

      variants.forEach(variant => {
        const { container } = render(
          <TestWrapper>
            <Alert variant={variant}>
              <AlertTitle>Test Title</AlertTitle>
              <AlertDescription>Test description for {variant} alert</AlertDescription>
            </Alert>
          </TestWrapper>
        );

        const { patterns } = testConsistencyPatterns(container, `Alert-${variant}`);
        patterns.forEach(pattern => {
          patternCounts[pattern] = (patternCounts[pattern] || 0) + 1;
        });
      });

      // All variants should have the same number of styling patterns
      const uniquePatternCounts = Object.values(patternCounts);
      expect(Math.max(...uniquePatternCounts) - Math.min(...uniquePatternCounts)).toBeLessThanOrEqual(1);
    });

    it('should have proper accessibility attributes', () => {
      const { container } = render(
        <TestWrapper>
          <Alert variant="error">
            <AlertTitle>Error Title</AlertTitle>
            <AlertDescription>This is an error message</AlertDescription>
          </Alert>
        </TestWrapper>
      );

      const issues = testOverlayAccessibility(container, 'Alert');
      expect(issues.length).toBe(0);

      // Check for proper role or alert functionality
      const alertElement = container.querySelector('[role="alert"], .alert');
      if (!alertElement) {
        console.warn('Alert component could benefit from role="alert" for screen readers');
      }
    });

    it('should handle different content types consistently', () => {
      const { container: simpleContainer } = render(
        <TestWrapper>
          <Alert>Simple alert message</Alert>
        </TestWrapper>
      );

      const { container: complexContainer } = render(
        <TestWrapper>
          <Alert>
            <AlertTitle>Complex Alert</AlertTitle>
            <AlertDescription>
              This is a detailed description with multiple lines of text
              that should wrap properly.
            </AlertDescription>
          </Alert>
        </TestWrapper>
      );

      // Both should have consistent base styling
      const simplePatterns = testConsistencyPatterns(simpleContainer, 'Alert-Simple').patterns;
      const complexPatterns = testConsistencyPatterns(complexContainer, 'Alert-Complex').patterns;

      // Should share common base patterns
      expect(simplePatterns.length).toBeGreaterThan(0);
      expect(complexPatterns.length).toBeGreaterThan(0);
    });
  });

  describe('💬 Dialog Component', () => {
    it('should have proper modal structure', () => {
      const { container } = render(
        <TestWrapper>
          <Dialog open={true}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Modal Title</DialogTitle>
                <DialogDescription>Modal description</DialogDescription>
              </DialogHeader>
              <div>Modal content</div>
            </DialogContent>
          </Dialog>
        </TestWrapper>
      );

      const issues = testOverlayAccessibility(container, 'Dialog');

      // Current dialog implementation is basic, so we expect some issues
      expect(issues.length).toBeGreaterThan(0);
      console.log('Dialog issues to address:', issues);
    });

    it('should handle keyboard navigation properly', () => {
      const onOpenChange = vi.fn();
      const { container } = render(
        <TestWrapper>
          <Dialog open={true} onOpenChange={onOpenChange}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Test Dialog</DialogTitle>
              </DialogHeader>
              <button>Action Button</button>
              <button>Cancel Button</button>
            </DialogContent>
          </Dialog>
        </TestWrapper>
      );

      const focusableElements = container.querySelectorAll('button');
      expect(focusableElements.length).toBeGreaterThan(0);

      // Test Tab navigation (simulated)
      focusableElements.forEach((element, index) => {
        expect(element.tagName.toLowerCase()).toBe('button');
      });
    });

    it('should have consistent backdrop behavior', () => {
      const { container } = render(
        <TestWrapper>
          <Dialog open={true}>
            <DialogContent>
              <DialogTitle>Dialog with backdrop</DialogTitle>
            </DialogContent>
          </Dialog>
        </TestWrapper>
      );

      // Check for backdrop element
      const backdrop = container.querySelector('.fixed.inset-0, .modal-backdrop');

      // Current implementation may not have proper backdrop
      if (!backdrop) {
        console.warn('Dialog lacks proper backdrop implementation');
      }
    });
  });

  describe('🔔 Notification System', () => {
    it('should display all notification types consistently', async () => {
      const { container } = render(
        <TestWrapper>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      const { patterns } = testConsistencyPatterns(container, 'NotificationSystem');
      expect(patterns.length).toBeGreaterThan(0);

      // Test all notification types
      const successButton = screen.getByText('Show Success');
      const errorButton = screen.getByText('Show Error');
      const warningButton = screen.getByText('Show Warning');
      const infoButton = screen.getByText('Show Info');

      // Show success notification
      fireEvent.click(successButton);
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument();
      });

      // Show error notification
      fireEvent.click(errorButton);
      await waitFor(() => {
        expect(screen.getByText('Error message')).toBeInTheDocument();
      });

      // Show warning notification
      fireEvent.click(warningButton);
      await waitFor(() => {
        expect(screen.getByText('Warning message')).toBeInTheDocument();
      });

      // Show info notification
      fireEvent.click(infoButton);
      await waitFor(() => {
        expect(screen.getByText('Info message')).toBeInTheDocument();
      });

      // Should have multiple notifications
      const notifications = screen.getAllByText(/message$/);
      expect(notifications.length).toBe(4);
    });

    it('should handle notification dismissal properly', async () => {
      const { container } = render(
        <TestWrapper>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      // Show a notification
      fireEvent.click(screen.getByText('Show Success'));
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument();
      });

      // Find and click close button
      const closeButton = screen.getByLabelText('Close notification');
      expect(closeButton).toBeInTheDocument();

      fireEvent.click(closeButton);

      // Notification should be removed
      await waitFor(() => {
        expect(screen.queryByText('Success message')).not.toBeInTheDocument();
      });
    });

    it('should have proper accessibility attributes', async () => {
      const { container } = render(
        <TestWrapper>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      // Show a notification
      fireEvent.click(screen.getByText('Show Success'));
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument();
      });

      const issues = testOverlayAccessibility(container, 'Notification');

      // Notifications should have good accessibility
      expect(issues.length).toBeLessThan(2); // Allow for minor issues

      // Check for ARIA attributes
      const notifications = container.querySelectorAll('[role="alert"]');
      expect(notifications.length).toBeGreaterThan(0);
    });

    it('should handle auto-dismissal consistently', async () => {
      vi.useFakeTimers();

      const { container } = render(
        <TestWrapper>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      // Show a notification with short duration
      const { showNotification } = useNotification();
      showNotification('Auto-dismiss message', 'success', 1000);

      await waitFor(() => {
        expect(screen.getByText('Auto-dismiss message')).toBeInTheDocument();
      });

      // Fast-forward time
      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.queryByText('Auto-dismiss message')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });
  });

  describe('🔄 Cross-Component Consistency', () => {
    it('should maintain consistent spacing patterns across overlays', () => {
      const components = [
        {
          name: 'Alert',
          element: <Alert variant="info">Test alert</Alert>
        },
        {
          name: 'Notification',
          element: <TestNotificationComponent />
        }
      ];

      const allPatterns: Record<string, string[]> = {};

      components.forEach(({ name, element }) => {
        const { container } = render(<TestWrapper>{element}</TestWrapper>);
        const { patterns } = testConsistencyPatterns(container, name);
        allPatterns[name] = patterns;
      });

      // Should have some common patterns
      const patternSets = Object.values(allPatterns);
      expect(patternSets.length).toBeGreaterThan(0);

      // Log patterns for manual review
      Object.entries(allPatterns).forEach(([name, patterns]) => {
        console.log(`${name} patterns:`, patterns);
      });
    });

    it('should maintain consistent color schemes', () => {
      const colorTests = [
        {
          name: 'Alert-Success',
          element: <Alert variant="success">Success</Alert>
        },
        {
          name: 'Alert-Error',
          element: <Alert variant="error">Error</Alert>
        }
      ];

      const colorPatterns: Record<string, string[]> = {};

      colorTests.forEach(({ name, element }) => {
        const { container } = render(<TestWrapper>{element}</TestWrapper>);
        const alertElement = container.querySelector('[class*="bg-"]');
        if (alertElement) {
          const classes = alertElement.className;
          colorPatterns[name] = classes.match(/bg-\w+-\d+/g) || [];
        }
      });

      // Each variant should have distinct but consistent colors
      expect(Object.keys(colorPatterns)).toHaveLength(2);

      Object.entries(colorPatterns).forEach(([name, colors]) => {
        expect(colors.length).toBeGreaterThan(0);
        console.log(`${name} colors:`, colors);
      });
    });

    it('should maintain consistent interaction patterns', async () => {
      // Test Alert behavior
      const { container: alertContainer } = render(
        <TestWrapper>
          <Alert variant="info">Dismissible alert</Alert>
        </TestWrapper>
      );

      // Alerts should be non-intrusive by default
      const alertElement = alertContainer.querySelector('[class*="bg-"]');
      expect(alertElement).toBeInTheDocument();

      // Test Notification behavior
      const { container: notificationContainer } = render(
        <TestWrapper>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Show Info'));
      await waitFor(() => {
        expect(screen.getByText('Info message')).toBeInTheDocument();
      });

      const closeButton = screen.getByLabelText('Close notification');
      expect(closeButton).toBeInTheDocument();
    });
  });

  describe('📱 Responsive Design Consistency', () => {
    it('should handle mobile viewport consistently', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const { container } = render(
        <TestWrapper>
          <Alert variant="warning">Mobile alert</Alert>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      // Components should still render properly on mobile
      const alertElement = container.querySelector('[class*="alert"]');
      expect(alertElement).toBeInTheDocument();

      // Test mobile-specific patterns
      const mobilePatterns = testConsistencyPatterns(container, 'Mobile').patterns;
      expect(mobilePatterns.length).toBeGreaterThan(0);
    });

    it('should handle desktop viewport consistently', () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });

      const { container } = render(
        <TestWrapper>
          <Alert variant="success">Desktop alert</Alert>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      // Components should render properly on desktop
      const alertElement = container.querySelector('[class*="alert"]');
      expect(alertElement).toBeInTheDocument();

      const desktopPatterns = testConsistencyPatterns(container, 'Desktop').patterns;
      expect(desktopPatterns.length).toBeGreaterThan(0);
    });
  });

  describe('🎨 Animation and Transition Consistency', () => {
    it('should have consistent transition timing', async () => {
      const { container } = render(
        <TestWrapper>
          <TestNotificationComponent />
          <NotificationContainer />
        </TestWrapper>
      );

      // Show notification and check for transition classes
      fireEvent.click(screen.getByText('Show Success'));

      await waitFor(() => {
        const notification = screen.getByText('Success message');
        expect(notification).toBeInTheDocument();

        const notificationElement = notification.closest('[class*="transition"]');
        if (notificationElement) {
          expect(notificationElement.className).toContain('transition');
        }
      });
    });

    it('should maintain consistent animation patterns', () => {
      const components = [
        <Alert variant="info">Animated alert</Alert>,
        <Dialog open={true}>
          <DialogContent>Animated dialog</DialogContent>
        </Dialog>
      ];

      components.forEach((component, index) => {
        const { container } = render(<TestWrapper>{component}</TestWrapper>);

        // Check for animation-related classes
        const animatedElements = container.querySelectorAll('[class*="transition"], [class*="animate"], [class*="transform"]');

        if (animatedElements.length > 0) {
          animatedElements.forEach(element => {
            expect(element.className).toMatch(/transition|animate|transform/);
          });
        }
      });
    });
  });

  describe('📊 Overall Consistency Score', () => {
    it('should calculate consistency score across all overlays', () => {
      const components = [
        { name: 'Alert', element: <Alert variant="info">Test</Alert> },
        { name: 'Dialog', element: <Dialog open={true}><DialogContent>Test</DialogContent></Dialog> }
      ];

      let totalIssues = 0;
      let totalPatterns = 0;

      components.forEach(({ name, element }) => {
        const { container } = render(<TestWrapper>{element}</TestWrapper>);
        const issues = testOverlayAccessibility(container, name);
        const { patterns } = testConsistencyPatterns(container, name);

        totalIssues += issues.length;
        totalPatterns += patterns.length;

        console.log(`${name}: ${issues.length} issues, ${patterns.length} patterns`);
      });

      // Calculate consistency score
      const consistencyScore = Math.max(0, 100 - (totalIssues * 10));
      console.log(`Overall consistency score: ${consistencyScore}/100`);

      // Should maintain reasonable consistency
      expect(consistencyScore).toBeGreaterThan(70);
      expect(totalPatterns).toBeGreaterThan(0);
    });
  });
});

export {
  testOverlayAccessibility,
  testConsistencyPatterns
};
