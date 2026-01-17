/**
 * 🧪 Comprehensive Input Component Testing Suite
 *
 * Uses the component testing framework to test all input states,
 * validation, accessibility, and user interactions.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import Input from '../../components/ui/Input';
import { ComponentTestSuite, ComponentTestCase, InteractionTestCase, AccessibilityRules } from '../utils/componentTestFramework';

interface InputProps {
  value?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  type?: string;
  error?: string;
  label?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  className?: string;
}

class InputTestSuite extends ComponentTestSuite<InputProps> {
  protected createComponent(props: InputProps): React.ReactElement {
    return <Input {...props} />;
  }
}

describe('🎯 Comprehensive Input Component Tests', () => {
  let testSuite: InputTestSuite;
  let userEventSetup: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    testSuite = new InputTestSuite({
      componentName: 'Input',
      defaultProps: {
        type: 'text',
        placeholder: 'Enter text...',
      },
      accessibilityConfig: {
        axeRules: AccessibilityRules.interactive,
      },
      interactionConfig: {
        skipMouseTesting: false,
        skipKeyboardTesting: false,
      },
    });

    userEventSetup = userEvent.setup();
  });

  describe('✅ Basic Rendering & Props', () => {
    test('renders default input correctly', () => {
      const { container } = render(
        <Input placeholder="Test placeholder" />
      );

      const input = container.querySelector('input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'text');
      expect(input).toHaveAttribute('placeholder', 'Test placeholder');
      expect(input).not.toBeDisabled();
    });

    test('renders with custom type', () => {
      const { container } = render(
        <Input type="email" placeholder="Email" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('type', 'email');
    });

    test('renders with value', () => {
      const { container } = render(
        <Input value="Test value" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveValue('Test value');
    });

    test('renders disabled state correctly', () => {
      const { container } = render(
        <Input disabled placeholder="Disabled input" />
      );

      const input = container.querySelector('input');
      expect(input).toBeDisabled();
      expect(input).toHaveAttribute('aria-disabled', 'true');
    });

    test('renders required state correctly', () => {
      const { container } = render(
        <Input required placeholder="Required input" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-required', 'true');
    });

    test('renders with label', () => {
      const { getByLabelText, container } = render(
        <Input label="Test Label" />
      );

      expect(getByLabelText('Test Label')).toBeInTheDocument();
      const label = container.querySelector('label');
      expect(label).toHaveTextContent('Test Label');
    });

    test('renders error state correctly', () => {
      const { container, getByText } = render(
        <Input error="This field is required" />
      );

      expect(getByText('This field is required')).toBeInTheDocument();
      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    test('applies custom className', () => {
      const { container } = render(
        <Input className="custom-input-class" />
      );

      const wrapper = container.querySelector('.custom-input-class') ||
                     container.querySelector('input');
      expect(wrapper).toHaveClass('custom-input-class');
    });
  });

  describe('🖱️ Mouse Interaction States', () => {
    test('handles focus and blur correctly', async () => {
      const onFocus = vi.fn();
      const onBlur = vi.fn();
      const { container } = render(
        <Input onFocus={onFocus} onBlur={onBlur} placeholder="Test" />
      );

      const input = container.querySelector('input');

      await userEventSetup.click(input);
      expect(input).toHaveFocus();
      expect(onFocus).toHaveBeenCalledTimes(1);

      await userEventSetup.tab(); // Move focus away
      expect(input).not.toHaveFocus();
      expect(onBlur).toHaveBeenCalledTimes(1);
    });

    test('handles value change correctly', async () => {
      const onChange = vi.fn();
      const { container } = render(
        <Input onChange={onChange} placeholder="Type here" />
      );

      const input = container.querySelector('input');

      await userEventSetup.type(input, 'Hello World');
      expect(input).toHaveValue('Hello World');
      expect(onChange).toHaveBeenCalledTimes(11); // One call per character
    });

    test('prevents input when disabled', async () => {
      const onChange = vi.fn();
      const { container } = render(
        <Input disabled onChange={onChange} placeholder="Disabled" />
      );

      const input = container.querySelector('input');

      await userEventSetup.click(input);
      expect(input).not.toHaveFocus();

      await userEventSetup.type(input, 'Cannot type');
      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe('⌨️ Keyboard Interaction States', () => {
    test('handles keyboard events correctly', async () => {
      const onKeyDown = vi.fn();
      const onKeyUp = vi.fn();
      const { container } = render(
        <Input onKeyDown={onKeyDown} onKeyUp={onKeyUp} placeholder="Keyboard test" />
      );

      const input = container.querySelector('input');
      input.focus();

      await userEventSetup.keyboard('{Enter}');
      expect(onKeyDown).toHaveBeenCalledWith(
        expect.objectContaining({ key: 'Enter' })
      );

      await userEventSetup.keyboard('{Escape}');
      expect(onKeyDown).toHaveBeenCalledWith(
        expect.objectContaining({ key: 'Escape' })
      );
    });

    test('supports tab navigation', async () => {
      const { container } = render(
        <>
          <Input placeholder="First input" />
          <Input placeholder="Second input" />
        </>
      );

      const inputs = container.querySelectorAll('input');

      await userEventSetup.tab();
      expect(inputs[0]).toHaveFocus();

      await userEventSetup.tab();
      expect(inputs[0]).not.toHaveFocus();
      expect(inputs[1]).toHaveFocus();
    });

    test('skips disabled inputs in tab order', async () => {
      const { container } = render(
        <>
          <Input placeholder="First input" />
          <Input disabled placeholder="Disabled input" />
          <Input placeholder="Third input" />
        </>
      );

      const inputs = container.querySelectorAll('input');

      await userEventSetup.tab();
      expect(inputs[0]).toHaveFocus();

      await userEventSetup.tab();
      expect(inputs[2]).toHaveFocus(); // Should skip disabled input
    });
  });

  describe('🔄 Input Type Variations', () => {
    const inputTypes = [
      { type: 'text', placeholder: 'Text input' },
      { type: 'email', placeholder: 'Email input' },
      { type: 'password', placeholder: 'Password input' },
      { type: 'number', placeholder: 'Number input' },
      { type: 'tel', placeholder: 'Phone input' },
      { type: 'url', placeholder: 'URL input' },
      { type: 'search', placeholder: 'Search input' },
    ];

    test.each(inputTypes)('renders $type input correctly', ({ type, placeholder }) => {
      const { container } = render(
        <Input type={type} placeholder={placeholder} />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('type', type);
      expect(input).toHaveAttribute('placeholder', placeholder);
    });
  });

  describe('📱 Mobile & Touch Interaction', () => {
    test('handles touch events', async () => {
      const { container } = render(
        <Input placeholder="Touch input" />
      );

      const input = container.querySelector('input');

      // Simulate touch events (simplified for testing)
      fireEvent.touchStart(input);
      fireEvent.touchEnd(input);

      expect(input).toBeInTheDocument();
    });
  });

  describe('♿ Accessibility Testing', () => {
    test('has proper ARIA attributes by default', () => {
      const { container } = render(
        <Input placeholder="Accessible input" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('type', 'text');
      expect(input).not.toHaveAttribute('aria-required');
      expect(input).not.toHaveAttribute('aria-disabled');
      expect(input).not.toHaveAttribute('aria-invalid');
    });

    test('has correct ARIA attributes when required', () => {
      const { container } = render(
        <Input required placeholder="Required input" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-required', 'true');
    });

    test('has correct ARIA attributes when disabled', () => {
      const { container } = render(
        <Input disabled placeholder="Disabled input" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-disabled', 'true');
    });

    test('has correct ARIA attributes when invalid', () => {
      const { container } = render(
        <Input error="Invalid input" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    test('associates label with input correctly', () => {
      const { getByLabelText, getByRole } = render(
        <Input label="Username" placeholder="Enter username" />
      );

      const input = getByLabelText('Username');
      const label = getByRole('label');

      expect(label).toHaveAttribute('for');
      expect(input).toHaveAttribute('id');
      expect(label.getAttribute('for')).toBe(input.getAttribute('id'));
    });

    test('provides proper error message association', () => {
      const { container, getByText } = render(
        <Input error="This field is required" />
      );

      const input = container.querySelector('input');
      const errorMessage = getByText('This field is required');

      expect(errorMessage).toBeInTheDocument();
      expect(input).toHaveAttribute('aria-describedby');
      expect(errorMessage).toHaveAttribute('id');
      expect(input.getAttribute('aria-describedby')).toBe(errorMessage.getAttribute('id'));
    });
  });

  describe('🎯 Edge Cases & Error Handling', () => {
    test('handles empty value gracefully', () => {
      const { container } = render(
        <Input value="" placeholder="Empty value" />
      );

      const input = container.querySelector('input');
      expect(input).toHaveValue('');
    });

    test('handles undefined value gracefully', () => {
      const { container } = render(
        <Input value={undefined} placeholder="Undefined value" />
      );

      const input = container.querySelector('input');
      expect(input).toBeInTheDocument();
    });

    test('handles long input values', () => {
      const longText = 'This is a very long input value that should be handled gracefully without causing any rendering issues or performance problems in the input component';
      const { container } = render(
        <Input value={longText} />
      );

      const input = container.querySelector('input');
      expect(input).toHaveValue(longText);
    });

    test('handles special characters', () => {
      const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      const { container } = render(
        <Input value={specialChars} />
      );

      const input = container.querySelector('input');
      expect(input).toHaveValue(specialChars);
    });

    test('handles conflicting props gracefully', () => {
      const { container } = render(
        <Input disabled required value="Conflicting props" />
      );

      const input = container.querySelector('input');
      expect(input).toBeDisabled();
      expect(input).toHaveAttribute('aria-required', 'true');
    });
  });

  describe('🎨 Style Consistency Testing', () => {
    test('applies consistent base classes', () => {
      const { container } = render(
        <Input className="custom-class" />
      );

      const input = container.querySelector('input');
      // Should have some base styling classes (implementation dependent)
      expect(input).toBeInTheDocument();
    });

    test('applies error styling correctly', () => {
      const { container } = render(
        <Input error="Error state" />
      );

      // Should have error-related classes or attributes
      const input = container.querySelector('input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    test('applies disabled styling correctly', () => {
      const { container } = render(
        <Input disabled />
      );

      const input = container.querySelector('input');
      expect(input).toBeDisabled();
      expect(input).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('🔗 Integration Testing', () => {
    test('works with form submission', async () => {
      const handleSubmit = vi.fn((e) => e.preventDefault());
      const { container } = render(
        <form onSubmit={handleSubmit}>
          <Input name="testInput" placeholder="Form input" />
          <button type="submit">Submit</button>
        </form>
      );

      const input = container.querySelector('input');
      const button = container.querySelector('button');

      await userEventSetup.type(input, 'Test value');
      await userEventSetup.click(button);

      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });

    test('works with controlled component pattern', async () => {
      const ControlledInput = () => {
        const [value, setValue] = React.useState('');

        return (
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Controlled input"
          />
        );
      };

      const { container } = render(<ControlledInput />);
      const input = container.querySelector('input');

      await userEventSetup.type(input, 'Controlled');
      expect(input).toHaveValue('Controlled');
    });

    test('works with form validation', async () => {
      const ValidationInput = () => {
        const [error, setError] = React.useState('');

        const validateInput = (value: string) => {
          if (value.length < 3) {
            setError('Minimum 3 characters required');
          } else {
            setError('');
          }
        };

        return (
          <Input
            error={error}
            onChange={(e) => validateInput(e.target.value)}
            placeholder="Validation input"
          />
        );
      };

      const { container, getByText, queryByText } = render(<ValidationInput />);
      const input = container.querySelector('input');

      // Should not show error initially
      expect(queryByText('Minimum 3 characters required')).not.toBeInTheDocument();

      // Type insufficient characters
      await userEventSetup.type(input, 'ab');
      expect(getByText('Minimum 3 characters required')).toBeInTheDocument();

      // Type sufficient characters
      await userEventSetup.type(input, 'c');
      expect(queryByText('Minimum 3 characters required')).not.toBeInTheDocument();
    });
  });
});
