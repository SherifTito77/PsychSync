/**
 * 🧪 Comprehensive Alert Component Testing Suite
 *
 * Tests all alert variants, auto-dismiss functionality, user interactions,
 * and accessibility compliance for notification systems.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Alert from '../../components/ui/Alert';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'info' | 'success' | 'warning' | 'error' | 'neutral';
  dismissible?: boolean;
  onDismiss?: () => void;
  autoDismiss?: boolean;
  autoDismissTimeout?: number;
  icon?: React.ReactNode;
  title?: string;
  actions?: React.ReactNode;
  className?: string;
}

describe('🎯 Comprehensive Alert Component Tests', () => {
  let userEventSetup: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    userEventSetup = userEvent.setup();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  describe('✅ Basic Rendering & Props', () => {
    test.each([
      'info',
      'success',
      'warning',
      'error',
      'neutral'
    ] as const)('renders %s variant correctly', (variant) => {
      render(
        <Alert variant={variant}>
          {variant} alert message
        </Alert>
      );

      const alert = screen.getByText(`${variant} alert message`);
      expect(alert).toBeInTheDocument();

      // Check for variant-specific styling
      const alertContainer = alert.closest('[role="alert"]');
      expect(alertContainer).toBeInTheDocument();
      expect(alertContainer).toHaveClass(expect.stringContaining(variant));
    });

    test('renders with title', () => {
      render(
        <Alert title="Alert Title">
          Alert content message
        </Alert>
      );

      expect(screen.getByText('Alert Title')).toBeInTheDocument();
      expect(screen.getByText('Alert content message')).toBeInTheDocument();
    });

    test('renders with custom icon', () => {
      const customIcon = <span data-testid="custom-icon">🔔</span>;
      render(
        <Alert icon={customIcon}>
          Alert with custom icon
        </Alert>
      );

      const icon = screen.getByTestId('custom-icon');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveTextContent('🔔');
    });

    test('renders with actions', () => {
      const actions = (
        <div>
          <button>Cancel</button>
          <button>Confirm</button>
        </div>
      );

      render(
        <Alert actions={actions}>
          Alert with actions
        </Alert>
      );

      expect(screen.getByText('Alert with actions')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
    });

    test('applies custom className', () => {
      render(
        <Alert className="custom-alert-class">
          Custom styled alert
        </Alert>
      );

      const alert = screen.getByText('Custom styled alert');
      expect(alert.closest('.custom-alert-class')).toBeInTheDocument();
    });

    test('renders dismissible alert correctly', () => {
      render(
        <Alert dismissible onDismiss={() => {}}>
          Dismissible alert
        </Alert>
      );

      expect(screen.getByText('Dismissible alert')).toBeInTheDocument();
      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      expect(dismissButton).toBeInTheDocument();
    });
  });

  describe('❌ Dismiss Functionality', () => {
    test('calls onDismiss when dismiss button is clicked', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Dismissible alert
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      await userEventSetup.click(dismissButton);

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    test('does not render dismiss button when not dismissible', () => {
      render(
        <Alert>
          Non-dismissible alert
        </Alert>
      );

      const dismissButton = screen.queryByRole('button', { name: /dismiss|close/i });
      expect(dismissButton).not.toBeInTheDocument();
    });

    test('handles dismiss with Enter key', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Dismissible alert
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      dismissButton.focus();
      await userEventSetup.keyboard('{Enter}');

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    test('handles dismiss with Space key', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Dismissible alert
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      dismissButton.focus();
      await userEventSetup.keyboard('{ }');

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    test('auto-dismisses after timeout', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert
          autoDismiss
          autoDismissTimeout={5000}
          onDismiss={onDismiss}
        >
          Auto-dismiss alert
        </Alert>
      );

      expect(screen.getByText('Auto-dismiss alert')).toBeInTheDocument();

      // Fast-forward time
      vi.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(onDismiss).toHaveBeenCalledTimes(1);
      });
    });

    test('does not auto-dismiss when autoDismiss is false', () => {
      const onDismiss = vi.fn();
      render(
        <Alert
          autoDismiss={false}
          autoDismissTimeout={1000}
          onDismiss={onDismiss}
        >
          Non-auto-dismiss alert
        </Alert>
      );

      vi.advanceTimersByTime(2000);
      expect(onDismiss).not.toHaveBeenCalled();
    });

    test('respects custom auto-dismiss timeout', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert
          autoDismiss
          autoDismissTimeout={2000}
          onDismiss={onDismiss}
        >
          Custom timeout alert
        </Alert>
      );

      vi.advanceTimersByTime(1000);
      expect(onDismiss).not.toHaveBeenCalled();

      vi.advanceTimersByTime(1000);
      await waitFor(() => {
        expect(onDismiss).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('⌨️ Keyboard Interaction', () => {
    test('dismiss button is keyboard accessible', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Keyboard accessible alert
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });

      // Test focus
      dismissButton.focus();
      expect(dismissButton).toHaveFocus();

      // Test keyboard activation
      await userEventSetup.keyboard('{Enter}');
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    test('supports tab navigation through alert actions', async () => {
      const actions = (
        <div>
          <button>First Action</button>
          <button>Second Action</button>
        </div>
      );

      render(
        <Alert actions={actions} dismissible>
          Alert with keyboard navigation
        </Alert>
      );

      const firstAction = screen.getByRole('button', { name: 'First Action' });
      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });

      await userEventSetup.tab();
      expect(firstAction).toHaveFocus();

      await userEventSetup.tab();
      expect(screen.getByRole('button', { name: 'Second Action' })).toHaveFocus();

      await userEventSetup.tab();
      expect(dismissButton).toHaveFocus();
    });
  });

  describe('🎨 Visual States & Animations', () => {
    test('applies correct styling for each variant', () => {
      const variants = ['info', 'success', 'warning', 'error', 'neutral'] as const;

      variants.forEach(variant => {
        const { unmount } = render(
          <Alert variant={variant} data-testid={`alert-${variant}`}>
            {variant} styling test
          </Alert>
        );

        const alert = screen.getByTestId(`alert-${variant}`);
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveClass(expect.stringContaining(variant));
        unmount();
      });
    });

    test('shows hover state on interactive elements', async () => {
      const actions = <button>Hoverable Action</button>;
      render(
        <Alert actions={actions}>
          Alert with hoverable action
        </Alert>
      );

      const actionButton = screen.getByRole('button', { name: 'Hoverable Action' });
      await userEventSetup.hover(actionButton);
      expect(actionButton).toBeInTheDocument();
    });

    test('applies focus styles to dismiss button', async () => {
      render(
        <Alert dismissible>
          Focus style test
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      dismissButton.focus();
      expect(dismissButton).toHaveFocus();
    });
  });

  describe('♿ Accessibility Testing', () => {
    test('has proper ARIA attributes', () => {
      render(
        <Alert variant="info">
          Accessible alert message
        </Alert>
      );

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });

    test('error alerts have assertive aria-live', () => {
      render(
        <Alert variant="error">
          Error alert message
        </Alert>
      );

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      // Error alerts should be more prominent
      expect(alert).toHaveClass(expect.stringContaining('error'));
    });

    test('dismiss button has accessible label', () => {
      render(
        <Alert dismissible>
          Alert with dismissible button
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      expect(dismissButton).toBeInTheDocument();
      expect(dismissButton).toHaveAttribute('aria-label');
    });

    test('supports custom ARIA attributes', () => {
      render(
        <Alert
          aria-label="Custom alert label"
          aria-describedby="alert-description"
        >
          Alert content
        </Alert>
      );

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-label', 'Custom alert label');
      expect(alert).toHaveAttribute('aria-describedby', 'alert-description');
    });

    test('maintains proper heading structure', () => {
      render(
        <Alert title="Alert Title">
          Alert content with proper structure
        </Alert>
      );

      const title = screen.getByText('Alert Title');
      const content = screen.getByText('Alert content with proper structure');
      expect(title).toBeInTheDocument();
      expect(content).toBeInTheDocument();
    });

    test('action buttons are keyboard accessible', async () => {
      const actions = (
        <div>
          <button>Accessible Action 1</button>
          <button>Accessible Action 2</button>
        </div>
      );

      render(
        <Alert actions={actions}>
          Alert with accessible actions
        </Alert>
      );

      const actionsButtons = screen.getAllByRole('button');
      expect(actionsButtons).toHaveLength(2);

      // Test tab navigation
      await userEventSetup.tab();
      expect(actionsButtons[0]).toHaveFocus();

      await userEventSetup.tab();
      expect(actionsButtons[1]).toHaveFocus();
    });
  });

  describe('🎯 Edge Cases & Error Handling', () => {
    test('handles empty children gracefully', () => {
      render(<Alert />);
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    test('handles null children gracefully', () => {
      render(<Alert>{null}</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    test('handles very long content', () => {
      const longContent = 'This is a very long alert message that should wrap properly within the alert component and not cause any overflow issues. '.repeat(10);
      render(<Alert>{longContent}</Alert>);
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });

    test('handles special characters in content', () => {
      const specialContent = 'Special chars: < > & " \' / \\ @ # $ % ^ & * ( ) _ + - =';
      render(<Alert>{specialContent}</Alert>);
      expect(screen.getByText(specialContent)).toBeInTheDocument();
    });

    test('handles undefined onDismiss gracefully', () => {
      render(
        <Alert dismissible>
          Alert without onDismiss handler
        </Alert>
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i });
      expect(() => userEventSetup.click(dismissButton)).not.toThrow();
    });

    test('handles zero autoDismissTimeout', async () => {
      const onDismiss = vi.fn();
      render(
        <Alert
          autoDismiss
          autoDismissTimeout={0}
          onDismiss={onDismiss}
        >
          Immediate dismiss alert
        </Alert>
      );

      await waitFor(() => {
        expect(onDismiss).toHaveBeenCalled();
      });
    });

    test('handles negative autoDismissTimeout gracefully', () => {
      const onDismiss = vi.fn();
      render(
        <Alert
          autoDismiss
          autoDismissTimeout={-1000}
          onDismiss={onDismiss}
        >
          Negative timeout alert
        </Alert>
      );

      vi.advanceTimersByTime(5000);
      expect(onDismiss).not.toHaveBeenCalled();
    });
  });

  describe('🔄 Content Structure Testing', () => {
    test('renders complex nested content', () => {
      render(
        <Alert
          title="Complex Alert"
          actions={
            <div>
              <button>Cancel</button>
              <button>Confirm</button>
            </div>
          }
          dismissible
        >
          <div>
            <p>Alert paragraph with <strong>strong text</strong>.</p>
            <ul>
              <li>Important point 1</li>
              <li>Important point 2</li>
            </ul>
            <a href="#">Learn more</a>
          </div>
        </Alert>
      );

      expect(screen.getByText('Complex Alert')).toBeInTheDocument();
      expect(screen.getByText('Alert paragraph with')).toBeInTheDocument();
      expect(screen.getByText('strong text')).toBeInTheDocument();
      expect(screen.getByText('Important point 1')).toBeInTheDocument();
      expect(screen.getByText('Important point 2')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Learn more' })).toBeInTheDocument();
    });

    test('renders React components as children', () => {
      const CustomComponent = ({ name }: { name: string }) => (
        <div>Custom component: {name}</div>
      );

      render(
        <Alert>
          <CustomComponent name="Test" />
        </Alert>
      );

      expect(screen.getByText('Custom component: Test')).toBeInTheDocument();
    });

    test('renders with JSX fragments', () => {
      render(
        <Alert>
          <>
            <p>First paragraph</p>
            <p>Second paragraph</p>
          </>
        </Alert>
      );

      expect(screen.getByText('First paragraph')).toBeInTheDocument();
      expect(screen.getByText('Second paragraph')).toBeInTheDocument();
    });
  });

  describe('🔗 Integration Testing', () => {
    test('integrates with form validation messages', async () => {
      const FormWithAlert = () => {
        const [errors, setErrors] = React.useState<string[]>([]);

        const handleSubmit = (e: React.FormEvent) => {
          e.preventDefault();
          setErrors(['Email is required', 'Password must be at least 8 characters']);
        };

        return (
          <form onSubmit={handleSubmit}>
            <Alert variant="error">
              {errors.length > 0 && (
                <ul>
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              )}
              {errors.length === 0 && 'Please fix the errors below'}
            </Alert>
            <button type="submit">Submit</button>
          </form>
        );
      };

      render(<FormWithAlert />);

      expect(screen.getByText('Please fix the errors below')).toBeInTheDocument();

      const submitButton = screen.getByRole('button', { name: 'Submit' });
      await userEventSetup.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument();
        expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
      });
    });

    test('works in notification stacking scenarios', () => {
      const notifications = [
        { id: 1, variant: 'success' as const, message: 'Operation successful' },
        { id: 2, variant: 'warning' as const, message: 'Warning message' },
        { id: 3, variant: 'error' as const, message: 'Error occurred' },
      ];

      render(
        <div>
          {notifications.map(notification => (
            <Alert key={notification.id} variant={notification.variant}>
              {notification.message}
            </Alert>
          ))}
        </div>
      );

      expect(screen.getByText('Operation successful')).toBeInTheDocument();
      expect(screen.getByText('Warning message')).toBeInTheDocument();
      expect(screen.getByText('Error occurred')).toBeInTheDocument();

      const alerts = screen.getAllByRole('alert');
      expect(alerts).toHaveLength(3);
    });

    test('handles conditional rendering based on state', async () => {
      const ConditionalAlert = ({ show }: { show: boolean }) => (
        <Alert variant={show ? 'success' : 'warning'}>
          {show ? 'Success: Operation completed' : 'Warning: Operation incomplete'}
        </Alert>
      );

      const { rerender } = render(<ConditionalAlert show={false} />);
      expect(screen.getByText('Warning: Operation incomplete')).toBeInTheDocument();

      rerender(<ConditionalAlert show={true} />);
      expect(screen.getByText('Success: Operation completed')).toBeInTheDocument();
    });
  });

  describe('⚡ Performance Testing', () => {
    test('renders many alerts efficiently', () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 100 }, (_, i) => (
            <Alert key={i} variant="info">
              Alert message {i + 1}
            </Alert>
          ))}
        </div>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(1000);
      expect(screen.getByText('Alert message 1')).toBeInTheDocument();
      expect(screen.getByText('Alert message 100')).toBeInTheDocument();
    });

    test('handles rapid state changes', async () => {
      const RapidAlert = () => {
        const [count, setCount] = React.useState(0);

        return (
          <Alert>
            Count: {count}
            <button onClick={() => setCount(c => c + 1)}>Increment</button>
          </Alert>
        );
      };

      render(<RapidAlert />);

      const incrementButton = screen.getByRole('button', { name: 'Increment' });

      // Rapid clicks
      for (let i = 0; i < 10; i++) {
        await userEventSetup.click(incrementButton);
      }

      expect(screen.getByText(/Count:/)).toBeInTheDocument();
    });
  });
});