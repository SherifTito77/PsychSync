// src/components/subscription/CancelFlow.tsx
// Cancel flow with retention offers to reduce churn
import React, { useState, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { SubscriptionTier } from '../../types/subscription';

interface RetentionOffer {
  id: string;
  title: string;
  description: string;
  discount: number;
  billing: 'monthly' | 'annual';
  savings: string;
  popular?: boolean;
  features: string[];
}

const RETENTION_OFFERS: RetentionOffer[] = [
  {
    id: 'pause',
    title: 'Pause Instead',
    description: 'Take a break without losing your data or progress',
    discount: 0,
    billing: 'monthly',
    savings: 'Freeze your account',
    features: [
      'Keep all your data',
      'Resume anytime',
      'No charges while paused',
      'Access when you return',
    ],
  },
  {
    id: 'annual_switch',
    title: 'Switch to Annual & Save 16%',
    description: 'Lock in your current plan and save big',
    discount: 16,
    billing: 'annual',
    savings: '$58/year compared to monthly',
    popular: true,
    features: [
      '2 months free',
      'Price locked for a year',
      'All current features',
      'Cancel anytime',
    ],
  },
  {
    id: 'downgrade',
    title: 'Downgrade to Free',
    description: 'Keep using PsychSync with our free tier',
    discount: 100,
    billing: 'monthly',
    savings: 'Save 100%',
    features: [
      '3 assessments per month',
      'Basic personality reports',
      'Community support',
      'No credit card required',
    ],
  },
];

const CANCEL_REASONS = [
  'Too expensive',
  'Not using features',
  'Technical issues',
  'Found alternative',
  'Temporary pause',
  'Other',
];

interface CancelFlowProps {
  onCancelComplete?: () => void;
  onOfferAccepted?: (offerId: string) => void;
}

const CancelFlow: React.FC<CancelFlowProps> = ({ onCancelComplete, onOfferAccepted }) => {
  const navigate = useNavigate();
  const { subscription } = useSubscription();
  const [step, setStep] = useState<'reason' | 'offers' | 'feedback' | 'confirm'>('reason');
  const [selectedReason, setSelectedReason] = useState<string>('');
  const [feedback, setFeedback] = useState<string>('');
  const [selectedOffer, setSelectedOffer] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  if (!subscription || subscription.tier === SubscriptionTier.FREE) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <p className="text-gray-600">You don't have an active subscription to cancel.</p>
      </div>
    );
  }

  const handleReasonNext = () => {
    if (selectedReason === 'Temporary pause') {
      // Skip to pause offer
      setSelectedOffer('pause');
      setStep('offers');
    } else {
      setStep('offers');
    }
  };

  const handleOfferAccept = async (offerId: string) => {
    setProcessing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (offerId === 'pause') {
      // Pause subscription
      console.log('Pausing subscription');
      onOfferAccepted?.(offerId);
    } else if (offerId === 'annual_switch') {
      // Switch to annual billing
      console.log('Switching to annual billing');
      onOfferAccepted?.(offerId);
    } else if (offerId === 'downgrade') {
      // Process downgrade
      console.log('Downgrading to free');
      onOfferAccepted?.(offerId);
    }

    setProcessing(false);
  };

  const handleConfirmCancel = async () => {
    setProcessing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('Cancellation confirmed');
    onCancelComplete?.();
    setProcessing(false);
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {['reason', 'offers', 'feedback', 'confirm'].map((s, index) => (
            <React.Fragment key={s}>
              <div className={`flex items-center ${step === s ? 'text-indigo-600' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  ['reason', 'offers', 'feedback', 'confirm'].indexOf(step) >= index ? 'bg-indigo-600 text-white' : 'bg-gray-200'
                }`}>
                  {index + 1}
                </div>
                <span className="ml-2 text-sm font-medium hidden sm:inline">
                  {s === 'reason' && 'Reason'}
                  {s === 'offers' && 'Review Options'}
                  {s === 'feedback' && 'Feedback'}
                  {s === 'confirm' && 'Confirm'}
                </span>
              </div>
              {index < 3 && (
                <div className={`flex-1 h-1 mx-4 ${['reason', 'offers', 'feedback', 'confirm'].indexOf(step) > index ? 'bg-indigo-600' : 'bg-gray-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step 1: Reason */}
      {step === 'reason' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">We're sorry to see you go</h2>
          <p className="text-gray-600 mb-6">
            Help us understand why you're leaving so we can improve PsychSync.
          </p>

          <div className="space-y-3">
            {CANCEL_REASONS.map((reason) => (
              <button
                key={reason}
                onClick={() => setSelectedReason(reason)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-colors ${
                  selectedReason === reason
                    ? 'border-indigo-600 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{reason}</span>
                  {selectedReason === reason && (
                    <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>

          <button
            onClick={handleReasonNext}
            disabled={!selectedReason}
            className="mt-6 w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Continue
          </button>
        </div>
      )}

      {/* Step 2: Retention Offers */}
      {step === 'offers' && (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {selectedReason === 'Too expensive' ? 'We have options for you' : 'Before you go...'}
            </h2>
            <p className="text-gray-600">
              {selectedReason === 'Too expensive'
                ? 'Save money with these alternatives to cancellation'
                : 'Consider these alternatives before cancelling'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {RETENTION_OFFERS.map((offer) => (
              <div
                key={offer.id}
                className={`bg-white rounded-lg border-2 p-6 transition-all ${
                  offer.popular
                    ? 'border-indigo-600 shadow-lg relative'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {offer.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                      RECOMMENDED
                    </span>
                  </div>
                )}

                <h3 className="text-lg font-bold text-gray-900 mb-2">{offer.title}</h3>
                <p className="text-sm text-gray-600 mb-4">{offer.description}</p>

                {offer.discount > 0 && (
                  <div className="mb-4">
                    <span className="text-2xl font-bold text-green-600">{offer.discount}% off</span>
                    {offer.savings && <p className="text-xs text-gray-500 mt-1">{offer.savings}</p>}
                  </div>
                )}

                <ul className="space-y-2 mb-6">
                  {offer.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start text-sm">
                      <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleOfferAccept(offer.id)}
                  disabled={processing}
                  className={`w-full py-2 px-4 rounded-lg font-semibold transition-colors ${
                    offer.popular
                      ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  } disabled:opacity-50`}
                >
                  {processing ? 'Processing...' : 'Select This Option'}
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={() => setStep('feedback')}
            className="w-full text-gray-600 hover:text-gray-800 text-sm"
          >
            None of these work for me → Continue to cancellation
          </button>
        </div>
      )}

      {/* Step 3: Feedback */}
      {step === 'feedback' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">One last thing</h2>
          <p className="text-gray-600 mb-6">
            Your feedback helps us improve PsychSync. What could we have done better?
          </p>

          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Tell us more about your experience..."
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            rows={4}
          />

          <div className="mt-6 flex gap-4">
            <button
              onClick={() => setStep('offers')}
              className="flex-1 py-3 px-6 rounded-lg font-semibold border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Go Back
            </button>
            <button
              onClick={() => setStep('confirm')}
              className="flex-1 bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Confirm */}
      {step === 'confirm' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-center mb-6">
            <div className="text-5xl mb-4">😢</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Are you sure?</h2>
            <p className="text-gray-600">
              You'll lose access to all Premium features at the end of your billing period.
            </p>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-red-900 mb-2">What happens when you cancel:</h4>
            <ul className="text-sm text-red-800 space-y-1">
              <li>• Access continues until {new Date(subscription.nextBillingDate).toLocaleDateString()}</li>
              <li>• All your data is saved for 30 days</li>
              <li>• You can reactivate anytime</li>
              <li>• Team members will lose access</li>
            </ul>
          </div>

          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-2">Cancellation summary:</h4>
            <div className="bg-gray-50 rounded-lg p-4 text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Plan:</span>
                <span className="font-medium">{subscription.tier}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Reason:</span>
                <span className="font-medium">{selectedReason}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last day of access:</span>
                <span className="font-medium">{new Date(subscription.nextBillingDate).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setStep('offers')}
              disabled={processing}
              className="flex-1 py-3 px-6 rounded-lg font-semibold border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
            >
              I Changed My Mind
            </button>
            <button
              onClick={handleConfirmCancel}
              disabled={processing}
              className="flex-1 bg-red-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              {processing ? 'Processing...' : 'Confirm Cancellation'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

CancelFlow.displayName = 'CancelFlow';

export default CancelFlow;
