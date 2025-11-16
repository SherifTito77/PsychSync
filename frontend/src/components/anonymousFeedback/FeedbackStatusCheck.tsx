// Feedback Status Check Component
// Production-ready React component for checking anonymous feedback status
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Separator } from '@/components/ui/separator';
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  Search,
  Eye,
  Shield,
  Calendar,
  Info,
  RefreshCw,
  XCircle,
  TrendingUp,
  Users,
  FileText
} from 'lucide-react';
import { FeedbackStatusResponse } from '@/types/anonymousFeedback';
import { anonymousFeedbackService } from '@/services/anonymousFeedbackService';
interface FeedbackStatusCheckProps {
  initialTrackingId?: string;
  onStatusFound?: (trackingId: string, status: FeedbackStatusResponse) => void;
  className?: string;
}
export const FeedbackStatusCheck: React.FC<FeedbackStatusCheckProps> = ({
  initialTrackingId,
  onStatusFound,
  className
}) => {
  const [trackingId, setTrackingId] = useState(initialTrackingId || '');
  const [isChecking, setIsChecking] = useState(false);
  const [statusData, setStatusData] = useState<FeedbackStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedTrackingIds, setSavedTrackingIds] = useState<Array<any>>([]);
  // Load saved tracking IDs from localStorage
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('anonymous_feedback_tracking_ids') || '[]');
      setSavedTrackingIds(saved);
    } catch (err) {
      console.error('Failed to load saved tracking IDs:', err);
    }
  }, []);
  // Handle status check
  const handleCheckStatus = useCallback(async () => {
    if (!trackingId.trim()) {
      setError('Please enter a tracking ID');
      return;
    }
    setIsChecking(true);
    setError(null);
    try {
      const response = await anonymousFeedbackService.checkFeedbackStatus(trackingId.trim());
      if (response.found) {
        setStatusData(response);
        onStatusFound?.(trackingId.trim(), response);
      } else {
        setError(response.message || 'Tracking ID not found');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to check status');
    } finally {
      setIsChecking(false);
    }
  }, [trackingId, onStatusFound]);
  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleCheckStatus();
  }, [handleCheckStatus]);
  // Use saved tracking ID
  const useSavedTrackingId = useCallback((savedId: string) => {
    setTrackingId(savedId);
    setError(null);
  }, []);
  // Get status icon and color
  const getStatusInfo = useCallback((status?: string) => {
    switch (status) {
      case 'resolved':
        return {
          icon: CheckCircle,
          color: 'text-green-600 bg-green-50 border-green-200',
          text: 'Resolved'
        };
      case 'investigating':
        return {
          icon: Search,
          color: 'text-blue-600 bg-blue-50 border-blue-200',
          text: 'Investigating'
        };
      case 'pending_review':
        return {
          icon: Clock,
          color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
          text: 'Pending Review'
        };
      case 'escalated':
      case 'critical':
        return {
          icon: AlertTriangle,
          color: 'text-red-600 bg-red-50 border-red-200',
          text: status === 'escalated' ? 'Escalated' : 'Critical'
        };
      case 'closed':
        return {
          icon: XCircle,
          color: 'text-gray-600 bg-gray-50 border-gray-200',
          text: 'Closed'
        };
      case 'requires_more_info':
        return {
          icon: FileText,
          color: 'text-orange-600 bg-orange-50 border-orange-200',
          text: 'Requires More Info'
        };
      default:
        return {
          icon: Clock,
          color: 'text-blue-600 bg-blue-50 border-blue-200',
          text: 'In Progress'
        };
    }
  }, []);
  // Get severity icon and color
  const getSeverityInfo = useCallback((severity?: string) => {
    switch (severity) {
      case 'critical':
        return {
          icon: AlertTriangle,
          color: 'text-red-600 bg-red-50 border-red-200',
          text: 'Critical'
        };
      case 'high':
        return {
          icon: AlertTriangle,
          color: 'text-orange-600 bg-orange-50 border-orange-200',
          text: 'High'
        };
      case 'medium':
        return {
          icon: AlertTriangle,
          color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
          text: 'Medium'
        };
      case 'low':
        return {
          icon: CheckCircle,
          color: 'text-green-600 bg-green-50 border-green-200',
          text: 'Low'
        };
      default:
        return null;
    }
  }, []);
  return (
    <div className={className}>
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Check Feedback Status
          </CardTitle>
          <CardDescription>
            Enter your tracking ID to check the status of your anonymous feedback
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Saved Tracking IDs */}
          {savedTrackingIds.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-2">Recent Submissions:</h3>
              <div className="space-y-2">
                {savedTrackingIds.slice(0, 5).map((saved, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => useSavedTrackingId(saved.tracking_id)}
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={getSeverityInfo(saved.severity)?.color}>
                        {saved.severity}
                      </Badge>
                      <span className="text-sm font-mono">
                        {anonymousFeedbackService.formatTrackingId(saved.tracking_id)}
                      </span>
                      <span className="text-xs text-gray-500 capitalize">
                        {saved.category.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(saved.submitted_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="trackingId" className="block text-sm font-medium mb-2">
                Tracking ID
              </label>
              <div className="flex gap-2">
                <Input
                  id="trackingId"
                  type="text"
                  placeholder="Enter your tracking ID"
                  value={trackingId}
                  onChange={(e) => setTrackingId(e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={isChecking || !trackingId.trim()}
                  className="min-w-24"
                >
                  {isChecking ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Checking...
                    </>
                  ) : (
                    'Check Status'
                  )}
                </Button>
              </div>
            </div>
          </form>
          {/* Error Message */}
          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="w-4 h-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {/* Privacy Reminder */}
          <Alert className="text-xs">
            <Shield className="w-3 h-3" />
            <AlertDescription>
              Your identity remains completely anonymous throughout this process.
              No identifying information is ever revealed.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
      {/* Status Results */}
      {statusData && statusData.found && (
        <Card className="max-w-2xl mx-auto mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {(() => {
                const StatusIcon = getStatusInfo(statusData.status).icon;
                return <StatusIcon className="w-5 h-5" />;
              })()}
              Feedback Status: {getStatusInfo(statusData.status).text}
            </CardTitle>
            <CardDescription>
              Tracking ID: {anonymousFeedbackService.formatTrackingId(trackingId)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Status Details */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Status Information
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Current Status:</span>
                    <Badge variant="outline" className={getStatusInfo(statusData.status).color}>
                      {getStatusInfo(statusData.status).text}
                    </Badge>
                  </div>
                  {statusData.status_description && (
                    <div>
                      <span className="font-medium">Description:</span>
                      <p className="text-gray-600 mt-1">{statusData.status_description}</p>
                    </div>
                  )}
                  {statusData.category && (
                    <div className="flex justify-between">
                      <span>Category:</span>
                      <span className="capitalize">{statusData.category.replace('_', ' ')}</span>
                    </div>
                  )}
                  {statusData.severity && (
                    <div className="flex justify-between">
                      <span>Severity:</span>
                      <Badge variant="outline" className={getSeverityInfo(statusData.severity)?.color}>
                        {getSeverityInfo(statusData.severity)?.text}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Timeline
                </h4>
                <div className="space-y-2 text-sm">
                  {statusData.submitted_at && (
                    <div className="flex justify-between">
                      <span>Submitted:</span>
                      <span>{anonymousFeedbackService.formatSubmissionDate(statusData.submitted_at)}</span>
                    </div>
                  )}
                  {statusData.days_since_submission !== undefined && (
                    <div className="flex justify-between">
                      <span>Days Since Submission:</span>
                      <span>{statusData.days_since_submission}</span>
                    </div>
                  )}
                  {statusData.estimated_resolution_days !== undefined && (
                    <div className="flex justify-between">
                      <span>Estimated Resolution:</span>
                      <span>{statusData.estimated_resolution_days} days</span>
                    </div>
                  )}
                  {statusData.review_timeline && (
                    <div>
                      <span className="font-medium">Review Timeline:</span>
                      <p className="text-gray-600 mt-1">{statusData.review_timeline}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <Separator />
            {/* Public Notes */}
            {statusData.public_notes && (
              <div>
                <h4 className="font-medium mb-2">Update from HR:</h4>
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">{statusData.public_notes}</p>
                </div>
              </div>
            )}
            {/* Next Steps */}
            {statusData.next_steps && statusData.next_steps.length > 0 && (
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Next Steps
                </h4>
                <ul className="space-y-2">
                  {statusData.next_steps.map((step, index) => (
                    <li key={index} className="text-sm flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {/* Follow-up Options */}
            {statusData.can_follow_up && (
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    if (statusData.follow_up_url) {
                      window.open(statusData.follow_up_url, '_blank');
                    }
                  }}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Add Follow-up Information
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    navigator.clipboard.writeText(trackingId);
                  }}
                >
                  Copy Tracking ID
                </Button>
              </div>
            )}
            {/* Privacy Reminder */}
            <Alert>
              <Shield className="w-4 h-4" />
              <AlertDescription>
                {statusData.privacy_reminder}
              </AlertDescription>
            </Alert>
            {/* Action Buttons */}
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={handleCheckStatus}
                disabled={isChecking}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Status
              </Button>
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(trackingId);
                }}
              >
                Copy Tracking ID
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};