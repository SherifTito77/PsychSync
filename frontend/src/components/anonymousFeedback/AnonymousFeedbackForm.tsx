// Anonymous Feedback Form Component
// Production-ready React component with enhanced privacy features and psychological safety focus
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/Form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Separator } from '@/components/ui/separator';
import { AlertTriangle, Shield, Eye, EyeOff, Clock, CheckCircle, Info } from 'lucide-react';
import { AnonymousFeedbackSubmission, AnonymousFeedbackCategoriesResponse } from '@/types/anonymousFeedback';
import { anonymousFeedbackService } from '@/services/anonymousFeedbackService';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
// Form validation schema
const feedbackFormSchema = z.object({
  feedback_type: z.string().min(1, 'Please select a feedback type'),
  category: z.string().min(1, 'Please select a category'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters')
    .max(5000, 'Description must be less than 5000 characters'),
  severity: z.enum(['low', 'medium', 'high', 'critical']).refine((val) => val, {
  message: 'Please select a severity level',
}),
  target_type: z.string().optional(),
  target_id: z.string().optional(),
  evidence_urls: z.array(z.string().url('Please enter valid URLs')).optional(),
  incident_date: z.string().optional(),
  organization_id: z.string().min(1, 'Organization ID is required'),
});
type FeedbackFormData = z.infer<typeof feedbackFormSchema>;
interface AnonymousFeedbackFormProps {
  onSubmit?: (trackingId: string, response: any) => void;
  organizationId?: string;
  initialData?: Partial<FeedbackFormData>;
}
export const AnonymousFeedbackForm: React.FC<AnonymousFeedbackFormProps> = ({
  onSubmit,
  organizationId,
  initialData,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [categories, setCategories] = useState<AnonymousFeedbackCategoriesResponse | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submissionResponse, setSubmissionResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidenceUrls, setEvidenceUrls] = useState<string[]>(['']);
  const [showPrivacyInfo, setShowPrivacyInfo] = useState(true);
  const form = useForm<FeedbackFormData>({
    resolver: zodResolver(feedbackFormSchema),
    defaultValues: {
      feedback_type: initialData?.feedback_type || '',
      category: initialData?.category || '',
      description: initialData?.description || '',
      severity: initialData?.severity || undefined,
      target_type: initialData?.target_type || '',
      target_id: initialData?.target_id || '',
      evidence_urls: initialData?.evidence_urls || [],
      incident_date: initialData?.incident_date || '',
      organization_id: organizationId || initialData?.organization_id || '',
    },
  });
  const selectedFeedbackType = form.watch('feedback_type');
  const selectedSeverity = form.watch('severity');
  // Load feedback categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await anonymousFeedbackService.getFeedbackCategories();
        setCategories(response);
      } catch (err: any) {
        console.error('Failed to load feedback categories:', err);
        setError('Unable to load feedback categories. Please refresh the page.');
      }
    };
    loadCategories();
  }, []);
  // Handle evidence URLs
  const addEvidenceUrl = useCallback(() => {
    setEvidenceUrls(prev => [...prev, '']);
  }, []);
  const updateEvidenceUrl = useCallback((index: number, value: string) => {
    setEvidenceUrls(prev => {
      const newUrls = [...prev];
      newUrls[index] = value;
      return newUrls;
    });
  }, []);
  const removeEvidenceUrl = useCallback((index: number) => {
    setEvidenceUrls(prev => prev.filter((_, i) => i !== index));
  }, []);
  // Form submission handler
  const onSubmitForm = useCallback(async (data: FeedbackFormData) => {
    setIsSubmitting(true);
    setError(null);
    try {
      // Filter out empty evidence URLs
      const validEvidenceUrls = evidenceUrls.filter(url => url.trim() !== '');
      const submissionData: AnonymousFeedbackSubmission = {
        ...data,
        evidence_urls: validEvidenceUrls.length > 0 ? validEvidenceUrls : undefined,
      };
      const response = await anonymousFeedbackService.submitFeedback(submissionData);
      setSubmitSuccess(true);
      setSubmissionResponse(response);
      // Save tracking ID to localStorage for user convenience
      if (response.tracking_id) {
        const savedTrackingIds = JSON.parse(localStorage.getItem('anonymous_feedback_tracking_ids') || '[]');
        savedTrackingIds.unshift({
          tracking_id: response.tracking_id,
          submitted_at: new Date().toISOString(),
          category: data.category,
          severity: data.severity,
        });
        // Keep only last 10 tracking IDs
        localStorage.setItem('anonymous_feedback_tracking_ids', JSON.stringify(savedTrackingIds.slice(0, 10)));
      }
      onSubmit?.(response.tracking_id, response);
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  }, [evidenceUrls, onSubmit]);
  // Reset form
  const resetForm = useCallback(() => {
    form.reset();
    setEvidenceUrls(['']);
    setSubmitSuccess(false);
    setSubmissionResponse(null);
    setError(null);
  }, [form]);
  // Get available categories for selected feedback type
  const getAvailableCategories = useCallback(() => {
    if (!categories || !selectedFeedbackType) return [];
    const feedbackTypeData = categories.feedback_categories[selectedFeedbackType];
    return feedbackTypeData?.subcategories || [];
  }, [categories, selectedFeedbackType]);
  // Get severity color and description
  const getSeverityInfo = useCallback((severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          color: 'text-red-600 bg-red-50 border-red-200',
          description: 'Immediate threat to safety or severe violation requiring urgent intervention',
        };
      case 'high':
        return {
          color: 'text-orange-600 bg-orange-50 border-orange-200',
          description: 'Serious issue requiring prompt investigation and action',
        };
      case 'medium':
        return {
          color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
          description: 'Significant issue that should be addressed in a timely manner',
        };
      case 'low':
        return {
          color: 'text-green-600 bg-green-50 border-green-200',
          description: 'Minor issue that should be addressed but doesn\'t pose immediate risk',
        };
      default:
        return {
          color: 'text-gray-600 bg-gray-50 border-gray-200',
          description: '',
        };
    }
  }, []);
  if (submitSuccess && submissionResponse) {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <CardTitle className="text-2xl text-green-800">
            Feedback Submitted Successfully
          </CardTitle>
          <CardDescription>
            Your anonymous feedback has been received and will be reviewed confidentially
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Tracking ID Display */}
          <Alert className="border-blue-200 bg-blue-50">
            <Eye className="w-4 h-4" />
            <AlertDescription className="font-mono text-lg">
              <strong>Your Tracking ID:</strong> {submissionResponse.tracking_id}
            </AlertDescription>
          </Alert>
          <Alert>
            <Info className="w-4 h-4" />
            <AlertDescription>
              Please save your tracking ID. You can use it to check the status of your feedback anonymously.
            </AlertDescription>
          </Alert>
          {/* Privacy Guarantee */}
          <Card className="bg-green-50 border-green-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-800">
                <Shield className="w-5 h-5" />
                Privacy Guaranteed
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {submissionResponse.privacy_guarantee && (
                <>
                  <p className="text-sm text-green-700">
                    ✓ {submissionResponse.privacy_guarantee.anonymous}
                  </p>
                  <p className="text-sm text-green-700">
                    ✓ {submissionResponse.privacy_guarantee.untraceable}
                  </p>
                  <p className="text-sm text-green-700">
                    ✓ {submissionResponse.privacy_guarantee.no_logging}
                  </p>
                  <p className="text-sm text-green-700">
                    ✓ {submissionResponse.privacy_guarantee.protection}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
          {/* Next Steps */}
          {submissionResponse.next_steps && submissionResponse.next_steps.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Next Steps
              </h4>
              <ul className="space-y-2">
                {submissionResponse.next_steps.map((step: string, index: number) => (
                  <li key={index} className="text-sm flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {/* Support Resources */}
          {submissionResponse.support_resources && submissionResponse.support_resources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Support Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {submissionResponse.support_resources.map((resource: any, index: number) => (
                    <div key={index} className="border-l-4 border-blue-200 pl-4">
                      <h5 className="font-medium">{resource.name}</h5>
                      <p className="text-sm text-gray-600">{resource.description}</p>
                      <p className="text-sm font-mono text-blue-600">{resource.contact}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          {/* Action Buttons */}
          <div className="flex gap-3 justify-center">
            <Button
              onClick={() => {
                // Copy tracking ID to clipboard
                navigator.clipboard.writeText(submissionResponse.tracking_id);
              }}
              variant="outline"
            >
              Copy Tracking ID
            </Button>
            <Button onClick={resetForm}>
              Submit Another Report
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Anonymous Feedback Submission
        </CardTitle>
        <CardDescription>
          Submit feedback completely anonymously. No identifying information will be stored.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Privacy Information */}
        {showPrivacyInfo && (
          <Alert className="mb-6 border-green-200 bg-green-50">
            <Shield className="w-4 h-4" />
            <AlertDescription>
              <strong>100% Anonymous:</strong> Your feedback is completely confidential.
              We do not track IP addresses, require accounts, or store any identifying information.
              <Button
                variant="link"
                className="p-0 h-auto ml-2 text-green-700"
                onClick={() => setShowPrivacyInfo(false)}
              >
                Hide
              </Button>
            </AlertDescription>
          </Alert>
        )}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmitForm)} className="space-y-6">
            {/* Organization ID */}
            <FormField
              control={form.control}
              name="organization_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Organization ID</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter organization ID"
                      {...field}
                      disabled={!!organizationId}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Feedback Type */}
            <FormField
              control={form.control}
              name="feedback_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Feedback Type</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select the type of feedback" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {categories && Object.entries(categories.feedback_categories).map(([type, data]) => (
                        <SelectItem key={type} value={type}>
                          <div>
                            <div className="font-medium capitalize">
                              {type.replace('_', ' ')}
                            </div>
                            <div className="text-sm text-gray-600">
                              {data.description}
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Category */}
            {selectedFeedbackType && (
              <FormField
                control={form.control}
                name="category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select specific category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {getAvailableCategories().map((category) => (
                          <SelectItem key={category} value={category}>
                            <div className="capitalize">
                              {category.replace('_', ' ')}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
            {/* Severity */}
            <FormField
              control={form.control}
              name="severity"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Severity Level</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select severity level" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {categories && Object.entries(categories.severity_levels).map(([severity, description]) => (
                        <SelectItem key={severity} value={severity}>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className={getSeverityInfo(severity).color}>
                              {severity}
                            </Badge>
                            <span className="text-sm">{description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                  {selectedSeverity && (
                    <FormDescription className="text-sm">
                      {getSeverityInfo(selectedSeverity).description}
                    </FormDescription>
                  )}
                </FormItem>
              )}
            />
            {/* Description */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Detailed Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Please provide a detailed description of the issue. Be as specific as possible while maintaining your privacy."
                      className="min-h-32"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Minimum 10 characters. Maximum 5000 characters.
                    All identifying information will be automatically redacted.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Target Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Target Information (Optional)</h3>
              <FormField
                control={form.control}
                name="target_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Target Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Is this about a person, team, or policy?" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {categories?.target_types?.map((target) => (
                          <SelectItem key={target.type} value={target.type}>
                            <div>
                              <div className="font-medium capitalize">
                                {target.type}
                              </div>
                              <div className="text-sm text-gray-600">
                                {target.description}
                              </div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="target_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Target Identifier (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Any identifier that helps identify the target (will be hashed for privacy)"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      This will be automatically hashed and cannot be traced back to individuals.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            {/* Incident Date */}
            <FormField
              control={form.control}
              name="incident_date"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Incident Date (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      type="date"
                      max={new Date().toISOString().split('T')[0]}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    When did this incident occur?
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Evidence URLs */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Evidence URLs (Optional)</h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addEvidenceUrl}
                >
                  Add URL
                </Button>
              </div>
              {evidenceUrls.map((url, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder="https://example.com/evidence"
                    value={url}
                    onChange={(e) => updateEvidenceUrl(index, e.target.value)}
                  />
                  {evidenceUrls.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeEvidenceUrl(index)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
            </div>
            <Separator />
            {/* Submit Button */}
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="min-w-32"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Submitting...
                  </>
                ) : (
                  'Submit Feedback'
                )}
              </Button>
            </div>
            {/* Final Privacy Notice */}
            <Alert className="text-xs">
              <EyeOff className="w-3 h-3" />
              <AlertDescription>
                <strong>Privacy Notice:</strong> This submission is completely anonymous.
                No IP addresses, session data, or personal information is stored.
                Your tracking ID is the only way to check status.
              </AlertDescription>
            </Alert>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};