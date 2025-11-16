import React, { useState, useEffect } from 'react';
import { AlertCircle, Clock, CheckCircle, Filter, Download, TrendingUp, Shield } from 'lucide-react';
interface FeedbackItem {
  id: string;
  feedback_type: string;
  category: string;
  description: string;
  severity: string;
  target_type?: string;
  submitted_at: string;
  days_pending: number;
  status: string;
  evidence_count: number;
  urgency_score: number;
  recommended_actions: string[];
}
interface FeedbackSummary {
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  average_urgency_score: number;
  critical_count: number;
  high_priority_count: number;
  pending_review_count: number;
}
const AnonymousFeedbackHRDashboard: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [summary, setSummary] = useState<FeedbackSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackItem | null>(null);
  const [filters, setFilters] = useState({
    status: 'pending_review',
    severity: '',
    category: ''
  });
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusUpdate, setStatusUpdate] = useState({
    new_status: '',
    resolution_notes: '',
    public_resolution_notes: ''
  });
  // Mock organization ID - in real app this would come from context/props
  const organizationId = 'mock-org-id';
  useEffect(() => {
    loadFeedbackData();
  }, [filters]);
  const loadFeedbackData = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams({
        organization_id: organizationId,
        ...(filters.status && { status_filter: filters.status }),
        ...(filters.severity && { severity_filter: filters.severity }),
        ...(filters.category && { category_filter: filters.category })
      });
      const response = await fetch(`/api/v1/anonymous-feedback/review?${queryParams}`);
      const data = await response.json();
      if (response.ok) {
        setFeedbacks(data.feedbacks || []);
        setSummary(data.summary || {});
      }
    } catch (error) {
      console.error('Failed to load feedback data:', error);
    } finally {
      setLoading(false);
    }
  };
  const updateFeedbackStatus = async (feedbackId: string) => {
    try {
      const response = await fetch(`/api/v1/anonymous-feedback/${feedbackId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(statusUpdate),
      });
      if (response.ok) {
        setShowStatusModal(false);
        setSelectedFeedback(null);
        setStatusUpdate({ new_status: '', resolution_notes: '', public_resolution_notes: '' });
        loadFeedbackData();
      }
    } catch (error) {
      console.error('Failed to update feedback status:', error);
    }
  };
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-700 bg-red-100 border-red-200';
      case 'high': return 'text-orange-700 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-green-700 bg-green-100 border-green-200';
      default: return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'resolved': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'investigating': return <Clock className="w-4 h-4 text-blue-500" />;
      case 'pending_review': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };
  const getUrgencyColor = (score: number) => {
    if (score >= 0.8) return 'text-red-600';
    if (score >= 0.6) return 'text-orange-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading feedback data...</p>
        </div>
      </div>
    );
  }
  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Anonymous Feedback Review</h1>
            <p className="text-gray-600 mt-2">
              Review and manage anonymous employee feedback. All submissions are completely anonymous.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Shield className="w-6 h-6 text-blue-600" />
            <span className="text-sm text-gray-600">100% Anonymous</span>
          </div>
        </div>
      </div>
      {/* Privacy Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start">
          <Shield className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-blue-900 mb-1">Confidentiality Notice</h3>
            <p className="text-sm text-blue-800">
              All feedback is completely anonymous. Do not attempt to identify submitters.
              Focus on addressing the issues, not finding sources. Maintain confidentiality throughout investigations.
            </p>
          </div>
        </div>
      </div>
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Pending</p>
                <p className="text-2xl font-bold text-gray-900">{summary.pending_review_count}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Critical Issues</p>
                <p className="text-2xl font-bold text-red-600">{summary.critical_count}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">High Priority</p>
                <p className="text-2xl font-bold text-orange-600">{summary.high_priority_count}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-500" />
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Urgency</p>
                <p className={`text-2xl font-bold ${getUrgencyColor(summary.average_urgency_score)}`}>
                  {(summary.average_urgency_score * 100).toFixed(0)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>
      )}
      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="pending_review">Pending Review</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              className="p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Categories</option>
              <option value="harassment">Harassment</option>
              <option value="bullying">Bullying</option>
              <option value="discrimination">Discrimination</option>
              <option value="safety_concern">Safety Concern</option>
              <option value="toxic_behavior">Toxic Behavior</option>
            </select>
          </div>
          <button
            onClick={loadFeedbackData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
      {/* Feedback List */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Feedback Items ({feedbacks.length})
          </h2>
        </div>
        {feedbacks.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-600">No feedback items found with current filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Pending
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Urgency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {feedbacks.map((feedback) => (
                  <tr key={feedback.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(feedback.status)}
                        <span className="ml-2 text-sm text-gray-900">
                          {feedback.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityColor(feedback.severity)}`}>
                        {feedback.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {feedback.category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs truncate">
                        {feedback.description}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {feedback.days_pending}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`font-medium ${getUrgencyColor(feedback.urgency_score)}`}>
                        {(feedback.urgency_score * 100).toFixed(0)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedFeedback(feedback)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        Review
                      </button>
                      <button
                        onClick={() => {
                          setSelectedFeedback(feedback);
                          setShowStatusModal(true);
                        }}
                        className="text-gray-600 hover:text-gray-900"
                      >
                        Update
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {/* Review Modal */}
      {selectedFeedback && !showStatusModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <h3 className="text-xl font-bold text-gray-900">Feedback Review</h3>
                <button
                  onClick={() => setSelectedFeedback(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Category</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedFeedback.category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Severity</label>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityColor(selectedFeedback.severity)}`}>
                      {selectedFeedback.severity}
                    </span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Status</label>
                    <div className="flex items-center mt-1">
                      {getStatusIcon(selectedFeedback.status)}
                      <span className="ml-2 text-sm text-gray-900">
                        {selectedFeedback.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Days Pending</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedFeedback.days_pending}</p>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-900">{selectedFeedback.description}</p>
                  </div>
                </div>
                {selectedFeedback.recommended_actions && selectedFeedback.recommended_actions.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Recommended Actions</label>
                    <ul className="space-y-1">
                      {selectedFeedback.recommended_actions.map((action, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-blue-600 mr-2">•</span>
                          <span className="text-sm text-gray-700">{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setShowStatusModal(true);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Update Status
                  </button>
                  <button
                    onClick={() => setSelectedFeedback(null)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Status Update Modal */}
      {showStatusModal && selectedFeedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <h3 className="text-xl font-bold text-gray-900">Update Feedback Status</h3>
                <button
                  onClick={() => {
                    setShowStatusModal(false);
                    setStatusUpdate({ new_status: '', resolution_notes: '', public_resolution_notes: '' });
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">New Status</label>
                  <select
                    value={statusUpdate.new_status}
                    onChange={(e) => setStatusUpdate({ ...statusUpdate, new_status: e.target.value })}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select new status...</option>
                    <option value="pending_review">Pending Review</option>
                    <option value="investigating">Investigating</option>
                    <option value="awaiting_more_info">Awaiting More Info</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                    <option value="escalated">Escalated</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Private Notes (HR Only)</label>
                  <textarea
                    value={statusUpdate.resolution_notes}
                    onChange={(e) => setStatusUpdate({ ...statusUpdate, resolution_notes: e.target.value })}
                    rows={4}
                    placeholder="Internal notes for HR team only..."
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Public Resolution Notes</label>
                  <textarea
                    value={statusUpdate.public_resolution_notes}
                    onChange={(e) => setStatusUpdate({ ...statusUpdate, public_resolution_notes: e.target.value })}
                    rows={4}
                    placeholder="Notes visible to submitter via tracking ID (will be sanitized for privacy)..."
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => updateFeedbackStatus(selectedFeedback.id)}
                    disabled={!statusUpdate.new_status}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Update Status
                  </button>
                  <button
                    onClick={() => {
                      setShowStatusModal(false);
                      setStatusUpdate({ new_status: '', resolution_notes: '', public_resolution_notes: '' });
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default AnonymousFeedbackHRDashboard;