/**
 * IMAP Connection Modal
 * Form for connecting to email via IMAP/POP3
 */

import React, { useState } from 'react';
import { testIMAPConnection } from '../../services/emailConnectorService';

interface IMAPConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (credentials: {
    email_address: string;
    server: string;
    port: number;
    use_ssl: boolean;
    username?: string;
    password: string;
  }) => void;
  loading?: boolean;
}

const IMAPConnectionModal: React.FC<IMAPConnectionModalProps> = ({
  isOpen,
  onClose,
  onConnect,
  loading = false,
}) => {
  const [formData, setFormData] = useState({
    email_address: '',
    server: '',
    port: 993,
    use_ssl: true,
    username: '',
    password: '',
  });

  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConnect(formData);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await testIMAPConnection({
        email_address: formData.email_address,
        server: formData.server,
        port: formData.port,
        use_ssl: formData.use_ssl,
        username: formData.username || formData.email_address,
        password: formData.password,
      });

      setTestResult({
        success: result.success,
        message: result.success
          ? 'Connection successful! You can now connect.'
          : result.error_message || 'Connection failed. Please check your credentials.',
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              Connect via IMAP/POP3
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
              disabled={loading || testing}
            >
              <svg
                className="h-6 w-6"
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
            </button>
          </div>
          <p className="mt-2 text-sm text-gray-600">
            Enter your email server credentials to connect. Your password is encrypted
            and never stored.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Email Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={formData.email_address}
              onChange={(e) =>
                setFormData({ ...formData, email_address: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="you@example.com"
              disabled={loading || testing}
            />
          </div>

          {/* Server Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              IMAP/POP3 Server
            </label>
            <input
              type="text"
              required
              value={formData.server}
              onChange={(e) =>
                setFormData({ ...formData, server: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="imap.example.com"
              disabled={loading || testing}
            />
            <p className="mt-1 text-xs text-gray-500">
              Common servers: imap.gmail.com, outlook.office365.com
            </p>
          </div>

          {/* Port and SSL */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Port
              </label>
              <input
                type="number"
                required
                value={formData.port}
                onChange={(e) =>
                  setFormData({ ...formData, port: parseInt(e.target.value) })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="993"
                disabled={loading || testing}
              />
              <p className="mt-1 text-xs text-gray-500">
                993 for IMAPS, 995 for POP3S
              </p>
            </div>

            <div className="flex items-end">
              <label className="flex items-center space-x-2 mb-3">
                <input
                  type="checkbox"
                  checked={formData.use_ssl}
                  onChange={(e) =>
                    setFormData({ ...formData, use_ssl: e.target.checked })
                  }
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  disabled={loading || testing}
                />
                <span className="text-sm text-gray-700">Use SSL/TLS</span>
              </label>
            </div>
          </div>

          {/* Username (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Leave blank if same as email"
              disabled={loading || testing}
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password / App Password
            </label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Your email password or app-specific password"
              disabled={loading || testing}
            />
            <p className="mt-1 text-xs text-gray-500">
              For Gmail, use an{' '}
              <a
                href="https://support.google.com/accounts/answer/185833"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-700"
              >
                app-specific password
              </a>
            </p>
          </div>

          {/* Test Result */}
          {testResult && (
            <div
              className={`p-3 rounded-lg ${
                testResult.success
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <p
                className={`text-sm ${
                  testResult.success ? 'text-green-700' : 'text-red-700'
                }`}
              >
                {testResult.message}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing || loading || !formData.email_address || !formData.server || !formData.password}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            <button
              type="submit"
              disabled={loading || testing}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        </form>

        {/* Security Notice */}
        <div className="px-6 pb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-700">
              <strong>🔒 Secure:</strong> Your credentials are encrypted using
              industry-standard encryption. We never store your password in plain
              text.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IMAPConnectionModal;
