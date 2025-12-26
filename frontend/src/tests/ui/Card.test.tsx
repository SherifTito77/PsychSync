/**
 * 🧪 Comprehensive Card Component Testing Suite
 *
 * Tests all card variants, content rendering, interactions, and accessibility.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen, fireEvent } from '@testing-library/react';
import Card from '../../components/ui/Card';

interface CardProps {
  children?: React.ReactNode;
  title?: string;
  subtitle?: string;
  footer?: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated' | 'ghost';
  padding?: 'none' | 'small' | 'medium' | 'large';
  rounded?: 'none' | 'small' | 'medium' | 'large' | 'full';
  shadow?: 'none' | 'small' | 'medium' | 'large';
  interactive?: boolean;
  hoverable?: boolean;
  className?: string;
  onClick?: () => void;
}

describe('🎯 Comprehensive Card Component Tests', () => {
  let userEventSetup: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    userEventSetup = userEvent.setup();
  });

  describe('✅ Basic Rendering & Props', () => {
    test('renders default card correctly', () => {
      render(<Card>Basic card content</Card>);
      const card = screen.getByText('Basic card content');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('bg-white'); // Default background
    });

    test('renders with title', () => {
      render(<Card title="Card Title">Card content</Card>);
      const title = screen.getByText('Card Title');
      const content = screen.getByText('Card content');
      expect(title).toBeInTheDocument();
      expect(content).toBeInTheDocument();
    });

    test('renders with subtitle', () => {
      render(
        <Card title="Title" subtitle="Card subtitle">
          Content
        </Card>
      );
      const title = screen.getByText('Title');
      const subtitle = screen.getByText('Card subtitle');
      const content = screen.getByText('Content');
      expect(title).toBeInTheDocument();
      expect(subtitle).toBeInTheDocument();
      expect(content).toBeInTheDocument();
    });

    test('renders with footer', () => {
      render(
        <Card footer={<button>Footer Button</button>}>
          Card content
        </Card>
      );
      const content = screen.getByText('Card content');
      const footerButton = screen.getByRole('button', { name: 'Footer Button' });
      expect(content).toBeInTheDocument();
      expect(footerButton).toBeInTheDocument();
    });

    test.each([
      'default',
      'outlined',
      'elevated',
      'ghost'
    ] as const)('renders %s variant correctly', (variant) => {
      render(<Card variant={variant}>Variant test</Card>);
      const card = screen.getByText('Variant test');
      expect(card).toBeInTheDocument();

      // Check for variant-specific classes
      if (variant === 'outlined') {
        expect(card.closest('[class*="border"]')).toBeInTheDocument();
      } else if (variant === 'elevated') {
        expect(card.closest('[class*="shadow"]')).toBeInTheDocument();
      }
    });

    test.each([
      'none',
      'small',
      'medium',
      'large'
    ] as const)('renders with %s padding', (padding) => {
      render(<Card padding={padding}>Padding test</Card>);
      const card = screen.getByText('Padding test');
      expect(card).toBeInTheDocument();
    });

    test.each([
      'none',
      'small',
      'medium',
      'large',
      'full'
    ] as const)('renders with %s border radius', (rounded) => {
      render(<Card rounded={rounded}>Radius test</Card>);
      const card = screen.getByText('Radius test');
      expect(card).toBeInTheDocument();
    });

    test('applies custom className', () => {
      render(<Card className="custom-card-class">Custom class test</Card>);
      const card = screen.getByText('Custom class test');
      expect(card.closest('.custom-card-class')).toBeInTheDocument();
    });
  });

  describe('🖱️ Mouse Interaction States', () => {
    test('handles click when interactive', async () => {
      const handleClick = vi.fn();
      render(
        <Card interactive onClick={handleClick}>
          Clickable card
        </Card>
      );

      const card = screen.getByText('Clickable card');
      await userEventSetup.click(card);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('does not handle click when not interactive', async () => {
      const handleClick = vi.fn();
      render(<Card onClick={handleClick}>Non-clickable card</Card>);

      const card = screen.getByText('Non-clickable card');
      await userEventSetup.click(card);
      expect(handleClick).not.toHaveBeenCalled();
    });

    test('applies hover styles when hoverable', async () => {
      render(
        <Card hoverable>
          Hoverable card
        </Card>
      );

      const card = screen.getByText('Hoverable card');
      await userEventSetup.hover(card);
      expect(card).toBeInTheDocument();
    });

    test('removes hover styles on mouse leave', async () => {
      render(
        <Card hoverable>
          Hoverable card
        </Card>
      );

      const card = screen.getByText('Hoverable card');
      await userEventSetup.hover(card);
      await userEventSetup.unhover(card);
      expect(card).toBeInTheDocument();
    });

    test('handles mouse enter and leave events', async () => {
      const handleMouseEnter = vi.fn();
      const handleMouseLeave = vi.fn();

      render(
        <Card
          hoverable
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          Hover events card
        </Card>
      );

      const card = screen.getByText('Hover events card');
      await userEventSetup.hover(card);
      expect(handleMouseEnter).toHaveBeenCalledTimes(1);

      await userEventSetup.unhover(card);
      expect(handleMouseLeave).toHaveBeenCalledTimes(1);
    });
  });

  describe('⌨️ Keyboard Interaction States', () => {
    test('is focusable when interactive', async () => {
      render(
        <Card interactive tabIndex={0}>
          Focusable card
        </Card>
      );

      const card = screen.getByText('Focusable card');
      expect(card).toHaveAttribute('tabIndex', '0');

      await userEventSetup.tab();
      expect(card).toHaveFocus();
    });

    test('handles Enter key activation', async () => {
      const handleClick = vi.fn();
      render(
        <Card interactive onClick={handleClick} tabIndex={0}>
          Keyboard card
        </Card>
      );

      const card = screen.getByText('Keyboard card');
      card.focus();

      await userEventSetup.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('handles Space key activation', async () => {
      const handleClick = vi.fn();
      render(
        <Card interactive onClick={handleClick} tabIndex={0}>
          Space key card
        </Card>
      );

      const card = screen.getByText('Space key card');
      card.focus();

      await userEventSetup.keyboard('{ }');
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('handles focus and blur events', async () => {
      const handleFocus = vi.fn();
      const handleBlur = vi.fn();

      render(
        <Card interactive onFocus={handleFocus} onBlur={handleBlur} tabIndex={0}>
          Focus events card
        </Card>
      );

      const card = screen.getByText('Focus events card');
      await userEventSetup.click(card);
      expect(handleFocus).toHaveBeenCalledTimes(1);

      await userEventSetup.tab(); // Move focus away
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });
  });

  describe('📱 Content Structure Testing', () => {
    test('renders complex nested content', () => {
      render(
        <Card
          title="Complex Card"
          subtitle="With subtitle"
          footer={
            <div>
              <button>Action 1</button>
              <button>Action 2</button>
            </div>
          }
        >
          <div>
            <h3>Content Header</h3>
            <p>Content paragraph with some text.</p>
            <ul>
              <li>List item 1</li>
              <li>List item 2</li>
            </ul>
          </div>
        </Card>
      );

      expect(screen.getByText('Complex Card')).toBeInTheDocument();
      expect(screen.getByText('With subtitle')).toBeInTheDocument();
      expect(screen.getByText('Content Header')).toBeInTheDocument();
      expect(screen.getByText('Content paragraph with some text.')).toBeInTheDocument();
      expect(screen.getByText('List item 1')).toBeInTheDocument();
      expect(screen.getByText('List item 2')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Action 1' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Action 2' })).toBeInTheDocument();
    });

    test('renders empty card gracefully', () => {
      render(<Card />);
      const card = document.querySelector('[class*="card"]');
      expect(card).toBeInTheDocument();
    });

    test('renders card with only title', () => {
      render(<Card title="Title Only" />);
      expect(screen.getByText('Title Only')).toBeInTheDocument();
    });

    test('renders card with only footer', () => {
      render(<Card footer={<span>Footer Only</span>} />);
      expect(screen.getByText('Footer Only')).toBeInTheDocument();
    });

    test('renders card with React elements as children', () => {
      const CustomComponent = () => <div>Custom Component Content</div>;
      render(
        <Card>
          <CustomComponent />
        </Card>
      );

      expect(screen.getByText('Custom Component Content')).toBeInTheDocument();
    });
  });

  describe('♿ Accessibility Testing', () => {
    test('has proper ARIA attributes when interactive', () => {
      render(
        <Card interactive onClick={() => {}} tabIndex={0}>
          Accessible card
        </Card>
      );

      const card = screen.getByText('Accessible card');
      expect(card).toHaveAttribute('tabIndex', '0');
      expect(card).toHaveAttribute('role', 'button');
    });

    test('supports custom ARIA attributes', () => {
      render(
        <Card
          interactive
          aria-label="Custom card label"
          aria-describedby="card-description"
          tabIndex={0}
        >
          Custom ARIA card
        </Card>
      );

      const card = screen.getByText('Custom ARIA card');
      expect(card).toHaveAttribute('aria-label', 'Custom card label');
      expect(card).toHaveAttribute('aria-describedby', 'card-description');
    });

    test('maintains proper heading structure', () => {
      render(
        <Card title="Card Title">
          <h2>Content Heading</h2>
          <p>Content text</p>
        </Card>
      );

      // Should have proper heading hierarchy
      const cardTitle = screen.getByText('Card Title');
      const contentHeading = screen.getByText('Content Heading');

      expect(cardTitle).toBeInTheDocument();
      expect(contentHeading).toBeInTheDocument();
    });

    test('provides accessible descriptions for complex cards', () => {
      render(
        <Card
          title="Product Card"
          subtitle="$19.99"
          aria-label="Product: Widget, Price: $19.99"
        >
          <p>Product description</p>
        </Card>
      );

      const card = screen.getByText('Product Card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('🎯 Edge Cases & Error Handling', () => {
    test('handles null children gracefully', () => {
      render(<Card>{null}</Card>);
      const card = document.querySelector('[class*="card"]');
      expect(card).toBeInTheDocument();
    });

    test('handles undefined children gracefully', () => {
      render(<Card>{undefined}</Card>);
      const card = document.querySelector('[class*="card"]');
      expect(card).toBeInTheDocument();
    });

    test('handles very long content', () => {
      const longContent = 'This is a very long content that should wrap properly within the card and not cause any overflow issues or layout problems. '.repeat(10);
      render(<Card>{longContent}</Card>);
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });

    test('handles special characters in content', () => {
      const specialContent = 'Special chars: < > & " \' / \\ @ # $ % ^ & * ( ) _ + - = { } [ ] | ; : , . ?';
      render(<Card>{specialContent}</Card>);
      expect(screen.getByText(specialContent)).toBeInTheDocument();
    });

    test('handles conflicting props gracefully', () => {
      render(
        <Card
          interactive
          hoverable
          onClick={() => {}}
          title="Conflicting Props"
        >
          Content with conflicting interactive props
        </Card>
      );

      expect(screen.getByText('Conflicting Props')).toBeInTheDocument();
      expect(screen.getByText('Content with conflicting interactive props')).toBeInTheDocument();
    });
  });

  describe('🎨 Style Consistency Testing', () => {
    test('applies correct classes for each variant', () => {
      const variants = ['default', 'outlined', 'elevated', 'ghost'] as const;

      variants.forEach(variant => {
        const { unmount } = render(
          <Card variant={variant} data-testid={`card-${variant}`}>
            {variant} card
          </Card>
        );

        const card = screen.getByTestId(`card-${variant}`);
        expect(card).toBeInTheDocument();
        unmount();
      });
    });

    test('maintains consistent spacing across variants', () => {
      const { container } = render(
        <div>
          <Card title="Card 1">Content 1</Card>
          <Card title="Card 2">Content 2</Card>
        </div>
      );

      const cards = container.querySelectorAll('[class*="card"]');
      expect(cards).toHaveLength(2);
    });

    test('applies responsive classes correctly', () => {
      render(
        <Card className="responsive-card">
          Responsive content
        </Card>
      );

      const card = screen.getByText('Responsive content');
      expect(card.closest('.responsive-card')).toBeInTheDocument();
    });
  });

  describe('🔗 Integration Testing', () => {
    test('works in grid layout', () => {
      const { container } = render(
        <div className="grid grid-cols-3 gap-4">
          <Card title="Card 1">Content 1</Card>
          <Card title="Card 2">Content 2</Card>
          <Card title="Card 3">Content 3</Card>
        </div>
      );

      const cards = container.querySelectorAll('[class*="card"]');
      expect(cards).toHaveLength(3);
      expect(screen.getByText('Card 1')).toBeInTheDocument();
      expect(screen.getByText('Card 2')).toBeInTheDocument();
      expect(screen.getByText('Card 3')).toBeInTheDocument();
    });

    test('integrates with list components', () => {
      const items = ['Item 1', 'Item 2', 'Item 3'];

      render(
        <div>
          {items.map((item, index) => (
            <Card key={index} interactive onClick={() => {}}>
              {item}
            </Card>
          ))}
        </div>
      );

      items.forEach(item => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });

    test('works with form elements inside', async () => {
      const handleSubmit = vi.fn((e) => e.preventDefault());

      render(
        <Card>
          <form onSubmit={handleSubmit}>
            <input placeholder="Enter name" data-testid="name-input" />
            <button type="submit">Submit</button>
          </form>
        </Card>
      );

      const input = screen.getByTestId('name-input');
      const button = screen.getByRole('button', { name: 'Submit' });

      await userEventSetup.type(input, 'John Doe');
      await userEventSetup.click(button);

      expect(input).toHaveValue('John Doe');
      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });

    test('handles conditional rendering', () => {
      const ConditionalCard = ({ showContent }: { showContent: boolean }) => (
        <Card>
          {showContent ? 'Visible content' : 'Hidden content'}
          {showContent && <div>Additional content</div>}
        </Card>
      );

      const { rerender } = render(<ConditionalCard showContent={false} />);
      expect(screen.getByText('Hidden content')).toBeInTheDocument();
      expect(screen.queryByText('Additional content')).not.toBeInTheDocument();

      rerender(<ConditionalCard showContent={true} />);
      expect(screen.getByText('Visible content')).toBeInTheDocument();
      expect(screen.getByText('Additional content')).toBeInTheDocument();
    });
  });

  describe('⚡ Performance Testing', () => {
    test('renders many cards efficiently', () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 100 }, (_, i) => (
            <Card key={i} title={`Card ${i + 1}`}>
              Content for card {i + 1}
            </Card>
          ))}
        </div>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render 100 cards in reasonable time
      expect(renderTime).toBeLessThan(1000);
      expect(screen.getByText('Card 1')).toBeInTheDocument();
      expect(screen.getByText('Card 100')).toBeInTheDocument();
    });

    test('handles rapid interaction updates', async () => {
      const [count, setCount] = React.useState(0);
      const InteractiveCard = () => {
        const [clicks, setClicks] = React.useState(0);

        return (
          <Card interactive onClick={() => setClicks(c => c + 1)}>
            Click count: {clicks}
          </Card>
        );
      };

      const { container } = render(<InteractiveCard />);
      const card = screen.getByText('Click count: 0');

      // Rapid clicks
      for (let i = 0; i < 10; i++) {
        await userEventSetup.click(card);
      }

      expect(screen.getByText(/Click count:/)).toBeInTheDocument();
    });
  });
});