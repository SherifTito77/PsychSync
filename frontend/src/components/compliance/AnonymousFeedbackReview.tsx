import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Shield,
  Clock,
  CheckCircle,
  Search,
  Filter,
  Download,
  MessageSquare,
  FileText,
  Calendar,
  User,
  Scale
} from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
import { AnonymousFeedback } from '../../types/compliance';
import { Button } from '../common/Button';
import { Card } from '../common/card';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
interface AnonymousFeedbackReviewProps {
  className?: string;
}
export const AnonymousFeedbackReview: React.FC<AnonymousFeedbackReviewProps> = ({ className = '' }) => {
  const [feedback, setFeedback] = useState<AnonymousFeedback[]>([]);
  const [filteredFeedback, setFilteredFeedback] = useState<AnonymousFeedback[]>([]);
  const [selectedFeedback, setSelectedFeedback] = useState<AnonymousFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [filters, setFilters] = useState({
    status: 'all',
    severity: 'all',
    feedback_type: 'all',
    search: ''
  });
  const { showNotification } = useNotification();
  useEffect(() => {
    loadFeedback();
  }, []);
  useEffect(() => {
    filterFeedback();
  }, [feedback, filters]);
  const loadFeedback = async () => {
    try {
      setLoading(true);
      const data = await complianceService.getFeedbackForReview(filters);
      setFeedback(data.feedbacks);
    } catch (error) {
      console.error('Failed to load feedback:', error);
      showNotification('Failed to load feedback', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterFeedback = () => {
    let filtered = [...feedback];
    if (filters.status !== 'all') {
      filtered = filtered.filter(f => f.status === filters.status);
    }
    if (filters.severity !== 'all') {
      filtered = filtered.filter(f => f.severity === filters.severity);
    }
    if (filters.feedback_type !== 'all') {
      filtered = filtered.filter(f => f.feedback_type === filters.feedback_type);
    }
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(f =>
        f.feedback_type.toLowerCase().includes(search) ||
        f.category.toLowerCase().includes(search) ||
        f.description.toLowerCase().includes(search)
      );
    }
    setFilteredFeedback(filtered);
  };
  const updateFeedbackStatus = async (feedbackId: string, update: any) => {
    try {
      setUpdating(true);
      await complianceService.updateFeedbackStatus(feedbackId, update);
      showNotification('Feedback updated successfully', 'success');
      await loadFeedback();
      // Update selected feedback if it's currently selected
      if (selectedFeedback?.id === feedbackId) {
        setSelectedFeedback(prev => prev ? { ...prev, ...update } : null);
      }
    } catch (error) {
      showNotification('Failed to update feedback', 'error');
    } finally {
      setUpdating(false);
    }
  };
  const exportReport = async () => {
    try {
      const response = await fetch('/api/v1/reports/anonymous-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ filters })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `anonymous-feedback-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Report exported successfully', 'success');
      }
    } catch (error) {
      showNotification('Failed to export report', 'error');
    }
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  const stats = {
    total: feedback.length,
    critical: feedback.filter(f => f.severity === 'critical').length,
    high: feedback.filter(f => f.severity === 'high').length,
    pending: feedback.filter(f => f.status === 'pending_review').length
  };
  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Anonymous Feedback Review</h1>
          <p className="text-gray-600 mt-1">
            Review and respond to employee feedback. Remember: submissions are anonymous.
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={exportReport}
            icon={<Download className="w-4 h-4" />}
          >
            Export Report
          </Button>
        </div>
      </div>
      {/* Privacy Reminder */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-yellow-400" />
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <strong>Privacy Reminder:</strong> These submissions are completely anonymous.
              Do not attempt to identify submitters. Any identifying information has been removed.
            </p>
          </div>
        </div>
      </div>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          value={stats.total}
          icon={<MessageSquare className="w-6 h-6" />}
          color="blue"
        />
        <StatsCard
          value={stats.critical}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          sub
        />
        <StatsCard
          value={stats.high}
          icon={<Scale className="w-6 h-6" />}
          color="orange"
          sub
        />
        <StatsCard
          value={stats.pending}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
          sub
        />
      </div>
      {/* Filters */}
      <Card>
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search feedback..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="pending_review">Pending Review</option>
              <option value="under_review">Under Review</option>
              <option value="investigating">Investigating</option>
              <option value="action_taken">Action Taken</option>
              <option value="resolved">Resolved</option>
            </select>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={filters.feedback_type}
              onChange={(e) => setFilters({ ...filters, feedback_type: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              <option value="harassment">Harassment</option>
              <option value="discrimination">Discrimination</option>
              <option value="safety">Safety</option>
              <option value="toxic_culture">Toxic Culture</option>
            </select>
          </div>
        </div>
      </Card>
      {/* Feedback List and Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feedback List */}
        <div className="space-y-4">
          {filteredFeedback.length === 0 ? (
            <Card>
              <div className="text-center py-8">
                <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No feedback found matching your filters</p>
              </div>
            </Card>
          ) : (
            filteredFeedback.map((item) => (
              <FeedbackCard
                key={item.id}
                feedback={item}
                onClick={() => setSelectedFeedback(item)}
                isSelected={selectedFeedback?.id === item.id}
              />
            ))
          )}
        </div>
        {/* Feedback Detail Panel */}
        <div className="lg:sticky lg:top-6 h-fit">
          {selectedFeedback ? (
            <FeedbackDetailPanel
              feedback={selectedFeedback}
              onUpdate={(update) => updateFeedbackStatus(selectedFeedback.id, update)}
              updating={updating}
            />
          ) : (
            <Card>
              <div className="text-center py-12 text-gray-500">
                <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p>Select feedback to view details</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
// Helper Components
interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'orange';
  subtitle?: string;
}
const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color, subtitle }) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-600',
      green: 'bg-green-500 text-green-600',
      yellow: 'bg-yellow-500 text-yellow-600',
      red: 'bg-red-500 text-red-600',
      orange: 'bg-orange-500 text-orange-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <Card>
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-opacity-10 ${getColorClasses(color)}`}>
          {icon}
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </Card>
  );
};
interface FeedbackCardProps {
  feedback: AnonymousFeedback;
  onClick: () => void;
  isSelected: boolean;
}
const FeedbackCard: React.FC<FeedbackCardProps> = ({ feedback, onClick, isSelected }) => {
  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-blue-100 text-blue-800 border-blue-300'
    };
    return colors[severity as keyof typeof colors] || colors.medium;
  };
  const getDaysAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return `${Math.ceil(diffDays / 7)} weeks ago`;
  };
  return (
    <Card
      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
        isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(feedback.severity)}`}>
            {feedback.severity.toUpperCase()}
          </span>
          <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
            {feedback.feedback_type.replace('_', ' ').toUpperCase()}
          </span>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">{getDaysAgo(feedback.submitted_at)}</p>
          <StatusBadge status={feedback.status} />
        </div>
      </div>
      <p className="text-sm text-gray-700 line-clamp-3 mb-3 leading-relaxed">
        {feedback.description}
      </p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span>Category: <strong>{feedback.category}</strong></span>
          {feedback.evidence_count > 0 && (
            <span className="flex items-center">
              <FileText className="w-3 h-3 mr-1" />
              {feedback.evidence_count} file(s)
            </span>
          )}
        </div>
        {feedback.has_follow_ups && (
          <span className="flex items-center text-blue-600">
            <MessageSquare className="w-3 h-3 mr-1" />
            Follow-up
          </span>
        )}
      </div>
    </Card>
  );
};
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusConfig = {
    pending_review: { color: 'yellow', label: 'Pending' },
    under_review: { color: 'blue', label: 'Under Review' },
    investigating: { color: 'purple', label: 'Investigating' },
    requires_more_info: { color: 'orange', label: 'Needs Info' },
    action_taken: { color: 'green', label: 'Action Taken' },
    resolved: { color: 'green', label: 'Resolved' },
    closed: { color: 'gray', label: 'Closed' }
  };
  const config = statusConfig[status as keyof typeof statusConfig] || {
    color: 'gray',
    label: status
  };
  return <Badge color={config.color} size="sm">{config.label}</Badge>;
};
interface FeedbackDetailPanelProps {
  feedback: AnonymousFeedback;
  onUpdate: (update: any) => void;
  updating: boolean;
}
const FeedbackDetailPanel: React.FC<FeedbackDetailPanelProps> = ({
  feedback,
  onUpdate,
  updating
}) => {
  const [newStatus, setNewStatus] = useState(feedback.status);
  const [internalNotes, setInternalNotes] = useState('');
  const [publicNotes, setPublicNotes] = useState('');
  const [actionsTaken, setActionsTaken] = useState('');
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onUpdate({
      new_status: newStatus,
      internal_notes: internalNotes,
      public_notes: publicNotes,
      actions_taken: actionsTaken
    });
    // Clear form
    setInternalNotes('');
    setPublicNotes('');
    setActionsTaken('');
  };
  return (
    <Card>
      <div className="space-y-6">
        {/* Header */}
        <div className="border-b pb-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-semibold">Feedback Details</h2>
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                feedback.severity === 'critical' ? 'bg-red-100 text-red-800' :
                feedback.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {feedback.severity.toUpperCase()}
              </span>
              <StatusBadge status={feedback.status} />
            </div>
          </div>
          <div className="text-sm text-gray-600">
            Submitted {new Date(feedback.submitted_at).toLocaleDateString()} •
            Category: {feedback.category}
          </div>
        </div>
        {/* Feedback Content */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type of Issue
            </label>
            <p className="text-gray-900">{feedback.feedback_type.replace('_', ' ').title()}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <p className="text-gray-900 whitespace-pre-wrap bg-gray-50 p-3 rounded-lg">
              {feedback.description}
            </p>
          </div>
          {feedback.evidence_count > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Evidence
              </label>
              <p className="text-sm text-gray-600">
                {feedback.evidence_count} file(s) attached
              </p>
            </div>
          )}
        </div>
        {/* Update Form */}
        <form onSubmit={handleSubmit} className="space-y-4 border-t pt-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Update Status
            </label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="pending_review">Pending Review</option>
              <option value="under_review">Under Review</option>
              <option value="investigating">Investigating</option>
              <option value="requires_more_info">Requires More Info</option>
              <option value="action_taken">Action Taken</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Internal Notes (HR only)
            </label>
            <textarea
              value={internalNotes}
              onChange={(e) => setInternalNotes(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Notes for internal use only..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Public Notes (Visible to submitter)
            </label>
            <textarea
              value={publicNotes}
              onChange={(e) => setPublicNotes(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Message that will be visible to the submitter..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Actions Taken
            </label>
            <textarea
              value={actionsTaken}
              onChange={(e) => setActionsTaken(e.target.value)}
              rows={2}
              className="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Summary of actions taken..."
            />
          </div>
          <Button
            type="submit"
            disabled={updating}
            loading={updating}
            className="w-full"
          >
            Update Feedback
          </Button>
        </form>
      </div>
    </Card>
  );
};