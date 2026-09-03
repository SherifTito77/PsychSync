/**
 * Email OAuth Callback Handler
 * Handles OAuth2 callbacks from Gmail and Outlook
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { handleOAuthCallback } from '../../services/emailConnectorService';

const EmailOAuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const provider = searchParams.get('provider') || 'gmail'; // Default to gmail

      if (!code || !state) {
        setStatus('error');
        setMessage('Missing OAuth parameters. Please try again.');
        setTimeout(() => navigate('/email-connector'), 3000);
        return;
      }

      try {
        const result = await handleOAuthCallback(provider, code, state);

        if (result.success && result.connection_id) {
          setStatus('success');
          setMessage(
            `Successfully connected ${result.email_address || provider}! You can now start syncing your emails.`
          );
          setTimeout(() => navigate('/email-connector'), 2000);
        } else {
          setStatus('error');
          setMessage(
            result.error || 'Connection failed. Please try again or contact support.'
          );
          setTimeout(() => navigate('/email-connector'), 3000);
        }
      } catch (error) {
        setStatus('error');
        setMessage(
          `An error occurred: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
        setTimeout(() => navigate('/email-connector'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Status Icon */}
          <div className="flex justify-center mb-6">
            {status === 'loading' && (
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600"></div>
            )}
            {status === 'success' && (
              <div className="rounded-full h-16 w-16 bg-green-100 flex items-center justify-center">
                <svg
                  className="h-10 w-10 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            )}
            {status === 'error' && (
              <div className="rounded-full h-16 w-16 bg-red-100 flex items-center justify-center">
                <svg
                  className="h-10 w-10 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
            )}
          </div>

          {/* Status Message */}
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-4">
            {status === 'loading' && 'Connecting...'}
            {status === 'success' && 'Connection Successful!'}
            {status === 'error' && 'Connection Failed'}
          </h2>

          <p className="text-center text-gray-600 mb-6">{message}</p>

          {/* Progress indicator */}
          {status === 'loading' && (
            <div className="flex justify-center">
              <p className="text-sm text-gray-500">
                Redirecting you back to Email Connector...
              </p>
            </div>
          )}

          {/* Manual redirect link */}
          {status !== 'loading' && (
            <div className="text-center">
              <button
                onClick={() => navigate('/email-connector')}
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Return to Email Connector →
              </button>
            </div>
          )}
        </div>

        {/* Security Notice */}
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-xs text-blue-700 text-center">
            <strong>🔒 Secure Connection:</strong> Your email credentials are encrypted
            and never stored. We use OAuth2 for secure authentication.
          </p>
        </div>
      </div>
    </div>
  );
};

export default EmailOAuthCallback;
