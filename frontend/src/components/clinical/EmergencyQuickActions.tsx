import React from 'react';
import { Button } from '@/components/ui/button';

interface EmergencyQuickActionsProps {
  compact?: boolean;
}

const EmergencyQuickActions: React.FC<EmergencyQuickActionsProps> = ({ compact = false }) => {
  const handleCall988 = () => {
    window.open('tel:988');
  };

  const handleTextCrisis = () => {
    window.open('sms:741741&body=HOME', '_blank');
  };

  const handleCall911 = () => {
    window.open('tel:911');
  };

  const handleGoToEmergency = () => {
    window.location.href = '/clinical/emergency';
  };

  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCall988}
          className="text-red-600 border-red-200 hover:bg-red-50"
        >
          Call 988
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleGoToEmergency}
          className="text-red-600 border-red-200 hover:bg-red-50"
        >
          Get Help
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-red-900 mb-4">
        Immediate Help Available
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Button
          onClick={handleCall988}
          className="bg-red-600 hover:bg-red-700 text-white"
          size="lg"
        >
          <div className="flex flex-col items-center">
            <svg className="h-6 w-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span>Call 988</span>
            <span className="text-xs font-normal">Crisis Lifeline</span>
          </div>
        </Button>

        <Button
          onClick={handleTextCrisis}
          variant="outline"
          size="lg"
          className="border-red-300 text-red-700 hover:bg-red-100"
        >
          <div className="flex flex-col items-center">
            <svg className="h-6 w-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>Text HOME to 741741</span>
            <span className="text-xs font-normal">Crisis Text Line</span>
          </div>
        </Button>
      </div>

      <div className="space-y-3">
        <Button
          onClick={handleCall911}
          variant="destructive"
          className="w-full"
          size="lg"
        >
          <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          Call 911 - Emergency Services
        </Button>

        <div className="text-center">
          <Button
            onClick={handleGoToEmergency}
            variant="outline"
            className="text-red-600 border-red-300 hover:bg-red-50"
          >
            View All Emergency Resources
          </Button>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-red-200">
        <p className="text-sm text-red-800">
          <strong>Remember:</strong> You are not alone. Help is available 24/7, and it's okay to reach out.
        </p>
      </div>
    </div>
  );
};

export default EmergencyQuickActions;
