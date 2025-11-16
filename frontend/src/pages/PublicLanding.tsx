// frontend/src/pages/PublicLanding.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Search, Users, BarChart } from 'lucide-react';
const PublicLanding: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="content-wrapper py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to PsychSync
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your comprehensive platform for psychological assessments, team analytics, and anonymous feedback.
          </p>
        </div>
        {/* Main Features */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {/* Anonymous Feedback Section */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex items-center mb-6">
              <Shield className="w-8 h-8 text-blue-600 mr-3" />
              <h2 className="text-2xl font-semibold text-gray-900">
                Anonymous Feedback
              </h2>
            </div>
            <p className="text-gray-600 mb-6">
              Report workplace concerns completely anonymously. Your identity is protected through advanced privacy measures.
            </p>
            <div className="space-y-3 mb-6">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">Completely anonymous reporting</p>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">No IP tracking or user accounts required</p>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">Secure tracking ID for follow-ups</p>
              </div>
            </div>
            <div className="space-y-3">
              <Link
                to="/anonymous-feedback"
                className="block w-full bg-blue-600 text-white text-center py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Submit Anonymous Feedback
              </Link>
              <Link
                to="/feedback-status"
                className="block w-full bg-gray-100 text-gray-700 text-center py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                Check Submission Status
              </Link>
            </div>
          </div>
          {/* Team Analytics Section */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex items-center mb-6">
              <BarChart className="w-8 h-8 text-green-600 mr-3" />
              <h2 className="text-2xl font-semibold text-gray-900">
                Team Analytics
              </h2>
            </div>
            <p className="text-gray-600 mb-6">
              Comprehensive team insights and compatibility analysis powered by advanced psychological assessments.
            </p>
            <div className="space-y-3 mb-6">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">Team compatibility analysis</p>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">Personality assessments</p>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-600 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">Performance predictions</p>
              </div>
            </div>
            <div className="space-y-3">
              <Link
                to="/login"
                className="block w-full bg-green-600 text-white text-center py-3 px-6 rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                Sign In to Dashboard
              </Link>
              <Link
                to="/register"
                className="block w-full bg-gray-200 text-gray-800 text-center py-3 px-6 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                Create Account
              </Link>
            </div>
          </div>
        </div>
        {/* Quick Access Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">
            Quick Access
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <Link
              to="/anonymous-feedback"
              className="flex flex-col items-center p-6 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <Shield className="w-12 h-12 text-blue-600 mb-3" />
              <span className="font-medium text-gray-900">Report Anonymously</span>
            </Link>
            <Link
              to="/feedback-status"
              className="flex flex-col items-center p-6 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <Search className="w-12 h-12 text-green-600 mb-3" />
              <span className="font-medium text-gray-900">Check Status</span>
            </Link>
            <Link
              to="/login"
              className="flex flex-col items-center p-6 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <BarChart className="w-12 h-12 text-purple-600 mb-3" />
              <span className="font-medium text-gray-900">View Dashboard</span>
            </Link>
          </div>
        </div>
        {/* Privacy Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start">
            <Shield className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-blue-900 mb-1">Privacy & Safety</h4>
              <p className="text-sm text-blue-800">
                PsychSync is committed to protecting your privacy. Anonymous feedback submissions are
                completely confidential and cannot be traced back to individuals. All platform data is
                encrypted and handled according to the highest privacy standards.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default PublicLanding;