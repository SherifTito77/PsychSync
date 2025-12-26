// src/components/OnboardingNavigation.tsx
// Simple navigation to switch between onboarding flows
import React from 'react';

const OnboardingNavigation: React.FC = () => {
  return (
    <div className="fixed top-4 right-4 z-50 bg-white rounded-lg shadow-lg border border-gray-200 p-4">
      <h4 className="font-semibold text-gray-900 mb-3 text-sm">Quick Navigation</h4>
      <div className="space-y-2">
        <a
          href="/"
          className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
        >
          🚀 New Value-First Onboarding
        </a>
        <a
          href="/login"
          className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
        >
          🔐 Traditional Login (testuser2025@example.com)
        </a>
        <a
          href="/register"
          className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
        >
          📝 Register New Account
        </a>
        <a
          href="/preview"
          className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
        >
          👁️ Quick Assessment Preview
        </a>
        <a
          href="/assessments"
          className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
        >
          📊 All Assessments (requires login)
        </a>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Test Credentials:<br />
          📧 testuser2025@example.com<br />
          🔑 testuser2025@example.com
        </p>
      </div>
    </div>
  );
};

export default OnboardingNavigation;