// src/components/OnboardingNavigation.tsx
// Simple navigation to switch between onboarding flows
import React, { useState } from 'react';

const OnboardingNavigation: React.FC = () => {
  const [isMinimized, setIsMinimized] = useState(true);

  return (
    <div className={`fixed top-20 right-4 z-[100] bg-white rounded-lg shadow-xl border border-gray-200 transition-all duration-300 ${isMinimized ? 'p-2' : 'p-4'}`}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsMinimized(!isMinimized)}
        className="w-full flex items-center justify-between text-gray-700 hover:text-gray-900"
        title={isMinimized ? 'Expand navigation' : 'Minimize'}
      >
        <span className={`font-semibold ${isMinimized ? 'text-xs' : 'text-sm'}`}>
          {isMinimized ? '📋 Menu' : 'Quick Navigation'}
        </span>
        <span className="text-lg ml-2">
          {isMinimized ? '▶' : '▼'}
        </span>
      </button>

      {/* Content - Hidden when minimized */}
      {!isMinimized && (
        <div className="mt-3 space-y-2">
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
            🔐 Traditional Login
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

          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Test Credentials:<br />
              📧 test@example.com<br />
              🔑 test123
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnboardingNavigation;
