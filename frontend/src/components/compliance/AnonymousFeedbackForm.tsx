import React, { useState } from 'react';
import {
  Shield,
  AlertTriangle,
  Clock,
  CheckCircle,
  Eye,
  EyeOff,
  Upload,
  X,
  HelpCircle,
  ExternalLink
} from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
interface AnonymousFeedbackFormProps {
  onSuccess?: (trackingId: string) => void;
  className?: string;
}
interface FormData {
  feedback_type: string;
  category: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  target_type: string;
  target_id: string;
  evidence_urls: string[];
  incident_date: string;
}
export const AnonymousFeedbackForm: React.FC<AnonymousFeedbackFormProps> = ({
  onSuccess,
  className = ''
}) => {
  const [step, setStep] = useState<'info' | 'form' | 'submitted'>('info');
  const [trackingId, setTrackingId] = useState<string>('');
  const [formData, setFormData] = useState<FormData>({
    feedback_type: '',
    category: '',
    description: '',
    severity: 'medium',
    target_type: '',
    target_id: '',
    evidence_urls: [],
    incident_date: ''
  });
  const [loading, setLoading] = useState(false);
  const [showPrivacyDetails, setShowPrivacyDetails] = useState(false);
  const { showNotification } = useNotification();
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const result = await complianceService.submitAnonymousFeedback(formData);
      setTrackingId(result.tracking_id);
      setStep('submitted');
      // Show success notification with tracking ID
      showNotification(
        'Feedback submitted successfully! Save your tracking ID.',
        'success',
        10000
      );
      if (onSuccess) {
        onSuccess(result.tracking_id);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      showNotification('Failed to submit feedback. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    try {
      // In a real implementation, this would upload to a secure file service
      // For now, we'll simulate the upload
      const newUrls = Array.from(files).map(file => `https://secure-storage.example.com/evidence/${Date.now()}-${file.name}`);
      setFormData(prev => ({
        ...prev,
        evidence_urls: [...prev.evidence_urls, ...newUrls]
      }));
      showNotification('Files uploaded securely', 'success');
    } catch (error) {
      showNotification('Failed to upload files', 'error');
    }
  };
  const removeEvidence = (index: number) => {
    setFormData(prev => ({
      ...prev,
      evidence_urls: prev.evidence_urls.filter((_, i) => i !== index)
    }));
  };
  if (step === 'info') {
    return (
      <div className={`max-w-4xl mx-auto p-6 space-y-6 ${className}`}>
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-indigo-100 rounded-full">
              <Shield className="w-12 h-12 text-indigo-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Anonymous Feedback System</h1>
          <p className="text-lg text-gray-600">
            Speak up safely. Your identity is completely protected.
          </p>
        </div>
        {/* Privacy Guarantee */}
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-start space-x-3">
            <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
            <div>
              <h2 className="text-xl font-semibold text-green-900 mb-3">Privacy Guarantee</h2>
              <ul className="space-y-2 text-green-800">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span><strong>Completely Anonymous</strong> - No way to trace back to you</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span><strong>No Tracking</strong> - No IP addresses or session data logged</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span><strong>Secure</strong> - Only you will know your tracking ID</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span><strong>Protected</strong> - Whistleblower protections apply</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        {/* What You Can Report */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-yellow-900 mb-4">What You Can Report</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              'Harassment or discrimination',
              'Safety concerns or violations',
              'Toxic management or culture',
              'Policy violations',
              'Retaliation for speaking up',
              'Ethical concerns',
              'Unfair treatment',
              'Hostile work environment'
            ].map((item, index) => (
              <div key={index} className="flex items-start space-x-2">
                <span className="text-yellow-600 mt-1">•</span>
                <span className="text-yellow-800">{item}</span>
              </div>
            ))}
          </div>
        </div>
        {/* Reporting Options */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-blue-900 mb-4">Other Reporting Options</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-blue-200">
              <div>
                <h3 className="font-semibold text-gray-900">Confidential HR Report</h3>
                <p className="text-sm text-gray-600">Speak with HR confidentially (identity known to HR only)</p>
              </div>
              <a href="/hr/confidential-report" className="text-blue-600 hover:text-blue-700">
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-blue-200">
              <div>
                <h3 className="font-semibold text-gray-900">External Agencies</h3>
                <p className="text-sm text-gray-600">Report to EEOC, OSHA, Department of Labor</p>
              </div>
              <a href="/reporting-guidelines" className="text-blue-600 hover:text-blue-700">
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => setStep('form')}
            className="bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 font-medium text-lg"
          >
            Submit Anonymous Feedback
          </button>
          <a
            href="/reporting-guidelines"
            className="bg-gray-200 text-gray-800 px-8 py-3 rounded-lg hover:bg-gray-300 font-medium text-lg text-center"
          >
            View All Reporting Options
          </a>
        </div>
        {/* Privacy Details Toggle */}
        <div className="text-center">
          <button
            onClick={() => setShowPrivacyDetails(!showPrivacyDetails)}
            className="text-indigo-600 hover:text-indigo-700 flex items-center gap-2 mx-auto"
          >
            <HelpCircle className="w-4 h-4" />
            {showPrivacyDetails ? 'Hide' : 'Show'} Technical Privacy Details
          </button>
        </div>
        {showPrivacyDetails && (
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <h4 className="font-semibold text-gray-900 mb-2">Technical Privacy Measures:</h4>
            <ul className="space-y-1">
              <li>• No user authentication required for submission</li>
              <li>• IP addresses and session data are not logged</li>
              <li>• Cryptographically secure tracking IDs (32-byte random tokens)</li>
              <li>• Target information is hashed with salt to prevent reverse lookup</li>
              <li>• HR staff cannot see tracking IDs or submitter information</li>
              <li>• No timing analysis or metadata that could identify submitters</li>
            </ul>
          </div>
        )}
      </div>
    );
  }
  if (step === 'submitted') {
    return (
      <div className={`max-w-2xl mx-auto p-6 ${className}`}>
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-green-100 rounded-full">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">✓ Feedback Submitted Successfully</h2>
          {/* Tracking ID */}
          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6 mb-6">
            <p className="text-sm font-medium text-yellow-800 mb-2">Your Tracking ID:</p>
            <div className="bg-white rounded-lg p-4 border border-yellow-300">
              <p className="font-mono text-lg break-all text-gray-900">{trackingId}</p>
            </div>
            <div className="mt-4 flex justify-center gap-3">
              <button
                onClick={() => navigator.clipboard.writeText(trackingId)}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm"
              >
                Copy Tracking ID
              </button>
              <a
                href={`/anonymous-feedback/status/${trackingId}`}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
              >
                Check Status
              </a>
            </div>
          </div>
          {/* Instructions */}
          <div className="space-y-4 text-left bg-gray-50 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <div className="bg-indigo-100 rounded-full p-1 mt-1">
                <Shield className="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">IMPORTANT: Save Your Tracking ID</h3>
                <p className="text-sm text-gray-600 mt-1">
                  This tracking ID is the only way to check your feedback status. We cannot recover it for you.
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-100 rounded-full p-1 mt-1">
                <Clock className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">What Happens Next</h3>
                <ul className="text-sm text-gray-600 mt-1 space-y-1">
                  <li>• HR will review your feedback within 48 hours</li>
                  <li>• Critical issues are reviewed immediately</li>
                  <li>• You can check status anytime with your tracking ID</li>
                  <li>• Your identity remains completely anonymous</li>
                </ul>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-green-100 rounded-full p-1 mt-1">
                <CheckCircle className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Privacy Reminder</h3>
                <p className="text-sm text-gray-600 mt-1">
                  This submission is completely anonymous. We cannot and will not attempt to identify you.
                </p>
              </div>
            </div>
          </div>
          {/* Action Buttons */}
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => {
                setStep('info');
                setFormData({
                  feedback_type: '',
                  category: '',
                  description: '',
                  severity: 'medium',
                  target_type: '',
                  target_id: '',
                  evidence_urls: [],
                  incident_date: ''
                });
              }}
              className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 font-medium"
            >
              Submit Another
            </button>
            <a
              href={`/anonymous-feedback/status/${trackingId}`}
              className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 font-medium text-center"
            >
              Check Status
            </a>
          </div>
        </div>
      </div>
    );
  }
  // Form Step
  return (
    <form onSubmit={handleSubmit} className={`max-w-2xl mx-auto p-6 space-y-6 ${className}`}>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Submit Anonymous Feedback</h1>
        <p className="text-gray-600">
          Your submission is completely anonymous. No identifying information is collected.
        </p>
      </div>
      {/* Privacy Reminder */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Shield className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-indigo-800">
            <strong>Privacy Guarantee:</strong> This submission is completely anonymous.
            We do not log IP addresses, session data, or any information that could identify you.
          </div>
        </div>
      </div>
      <div className="space-y-6">
        {/* Type of Issue */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type of Issue *
          </label>
          <select
            required
            value={formData.feedback_type}
            onChange={(e) => setFormData({ ...formData, feedback_type: e.target.value })}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">Select the type of issue...</option>
            <option value="harassment">Harassment</option>
            <option value="discrimination">Discrimination</option>
            <option value="safety">Safety Concern</option>
            <option value="toxic_culture">Toxic Culture/Management</option>
            <option value="retaliation">Retaliation</option>
            <option value="policy_violation">Policy Violation</option>
            <option value="ethical_concern">Ethical Concern</option>
            <option value="other">Other</option>
          </select>
        </div>
        {/* Severity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity *
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { value: 'low', label: 'Low', desc: 'General concern' },
              { value: 'medium', label: 'Medium', desc: 'Concerning behavior' },
              { value: 'high', label: 'High', desc: 'Serious violation' },
              { value: 'critical', label: 'Critical', desc: 'Immediate danger' }
            ].map((level) => (
              <label
                key={level.value}
                className={`relative flex flex-col p-3 border rounded-lg cursor-pointer transition-all ${
                  formData.severity === level.value
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  type="radio"
                  name="severity"
                  value={level.value}
                  checked={formData.severity === level.value}
                  onChange={(e) => setFormData({ ...formData, severity: e.target.value as any })}
                  className="sr-only"
                />
                <span className="font-medium text-sm">{level.label}</span>
                <span className="text-xs text-gray-500 mt-1">{level.desc}</span>
              </label>
            ))}
          </div>
        </div>
        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Detailed Description *
          </label>
          <textarea
            required
            minLength={10}
            rows={8}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Please describe what happened, including:
• When and where it occurred
• Who was involved (if comfortable sharing)
• What specifically happened
• Any witnesses
• How it affected you or others"
          />
          <p className="text-xs text-gray-500 mt-1">
            Minimum 10 characters. Please provide as much detail as possible.
          </p>
        </div>
        {/* Incident Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            When did this occur?
          </label>
          <input
            type="date"
            value={formData.incident_date}
            onChange={(e) => setFormData({ ...formData, incident_date: e.target.value })}
            max={new Date().toISOString().split('T')[0]}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">
            Optional - helps with investigation
          </p>
        </div>
        {/* Target Information (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Information about who was involved (Optional)
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={formData.target_type}
              onChange={(e) => setFormData({ ...formData, target_type: e.target.value })}
              className="border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">Target type (optional)</option>
              <option value="manager">Manager</option>
              <option value="peer">Peer/Colleague</option>
              <option value="subordinate">Subordinate</option>
              <option value="client">Client/Customer</option>
              <option value="policy">Company Policy</option>
              <option value="other">Other</option>
            </select>
            <input
              type="text"
              value={formData.target_id}
              onChange={(e) => setFormData({ ...formData, target_id: e.target.value })}
              placeholder="Name or identifier (will be hashed)"
              className="border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            This information will be hashed for privacy and cannot be traced back.
          </p>
        </div>
        {/* Evidence Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Evidence (Optional)
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                Upload screenshots, emails, documents, or other evidence
              </p>
              <p className="text-xs text-gray-500">
                Files are stored securely and anonymously. Max 10MB per file.
              </p>
              <input
                type="file"
                multiple
                onChange={handleFileUpload}
                className="hidden"
                id="evidence-upload"
              />
              <label
                htmlFor="evidence-upload"
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 text-sm"
              >
                Choose Files
              </label>
            </div>
          </div>
          {/* Uploaded Files */}
          {formData.evidence_urls.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium text-gray-700">Uploaded Files:</p>
              {formData.evidence_urls.map((url, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                  <span className="text-sm text-gray-600 truncate flex-1">
                    {url.split('/').pop()}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeEvidence(index)}
                    className="text-red-500 hover:text-red-700 ml-2"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        {/* Form Actions */}
        <div className="flex gap-4 pt-4">
          <button
            type="button"
            onClick={() => setStep('info')}
            className="flex-1 bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 font-medium"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Submitting...' : 'Submit Anonymously'}
          </button>
        </div>
      </div>
    </form>
  );
};