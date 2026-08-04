
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotification } from '../contexts/NotificationContext';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { verifyMfa } from '../services/authService';

const MFAVerification: React.FC = () => {
  const [totpCode, setTotpCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { showNotification } = useNotification();
  const { refreshToken } = useAuth();

  // Retrieve challenge token and original destination from login state
  const mfaChallengeToken = (location.state as any)?.mfa_challenge_token;
  const from = (location.state as any)?.from || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaChallengeToken) {
      showNotification('MFA session expired. Please login again.', 'error');
      navigate('/login');
      return;
    }

    setIsLoading(true);
    try {
      // Use authService to verify MFA and persist session
      await verifyMfa(mfaChallengeToken, totpCode);

      // Update global auth state
      await refreshToken();

      showNotification('MFA verified successfully!', 'success');

      // Navigate to the original destination or dashboard
      // We use replace: true to prevent going back to MFA screen
      navigate(from, { replace: true });
    } catch (err: any) {
      showNotification(err.response?.data?.detail || 'Invalid MFA code.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  if (!mfaChallengeToken) {
    return <div className="p-8 text-center">MFA session invalid. <a href="/login" className="text-indigo-600">Return to Login</a></div>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6 text-center">MFA Verification</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Enter Authentication Code</label>
            <input
              type="text"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
              placeholder="000000"
              maxLength={6}
              required
            />
          </div>
          <Button type="submit" disabled={isLoading} fullWidth>
            {isLoading ? <LoadingSpinner size="small" /> : 'Verify Code'}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default MFAVerification;
