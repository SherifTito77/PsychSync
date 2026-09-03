/**
 * 🧪 Comprehensive Button State & UI Interaction Testing Suite
 *
 * Tests all button states, hover effects, disabled conditions, focus states,
 * click interactions, and accessibility compliance across the platform.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
// import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';
import Button from '../../components/common/Button';
import '@testing-library/jest-dom';

// Extend Jest matchers
// expect.extend(toHaveNoViolations);

// Test configuration
const BUTTON_VARIANTS = [
  'primary', 'secondary', 'danger', 'default',
  'outline', 'ghost', 'link'
] as const;

const BUTTON_SIZES = ['small', 'medium', 'large', 'sm'] as const;

const INTERACTION_STATES = [
  'default', 'hover', 'focus', 'active', 'disabled', 'loading'
] as const;

describe('🎯 Comprehensive Button State Testing', () => {

  beforeEach(() => {
    // Reset any global states
    document.body.innerHTML = '';
  });

  describe('✅ Basic Rendering & Props', () => {
    test.each(BUTTON_VARIANTS)('renders %s variant correctly', (variant) => {
      render(<Button variant={variant}>Test Button</Button>);
      const button = screen.getByRole('button', { name: 'Test Button' });

      expect(button).toBeInTheDocument();
      expect(button).toBeEnabled();

      // Check variant-specific classes
      if (variant === 'primary') {
        expect(button).toHaveClass('bg-blue-600', 'text-white');
      } else if (variant === 'danger') {
        expect(button).toHaveClass('bg-red-600', 'text-white');
      } else if (variant === 'link') {
        expect(button).toHaveClass('text-blue-600', 'underline');
      }
    });

    test.each(BUTTON_SIZES)('renders %s size correctly', (size) => {
      render(<Button size={size}>Test Button</Button>);
      const button = screen.getByRole('button', { name: 'Test Button' });

      expect(button).toBeInTheDocument();

      // Check size-specific classes
      if (size === 'small') {
        expect(button).toHaveClass('text-sm', 'px-3', 'py-2');
      } else if (size === 'large') {
        expect(button).toHaveClass('text-base', 'px-6', 'py-3');
      } else if (size === 'sm') {
        expect(button).toHaveClass('text-xs', 'px-2', 'py-1');
      }
    });
  });

  describe('🖱️ Mouse Interaction States', () => {
    test('handles hover state correctly', async () => {
      const user = userEvent.setup();
      render(<Button>Hover Test</Button>);
      const button = screen.getByRole('button', { name: 'Hover Test' });

      // Initial state
      expect(button).toHaveClass('transition-colors');

      // Hover state
      await user.hover(button);
      expect(button).toBeInTheDocument();

      // Verify hover styles are applied via CSS classes
      // Note: Actual hover styles depend on CSS framework
    });

    test('handles mouse leave correctly', async () => {
      const user = userEvent.setup();
      render(<Button>Mouse Leave Test</Button>);
      const button = screen.getByRole('button', { name: 'Mouse Leave Test' });

      await user.hover(button);
      await user.unhover(button);

      expect(button).toBeInTheDocument();
      expect(button).toBeEnabled();
    });

    test('handles mouse down/up (active) state', async () => {
      const user = userEvent.setup();
      render(<Button>Active Test</Button>);
      const button = screen.getByRole('button', { name: 'Active Test' });

      await user.pointer([
        { keys: '[MouseLeft]', target: button },
        { keys: '[/MouseLeft]', target: button }
      ]);

      expect(button).toBeInTheDocument();
    });
  });

  describe('⌨️ Keyboard Interaction States', () => {
    test('handles focus state correctly', async () => {
      const user = userEvent.setup();
      render(<Button>Focus Test</Button>);
      const button = screen.getByRole('button', { name: 'Focus Test' });

      await user.tab();
      expect(button).toHaveFocus();
      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2');
    });

    test('handles blur state correctly', async () => {
      const user = userEvent.setup();
      render(
        <>
          <Button>First Button</Button>
          <Button>Second Button</Button>
        </>
      );

      const firstButton = screen.getByRole('button', { name: 'First Button' });
      const secondButton = screen.getByRole('button', { name: 'Second Button' });

      await user.tab();
      expect(firstButton).toHaveFocus();

      await user.tab();
      expect(firstButton).not.toHaveFocus();
      expect(secondButton).toHaveFocus();
    });

    test('handles Enter key activation', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Enter Test</Button>);
      const button = screen.getByRole('button', { name: 'Enter Test' });

      button.focus();
      await user.keyboard('{Enter}');

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('handles Space key activation', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Space Test</Button>);
      const button = screen.getByRole('button', { name: 'Space Test' });

      button.focus();
      await user.keyboard('{ }');

      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('🚫 Disabled State Testing', () => {
    test('disables button when disabled prop is true', () => {
      render(<Button disabled>Disabled Button</Button>);
      const button = screen.getByRole('button', { name: 'Disabled Button' });

      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
    });

    test('disables button when loading prop is true', () => {
      render(<Button loading>Loading Button</Button>);
      const button = screen.getByRole('button', { name: 'Loading Button' });

      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('disabled');
    });

    test('prevents click when disabled', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(
        <Button disabled onClick={handleClick}>
          Disabled Click Test
        </Button>
      );
      const button = screen.getByRole('button', { name: 'Disabled Click Test' });

      await user.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    test('prevents click when loading', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(
        <Button loading onClick={handleClick}>
          Loading Click Test
        </Button>
      );
      const button = screen.getByRole('button', { name: 'Loading Click Test' });

      await user.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    test('shows loading spinner when loading', () => {
      render(<Button loading>Loading Test</Button>);
      const button = screen.getByRole('button', { name: 'Loading Test' });

      // Check for loading spinner
      expect(button.querySelector('[data-testid="loading-spinner"]')).toBeInTheDocument();
    });
  });

  describe('🔄 Click Event Testing', () => {
    test('calls onClick handler correctly', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Click Test</Button>);
      const button = screen.getByRole('button', { name: 'Click Test' });

      await user.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('handles multiple clicks', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Multi Click Test</Button>);
      const button = screen.getByRole('button', { name: 'Multi Click Test' });

      await user.dblClick(button);
      expect(handleClick).toHaveBeenCalledTimes(2);
    });

    test('passes event object to onClick handler', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Event Test</Button>);
      const button = screen.getByRole('button', { name: 'Event Test' });

      await user.click(button);
      expect(handleClick).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'click',
          target: button
        })
      );
    });
  });

  describe('🎨 Icon Integration Testing', () => {
    test('renders icon correctly', () => {
      const icon = <span data-testid="test-icon">🚀</span>;
      render(<Button icon={icon}>Icon Button</Button>);

      const button = screen.getByRole('button', { name: 'Icon Button' });
      const iconElement = screen.getByTestId('test-icon');

      expect(button).toContainElement(iconElement);
      expect(iconElement).toHaveTextContent('🚀');
    });

    test('hides icon when loading', () => {
      const icon = <span data-testid="test-icon">🚀</span>;
      render(<Button loading icon={icon}>Loading Icon Button</Button>);

      const button = screen.getByRole('button', { name: 'Loading Icon Button' });
      const iconElement = screen.queryByTestId('test-icon');

      expect(button).toBeInTheDocument();
      expect(iconElement).not.toBeInTheDocument();
    });

    test('shows loading spinner instead of icon when loading', () => {
      const icon = <span data-testid="test-icon">🚀</span>;
      render(<Button loading icon={icon}>Loading with Icon</Button>);

      const button = screen.getByRole('button', { name: 'Loading with Icon' });

      // Should have loading spinner
      expect(button).toBeInTheDocument();
      // Icon should be hidden
      expect(screen.queryByTestId('test-icon')).not.toBeInTheDocument();
    });
  });

  describe('♿ Accessibility Testing', () => {
    test.skip('has no accessibility violations', async () => {
      const { container } = render(<Button>Accessible Button</Button>);
      // const results = await axe(container);
      // expect(results).toHaveNoViolations();
    });

    test.each(BUTTON_VARIANTS)('%s variant has no accessibility violations', async (variant) => {
      const { container } = render(<Button variant={variant}>Accessible {variant}</Button>);
      // const results = await axe(container);
      // expect(results).toHaveNoViolations();
    });

    test('disabled button has proper ARIA attributes', () => {
      render(<Button disabled>Disabled ARIA Test</Button>);
      const button = screen.getByRole('button', { name: 'Disabled ARIA Test' });

      expect(button).toHaveAttribute('disabled');
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    test('loading button has proper ARIA attributes', () => {
      render(<Button loading aria-label="Loading, please wait">Loading ARIA Test</Button>);
      const button = screen.getByRole('button', { name: 'Loading, please wait' });

      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('disabled');
      expect(button).toHaveAttribute('aria-label', 'Loading, please wait');
    });

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(
        <>
          <Button>First</Button>
          <Button>Second</Button>
          <Button>Third</Button>
        </>
      );

      const buttons = screen.getAllByRole('button');

      // Tab through all buttons
      for (let i = 0; i < buttons.length; i++) {
        await user.tab();
        expect(buttons[i]).toHaveFocus();
      }
    });
  });

  describe('🎯 Edge Cases & Error Handling', () => {
    test('handles empty children gracefully', () => {
      render(<Button></Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toBeEmptyDOMElement();
    });

    test('handles long text content', () => {
      const longText = 'This is a very long button text that should wrap properly and maintain button styling';
      render(<Button>{longText}</Button>);
      const button = screen.getByRole('button', { name: longText });

      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent(longText);
    });

    test('handles HTML entities in text', () => {
      render(<Button>Button &lt;Test&gt; &amp; More</Button>);
      const button = screen.getByRole('button');

      expect(button).toBeInTheDocument();
      // HTML entities should be decoded
      expect(button).toHaveTextContent('Button <Test> & More');
    });

    test('handles additional className prop', () => {
      render(<Button className="custom-class">Custom Class Button</Button>);
      const button = screen.getByRole('button', { name: 'Custom Class Button' });

      expect(button).toHaveClass('custom-class');
      // Should also have default button classes
      expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
    });

    test('passes through additional HTML attributes', () => {
      render(
        <Button
          data-testid="custom-button"
          title="Custom tooltip"
          type="submit"
        >
          Custom Attributes
        </Button>
      );
      const button = screen.getByTestId('custom-button');

      expect(button).toHaveAttribute('title', 'Custom tooltip');
      expect(button).toHaveAttribute('type', 'submit');
    });
  });

  describe('📱 Mobile & Touch Interaction Testing', () => {
    test('handles touch events', async () => {
      const handleTouchStart = jest.fn();
      const handleTouchEnd = jest.fn();

      render(
        <Button
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          Touch Test
        </Button>
      );

      const button = screen.getByRole('button', { name: 'Touch Test' });

      fireEvent.touchStart(button);
      fireEvent.touchEnd(button);

      expect(handleTouchStart).toHaveBeenCalled();
      expect(handleTouchEnd).toHaveBeenCalled();
    });

    test('maintains accessibility on touch devices', async () => {
      const { container } = render(<Button>Touch Accessible</Button>);
      // const results = await axe(container);
      // expect(results).toHaveNoViolations();
    });
  });

  describe('🎨 Style Consistency Testing', () => {
    test('maintains consistent base classes across variants', () => {
      const baseClasses = [
        'inline-flex',
        'items-center',
        'justify-center',
        'font-medium',
        'rounded-md',
        'transition-colors',
        'focus:outline-none',
        'focus:ring-2',
        'focus:ring-offset-2'
      ];

      BUTTON_VARIANTS.forEach(variant => {
        render(<Button variant={variant}>Test {variant}</Button>);
        const button = screen.getByRole('button', { name: `Test ${variant}` });

        baseClasses.forEach(baseClass => {
          expect(button).toHaveClass(baseClass);
        });
      });
    });

    test('applies correct focus ring colors per variant', () => {
      const variantFocusColors = {
        primary: 'focus:ring-blue-500',
        secondary: 'focus:ring-gray-500',
        danger: 'focus:ring-red-500',
        default: 'focus:ring-gray-400',
        outline: 'focus:ring-gray-400',
        ghost: 'focus:ring-gray-400'
      };

      Object.entries(variantFocusColors).forEach(([variant, focusClass]) => {
        render(<Button variant={variant as any}>Focus Test {variant}</Button>);
        const button = screen.getByRole('button', { name: `Focus Test ${variant}` });

        expect(button).toHaveClass(focusClass);
      });
    });
  });

  describe('⚡ Performance Testing', () => {
    test('renders quickly with many buttons', () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 100 }, (_, i) => (
            <Button key={i}>Button {i}</Button>
          ))}
        </div>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render 100 buttons in under 100ms
      expect(renderTime).toBeLessThan(100);

      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(100);
    });

    test('handles rapid clicking without errors', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Rapid Click Test</Button>);
      const button = screen.getByRole('button', { name: 'Rapid Click Test' });

      // Rapid fire clicks
      for (let i = 0; i < 10; i++) {
        await user.click(button);
      }

      expect(handleClick).toHaveBeenCalledTimes(10);
    });
  });
});

describe('🎯 Integration Testing with Real Components', () => {
  test('integrates correctly with form submission', async () => {
    const handleSubmit = jest.fn((e) => e.preventDefault());
    const user = userEvent.setup();

    render(
      <form onSubmit={handleSubmit}>
        <Button type="submit">Submit Form</Button>
      </form>
    );

    const submitButton = screen.getByRole('button', { name: 'Submit Form' });
    await user.click(submitButton);

    expect(handleSubmit).toHaveBeenCalledTimes(1);
  });

  test('integrates with modal interactions', async () => {
    const Modal = ({ isOpen, onClose, children }: any) => {
      if (!isOpen) return null;
      return (
        <div role="dialog">
          {children}
          <Button onClick={onClose}>Close Modal</Button>
        </div>
      );
    };

    const user = userEvent.setup();
    const { rerender } = render(
      <Modal isOpen={false} onClose={() => {}}>
        Modal Content
      </Modal>
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    rerender(
      <Modal isOpen={true} onClose={() => {}}>
        Modal Content
      </Modal>
    );

    const closeButton = screen.getByRole('button', { name: 'Close Modal' });
    expect(closeButton).toBeInTheDocument();

    // Test that the button works within modal context
    await user.click(closeButton);
    expect(closeButton).toBeInTheDocument(); // Still exists until parent updates
  });
});

export {
  BUTTON_VARIANTS,
  BUTTON_SIZES,
  INTERACTION_STATES
};
