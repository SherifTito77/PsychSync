// frontend/src/components/ResendVerification.tsx
import React, { useState } from 'react';
import api from '../services/api';
interface ResendVerificationProps {
  email: string;
}
const ResendVerification: React.FC<ResendVerificationProps> = ({ email }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const handleResend = async () => {
    setIsLoading(true);
    setMessage(null);
    try {
      await api.post('/auth/resend-verification', { email });
      setMessage({
        type: 'success',
        text: 'Verification email sent! Please check your inbox.',
      });
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to resend verification email',
      });
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-yellow-800">
            Email not verified
          </h3>
          <p className="mt-2 text-sm text-yellow-700">
            Please verify your email address to access all features.
          </p>
          <button
            onClick={handleResend}
            disabled={isLoading}
            className="mt-2 text-sm font-medium text-yellow-800 hover:text-yellow-900 underline disabled:opacity-50"
          >
            {isLoading ? 'Sending...' : 'Resend verification email'}
          </button>
          {message && (
            <p
              className={`mt-2 text-sm ${
                message.type === 'success' ? 'text-green-700' : 'text-red-700'
              }`}
            >
              {message.text}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
export default ResendVerification;
