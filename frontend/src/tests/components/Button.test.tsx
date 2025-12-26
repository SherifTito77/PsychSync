/**
 * 🧪 Comprehensive Button Component Test Suite
 *
 * Tests all button states, hover effects, disabled conditions, focus states,
 * click interactions, and accessibility compliance.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import Button from '../../components/common/Button';

const BUTTON_VARIANTS = ['primary', 'secondary', 'danger', 'default', 'outline', 'ghost', 'link'] as const;
const BUTTON_SIZES = ['small', 'medium', 'large', 'sm'] as const;

describe('🎯 Comprehensive Button Component Tests', () => {
  beforeEach(() => {
    // Reset DOM between tests
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
      } else if (variant === 'secondary') {
        expect(button).toHaveClass('bg-gray-200', 'text-gray-900');
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
      } else if (size === 'medium') {
        expect(button).toHaveClass('text-sm', 'px-4', 'py-2');
      }
    });

    it('renders with children content', () => {
      render(<Button>Test Button Content</Button>);
      expect(screen.getByText('Test Button Content')).toBeInTheDocument();
    });

    it('passes through additional props correctly', () => {
      render(
        <Button
          data-testid="custom-button"
          title="Custom tooltip"
          type="submit"
          name="test-button"
        >
          Custom Props
        </Button>
      );

      const button = screen.getByTestId('custom-button');
      expect(button).toHaveAttribute('title', 'Custom tooltip');
      expect(button).toHaveAttribute('type', 'submit');
      expect(button).toHaveAttribute('name', 'test-button');
    });
  });

  describe('🖱️ Mouse Interaction States', () => {
    it('handles hover state correctly', async () => {
      const user = userEvent.setup();
      render(<Button>Hover Test</Button>);
      const button = screen.getByRole('button', { name: 'Hover Test' });

      // Should have transition classes for hover
      expect(button).toHaveClass('transition-colors');

      // Hover state
      await user.hover(button);
      expect(button).toBeInTheDocument();

      // Verify hover class exists (though actual hover effect depends on CSS)
      expect(button).toHaveClass('hover:bg-blue-700');
    });

    it('handles mouse leave correctly', async () => {
      const user = userEvent.setup();
      render(<Button>Mouse Leave Test</Button>);
      const button = screen.getByRole('button', { name: 'Mouse Leave Test' });

      await user.hover(button);
      await user.unhover(button);

      expect(button).toBeInTheDocument();
      expect(button).toBeEnabled();
    });

    it('handles mouse down/up (active) state', async () => {
      const user = userEvent.setup();
      render(<Button>Active Test</Button>);
      const button = screen.getByRole('button', { name: 'Active Test' });

      await user.pointer([
        { keys: '[MouseLeft]', target: button },
        { keys: '[/MouseLeft]', target: button }
      ]);

      expect(button).toBeInTheDocument();
      expect(button).toBeEnabled();
    });
  });

  describe('⌨️ Keyboard Interaction States', () => {
    it('handles focus state correctly', async () => {
      const user = userEvent.setup();
      render(<Button>Focus Test</Button>);
      const button = screen.getByRole('button', { name: 'Focus Test' });

      await user.tab();
      expect(button).toHaveFocus();
      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2');
    });

    it('handles blur state correctly', async () => {
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

    it('handles Enter key activation', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Enter Test</Button>);
      const button = screen.getByRole('button', { name: 'Enter Test' });

      button.focus();
      await user.keyboard('{Enter}');

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles Space key activation', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Space Test</Button>);
      const button = screen.getByRole('button', { name: 'Space Test' });

      button.focus();
      await user.keyboard('{ }');

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('supports keyboard navigation between multiple buttons', async () => {
      const user = userEvent.setup();
      render(
        <>
          <Button>Button 1</Button>
          <Button>Button 2</Button>
          <Button>Button 3</Button>
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

  describe('🚫 Disabled State Testing', () => {
    it('disables button when disabled prop is true', () => {
      render(<Button disabled>Disabled Button</Button>);
      const button = screen.getByRole('button', { name: 'Disabled Button' });

      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
      expect(button).toHaveAttribute('disabled');
      expect(button).toHaveAttribute('aria-disabled', 'true');
      expect(button).toHaveAttribute('type', 'button');
    });

    it('disables button when loading prop is true', () => {
      render(<Button loading>Loading Button</Button>);
      const button = screen.getByRole('button', { name: 'Loading Button' });

      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('disabled');
      expect(button).toHaveAttribute('aria-disabled', 'true');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toHaveAttribute('type', 'button');
    });

    it('prevents click when disabled', async () => {
      const handleClick = vi.fn();
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

    it('prevents click when loading', async () => {
      const handleClick = vi.fn();
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

    it('prevents keyboard activation when disabled', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(
        <Button disabled onClick={handleClick}>
          Disabled Keyboard Test
        </Button>
      );

      // Try to focus with tab (should skip disabled button)
      await user.tab();

      // Try Enter and Space activation (should not work)
      await user.keyboard('{Enter}');
      await user.keyboard('{ }');

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('🔄 Click Event Testing', () => {
    it('calls onClick handler correctly', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Click Test</Button>);
      const button = screen.getByRole('button', { name: 'Click Test' });

      await user.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles multiple clicks', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Multi Click Test</Button>);
      const button = screen.getByRole('button', { name: 'Multi Click Test' });

      await user.dblClick(button);
      expect(handleClick).toHaveBeenCalledTimes(2);

      await user.tripleClick(button);
      expect(handleClick).toHaveBeenCalledTimes(5);
    });

    it('passes event object to onClick handler', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<Button onClick={handleClick}>Event Test</Button>);
      const button = screen.getByRole('button', { name: 'Event Test' });

      await user.click(button);
      expect(handleClick).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'click'
        })
      );
    });

    it('handles rapid clicking without errors', async () => {
      const handleClick = vi.fn();
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

  describe('🎨 Icon Integration Testing', () => {
    it('renders icon correctly', () => {
      const icon = <span data-testid="test-icon">🚀</span>;
      render(<Button icon={icon}>Icon Button</Button>);

      const button = screen.getByRole('button', { name: '🚀 Icon Button' });
      const iconElement = screen.getByTestId('test-icon');

      expect(button).toContainElement(iconElement);
      expect(iconElement).toHaveTextContent('🚀');
    });

    it('hides icon when loading', () => {
      const icon = <span data-testid="test-icon">🚀</span>;
      render(<Button loading icon={icon}>Loading Icon Button</Button>);

      const button = screen.getByRole('button', { name: 'Loading Icon Button' });
      const iconElement = screen.queryByTestId('test-icon');

      expect(button).toBeInTheDocument();
      expect(iconElement).not.toBeInTheDocument();
    });

    it('shows loading spinner when loading', () => {
      render(<Button loading>Loading Test</Button>);
      const button = screen.getByRole('button', { name: 'Loading Test' });

      // Check that loading spinner container exists
      expect(button.querySelector('.mr-2')).toBeInTheDocument();
    });

    it('does not show icon when loading', () => {
      const icon = <span data-testid="test-icon">🚀</span>;
      render(<Button loading icon={icon}>Loading with Icon</Button>);

      const button = screen.getByRole('button', { name: 'Loading with Icon' });

      // Should not have icon element
      expect(screen.queryByTestId('test-icon')).not.toBeInTheDocument();
      // Should have loading spinner
      expect(button.querySelector('.mr-2')).toBeInTheDocument();
    });
  });

  describe('♿ Accessibility Testing', () => {
    it('has proper ARIA attributes by default', () => {
      render(<Button>Accessible Button</Button>);
      const button = screen.getByRole('button', { name: 'Accessible Button' });

      expect(button).toHaveAttribute('type', 'button');
      expect(button).toHaveAttribute('aria-disabled', 'false');
      expect(button).toHaveAttribute('aria-busy', 'false');
      expect(button).not.toHaveAttribute('disabled');
    });

    it('has correct ARIA attributes when disabled', () => {
      render(<Button disabled>Disabled ARIA Test</Button>);
      const button = screen.getByRole('button', { name: 'Disabled ARIA Test' });

      expect(button).toHaveAttribute('disabled');
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    it('has correct ARIA attributes when loading', () => {
      render(<Button loading aria-label="Loading, please wait">Loading ARIA Test</Button>);
      const button = screen.getByRole('button', { name: 'Loading, please wait' });

      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('disabled');
      expect(button).toHaveAttribute('aria-label', 'Loading, please wait');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    it('supports custom ARIA attributes', () => {
      render(
        <Button
          aria-label="Custom label"
          aria-describedby="button-description"
          aria-expanded="false"
        >
          ARIA Button
        </Button>
      );

      const button = screen.getByRole('button', { name: 'Custom label' });
      expect(button).toHaveAttribute('aria-describedby', 'button-description');
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    it('maintains keyboard accessibility', async () => {
      const user = userEvent.setup();
      render(
        <>
          <Button>First</Button>
          <Button>Second</Button>
          <Button disabled>Third (Disabled)</Button>
          <Button>Fourth</Button>
        </>
      );

      const buttons = screen.getAllByRole('button');

      // Tab through all buttons (should skip disabled)
      await user.tab();
      expect(buttons[0]).toHaveFocus();

      await user.tab();
      expect(buttons[1]).toHaveFocus();

      await user.tab(); // Should skip disabled button
      expect(buttons[3]).toHaveFocus();
    });
  });

  describe('🎯 Edge Cases & Error Handling', () => {
    it('handles empty children gracefully', () => {
      render(<Button></Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toBeEmptyDOMElement();
    });

    it('handles null children gracefully', () => {
      render(<Button>{null}</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toBeEmptyDOMElement();
    });

    it('handles long text content', () => {
      const longText = 'This is a very long button text that should wrap properly and maintain button styling across multiple lines without breaking the layout or causing overflow issues';
      render(<Button>{longText}</Button>);
      const button = screen.getByRole('button', { name: longText });

      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent(longText);
    });

    it('handles special characters in text', () => {
      render(<Button>Button &lt;Test&gt; &amp; More</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Button <Test> & More');
    });

    it('handles additional className prop correctly', () => {
      render(
        <Button className="custom-class another-custom">
          Custom Class Button
        </Button>
      );
      const button = screen.getByRole('button', { name: 'Custom Class Button' });

      expect(button).toHaveClass('custom-class', 'another-custom');
      // Should also have default button classes
      expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
    });

    it('handles conflicting disabled and loading props', () => {
      render(
        <Button disabled loading>
          Conflicting Props
        </Button>
      );

      const button = screen.getByRole('button', { name: 'Conflicting Props' });
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toHaveAttribute('aria-disabled', 'true');
      // Loading should take precedence for visual state
    });
  });

  describe('🎨 Style Consistency Testing', () => {
    it('maintains consistent base classes across variants', () => {
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

    it('applies correct focus ring colors per variant', () => {
      const variantFocusColors = {
        primary: 'focus:ring-blue-500',
        secondary: 'focus:ring-gray-500',
        danger: 'focus:ring-red-500',
        default: 'focus:ring-gray-400',
        outline: 'focus:ring-gray-400',
        ghost: 'focus:ring-gray-400',
        link: 'focus:ring-blue-500' // Links often use blue focus
      };

      Object.entries(variantFocusColors).forEach(([variant, focusClass]) => {
        render(<Button variant={variant as any}>Focus Test {variant}</Button>);
        const button = screen.getByRole('button', { name: `Focus Test ${variant}` });

        expect(button).toHaveClass(focusClass);
      });
    });

    it('applies correct disabled state classes', () => {
      BUTTON_VARIANTS.forEach(variant => {
        render(<Button variant={variant} disabled>Disabled {variant}</Button>);
        const button = screen.getByRole('button', { name: `Disabled ${variant}` });

        expect(button).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
      });
    });
  });

  describe('🔗 Integration Testing', () => {
    it('integrates correctly with form submission', async () => {
      const handleSubmit = vi.fn((e) => e.preventDefault());
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

    it('works with conditional rendering', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<Button>Initial State</Button>);

      let button = screen.getByRole('button', { name: 'Initial State' });
      expect(button).toBeInTheDocument();

      // Rerender with different props
      rerender(<Button variant="danger">Updated State</Button>);
      button = screen.getByRole('button', { name: 'Updated State' });
      expect(button).toHaveClass('bg-red-600');

      // Rerender as disabled
      rerender(<Button disabled>Disabled State</Button>);
      button = screen.getByRole('button', { name: 'Disabled State' });
      expect(button).toBeDisabled();
    });
  });
});
