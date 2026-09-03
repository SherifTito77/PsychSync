/**
 * Refactored Login/Signup Component
 *
 * This refactored component addresses:
 * - Performance issues with proper memoization
 * - Accessibility violations with ARIA support
 * - TypeScript improvements with strict typing
 * - Component composition and separation of concerns
 * - Modern SaaS UX patterns
 * - Security improvements
 */

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { Eye, EyeOff, Mail, Lock, User, Building, AlertCircle, CheckCircle } from 'lucide-react';
import { useAnalytics } from '../../services/analytics/tracker';

// Types
interface LoginData {
  email: string;
  password: string;
}

interface SignupData {
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  organization_name?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
  };
}

interface FormErrors {
  [key: string]: string;
}

interface AuthInputProps {
  label: string;
  type: string;
  id: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  error?: string;
  required?: boolean;
  icon?: React.ReactNode;
  showPasswordToggle?: boolean;
  showPassword?: boolean;
  onTogglePassword?: () => void;
  autoComplete?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean;
}

// Constants
const VALIDATION_RULES = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_REQUIREMENTS: {
    UPPERCASE: /[A-Z]/,
    LOWERCASE: /[a-z]/,
    NUMBER: /[0-9]/,
    SPECIAL: /[!@#$%^&*(),.?":{}|<>]/
  },
  FORM_TIMEOUTS: {
    REDIRECT_DELAY: 1500,
    SWITCH_FORM_DELAY: 3000,
    SUCCESS_MESSAGE_DELAY: 5000
  }
} as const;

// Custom Hooks
const useFormValidation = () => {
  const validateEmail = useCallback((email: string): boolean => {
    return VALIDATION_RULES.EMAIL_REGEX.test(email.trim());
  }, []);

  const validatePassword = useCallback((password: string): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    if (password.length < VALIDATION_RULES.PASSWORD_MIN_LENGTH) {
      errors.push(`At least ${VALIDATION_RULES.PASSWORD_MIN_LENGTH} characters`);
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.UPPERCASE.test(password)) {
      errors.push('One uppercase letter');
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.LOWERCASE.test(password)) {
      errors.push('One lowercase letter');
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.NUMBER.test(password)) {
      errors.push('One number');
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.SPECIAL.test(password)) {
      errors.push('One special character');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }, []);

  const validateLoginForm = useCallback((data: LoginData): FormErrors => {
    const errors: FormErrors = {};

    if (!data.email.trim()) {
      errors.email = 'Email is required';
    } else if (!validateEmail(data.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!data.password) {
      errors.password = 'Password is required';
    }

    return errors;
  }, [validateEmail]);

  const validateSignupForm = useCallback((data: SignupData): FormErrors => {
    const errors: FormErrors = {};

    if (!data.email.trim()) {
      errors.email = 'Email is required';
    } else if (!validateEmail(data.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!data.full_name.trim()) {
      errors.full_name = 'Full name is required';
    } else if (data.full_name.trim().length < 2) {
      errors.full_name = 'Please enter your full name';
    }

    if (!data.password) {
      errors.password = 'Password is required';
    } else {
      const passwordValidation = validatePassword(data.password);
      if (!passwordValidation.isValid) {
        errors.password = `Password must include: ${passwordValidation.errors.join(', ')}`;
      }
    }

    if (!data.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (data.password !== data.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    return errors;
  }, [validateEmail, validatePassword]);

  return { validateLoginForm, validateSignupForm, validateEmail, validatePassword };
};

const useAuthAPI = () => {
  const login = useCallback(async (data: LoginData): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', data.email.trim().toLowerCase());
    formData.append('password', data.password);

    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Invalid email or password');
    }

    return response.json();
  }, []);

  const signup = useCallback(async (data: SignupData): Promise<void> => {
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: data.email.trim().toLowerCase(),
        password: data.password,
        full_name: data.full_name.trim(),
        organization_name: data.organization_name?.trim() || undefined,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(error.detail || 'Account creation failed');
    }
  }, []);

  return { login, signup };
};

// Utility Components
const AuthInput: React.FC<AuthInputProps> = React.memo(({
  label,
  type,
  id,
  value,
  onChange,
  placeholder,
  error,
  required = false,
  icon,
  showPasswordToggle,
  showPassword,
  onTogglePassword,
  autoComplete,
  'aria-describedby': ariaDescribedBy,
  'aria-invalid': ariaInvalid
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (error && inputRef.current) {
      inputRef.current.focus();
    }
  }, [error]);

  const inputId = `${id}-input`;
  const errorId = `${id}-error`;
  const describedBy = [ariaDescribedBy, error && errorId].filter(Boolean).join(' ') || undefined;

  return (
    <div className="space-y-1">
      <label
        htmlFor={inputId}
        className="block text-sm font-medium text-gray-700"
      >
        {label}
        {required && <span className="text-red-500 ml-1" aria-label="required">*</span>}
      </label>

      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none">
            {icon}
          </div>
        )}

        <input
          ref={inputRef}
          id={inputId}
          type={showPasswordToggle ? (showPassword ? 'text' : 'password') : type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          autoComplete={autoComplete}
          aria-invalid={ariaInvalid || !!error}
          aria-describedby={describedBy}
          className={`
            w-full py-2.5 px-3 border rounded-lg
            focus:ring-2 focus:ring-blue-500 focus:border-transparent
            transition-colors duration-200
            ${icon ? 'pl-10' : 'pl-3'}
            ${showPasswordToggle ? 'pr-10' : 'pr-3'}
            ${error
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 hover:border-gray-400'
            }
          `}
        />

        {showPasswordToggle && (
          <button
            type="button"
            onClick={onTogglePassword}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded p-1"
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
          </button>
        )}
      </div>

      {error && (
        <div
          id={errorId}
          className="flex items-center text-sm text-red-600"
          role="alert"
          aria-live="polite"
        >
          <AlertCircle className="w-4 h-4 mr-1 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
});

AuthInput.displayName = 'AuthInput';

const FormError: React.FC<{ message: string }> = React.memo(({ message }) => (
  <div
    className="flex items-center p-4 mb-4 text-red-800 bg-red-50 border border-red-200 rounded-lg"
    role="alert"
    aria-live="polite"
  >
    <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
    <span className="text-sm font-medium">{message}</span>
  </div>
));

FormError.displayName = 'FormError';

const FormSuccess: React.FC<{ message: string }> = React.memo(({ message }) => (
  <div
    className="flex items-center p-4 mb-4 text-green-800 bg-green-50 border border-green-200 rounded-lg"
    role="status"
    aria-live="polite"
  >
    <CheckCircle className="w-5 h-5 mr-2 flex-shrink-0" />
    <span className="text-sm font-medium">{message}</span>
  </div>
));

FormSuccess.displayName = 'FormSuccess';

const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' }> = React.memo(({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5'
  };

  return (
    <svg
      className={`animate-spin ${sizeClasses[size]} text-white`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';

// Form Components
const LoginForm: React.FC<{
  onSubmit: (e: React.FormEvent) => void;
  data: LoginData;
  onChange: (field: keyof LoginData, value: string) => void;
  errors: FormErrors;
  loading: boolean;
  showPassword: boolean;
  onTogglePassword: () => void;
}> = React.memo(({ onSubmit, data, onChange, errors, loading, showPassword, onTogglePassword }) => {
  const handleChange = useCallback((field: keyof LoginData) => (value: string) => {
    onChange(field, value);
  }, [onChange]);

  return (
    <form onSubmit={onSubmit} className="space-y-5" noValidate>
      <AuthInput
        label="Email Address"
        type="email"
        id="login-email"
        value={data.email}
        onChange={handleChange('email')}
        placeholder="you@example.com"
        error={errors.email}
        required
        icon={<Mail className="w-5 h-5" />}
        autoComplete="email"
        aria-invalid={!!errors.email}
      />

      <AuthInput
        label="Password"
        type="password"
        id="login-password"
        value={data.password}
        onChange={handleChange('password')}
        placeholder="Enter your password"
        error={errors.password}
        required
        icon={<Lock className="w-5 h-5" />}
        showPasswordToggle
        showPassword={showPassword}
        onTogglePassword={onTogglePassword}
        autoComplete="current-password"
        aria-invalid={!!errors.password}
      />

      <div className="flex items-center justify-between text-sm">
        <label className="flex items-center">
          <input
            type="checkbox"
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            aria-label="Remember me"
          />
          <span className="ml-2 text-gray-600">Remember me</span>
        </label>

        <a
          href="/forgot-password"
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Forgot password?
        </a>
      </div>

      <button
        type="submit"
        disabled={loading}
        aria-describedby={loading ? 'submit-status' : undefined}
        className={`
          w-full py-3 px-4 text-white font-medium rounded-lg
          transition-all duration-200 transform
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98]'
          }
        `}
      >
        <span className="flex items-center justify-center">
          {loading && <LoadingSpinner />}
          <span className={loading ? 'ml-2' : ''}>
            {loading ? 'Signing in...' : 'Sign In'}
          </span>
        </span>
        {loading && (
          <span id="submit-status" className="sr-only">
            Signing in, please wait
          </span>
        )}
      </button>
    </form>
  );
});

LoginForm.displayName = 'LoginForm';

const SignupForm: React.FC<{
  onSubmit: (e: React.FormEvent) => void;
  data: SignupData;
  onChange: (field: keyof SignupData, value: string) => void;
  errors: FormErrors;
  loading: boolean;
  showPassword: boolean;
  showConfirmPassword: boolean;
  onTogglePassword: () => void;
  onToggleConfirmPassword: () => void;
}> = React.memo(({
  onSubmit,
  data,
  onChange,
  errors,
  loading,
  showPassword,
  showConfirmPassword,
  onTogglePassword,
  onToggleConfirmPassword
}) => {
  const handleChange = useCallback((field: keyof SignupData) => (value: string) => {
    onChange(field, value);
  }, [onChange]);

  const passwordValidation = useMemo(() => {
    if (!data.password) return { isValid: true, errors: [] };
    // Reuse validation logic from hook
    const errors: string[] = [];

    if (data.password.length < VALIDATION_RULES.PASSWORD_MIN_LENGTH) {
      errors.push(`${VALIDATION_RULES.PASSWORD_MIN_LENGTH}+ characters`);
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.UPPERCASE.test(data.password)) {
      errors.push('Uppercase');
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.LOWERCASE.test(data.password)) {
      errors.push('Lowercase');
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.NUMBER.test(data.password)) {
      errors.push('Number');
    }

    if (!VALIDATION_RULES.PASSWORD_REQUIREMENTS.SPECIAL.test(data.password)) {
      errors.push('Special');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }, [data.password]);

  return (
    <form onSubmit={onSubmit} className="space-y-5" noValidate>
      <AuthInput
        label="Full Name"
        type="text"
        id="signup-name"
        value={data.full_name}
        onChange={handleChange('full_name')}
        placeholder="John Doe"
        error={errors.full_name}
        required
        icon={<User className="w-5 h-5" />}
        autoComplete="name"
        aria-invalid={!!errors.full_name}
      />

      <AuthInput
        label="Email Address"
        type="email"
        id="signup-email"
        value={data.email}
        onChange={handleChange('email')}
        placeholder="you@example.com"
        error={errors.email}
        required
        icon={<Mail className="w-5 h-5" />}
        autoComplete="email"
        aria-invalid={!!errors.email}
      />

      <AuthInput
        label="Organization Name"
        type="text"
        id="signup-org"
        value={data.organization_name || ''}
        onChange={handleChange('organization_name')}
        placeholder="Your Company (Optional)"
        icon={<Building className="w-5 h-5" />}
        autoComplete="organization"
      />

      <div className="space-y-2">
        <AuthInput
          label="Password"
          type="password"
          id="signup-password"
          value={data.password}
          onChange={handleChange('password')}
          placeholder="Create a strong password"
          error={errors.password}
          required
          icon={<Lock className="w-5 h-5" />}
          showPasswordToggle
          showPassword={showPassword}
          onTogglePassword={onTogglePassword}
          autoComplete="new-password"
          aria-invalid={!!errors.password}
          aria-describedby={data.password ? 'password-requirements' : undefined}
        />

        {data.password && (
          <div
            id="password-requirements"
            className="text-xs text-gray-500 space-y-1"
            aria-live="polite"
          >
            <p>Password must include:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li className={passwordValidation.errors.includes('8+ characters') ? 'line-through text-gray-400' : ''}>
                At least {VALIDATION_RULES.PASSWORD_MIN_LENGTH} characters
              </li>
              <li className={passwordValidation.errors.includes('Uppercase') ? 'line-through text-gray-400' : ''}>
                One uppercase letter
              </li>
              <li className={passwordValidation.errors.includes('Lowercase') ? 'line-through text-gray-400' : ''}>
                One lowercase letter
              </li>
              <li className={passwordValidation.errors.includes('Number') ? 'line-through text-gray-400' : ''}>
                One number
              </li>
              <li className={passwordValidation.errors.includes('Special') ? 'line-through text-gray-400' : ''}>
                One special character
              </li>
            </ul>
          </div>
        )}
      </div>

      <AuthInput
        label="Confirm Password"
        type="password"
        id="signup-confirm"
        value={data.confirmPassword}
        onChange={handleChange('confirmPassword')}
        placeholder="Confirm your password"
        error={errors.confirmPassword}
        required
        icon={<Lock className="w-5 h-5" />}
        showPasswordToggle
        showPassword={showConfirmPassword}
        onTogglePassword={onToggleConfirmPassword}
        autoComplete="new-password"
        aria-invalid={!!errors.confirmPassword}
      />

      <div className="space-y-2">
        <label className="flex items-start text-sm">
          <input
            type="checkbox"
            required
            className="w-4 h-4 mt-0.5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            aria-label="I agree to terms and conditions"
          />
          <span className="ml-2 text-gray-600">
            I agree to the{' '}
            <a
              href="/terms"
              className="text-blue-600 hover:text-blue-700 font-medium underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms and Conditions
            </a>{' '}
            and{' '}
            <a
              href="/privacy"
              className="text-blue-600 hover:text-blue-700 font-medium underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </a>
          </span>
        </label>
      </div>

      <button
        type="submit"
        disabled={loading}
        aria-describedby={loading ? 'signup-status' : undefined}
        className={`
          w-full py-3 px-4 text-white font-medium rounded-lg
          transition-all duration-200 transform
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98]'
          }
        `}
      >
        <span className="flex items-center justify-center">
          {loading && <LoadingSpinner />}
          <span className={loading ? 'ml-2' : ''}>
            {loading ? 'Creating account...' : 'Create Account'}
          </span>
        </span>
        {loading && (
          <span id="signup-status" className="sr-only">
            Creating account, please wait
          </span>
        )}
      </button>
    </form>
  );
});

SignupForm.displayName = 'SignupForm';

// Main Component
const LoginSignupRefactored: React.FC = () => {
  // Analytics tracking
  const { track, trackFunnel, trackPage } = useAnalytics();

  // Track page view on mount
  useEffect(() => {
    trackPage('auth', {
      view: isLogin ? 'login' : 'signup',
      referrer: document.referrer
    });
  }, []);

  // Form state
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [successMessage, setSuccessMessage] = useState('');

  // Form data
  const [loginData, setLoginData] = useState<LoginData>({
    email: '',
    password: '',
  });

  const [signupData, setSignupData] = useState<SignupData>({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    organization_name: '',
  });

  // Custom hooks
  const { validateLoginForm, validateSignupForm } = useFormValidation();
  const { login, signup } = useAuthAPI();

  // Refs for focus management
  const tabContainerRef = useRef<HTMLDivElement>(null);

  // Memoized form data handlers
  const handleLoginChange = useCallback((field: keyof LoginData, value: string) => {
    setLoginData(prev => ({ ...prev, [field]: value }));
    // Clear field-specific error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  }, [errors]);

  const handleSignupChange = useCallback((field: keyof SignupData, value: string) => {
    setSignupData(prev => ({ ...prev, [field]: value }));
    // Clear field-specific error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  }, [errors]);

  // API handlers with proper error handling
  const handleLogin = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors = validateLoginForm(loginData);
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setErrors({});
    setSuccessMessage('');

    // Track login funnel start
    track('user_button_clicked', {
      button_id: 'login_submit',
      page: 'auth'
    });
    trackFunnel('login', 'started', {
      email_domain: loginData.email.split('@')[1]
    });

    try {
      const response = await login(loginData);

      // Track successful login
      trackFunnel('login', 'completed', {
        user_id: response.user.id,
        email_domain: loginData.email.split('@')[1]
      });

      // Store token where axios interceptor reads it (localStorage)
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      setSuccessMessage('Login successful! Redirecting...');

      setTimeout(() => {
        window.location.href = '/dashboard';
      }, VALIDATION_RULES.FORM_TIMEOUTS.REDIRECT_DELAY);

    } catch (error) {
      // Track login failure
      track('system_error_occurred', {
        error_type: 'login_failed',
        error_message: error instanceof Error ? error.message : 'Authentication failed',
        funnel_step: 'login'
      });

      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setErrors({ form: errorMessage });
    } finally {
      setLoading(false);
    }
  }, [loginData, validateLoginForm, login, track, trackFunnel]);

  const handleSignup = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors = validateSignupForm(signupData);
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setErrors({});
    setSuccessMessage('');

    // Track signup funnel start
    track('user_button_clicked', {
      button_id: 'signup_submit',
      page: 'auth'
    });
    trackFunnel('signup', 'started', {
      has_organization: !!signupData.organization_name,
      email_domain: signupData.email.split('@')[1]
    });

    try {
      await signup(signupData);

      // Track successful signup
      trackFunnel('signup', 'completed', {
        has_organization: !!signupData.organization_name,
        email_domain: signupData.email.split('@')[1]
      });

      setSuccessMessage('Account created successfully! Please check your email to verify your account.');

      // Reset form
      setSignupData({
        email: '',
        password: '',
        confirmPassword: '',
        full_name: '',
        organization_name: '',
      });

      // Switch to login after delay
      setTimeout(() => {
        setIsLogin(true);
        setSuccessMessage('');
      }, VALIDATION_RULES.FORM_TIMEOUTS.SWITCH_FORM_DELAY);

    } catch (error) {
      // Track signup failure
      track('system_error_occurred', {
        error_type: 'signup_failed',
        error_message: error instanceof Error ? error.message : 'Account creation failed',
        funnel_step: 'signup'
      });

      const errorMessage = error instanceof Error ? error.message : 'Signup failed';
      setErrors({ form: errorMessage });
    } finally {
      setLoading(false);
    }
  }, [signupData, validateSignupForm, signup, track, trackFunnel]);

  // Tab switching with focus management
  const handleTabSwitch = useCallback((loginMode: boolean) => {
    setIsLogin(loginMode);
    setErrors({});
    setSuccessMessage('');
    setShowPassword(false);
    setShowConfirmPassword(false);

    // Track tab switch
    track('user_button_clicked', {
      button_id: loginMode ? 'switch_to_login' : 'switch_to_signup',
      page: 'auth',
      previous_view: loginMode ? 'signup' : 'login',
      new_view: loginMode ? 'login' : 'signup'
    });

    // Focus management for accessibility
    if (tabContainerRef.current) {
      const tabButton = tabContainerRef.current.querySelector(`[role="tab"][aria-selected="${loginMode}"]`) as HTMLButtonElement;
      tabButton?.focus();
    }
  }, [track]);

  // Clear success message after delay
  useEffect(() => {
    let timerId: NodeJS.Timeout | undefined;
    if (successMessage) {
      timerId = setTimeout(() => {
        setSuccessMessage('');
      }, VALIDATION_RULES.FORM_TIMEOUTS.SUCCESS_MESSAGE_DELAY);
    }
    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [successMessage]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            PsychSync
          </h1>
          <p className="text-lg text-gray-600">
            {isLogin ? 'Welcome back to your workspace' : 'Start your journey with us'}
          </p>
        </header>

        {/* Main Card */}
        <main className="bg-white rounded-2xl shadow-xl p-8">
          {/* Tab Navigation */}
          <div
            ref={tabContainerRef}
            className="flex mb-6 bg-gray-100 rounded-lg p-1"
            role="tablist"
            aria-label="Authentication options"
          >
            <button
              role="tab"
              aria-selected={isLogin}
              aria-controls="login-panel"
              id="login-tab"
              onClick={() => handleTabSwitch(true)}
              className={`
                flex-1 py-2.5 px-4 rounded-lg font-medium transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
                ${isLogin
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
                }
              `}
            >
              Sign In
            </button>
            <button
              role="tab"
              aria-selected={!isLogin}
              aria-controls="signup-panel"
              id="signup-tab"
              onClick={() => handleTabSwitch(false)}
              className={`
                flex-1 py-2.5 px-4 rounded-lg font-medium transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
                ${!isLogin
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
                }
              `}
            >
              Sign Up
            </button>
          </div>

          {/* Forms */}
          <div
            id="login-panel"
            role="tabpanel"
            aria-labelledby="login-tab"
            hidden={!isLogin}
          >
            {successMessage && <FormSuccess message={successMessage} />}
            {errors.form && <FormError message={errors.form} />}
            <LoginForm
              onSubmit={handleLogin}
              data={loginData}
              onChange={handleLoginChange}
              errors={errors}
              loading={loading}
              showPassword={showPassword}
              onTogglePassword={() => setShowPassword(!showPassword)}
            />
          </div>

          <div
            id="signup-panel"
            role="tabpanel"
            aria-labelledby="signup-tab"
            hidden={isLogin}
          >
            {successMessage && <FormSuccess message={successMessage} />}
            {errors.form && <FormError message={errors.form} />}
            <SignupForm
              onSubmit={handleSignup}
              data={signupData}
              onChange={handleSignupChange}
              errors={errors}
              loading={loading}
              showPassword={showPassword}
              showConfirmPassword={showConfirmPassword}
              onTogglePassword={() => setShowPassword(!showPassword)}
              onToggleConfirmPassword={() => setShowConfirmPassword(!showConfirmPassword)}
            />
          </div>

          {/* Social Login - Optional */}
          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-500 font-medium">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button
                className="flex items-center justify-center px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                aria-label="Sign in with Google"
                onClick={() => track('user_button_clicked', {
                  button_id: 'social_login_google',
                  page: 'auth',
                  auth_type: isLogin ? 'login' : 'signup'
                })}
              >
                {/* Google SVG */}
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span className="ml-2 text-sm font-medium text-gray-700">Google</span>
              </button>

              <button
                className="flex items-center justify-center px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                aria-label="Sign in with GitHub"
                onClick={() => track('user_button_clicked', {
                  button_id: 'social_login_github',
                  page: 'auth',
                  auth_type: isLogin ? 'login' : 'signup'
                })}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd"/>
                </svg>
                <span className="ml-2 text-sm font-medium text-gray-700">GitHub</span>
              </button>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="text-center mt-6">
          <p className="text-sm text-gray-600">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => handleTabSwitch(!isLogin)}
              className="text-blue-600 hover:text-blue-700 font-medium underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded px-1 py-0.5"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </footer>
      </div>
    </div>
  );
};

LoginSignupRefactored.displayName = 'LoginSignupRefactored';

export default LoginSignupRefactored;
