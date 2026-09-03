import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface ClinicalWelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
  isFirstTime?: boolean;
}

const ClinicalWelcomeModal: React.FC<ClinicalWelcomeModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  isFirstTime = false,
}) => {
  const [step, setStep] = useState(1);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setStep(1);
    }
  }, [isOpen]);

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = () => {
    if (dontShowAgain) {
      localStorage.setItem('clinical-welcome-dismissed', 'true');
    }
    onComplete?.();
    onClose();
  };

  const handleStartAssessment = () => {
    window.location.href = '/clinical-assessments';
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 9.343l1.414-1.414a4 4 0 115.656 0L16.828 4.828a4 4 0 01-5.656 0L5.172 4.828a4 4 0 010-5.656zm1.414 1.414L10 11.828l8.172-8.172a2 2 0 00-2.828 0L8.828 6.586a2 2 0 102.828 0z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome to Mental Health Screening
              </h2>
              <p className="text-gray-600 max-w-md mx-auto">
                {isFirstTime
                  ? "Take control of your mental wellbeing with evidence-based screening tools designed to help you understand your mental health better."
                  : "Continue your mental health journey with our confidential screening tools."
                }
              </p>
            </div>

            <div className="space-y-4 text-left">
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-semibold text-gray-900 mb-3">What you'll find:</h3>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 01-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414 1.414l-2-2z" clipRule="evenodd" />
                      </svg>
                      <span>Evidence-based depression and anxiety screening tools</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 01-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414 1.414l-2-2z" clipRule="evenodd" />
                      </svg>
                      <span>Personalized recommendations based on your results</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 01-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414 1.414l-2-2z" clipRule="evenodd" />
                      </svg>
                      <span>24/7 access to crisis support resources</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        );

      case 2:
        return (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Confidential & Secure
            </h2>
            <p className="text-gray-600 mb-6">
              Your mental health information is protected with enterprise-grade security and follows HIPAA privacy standards.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center mb-3">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
                      <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.866c0 5.594 3.824 10.29 9 11.622 5.272 1.134 9.286-1.134 9.286-1.134 1.135-9.286-1.134A11.954 11.954 0 002.166 4.999z" clipRule="evenodd" />
                        <path fillRule="evenodd" d="M12.866 1.56c-.18.638-.536 1.942-1.136 2.446a2.424 2.424 0 013.232.477c.785.16 1.659-.098 2.034-.477l.045.045c.375.378.984.307 1.291-.069l.012-.008c.282-.2.596-.363.875-.064l.01-.008c.273-.2.58.377.865.075l.015.012c.288.2.594.29.887.071l.014-.009c.29-.2.582-.283.859.068l.01.009c.303.213.582.291.884.07l.008.006c.32.215.605.292.9.068l.008.007c.293.2.574.29.868.07h.007c.293.2.574.29.868.07l.007.006c.3.208.594.29.9.07l.006.005c.32.216.604.288.9.064.003.002c.312.21.607.285.9.064.001c.32.213.604.28.9.054.002c.32.21.605.277.9.053.002c.32.212.604.28.8.052.003c.314.21.605.275.8.051.003c.312.21.603.275.8.05.003c.31.208.602.275.8.051c.31.208.602.275.8.05.004c.309.207.601.274.8.05c.3.207.601.274.8.05.004c.311.206.602.273.8.04c.31.206.601.273.8.04c.31.205.6.273.8.04c.312.204.6.272.8.038.003c.31.204.6.272.8.038c.311.203.6.272.8.038c.312.203.6.272.8.038.003c.31.202.6.272.8.038c.311.203.6.272.8.038c.312.203.6.272.8.038c.312.202.6.272.8.038c.312.202.6.272.8.038c.311.202.6.272.8.038c.311.202.6.272.8.038c.312.202.6.272.8.038c.311.202.6.272.8.038c.311.201.6.271.8.037c.311.202.6.271.8.037c.311.202.6.271.8.037.31.201.6.271.8.037.311.202.6.271.8.037.311.201.6.271.8.037.31.202.6.271.8.037.311.202.6.271.8.037.311.201.6.271.8.037.311.202.6.271.8.037.311.201.6.271.8.037.311.202.6.271.8.037z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">HIPAA Compliant</h4>
                      <p className="text-sm text-gray-600">Meets all healthcare privacy requirements</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center mb-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                      <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 0 6 6 0 00-6 6zM8 2a8 8 0 100 16 8 8 0 000-16z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">Encrypted Data</h4>
                      <p className="text-sm text-gray-600">Your information is protected and secure</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 01-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414 1.414l-2-2z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Ready to Get Started?
              </h2>
              <p className="text-gray-600 mb-6">
                You're all set to begin your mental health screening. It should only take 5-10 minutes to complete.
              </p>
            </div>

            <div className="space-y-4">
              <Button
                onClick={handleStartAssessment}
                className="w-full bg-blue-600 hover:bg-blue-700"
                size="sm"
              >
                Start Screening Now
              </Button>

              <Button
                variant="outline"
                onClick={onClose}
                className="w-full"
              >
                Maybe Later
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {isFirstTime ? 'Introduction' : 'Welcome Back'}
          </DialogTitle>
        </DialogHeader>

        <div className="py-6">
          {renderStep()}

          <div className="mt-6 flex items-center justify-between">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="dont-show-again"
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="dont-show-again" className="ml-2 text-sm text-gray-600">
                Don't show this again
              </label>
            </div>

            <div className="flex space-x-2">
              <Button variant="outline" onClick={onClose}>
                Skip
              </Button>
              <Button onClick={handleNext}>
                {step === 3 ? 'Complete' : 'Next'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ClinicalWelcomeModal;
