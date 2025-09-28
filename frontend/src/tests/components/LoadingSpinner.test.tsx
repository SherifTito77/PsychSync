
// src/tests/components/LoadingSpinner.test.tsx
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LoadingSpinner from '../../components/LoadingSpinner';

describe('LoadingSpinner Component', () => {
  it('renders with default props', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner).toHaveClass('animate-spin', 'h-8', 'w-8');
  });

  it('renders with small size', () => {
    const { container } = render(<LoadingSpinner size="small" />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner).toHaveClass('h-4', 'w-4');
  });

  it('renders with large size', () => {
    const { container } = render(<LoadingSpinner size="large" />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner).toHaveClass('h-12', 'w-12');
  });
});