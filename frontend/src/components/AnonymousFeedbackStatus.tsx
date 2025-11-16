import React, { useState } from 'react';
import { Search, Clock, CheckCircle, AlertCircle, Shield } from 'lucide-react';
import { anonymousFeedbackService } from '../services/anonymousFeedbackService';
import type { AnonymousFeedbackStatus } from '../types';
const AnonymousFeedbackStatus: React.FC = () => {
  const [trackingId, setTrackingId] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [statusData, setStatusData] = useState<AnonymousFeedbackStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const handleStatusCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackingId.trim()) {
      setError('Please enter a tracking ID');
      return;
    }
    setIsSearching(true);
    setError(null);
    try {
      const data = await anonymousFeedbackService.checkFeedbackStatus(trackingId.trim());
      if (data) {
        setStatusData(data);
      } else {
        setError('Tracking ID not found. Please check your tracking ID or contact support.');
      }
    } catch (err: any) {
      console.error('Status check error:', err);
      setError(err.message || 'Unable to check status. Please try again later.');
    } finally {
      setIsSearching(false);
    }
  };
  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'resolved':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'investigating':
        return <Clock className="w-6 h-6 text-blue-500" />;
      case 'under_review':
      case 'pending':
        return <Clock className="w-6 h-6 text-yellow-500" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-500" />;
    }
  };
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'investigating':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'under_review':
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };
  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };
  const formatDaysAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };
  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Check Feedback Status
        </h2>
        <p className="text-gray-600">
          Enter your tracking ID to check the status of your anonymous feedback submission.
        </p>
      </div>
      {/* Search Form */}
      <form onSubmit={handleStatusCheck} className="mb-8">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={trackingId}
              onChange={(e) => {
                setTrackingId(e.target.value);
                if (error) setError(null);
              }}
              placeholder="Enter your tracking ID..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !trackingId.trim()}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSearching ? 'Searching...' : 'Check Status'}
          </button>
        </div>
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
      </form>
      {/* Status Results */}
      {statusData && (
        <div className="space-y-6">
          {/* Status Header */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              {getStatusIcon(statusData.status)}
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Status: {statusData.status?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                <p className="text-sm text-gray-600">
                  Submitted {formatDaysAgo(statusData.created_at)} days ago
                </p>
              </div>
            </div>
            <div className="text-right">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(statusData.status)}`}>
                {statusData.severity?.charAt(0).toUpperCase() + statusData.severity?.slice(1)} Severity
              </span>
            </div>
          </div>
          {/* Status Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Category</h4>
              <p className="text-blue-800">
                {statusData.category?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
            </div>
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-2">Follow-ups Allowed</h4>
              <p className="text-green-800">
                {statusData.follow_ups_allowed ? 'Yes' : 'No'}
              </p>
            </div>
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="font-semibold text-purple-900 mb-2">Submitted</h4>
              <p className="text-purple-800">
                {new Date(statusData.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <h4 className="font-semibold text-orange-900 mb-2">Last Updated</h4>
              <p className="text-orange-800">
                {new Date(statusData.last_updated).toLocaleDateString()}
              </p>
            </div>
          </div>
          {/* HR Notes */}
          {statusData.hr_notes && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">HR Notes</h4>
              <p className="text-gray-700">{statusData.hr_notes}</p>
            </div>
          )}
          {/* Resolution Details */}
          {statusData.resolution_details && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-2">Resolution Details</h4>
              <p className="text-green-800">{statusData.resolution_details}</p>
            </div>
          )}
          {/* Privacy Reminder */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start">
              <Shield className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <h4 className="font-semibold text-blue-900 mb-1">Privacy Protected</h4>
                <p className="text-sm text-blue-800">
                  Your identity remains completely anonymous throughout this process.
                </p>
              </div>
            </div>
          </div>
          {/* Action Buttons */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => {
                setStatusData(null);
                setTrackingId('');
              }}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Check Another
            </button>
            <button
              onClick={() => window.open('/anonymous-feedback', '_blank')}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Submit New Feedback
            </button>
          </div>
        </div>
      )}
      {/* Help Section */}
      {!statusData && (
        <div className="mt-8 space-y-6">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-3">Need Help?</h3>
            <div className="space-y-3 text-sm text-gray-700">
              <div>
                <strong>Lost your tracking ID?</strong>
                <p className="mt-1">
                  Unfortunately, we cannot locate your specific submission without the tracking ID.
                  This is part of our commitment to complete anonymity. You can submit new feedback if needed.
                </p>
              </div>
              <div>
                <strong>Need immediate assistance?</strong>
                <p className="mt-1">
                  Contact HR directly through confidential channels or use external reporting hotlines
                  for urgent concerns.
                </p>
              </div>
              <div>
                <strong>Concerns about retaliation?</strong>
                <p className="mt-1">
                  Retaliation against anonymous feedback reporters is strictly prohibited by company policy.
                </p>
              </div>
            </div>
          </div>
          <div className="text-center">
            <button
              onClick={() => window.open('/anonymous-feedback', '_blank')}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              Submit New Anonymous Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default AnonymousFeedbackStatus;