// HR Review Dashboard Component
// Production-ready React component for HR personnel to review anonymous feedback
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Shield,
  AlertTriangle,
  Eye,
  Clock,
  TrendingUp,
  Users,
  Filter,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  FileText,
  Calendar,
  Target,
  Activity,
  BarChart3,
  Info
} from 'lucide-react';
import {
  FeedbackReviewResponse,
  FeedbackItemForReview,
  FeedbackUpdateRequest,
  FeedbackStatisticsResponse,
} from '@/types/anonymousFeedback';
import { anonymousFeedbackService } from '@/services/anonymousFeedbackService';
interface HRReviewDashboardProps {
  organizationId?: string;
  className?: string;
}
export const HRReviewDashboard: React.FC<HRReviewDashboardProps> = ({
  organizationId,
  className
}) => {
  const [feedbackData, setFeedbackData] = useState<FeedbackReviewResponse | null>(null);
  const [statistics, setStatistics] = useState<FeedbackStatisticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    feedback_type: '',
    date_from: '',
    date_to: '',
  });
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackItemForReview | null>(null);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [updateForm, setUpdateForm] = useState<FeedbackUpdateRequest>({
    new_status: 'pending_review',
    internal_notes: '',
    public_notes: '',
    actions_taken: '',
  });
  const [isUpdating, setIsUpdating] = useState(false);
  // Load feedback data
  const loadFeedbackData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const feedbackResponse = await anonymousFeedbackService.getFeedbackForReview({
        organization_id: organizationId,
        ...filters,
      });
      setFeedbackData(feedbackResponse);
      // Load statistics
      try {
        const statsResponse = await anonymousFeedbackService.getFeedbackStatistics({
          organization_id: organizationId,
        });
        setStatistics(statsResponse);
      } catch (statsErr) {
        console.error('Failed to load statistics:', statsErr);
        // Don't fail the whole dashboard if stats fail
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load feedback data');
    } finally {
      setIsLoading(false);
    }
  }, [organizationId, filters]);
  // Initial load
  useEffect(() => {
    loadFeedbackData();
  }, [loadFeedbackData]);
  // Handle filter changes
  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  }, []);
  // Clear filters
  const clearFilters = useCallback(() => {
    setFilters({
      status: '',
      severity: '',
      feedback_type: '',
      date_from: '',
      date_to: '',
    });
  }, []);
  // Handle feedback update
  const handleUpdateFeedback = useCallback(async () => {
    if (!selectedFeedback) return;
    setIsUpdating(true);
    try {
      await anonymousFeedbackService.updateFeedbackStatus(
        selectedFeedback.id,
        updateForm
      );
      // Reload data
      await loadFeedbackData();
      setUpdateDialogOpen(false);
      setSelectedFeedback(null);
      setUpdateForm({
        new_status: '',
        internal_notes: '',
        public_notes: '',
        actions_taken: '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to update feedback status');
    } finally {
      setIsUpdating(false);
    }
  }, [selectedFeedback, updateForm, loadFeedbackData]);
  // Get severity color
  const getSeverityColor = useCallback((severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  }, []);
  // Get status color
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'critical':
      case 'escalated':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'investigating':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'resolved':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'closed':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'requires_more_info':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'pending_review':
      default:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  }, []);
  // Calculate summary cards
  const summaryCards = useMemo(() => {
    if (!feedbackData?.summary) return [];
    const { summary } = feedbackData;
    return [
      {
        title: 'Total Submissions',
        value: feedbackData.total_count,
        icon: FileText,
        color: 'text-blue-600 bg-blue-50',
        description: 'All feedback items',
      },
      {
        title: 'Critical Issues',
        value: summary.critical_count || 0,
        icon: AlertTriangle,
        color: 'text-red-600 bg-red-50',
        description: 'Requiring immediate attention',
      },
      {
        title: 'Pending Review',
        value: summary.pending_review_count || 0,
        icon: Clock,
        color: 'text-yellow-600 bg-yellow-50',
        description: 'Awaiting initial review',
      },
      {
        title: 'Psychological Safety',
        value: summary.psychological_safety_concerns || 0,
        icon: Shield,
        color: 'text-purple-600 bg-purple-50',
        description: 'Psychological safety concerns',
      },
    ];
  }, [feedbackData]);
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  if (error) {
    return (
      <Alert className="max-w-2xl mx-auto mt-8 border-red-200 bg-red-50">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{error}</AlertDescription>
        <Button
          onClick={loadFeedbackData}
          className="mt-4"
          variant="outline"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </Alert>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="w-8 h-8" />
            Anonymous Feedback Review
          </h1>
          <p className="text-gray-600 mt-1">
            Review and manage anonymous feedback while maintaining complete submitter anonymity
          </p>
        </div>
        <Button onClick={loadFeedbackData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>
      {/* Privacy Guidelines */}
      <Alert className="border-green-200 bg-green-50">
        <Shield className="w-4 h-4" />
        <AlertDescription>
          <strong>Privacy Reminder:</strong> All feedback displayed is completely anonymous.
          Do not attempt to identify submitters. Focus on addressing issues, not finding sources.
        </AlertDescription>
      </Alert>
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <Card key={index}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{card.title}</p>
                    <p className="text-2xl font-bold mt-1">{card.value}</p>
                    <p className="text-xs text-gray-500 mt-1">{card.description}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${card.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Statuses</SelectItem>
                <SelectItem value="pending_review">Pending Review</SelectItem>
                <SelectItem value="investigating">Investigating</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
                <SelectItem value="escalated">Escalated</SelectItem>
                <SelectItem value="requires_more_info">Requires More Info</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.severity} onValueChange={(value) => handleFilterChange('severity', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.feedback_type} onValueChange={(value) => handleFilterChange('feedback_type', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Types</SelectItem>
                <SelectItem value="toxic_behavior">Toxic Behavior</SelectItem>
                <SelectItem value="psychological_safety">Psychological Safety</SelectItem>
                <SelectItem value="harassment">Harassment</SelectItem>
                <SelectItem value="discrimination">Discrimination</SelectItem>
                <SelectItem value="safety_concern">Safety Concern</SelectItem>
                <SelectItem value="retaliation">Retaliation</SelectItem>
              </SelectContent>
            </Select>
            <Input
              type="date"
              placeholder="From Date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
            />
            <Input
              type="date"
              placeholder="To Date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
            />
            <Button onClick={clearFilters} variant="outline">
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>
      {/* Feedback List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Feedback Items
              {feedbackData && (
                <Badge variant="outline">
                  {feedbackData.total_count} items
                </Badge>
              )}
            </span>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {feedbackData?.feedbacks && feedbackData.feedbacks.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Days Pending</TableHead>
                    <TableHead>Urgency</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {feedbackData.feedbacks.map((feedback) => (
                    <TableRow key={feedback.id}>
                      <TableCell className="capitalize">
                        {feedback.feedback_type.replace('_', ' ')}
                      </TableCell>
                      <TableCell className="capitalize">
                        {feedback.category.replace('_', ' ')}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getSeverityColor(feedback.severity)}>
                          {feedback.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getStatusColor(feedback.status)}>
                          {feedback.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {anonymousFeedbackService.formatSubmissionDate(feedback.submitted_at)}
                      </TableCell>
                      <TableCell>{feedback.days_pending}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${feedback.urgency_score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs">{Math.round(feedback.urgency_score * 100)}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Dialog open={updateDialogOpen && selectedFeedback?.id === feedback.id}>
                          <DialogTrigger asChild>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedFeedback(feedback)}
                            >
                              Review
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle>Review Feedback</DialogTitle>
                              <DialogDescription>
                                Update the status and add notes for this feedback item.
                              </DialogDescription>
                            </DialogHeader>
                            {selectedFeedback && (
                              <div className="space-y-6">
                                {/* Feedback Summary */}
                                <div className="p-4 bg-gray-50 rounded-lg">
                                  <h4 className="font-medium mb-2">Feedback Summary</h4>
                                  <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                      <span>Type:</span>
                                      <span className="capitalize">{selectedFeedback.feedback_type.replace('_', ' ')}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span>Category:</span>
                                      <span className="capitalize">{selectedFeedback.category.replace('_', ' ')}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span>Severity:</span>
                                      <Badge variant="outline" className={getSeverityColor(selectedFeedback.severity)}>
                                        {selectedFeedback.severity}
                                      </Badge>
                                    </div>
                                    <div className="flex justify-between">
                                      <span>Status:</span>
                                      <Badge variant="outline" className={getStatusColor(selectedFeedback.status)}>
                                        {selectedFeedback.status.replace('_', ' ')}
                                      </Badge>
                                    </div>
                                  </div>
                                </div>
                                {/* Description */}
                                <div>
                                  <h4 className="font-medium mb-2">Description</h4>
                                  <div className="p-3 bg-gray-50 rounded-lg text-sm max-h-32 overflow-y-auto">
                                    {selectedFeedback.description}
                                  </div>
                                </div>
                                {/* Update Form */}
                                <div className="space-y-4">
                                  <div>
                                    <label className="block text-sm font-medium mb-2">
                                      New Status
                                    </label>
                                    <Select
                                      value={updateForm.new_status}
                                      onValueChange={(value) => setUpdateForm(prev => ({ ...prev, new_status: value }))}
                                    >
                                      <SelectTrigger>
                                        <SelectValue placeholder="Select new status" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="pending_review">Pending Review</SelectItem>
                                        <SelectItem value="investigating">Investigating</SelectItem>
                                        <SelectItem value="resolved">Resolved</SelectItem>
                                        <SelectItem value="closed">Closed</SelectItem>
                                        <SelectItem value="escalated">Escalated</SelectItem>
                                        <SelectItem value="requires_more_info">Requires More Info</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div>
                                    <label className="block text-sm font-medium mb-2">
                                      Internal Notes (HR only)
                                    </label>
                                    <Textarea
                                      placeholder="Private notes for HR team..."
                                      value={updateForm.internal_notes}
                                      onChange={(e) => setUpdateForm(prev => ({ ...prev, internal_notes: e.target.value }))}
                                      rows={3}
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-sm font-medium mb-2">
                                      Public Notes (Visible to submitter)
                                    </label>
                                    <Textarea
                                      placeholder="Notes that will be visible to the submitter..."
                                      value={updateForm.public_notes}
                                      onChange={(e) => setUpdateForm(prev => ({ ...prev, public_notes: e.target.value }))}
                                      rows={3}
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-sm font-medium mb-2">
                                      Actions Taken
                                    </label>
                                    <Textarea
                                      placeholder="Describe actions taken or planned..."
                                      value={updateForm.actions_taken}
                                      onChange={(e) => setUpdateForm(prev => ({ ...prev, actions_taken: e.target.value }))}
                                      rows={3}
                                    />
                                  </div>
                                </div>
                                <div className="flex justify-end gap-3">
                                  <Button
                                    variant="outline"
                                    onClick={() => setUpdateDialogOpen(false)}
                                  >
                                    Cancel
                                  </Button>
                                  <Button
                                    onClick={handleUpdateFeedback}
                                    disabled={isUpdating || !updateForm.new_status}
                                  >
                                    {isUpdating ? (
                                      <>
                                        <LoadingSpinner size="sm" className="mr-2" />
                                        Updating...
                                      </>
                                    ) : (
                                      'Update Status'
                                    )}
                                  </Button>
                                </div>
                              </div>
                            )}
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No feedback items found matching the current filters.</p>
              <Button variant="outline" onClick={clearFilters} className="mt-4">
                Clear Filters
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      {/* Psychological Safety Insights */}
      {statistics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Organizational Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Psychological Safety Level
                </h4>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-semibold capitalize">
                      {statistics.insights.psychological_safety_level}
                    </span>
                    <Badge variant="outline" className={
                      statistics.insights.psychological_safety_level === 'healthy' ? 'text-green-600 bg-green-50' :
                      statistics.insights.psychological_safety_level === 'moderate' ? 'text-yellow-600 bg-yellow-50' :
                      statistics.insights.psychological_safety_level === 'concerning' ? 'text-orange-600 bg-orange-50' :
                      'text-red-600 bg-red-50'
                    }>
                      {statistics.insights.psychological_safety_level}
                    </Badge>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Primary Concerns
                </h4>
                <div className="space-y-2">
                  {statistics.insights.primary_concerns.slice(0, 3).map((concern, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm capitalize">{concern.category.replace('_', ' ')}</span>
                      <Badge variant="outline">{concern.count}</Badge>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Recommendations
                </h4>
                <div className="space-y-2">
                  {statistics.insights.recommendations.slice(0, 3).map((recommendation, index) => (
                    <div key={index} className="text-sm p-2 bg-blue-50 border-l-4 border-blue-200">
                      {recommendation}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Data Quality
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Sample Size:</span>
                    <span>{statistics.data_quality.sample_size}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Confidence Level:</span>
                    <span className="capitalize">{statistics.data_quality.confidence_level}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Resolution Time:</span>
                    <span>{statistics.average_resolution_time || 'N/A'} days</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};