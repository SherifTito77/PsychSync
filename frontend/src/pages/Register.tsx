// frontend/src/pages/Register.tsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useAnalytics } from '../services/analytics/tracker';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { showNotification } = useNotification();
  const { trackFunnel, track, trackPage } = useAnalytics();
  const [isLoading, setIsLoading] = useState(false);

  // Track page view on mount
  useEffect(() => {
    trackPage('register', {
      referrer: document.referrer
    });
  }, [trackPage]);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreedToTerms: false,
  });
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox'
      ? e.target.checked
      : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
    setError('');
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // ✅ FIXED: Validate BEFORE setting loading state
    // Validation
    if (!formData.agreedToTerms) {
      setError('You must agree to the Terms of Service and Privacy Policy');
      showNotification('You must agree to the Terms of Service and Privacy Policy', 'error');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      showNotification('Passwords do not match', 'error');
      return;
    }
    if (formData.password.length < 12) {
      setError('Password must be at least 12 characters long');
      showNotification('Password must be at least 12 characters long', 'error');
      return;
    }
    // Password complexity check
    const hasUpperCase = /[A-Z]/.test(formData.password);
    const hasLowerCase = /[a-z]/.test(formData.password);
    const hasNumbers = /\d/.test(formData.password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(formData.password);
    if (!hasUpperCase || !hasLowerCase || !hasNumbers || !hasSpecial) {
      setError('Password must contain uppercase, lowercase, numbers, and special characters (!@#$%^&*(),.?":{}|<>)');
      showNotification('Password must contain uppercase, lowercase, numbers, and special characters', 'error');
      return;
    }

    // ✅ Only set loading state after validation passes
    setIsLoading(true);

    // Track button click and funnel start
    track('user_button_clicked', {
      button_id: 'create_account',
      page: 'register',
      form_completed: true
    });

    trackFunnel('signup', 'started', {
      has_full_name: !!formData.full_name,
      email_domain: formData.email.split('@')[1]
    });

    try {
      const result = await register(formData);
      if (result.success) {
        // Track successful registration completion
        trackFunnel('signup', 'completed', {
          email_verified: false,
          timestamp: Date.now()
        });

        setShowSuccess(true);
        showNotification('Registration successful! Please check your email to verify your account.', 'success');
        // Redirect to login after 5 seconds
        setTimeout(() => {
          navigate('/login');
        }, 5000);
      } else {
        // Track registration failure
        track('system_error_occurred', {
          error_type: 'registration_failed',
          error_message: result.error,
          funnel_step: 'signup'
        });

        setError(result.error || 'Registration failed');
        showNotification(result.error || 'Registration failed', 'error');
      }
    } catch (err) {
      // Track unexpected registration error
      track('system_error_occurred', {
        error_type: 'registration_exception',
        error_message: err instanceof Error ? err.message : 'Unknown error',
        funnel_step: 'signup'
      });

      setError('An unexpected error occurred. Please try again.');
      showNotification('An unexpected error occurred. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  };
  // Success Screen
  if (showSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <div className="bg-white shadow-lg rounded-lg p-8">
            <div className="text-center">
              {/* Success Icon */}
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <svg
                  className="h-10 w-10 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              {/* Success Message */}
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                Registration Successful!
              </h3>
              <p className="text-gray-600 mb-4">
                We've sent a verification email to
              </p>
              <p className="text-indigo-600 font-semibold mb-4">
                {formData.email}
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                <p className="text-sm text-blue-800">
                  Please check your inbox and click the verification link to activate your account.
                </p>
              </div>
              {/* Loading Indicator */}
              <div className="flex items-center justify-center space-x-2 text-gray-500 mt-6">
                <LoadingSpinner size="small" color="indigo" />
                <span className="text-sm">Redirecting to login page...</span>
              </div>
              {/* Manual Redirect Link */}
              <div className="mt-6">
                <Link
                  to="/login"
                  className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
                >
                  Click here if not redirected automatically
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  // Registration Form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="bg-white shadow-lg rounded-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <svg
                className="h-12 w-12 text-indigo-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">Join PsychSync</h2>
            <p className="text-gray-600 mt-2">Create your account</p>
          </div>
          {/* Error Alert */}
          {error && (
            <div className="mb-6 p-4 rounded-md bg-red-50 border border-red-200">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}
          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Full Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Full Name
              </label>
              <input
                id="name"
                name="full_name"
                type="text"
                required
                value={formData.full_name}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="John Doe"
                autoComplete="name"
              />
            </div>
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="your@email.com"
                autoComplete="email"
              />
            </div>
            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="••••••••"
                autoComplete="new-password"
              />
              <p className="mt-1 text-xs text-gray-500">
                Must be at least 12 characters with uppercase, lowercase, numbers, and special characters (!@#$%^&*(),.?":{}|&lt;&gt;)
              </p>
            </div>
            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>
            {/* Terms & Conditions */}
            <div className="flex items-start">
              <input
                id="terms"
                name="agreedToTerms"
                type="checkbox"
                checked={formData.agreedToTerms}
                onChange={handleChange}
                disabled={isLoading}
                required
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mt-1"
              />
              <label htmlFor="terms" className="ml-2 block text-sm text-gray-700">
                I agree to the{' '}
                <Link to="/terms" className="text-indigo-600 hover:text-indigo-500">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link to="/privacy" className="text-indigo-600 hover:text-indigo-500">
                  Privacy Policy
                </Link>
              </label>
            </div>
            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="small" color="white" className="mr-2" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>
          </form>
          {/* Sign In Link */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Already have an account?
                </span>
              </div>
            </div>
            <div className="mt-6">
              <Link
                to="/login"
                className="w-full flex justify-center py-2 px-4 border border-indigo-600 rounded-md shadow-sm text-sm font-medium text-indigo-600 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                onClick={() => track('user_button_clicked', {
                  button_id: 'sign_in_instead',
                  page: 'register',
                  destination: 'login'
                })}
              >
                Sign in instead
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Register;
