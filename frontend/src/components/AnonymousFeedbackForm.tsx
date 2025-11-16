import React, { useState } from 'react';
import { Shield, AlertCircle, CheckCircle } from 'lucide-react';
import { anonymousFeedbackService } from '../services/anonymousFeedbackService';
import type { AnonymousFeedbackSubmission, FeedbackSubmissionResult } from '../types';
const AnonymousFeedbackForm: React.FC = () => {
  const [step, setStep] = useState<'info' | 'form' | 'submitted'>('info');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [trackingId, setTrackingId] = useState<string>('');
  const [result, setResult] = useState<FeedbackSubmissionResult | null>(null);
  const [formData, setFormData] = useState<AnonymousFeedbackSubmission>({
    organization_id: 'your-org-id', // This would come from user context
    feedback_type: '',
    category: '',
    description: '',
    severity: 'medium',
    target_type: '',
    target_id: '',
    evidence_urls: [],
    incident_date: ''
  });
  const feedbackCategories = {
    toxic_behavior: {
      description: 'Report toxic behavior, bullying, or harassment',
      subcategories: ['verbal_abuse', 'bullying', 'harassment', 'intimidation']
    },
    psychological_safety: {
      description: 'Report psychological safety concerns',
      subcategories: ['fear_speaking_up', 'exclusion', 'micromanagement', 'unfair_treatment']
    },
    harassment: {
      description: 'Report harassment and discriminatory behavior',
      subcategories: ['sexual_harassment', 'verbal_harassment', 'cyberbullying', 'stalking']
    },
    discrimination: {
      description: 'Report discrimination based on protected characteristics',
      subcategories: ['race_discrimination', 'gender_discrimination', 'age_discrimination', 'disability_discrimination']
    },
    safety_concern: {
      description: 'Report workplace safety issues',
      subcategories: ['physical_safety', 'psychological_safety', 'equipment_hazard', 'violence_threat']
    },
    retaliation: {
      description: 'Report retaliation for speaking up or reporting',
      subcategories: ['demotion', 'harassment', 'exclusion', 'unfair_punishment']
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const result: FeedbackSubmissionResult = await anonymousFeedbackService.submitFeedback(formData);
      if (result.success) {
        setTrackingId(result.tracking_id || '');
        setStep('submitted');
        setResult(result);
        // Alert user to save tracking ID
        alert(`IMPORTANT: Save this tracking ID: ${result.tracking_id}\n\nYou'll need it to check status later.`);
      } else {
        setResult(result);
      }
    } catch (error: any) {
      console.error('Failed to submit feedback:', error);
      setResult({
        success: false,
        error: error.message || 'Failed to submit feedback. Please try again.',
        alternatives: ['Contact HR directly', 'Try again later', 'Use external reporting hotlines']
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  const handleInputChange = (field: keyof AnonymousFeedbackSubmission, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  const addEvidenceUrl = () => {
    setFormData(prev => ({
      ...prev,
      evidence_urls: [...(prev.evidence_urls || []), '']
    }));
  };
  const updateEvidenceUrl = (index: number, value: string) => {
    setFormData(prev => {
      const urls = [...(prev.evidence_urls || [])];
      urls[index] = value;
      return { ...prev, evidence_urls: urls };
    });
  };
  const removeEvidenceUrl = (index: number) => {
    setFormData(prev => {
      const urls = [...(prev.evidence_urls || [])];
      urls.splice(index, 1);
      return { ...prev, evidence_urls: urls };
    });
  };
  if (step === 'info') {
    return (
      <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="text-center mb-8">
          <Shield className="w-16 h-16 text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Anonymous Feedback System</h1>
          <p className="text-gray-600 text-lg">Report workplace concerns completely anonymously</p>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-blue-900 mb-4 flex items-center">
            <Shield className="w-6 h-6 mr-2" />
            Privacy Guarantee
          </h2>
          <ul className="space-y-2">
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800"><strong>Completely Anonymous</strong> - No way to trace back to you</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800"><strong>No Tracking</strong> - No IP addresses or session data logged</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800"><strong>Secure</strong> - Only you know your tracking ID</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span className="text-blue-800"><strong>Protected</strong> - Whistleblower protections apply</span>
            </li>
          </ul>
        </div>
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="font-semibold text-green-900 mb-3">What You Can Report</h3>
            <ul className="space-y-1 text-sm text-green-800">
              <li>• Harassment or discrimination</li>
              <li>• Safety concerns or violations</li>
              <li>• Toxic management or culture</li>
              <li>• Policy violations</li>
              <li>• Retaliation</li>
              <li>• Psychological safety issues</li>
            </ul>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="font-semibold text-yellow-900 mb-3">How It Works</h3>
            <ol className="space-y-2 text-sm text-yellow-800">
              <li>1. Submit your feedback anonymously</li>
              <li>2. Save your tracking ID</li>
              <li>3. HR reviews within 48 hours</li>
              <li>4. Check status anytime</li>
              <li>5. Submit follow-ups if needed</li>
            </ol>
          </div>
        </div>
        <div className="flex justify-center gap-4">
          <button
            onClick={() => setStep('form')}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Submit Anonymous Feedback
          </button>
          <a
            href="/reporting-guidelines"
            className="bg-gray-200 text-gray-800 px-8 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            View All Options
          </a>
        </div>
      </div>
    );
  }
  if (step === 'submitted' && result?.success) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <CheckCircle className="w-16 h-16 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">✓ Feedback Submitted</h2>
          <div className="bg-green-50 border-2 border-green-600 rounded-lg p-6 mb-6">
            <p className="text-sm text-gray-600 mb-2">Your Tracking ID:</p>
            <p className="text-2xl font-mono font-bold text-green-800 break-all mb-4">{trackingId}</p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => navigator.clipboard.writeText(trackingId)}
                className="text-blue-600 hover:text-blue-800 underline text-sm"
              >
                Copy to Clipboard
              </button>
              <button
                onClick={() => window.print()}
                className="text-blue-600 hover:text-blue-800 underline text-sm"
              >
                Print This Page
              </button>
            </div>
          </div>
          <div className="space-y-4 text-gray-700 mb-8">
            <p><strong>IMPORTANT:</strong> Save this tracking ID. It's the only way to check your feedback status.</p>
            <p>✓ HR will review within 48 hours (immediately for critical issues)</p>
            <p>✓ Check status anytime at /feedback-status</p>
            <p>✓ Your identity remains completely anonymous</p>
          </div>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => {
                setStep('info');
                setFormData({
                  organization_id: 'your-org-id',
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
              className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Submit Another
            </button>
            <a
              href={`/feedback-status?tracking_id=${trackingId}`}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Check Status
            </a>
          </div>
        </div>
      </div>
    );
  }
  if (result?.success === false) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <AlertCircle className="w-16 h-16 text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Submission Failed</h2>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 mb-4">{result.error}</p>
            {result.alternatives && (
              <div>
                <p className="font-semibold text-red-900 mb-2">Alternative Options:</p>
                <ul className="text-left space-y-1">
                  {result.alternatives.map((alt, index) => (
                    <li key={index} className="text-red-700">• {alt}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => {
                setResult(null);
                setStep('form');
              }}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => setStep('info')}
              className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Back to Info
            </button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Submit Anonymous Feedback</h2>
          <button
            onClick={() => setStep('info')}
            className="text-gray-600 hover:text-gray-800"
          >
            ← Back
          </button>
        </div>
        <p className="text-gray-600 mt-2">Your submission is completely anonymous and confidential</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Feedback Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type of Issue *
          </label>
          <select
            required
            value={formData.feedback_type}
            onChange={(e) => {
              handleInputChange('feedback_type', e.target.value);
              handleInputChange('category', ''); // Reset category
            }}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a type...</option>
            {Object.entries(feedbackCategories).map(([key, category]) => (
              <option key={key} value={key}>
                {category.description}
              </option>
            ))}
          </select>
        </div>
        {/* Category */}
        {formData.feedback_type && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Specific Category *
            </label>
            <select
              required
              value={formData.category}
              onChange={(e) => handleInputChange('category', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a category...</option>
              {feedbackCategories[formData.feedback_type as keyof typeof feedbackCategories]?.subcategories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
        )}
        {/* Severity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity Level *
          </label>
          <select
            required
            value={formData.severity}
            onChange={(e) => handleInputChange('severity', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="low">Low - General concern or suggestion</option>
            <option value="medium">Medium - Concerning behavior</option>
            <option value="high">High - Serious violation</option>
            <option value="critical">Critical - Immediate safety/legal concern</option>
          </select>
        </div>
        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Detailed Description *
          </label>
          <textarea
            required
            minLength={10}
            rows={6}
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="Describe what happened, when, where, who was involved, and any other relevant details..."
          />
          <p className="text-sm text-gray-500 mt-1">
            Minimum 10 characters. All identifying information will be automatically removed.
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
            onChange={(e) => handleInputChange('incident_date', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        {/* Target Information */}
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Target Information (Optional)
          </label>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Target Type</label>
            <select
              value={formData.target_type}
              onChange={(e) => handleInputChange('target_type', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select target type...</option>
              <option value="person">Person</option>
              <option value="team">Team</option>
              <option value="department">Department</option>
              <option value="process">Process</option>
              <option value="policy">Policy</option>
            </select>
          </div>
          {formData.target_type && (
            <div>
              <label className="block text-sm text-gray-600 mb-1">Target Identifier</label>
              <input
                type="text"
                value={formData.target_id}
                onChange={(e) => handleInputChange('target_id', e.target.value)}
                placeholder="This information will be automatically hashed for anonymity"
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                This will be automatically hashed to protect all identities
              </p>
            </div>
          )}
        </div>
        {/* Evidence URLs */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Evidence URLs (Optional)
          </label>
          <p className="text-sm text-gray-600 mb-3">
            Add links to screenshots, documents, or other evidence. This is completely optional.
          </p>
          {(formData.evidence_urls || []).map((url, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="url"
                value={url}
                onChange={(e) => updateEvidenceUrl(index, e.target.value)}
                placeholder="https://example.com/evidence.png"
                className="flex-1 p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => removeEvidenceUrl(index)}
                className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addEvidenceUrl}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
          >
            Add Evidence URL
          </button>
        </div>
        {/* Privacy Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <Shield className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">Your Privacy is Protected</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Completely anonymous - no IP addresses stored</li>
                <li>• No user accounts or login required</li>
                <li>• Cryptographically secure tracking</li>
                <li>• All identifying information is automatically removed</li>
                <li>• Protected by company anti-retaliation policies</li>
              </ul>
            </div>
          </div>
        </div>
        {/* Submit Button */}
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-8 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Anonymous Feedback'}
          </button>
        </div>
      </form>
    </div>
  );
};
export default AnonymousFeedbackForm;