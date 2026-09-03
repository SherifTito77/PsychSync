// src/components/onboarding/StreamlinedRegister.tsx
// Simplified registration after user has seen value
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';

interface StreamlinedRegisterProps {
  userRole?: string;
  challenge?: string;
  onSkip?: () => void;
}

const StreamlinedRegister: React.FC<StreamlinedRegisterProps> = ({
  userRole,
  challenge,
  onSkip
}) => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    company_name: '', // Optional but helpful
  });

  const roleSpecificMessages: Record<string, string> = {
    manager: "Start optimizing your team's performance today",
    hr: "Get your organizational behavior insights",
    lead: "Build a more effective team",
    member: "Understand your team dynamics better",
    executive: "Access your leadership intelligence dashboard"
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Simplified validation - just the basics
    if (formData.full_name.length < 2) {
      setError('Please enter your full name');
      setIsLoading(false);
      return;
    }

    if (!formData.email.includes('@')) {
      setError('Please enter a valid email');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      setIsLoading(false);
      return;
    }

    try {
      const result = await register({
        ...formData,
        confirmPassword: formData.password, // Skip confirmation for speed
        ...(userRole && { user_role: userRole }),
        ...(challenge && { primary_challenge: challenge })
      });

      if (result.success) {
        setShowSuccess(true);
        // Redirect faster - no 5-second delay
        setTimeout(() => {
          navigate('/dashboard?onboarding=complete');
        }, 2000);
      } else {
        setError(result.error || 'Registration failed');
      }
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialSignup = (provider: string) => {
    // Implement social login
    setIsLoading(true);
    // Simulate social signup
    setTimeout(() => {
      navigate(`/dashboard?onboarding=social&provider=${provider}`);
    }, 1500);
  };

  if (showSuccess) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome to PsychSync!
        </h3>
        <p className="text-gray-600 mb-6">
          Your team insights dashboard is being prepared...
        </p>
        <LoadingSpinner size="medium" color="indigo" />
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      {/* Value Reminder */}
      <div className="bg-gradient-to-r from-indigo-500 to-blue-500 rounded-lg p-4 mb-6 text-white">
        <h3 className="font-semibold mb-1">You're almost there!</h3>
        <p className="text-sm opacity-90">
          {roleSpecificMessages[userRole]} - Your personalized insights are ready.
        </p>
      </div>

      {/* Social Login Options */}
      <div className="mb-6">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Quick signup</span>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <button
            onClick={() => handleSocialSignup('google')}
            disabled={isLoading}
            className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span className="text-sm font-medium">Google</span>
          </button>

          <button
            onClick={() => handleSocialSignup('microsoft')}
            disabled={isLoading}
            className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="#F25022" d="M11.4 11.4H0v11.4h11.4z"/>
              <path fill="#7FBA00" d="M24 11.4H12.6v11.4H24z"/>
              <path fill="#00A4EF" d="M11.4 0H0v11.4h11.4z"/>
              <path fill="#FFB900" d="M24 0H12.6v11.4H24z"/>
            </svg>
            <span className="text-sm font-medium">Microsoft</span>
          </button>
        </div>
      </div>

      {/* OR Divider */}
      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">or continue with email</span>
        </div>
      </div>

      {/* Registration Form - Simplified */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-md bg-red-50 border border-red-200">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Full Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Full Name
          </label>
          <input
            id="name"
            name="full_name"
            type="text"
            required
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="John Smith"
            autoComplete="name"
          />
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Work Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="john@company.com"
            autoComplete="email"
          />
        </div>

        {/* Company Name (Optional) */}
        <div>
          <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1">
            Company Name <span className="text-gray-400">(optional)</span>
          </label>
          <input
            id="company"
            name="company_name"
            type="text"
            value={formData.company_name}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Acme Corp"
            autoComplete="organization"
          />
        </div>

        {/* Password - Simplified */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="••••••••"
            autoComplete="new-password"
          />
          <p className="mt-1 text-xs text-gray-500">
            8+ characters recommended
          </p>
        </div>

        {/* Terms - Simplified */}
        <div className="flex items-start">
          <input
            id="terms"
            type="checkbox"
            required
            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mt-0.5"
          />
          <label htmlFor="terms" className="ml-2 block text-sm text-gray-700">
            I agree to PsychSync's Terms and Privacy Policy
          </label>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center"
          size="sm"
        >
          {isLoading ? (
            <>
              <LoadingSpinner size="small" color="white" className="mr-2" />
              Creating your account...
            </>
          ) : (
            'Create My Account'
          )}
        </Button>
      </form>

      {/* Skip Option */}
      {onSkip && (
        <div className="mt-6 text-center">
          <button
            onClick={onSkip}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Skip for now, continue exploring
          </button>
        </div>
      )}

      {/* Benefits */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">With your account you get:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Personalized team insights dashboard</li>
          <li>• Access to all assessment tools</li>
          <li>• Team optimization recommendations</li>
          <li>• No credit card required</li>
        </ul>
      </div>
    </div>
  );
};

export default StreamlinedRegister;
