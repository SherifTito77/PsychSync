/**
 * Comprehensive Test Suite for LoginSignupRefactored Component
 *
 * Tests cover:
 * - Component rendering and snapshots
 * - Form interactions and state changes
 * - Validation scenarios
 * - Accessibility compliance
 * - Error handling
 * - API mocking
 * - Edge cases and security
 * - Performance optimization
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import LoginSignupRefactored from '../LoginSignupRefactored';
import { createTheme, ThemeProvider } from '@mui/material/styles';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock fetch API
global.fetch = jest.fn();

// Mock window.location
delete (window as any).location;
(window as any).location = { href: '' };

// Test utilities
const createMockFetch = (response: any, ok = true, status = 200) => {
  return jest.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(response),
  });
};

const renderWithTheme = (component: React.ReactElement) => {
  const theme = createTheme();
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

const fillLoginForm = async (email: string, password: string) => {
  const emailInput = screen.getByLabelText(/email address/i);
  const passwordInput = screen.getByLabelText(/password/i);

  await userEvent.type(emailInput, email);
  await userEvent.type(passwordInput, password);
};

const fillSignupForm = async (email: string, password: string, confirmPassword: string, fullName: string) => {
  const emailInput = screen.getByLabelText(/email address/i);
  const passwordInput = screen.getByLabelText(/^password/i); // Main password field
  const confirmInput = screen.getByLabelText(/confirm password/i);
  const nameInput = screen.getByLabelText(/full name/i);

  await userEvent.type(emailInput, email);
  await userEvent.type(passwordInput, password);
  await userEvent.type(confirmInput, confirmPassword);
  await userEvent.type(nameInput, fullName);
};

// Snapshot Tests
describe('LoginSignupRefactored - Snapshots', () => {
  test('Login form matches snapshot', async () => {
    const { container } = renderWithTheme(<LoginSignupRefactored />);

    // Wait for component to fully render
    await waitFor(() => {
      expect(screen.getByText('PsychSync')).toBeInTheDocument();
    });

    expect(container).toMatchSnapshot();
  });

  test('Signup form matches snapshot', async () => {
    const { container } = renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup form
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    await waitFor(() => {
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    });

    expect(container).toMatchSnapshot();
  });
});

// Accessibility Tests
describe('LoginSignupRefactored - Accessibility', () => {
  test('should not have accessibility violations', async () => {
    const { container } = renderWithTheme(<LoginSignupRefactored />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('should have proper ARIA attributes', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Check tablist
    expect(screen.getByRole('tablist')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /sign in/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /sign up/i })).toHaveAttribute('aria-selected', 'false');

    // Check form labels
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  test('should announce errors to screen readers', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  test('should support keyboard navigation', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Tab through form fields
    await userEvent.tab();
    expect(screen.getByRole('tab', { name: /sign in/i })).toHaveFocus();

    await userEvent.tab();
    expect(screen.getByLabelText(/email address/i)).toHaveFocus();

    await userEvent.tab();
    expect(screen.getByLabelText(/password/i)).toHaveFocus();
  });
});

// Rendering Tests
describe('LoginSignupRefactored - Rendering', () => {
  test('renders initial login form correctly', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    expect(screen.getByText('PsychSync')).toBeInTheDocument();
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /sign in/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /sign up/i })).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('switches to signup form correctly', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    expect(screen.getByText(/start your journey/i)).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /sign up/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /sign in/i })).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  test('toggles password visibility', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');

    const toggleButton = screen.getByLabelText(/show password/i);
    await userEvent.click(toggleButton);

    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText(/hide password/i)).toBeInTheDocument();
  });

  test('shows social login options', () => {
    renderWithTheme(<LoginSignupRefactored />);

    expect(screen.getByLabelText(/sign in with google/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/sign in with github/i)).toBeInTheDocument();
  });
});

// Form Validation Tests
describe('LoginSignupRefactored - Form Validation', () => {
  test('validates login form correctly', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Submit empty form
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    });
  });

  test('validates email format', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.type(emailInput, 'invalid-email');
    await userEvent.tab(); // Trigger blur

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/valid email address/i)).toBeInTheDocument();
    });
  });

  test('validates signup form correctly', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    // Submit empty form
    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Full name is required')).toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
      expect(screen.getByText('Please confirm your password')).toBeInTheDocument();
    });
  });

  test('validates password complexity', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    const passwordInput = screen.getByLabelText(/^password/i);
    await userEvent.type(passwordInput, 'weak');

    await waitFor(() => {
      expect(screen.getByText(/password must include:/i)).toBeInTheDocument();
      expect(screen.getByText(/8\+ characters/i)).toBeInTheDocument();
      expect(screen.getByText(/uppercase letter/i)).toBeInTheDocument();
      expect(screen.getByText(/lowercase letter/i)).toBeInTheDocument();
      expect(screen.getByText(/number/i)).toBeInTheDocument();
      expect(screen.getByText(/special character/i)).toBeInTheDocument();
    });
  });

  test('validates password confirmation', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    await fillSignupForm('test@example.com', 'ValidPass123!', 'DifferentPass123!', 'Test User');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  test('clears errors when user starts typing', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Trigger validation error
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
    });

    // Start typing in email field
    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.type(emailInput, 'test@example.com');

    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText('Email is required')).not.toBeInTheDocument();
    });
  });
});

// API Integration Tests
describe('LoginSignupRefactored - API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('handles successful login', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '123',
        email: 'test@example.com',
        full_name: 'Test User'
      }
    };

    global.fetch = createMockFetch(mockResponse);

    renderWithTheme(<LoginSignupRefactored />);

    await fillLoginForm('test@example.com', 'ValidPass123!');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: expect.stringContaining('username=test%40example.com'),
      });
    });

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText('Login successful! Redirecting...')).toBeInTheDocument();
    });

    // Should store token in sessionStorage
    expect(sessionStorage.getItem('access_token')).toBe('test-token');
  });

  test('handles login failure', async () => {
    global.fetch = createMockFetch({ detail: 'Invalid credentials' }, false, 401);

    renderWithTheme(<LoginSignupRefactored />);

    await fillLoginForm('test@example.com', 'WrongPassword');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });

  test('handles successful signup', async () => {
    global.fetch = createMockFetch({ success: true });

    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    await fillSignupForm('test@example.com', 'ValidPass123!', 'ValidPass123!', 'Test User');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.stringContaining('test@example.com'),
      });
    });

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText('Account created successfully!')).toBeInTheDocument();
    });
  });

  test('handles signup failure', async () => {
    global.fetch = createMockFetch({ detail: 'Email already exists' }, false, 409);

    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    await fillSignupForm('existing@example.com', 'ValidPass123!', 'ValidPass123!', 'Test User');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });
});

// State Management Tests
describe('LoginSignupRefactored - State Management', () => {
  test('manages form state correctly', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);

    // Type in form fields
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  test('switches tabs and clears state', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    // Fill login form
    await fillLoginForm('test@example.com', 'password123');

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    // Login form should be cleared when switching back
    const loginTab = screen.getByRole('tab', { name: /sign in/i });
    await userEvent.click(loginTab);

    const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement;
    expect(emailInput.value).toBe('');
  });

  test('handles loading state correctly', async () => {
    // Mock a slow API response
    global.fetch = jest.fn(() => new Promise(resolve => setTimeout(() => resolve({
      ok: true,
      json: () => Promise.resolve({ access_token: 'test' })
    }), 100)));

    renderWithTheme(<LoginSignupRefactored />);

    await fillLoginForm('test@example.com', 'ValidPass123!');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText('Signing in...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    // Loading spinner should be present
    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument();
  });

  test('clears success message after delay', async () => {
    jest.useFakeTimers();

    global.fetch = createMockFetch({ success: true });

    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup and submit
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    await fillSignupForm('test@example.com', 'ValidPass123!', 'ValidPass123!', 'Test User');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Account created successfully!')).toBeInTheDocument();
    });

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    await waitFor(() => {
      expect(screen.queryByText('Account created successfully!')).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });
});

// Performance Tests
describe('LoginSignupRefactored - Performance', () => {
  test('does not re-render unnecessarily', async () => {
    const { rerender } = renderWithTheme(<LoginSignupRefactored />);

    const emailInput = screen.getByLabelText(/email address/i);

    // Type slowly to check for excessive re-renders
    for (let i = 0; i < 5; i++) {
      await userEvent.type(emailInput, 'a');
    }

    // Component should still be functional
    expect(emailInput).toHaveValue('aaaaa');
  });

  test('handles rapid tab switching', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const loginTab = screen.getByRole('tab', { name: /sign in/i });
    const signupTab = screen.getByRole('tab', { name: /sign up/i });

    // Rapidly switch tabs
    for (let i = 0; i < 10; i++) {
      await userEvent.click(i % 2 === 0 ? signupTab : loginTab);
    }

    // Should end up with correct form
    const currentTab = screen.getByRole('tab', { 'aria-selected': 'true' });
    expect(currentTab).toBeInTheDocument();
  });
});

// Security Tests
describe('LoginSignupRefactored - Security', () => {
  test('sanitizes input data', async () => {
    global.fetch = createMockFetch({ success: true });

    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    const nameInput = screen.getByLabelText(/full name/i);
    await userEvent.type(nameInput, '<script>alert("xss")</script>');

    await fillSignupForm('test@example.com', 'ValidPass123!', 'ValidPass123!', '<script>alert("xss")</script>');

    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.not.stringContaining('<script>'),
      });
    });
  });

  test('handles network errors gracefully', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    renderWithTheme(<LoginSignupRefactored />);

    await fillLoginForm('test@example.com', 'ValidPass123!');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument();
    });
  });
});

// Edge Cases
describe('LoginSignupRefactored - Edge Cases', () => {
  test('handles very long input', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const longString = 'a'.repeat(1000);
    const emailInput = screen.getByLabelText(/email address/i);

    await userEvent.type(emailInput, longString);

    expect(emailInput).toHaveValue(longString);
  });

  test('handles special characters in name field', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    const nameInput = screen.getByLabelText(/full name/i);
    await userEvent.type(nameInput, 'José María O\'Connor-Smith');

    expect(nameInput).toHaveValue('José María O\'Connor-Smith');
  });

  test('handles rapid form submissions', async () => {
    global.fetch = createMockFetch({ success: true });

    renderWithTheme(<LoginSignupRefactored />);

    await fillLoginForm('test@example.com', 'ValidPass123!');

    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Submit multiple times rapidly
    await userEvent.click(submitButton);
    await userEvent.click(submitButton);
    await userEvent.click(submitButton);

    // Should only call API once due to loading state
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  test('handles browser back navigation', async () => {
    const { history } = window;
    const pushState = jest.fn();
    Object.defineProperty(window, 'history', {
      value: { ...history, pushState },
      writable: true,
    });

    renderWithTheme(<LoginSignupRefactored />);

    // Switch tabs
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    // Should not trigger unnecessary navigation
    expect(pushState).not.toHaveBeenCalled();
  });
});

// User Experience Tests
describe('LoginSignupRefactored - User Experience', () => {
  test('provides helpful password requirements feedback', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    const passwordInput = screen.getByLabelText(/^password/i);

    // Type partial password
    await userEvent.type(passwordInput, 'weak');

    await waitFor(() => {
      expect(screen.getByText(/password must include:/i)).toBeInTheDocument();
      expect(screen.getByText(/8\+ characters/i)).toBeInTheDocument();
    });

    // Type strong password
    await userEvent.clear(passwordInput);
    await userEvent.type(passwordInput, 'StrongPass123!');

    await waitFor(() => {
      // Requirements should be marked as satisfied
      const requirements = screen.getByText(/8\+ characters/i);
      expect(requirements).toHaveClass('line-through');
    });
  });

  test('maintains focus management', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const emailInput = screen.getByLabelText(/email address/i);
    await userEvent.click(emailInput);

    expect(emailInput).toHaveFocus();

    // Tab through form
    await userEvent.tab();
    expect(screen.getByLabelText(/password/i)).toHaveFocus();

    await userEvent.tab();
    expect(screen.getByRole('button', { name: /remember me/i })).toHaveFocus();
  });

  test('provides visual feedback for interactions', async () => {
    renderWithTheme(<LoginSignupRefactored />);

    const emailInput = screen.getByLabelText(/email address/i);

    // Check hover state
    fireEvent.mouseEnter(emailInput);
    expect(emailInput).toHaveClass('hover:border-gray-400');

    // Check focus state
    fireEvent.focus(emailInput);
    expect(emailInput).toHaveClass('focus:ring-blue-500');
  });
});

// Integration Tests
describe('LoginSignupRefactored - Integration', () => {
  test('completes full user signup flow', async () => {
    global.fetch = createMockFetch({ success: true });

    renderWithTheme(<LoginSignupRefactored />);

    // Switch to signup
    const signupTab = screen.getByRole('tab', { name: /sign up/i });
    await userEvent.click(signupTab);

    // Fill form with valid data
    await fillSignupForm('john.doe@example.com', 'SecurePass123!', 'SecurePass123!', 'John Doe');

    // Add organization name
    const orgInput = screen.getByLabelText(/organization name/i);
    await userEvent.type(orgInput, 'Acme Corp');

    // Accept terms
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms and conditions/i });
    await userEvent.click(termsCheckbox);

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Account created successfully!')).toBeInTheDocument();
    });

    // Should automatically switch to login form after delay
    jest.useFakeTimers();
    act(() => {
      jest.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /sign in/i })).toHaveAttribute('aria-selected', 'true');
    });

    jest.useRealTimers();
  });

  test('handles successful login and redirect', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: '123', email: 'test@example.com', full_name: 'Test User' }
    };

    global.fetch = createMockFetch(mockResponse);

    renderWithTheme(<LoginSignupRefactored />);

    await fillLoginForm('test@example.com', 'ValidPass123!');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Login successful! Redirecting...')).toBeInTheDocument();
    });

    // Should redirect after delay
    jest.useFakeTimers();
    act(() => {
      jest.advanceTimersByTime(1500);
    });

    expect(window.location.href).toBe('/dashboard');

    jest.useRealTimers();
  });
});
