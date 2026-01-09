/**
 * Severity Banner Component
 *
 * Displays crisis alert banner when assessment results indicate severe symptoms.
 */

import React from 'react';
import { Alert, AlertTitle } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { useNavigate } from 'react-router-dom';

interface SeverityBannerProps {
  crisisAlert: boolean;
}

export const SeverityBanner: React.FC<SeverityBannerProps> = ({ crisisAlert }) => {
  const navigate = useNavigate();

  if (!crisisAlert) return null;

  return (
    <Alert variant="destructive" className="mb-8">
      <AlertTitle>Immediate Attention Recommended</AlertTitle>
      <p className="mt-2">
        Your responses indicate that you may benefit from immediate professional support.
        Please reach out to one of the crisis resources below or contact emergency services.
      </p>
      <div className="mt-4">
        <Button
          variant="destructive"
          onClick={() => navigate('/clinical/emergency')}
        >
          Get Immediate Help
        </Button>
      </div>
    </Alert>
  );
};
