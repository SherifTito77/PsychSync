/**
 * Example Integration of Email Actions
 * Shows how to add email action buttons to your dashboard
 */

import React from 'react';
import { Reply, Forward, Mail } from 'lucide-react';
import { useEmailActions } from '@/hooks/useEmailActions';
import EmailActionsModal from '@/components/EmailActionsModal';

export const EmailActionsExample: React.FC = () => {
  const { isOpen, mode, originalEmail, openReply, openForward, openCompose, close } =
    useEmailActions();

  // Example email data (this would come from your email monitoring data)
  const exampleEmail = {
    from_email: 'sender@example.com',
    subject: 'Important Security Alert',
    body: 'This is a sample email body...',
    message_id: 'msg-12345',
    date: new Date().toISOString(),
    cc: ['cc@example.com'],
  };

  return (
    <>
      <div className="space-y-6 p-6">
        <h3 className="text-lg font-semibold text-gray-900">Email Actions Demo</h3>

        {/* Example 1: Reply Button */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Reply to Email</h4>
          <p className="text-sm text-gray-600 mb-4">
            Click to reply to the selected email
          </p>
          <button
            onClick={() => openReply(exampleEmail)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Reply className="w-5 h-5 mr-2" />
            Reply
          </button>
        </div>

        {/* Example 2: Forward Button */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Forward Email</h4>
          <p className="text-sm text-gray-600 mb-4">
            Click to forward the selected email to someone else
          </p>
          <button
            onClick={() => openForward(exampleEmail)}
            className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            <Forward className="w-5 h-5 mr-2" />
            Forward
          </button>
        </div>

        {/* Example 3: Compose New Email */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Compose New Email</h4>
          <p className="text-sm text-gray-600 mb-4">
            Click to compose a brand new email
          </p>
          <button
            onClick={openCompose}
            className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            <Mail className="w-5 h-5 mr-2" />
            Compose
          </button>
        </div>

        {/* Example 4: Action Menu */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Email Action Menu</h4>
          <p className="text-sm text-gray-600 mb-4">
            Dropdown menu with multiple actions (like in Gmail)
          </p>
          <div className="relative inline-block text-left group">
            <button
              type="button"
              className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              onClick={() => {}}
            >
              Actions
              <svg
                className="w-5 h-5 ml-2"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
            <div className="absolute right-0 mt-2 w-56 origin-top-right bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 hidden group-hover:block z-10">
              <div className="py-1">
                <button
                  onClick={() => openReply(exampleEmail)}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <Reply className="w-4 h-4 mr-3" />
                  Reply
                </button>
                <button
                  onClick={() => openForward(exampleEmail)}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <Forward className="w-4 h-4 mr-3" />
                  Forward
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Email Actions Modal */}
      <EmailActionsModal
        isOpen={isOpen}
        mode={mode}
        originalEmail={originalEmail || undefined}
        onClose={close}
        onSuccess={() => {
          console.log('Email sent successfully!');
          // Refresh your data here
        }}
      />
    </>
  );
};

export default EmailActionsExample;
