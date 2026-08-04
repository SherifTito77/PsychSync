/**
 * Email Actions Modal Component
 * Provides UI for replying to, forwarding, and composing emails
 */

import React, { useState } from 'react';
import {
  X,
  Send,
  Forward,
  Reply,
  Mail,
} from 'lucide-react';

interface EmailActionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'reply' | 'forward' | 'compose';
  originalEmail?: {
    from_email: string;
    subject: string;
    body: string;
    message_id?: string;
    date?: string;
  };
  onSuccess?: () => void;
}

export const EmailActionsModal: React.FC<EmailActionsModalProps> = ({
  isOpen,
  onClose,
  mode,
  originalEmail,
  onSuccess,
}) => {
  const [toEmail, setToEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Initialize form based on mode
  React.useEffect(() => {
    if (isOpen && originalEmail) {
      if (mode === 'reply') {
        setToEmail(originalEmail.from_email || '');
        const replySubject = originalEmail.subject?.startsWith('Re:')
          ? originalEmail.subject
          : `Re: ${originalEmail.subject}`;
        setSubject(replySubject);
        setBody('');
      } else if (mode === 'forward') {
        setSubject(`Fwd: ${originalEmail.subject}`);
        setBody(`\n\n---------- Forwarded message ----------\nFrom: ${originalEmail.from_email}\nDate: ${originalEmail.date}\nSubject: ${originalEmail.subject}\n\n${originalEmail.body}`);
      } else if (mode === 'compose') {
        setToEmail('');
        setSubject('');
        setBody('');
      }
    }
    setError('');
    setSuccess(false);
  }, [isOpen, mode, originalEmail]);

  if (!isOpen) return null;

  const handleSend = async () => {
    // Validation
    if (!toEmail || !subject || !body) {
      setError('Please fill in all fields');
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(toEmail)) {
      setError('Please enter a valid email address');
      return;
    }

    setSending(true);
    setError('');

    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE = 'http://localhost:8000/api/v1';

      let endpoint = '';
      let payload: any = {};

      if (mode === 'reply') {
        endpoint = `${API_BASE}/email-actions/reply`;
        payload = {
          original_email: originalEmail,
          reply_body: body,
          reply_all: false,
        };
      } else if (mode === 'forward') {
        endpoint = `${API_BASE}/email-actions/forward`;
        payload = {
          original_email: originalEmail,
          forward_to: toEmail,
          forward_message: body.split('\n\n----------')[0], // Get only the new message part
        };
      } else if (mode === 'compose') {
        endpoint = `${API_BASE}/email-actions/compose`;
        payload = {
          to: toEmail,
          subject: subject,
          body: body,
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        if (onSuccess) onSuccess();
        setTimeout(() => {
          handleClose();
        }, 2000);
      } else {
        setError(data.detail || 'Failed to send email');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Error sending email:', err);
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    if (!sending) {
      setToEmail('');
      setSubject('');
      setBody('');
      setError('');
      setSuccess(false);
      onClose();
    }
  };

  const getModeIcon = () => {
    switch (mode) {
      case 'reply':
        return <Reply className="w-6 h-6 text-blue-600" />;
      case 'forward':
        return <Forward className="w-6 h-6 text-green-600" />;
      case 'compose':
        return <Mail className="w-6 h-6 text-purple-600" />;
    }
  };

  const getModeTitle = () => {
    switch (mode) {
      case 'reply':
        return 'Reply to Email';
      case 'forward':
        return 'Forward Email';
      case 'compose':
        return 'Compose New Email';
    }
  };

  const getButtonText = () => {
    switch (mode) {
      case 'reply':
        return 'Send Reply';
      case 'forward':
        return 'Forward Email';
      case 'compose':
        return 'Send Email';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            {getModeIcon()}
            <h2 className="text-xl font-semibold text-gray-900">{getModeTitle()}</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={sending}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-4">
          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-green-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">
                    Email sent successfully!
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm font-medium text-red-800">{error}</p>
            </div>
          )}

          {/* To Field */}
          <div>
            <label htmlFor="to" className="block text-sm font-medium text-gray-700 mb-1">
              To
            </label>
            <input
              type="email"
              id="to"
              value={toEmail}
              onChange={(e) => setToEmail(e.target.value)}
              disabled={mode === 'reply' || sending}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              placeholder="recipient@example.com"
            />
          </div>

          {/* Subject Field */}
          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
              Subject
            </label>
            <input
              type="text"
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={sending}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              placeholder="Email subject"
            />
          </div>

          {/* Message Body */}
          <div>
            <label htmlFor="body" className="block text-sm font-medium text-gray-700 mb-1">
              Message
            </label>
            <textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled={sending}
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 font-mono text-sm"
              placeholder="Write your message here..."
            />
            <p className="text-xs text-gray-500 mt-1">
              {body.length} characters
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleClose}
            disabled={sending}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSend}
            disabled={sending || success}
            className="inline-flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {sending ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Sending...
              </>
            ) : success ? (
              <>
                <Send className="w-5 h-5 mr-2" />
                Sent!
              </>
            ) : (
              <>
                <Send className="w-5 h-5 mr-2" />
                {getButtonText()}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailActionsModal;
