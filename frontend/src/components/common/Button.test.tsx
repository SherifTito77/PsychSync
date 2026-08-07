import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '@/components/common/Button';

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies variant styles correctly', () => {
    render(<Button variant="primary">Primary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600');
  });

  it('is accessible', () => {
    render(<Button aria-label="Submit form">Submit</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Submit form');
  });
});
