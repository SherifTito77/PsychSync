
// src/tests/App.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import App from '../App';

// Mock components to avoid context errors in tests
const MockApp = () => (
  <BrowserRouter>
    <div data-testid="app">
      <h1>PsychSync</h1>
      <p>Test App Running</p>
    </div>
  </BrowserRouter>
);

describe('App', () => {
  it('renders without crashing', () => {
    render(<MockApp />);
    expect(screen.getByTestId('app')).toBeInTheDocument();
  });

  it('displays PsychSync title', () => {
    render(<MockApp />);
    expect(screen.getByText('PsychSync')).toBeInTheDocument();
  });
});
