import React from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/button';

interface ClinicalAlertBannerProps {
  message: string;
  severity?: 'info' | 'warning' | 'error';
  showEmergencyButton?: boolean;
  onDismiss?: () => void;
}

const ClinicalAlertBanner: React.FC<ClinicalAlertBannerProps> = ({
  message,
  severity = 'info',
  showEmergencyButton = false,
  onDismiss,
}) => {
  const handleEmergencyClick = () => {
    window.location.href = '/clinical/emergency';
  };

  const getVariant = () => {
    switch (severity) {
      case 'error':
        return 'destructive';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Alert variant={getVariant()} className="mb-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="font-medium">{message}</p>
          {severity === 'error' && (
            <p className="text-sm mt-2">
              Immediate support is available. Please reach out for help.
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2 ml-4">
          {showEmergencyButton && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleEmergencyClick}
            >
              Get Help Now
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
            >
              Dismiss
            </Button>
          )}
        </div>
      </div>
    </Alert>
  );
};

export default ClinicalAlertBanner;
