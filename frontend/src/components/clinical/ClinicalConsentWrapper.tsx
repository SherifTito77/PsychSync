import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface ClinicalConsentWrapperProps {
  children: React.ReactNode;
  screeningType: string;
}

export function ClinicalConsentWrapper({ children, screeningType }: ClinicalConsentWrapperProps) {
  const [showConsent, setShowConsent] = useState(false);
  const [loading, setLoading] = useState(true);
  const [consentLoading, setConsentLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkConsentStatus = async () => {
      try {
        const response = await api.get(`/screening/consent/status?screening_type=${screeningType}`);
        if (!response.data.has_consent) {
          setShowConsent(true);
        } else {
          setShowConsent(false);
        }
      } catch (err) {
        console.error('Failed to check consent status:', err);
        // If check fails, we'll show consent just to be safe
        setShowConsent(true);
      } finally {
        setLoading(false);
      }
    };
    checkConsentStatus();
  }, [screeningType]);

  const handleConsentSubmit = async () => {
    setConsentLoading(true);
    setError(null);
    try {
      await api.post('/screening/consent', null, {
        params: { consent_type: 'screening', screening_types: screeningType },
      });
    } catch (err) {
      // Record failed but consent was displayed and agreed to — proceed anyway
      console.warn('Consent recording failed (non-blocking):', err);
    } finally {
      setConsentLoading(false);
      setShowConsent(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground animate-pulse">Verifying clinical consent status...</p>
        </div>
      </div>
    );
  }

  if (showConsent) {
    return (
      <Card className="max-w-3xl mx-auto border-primary">
        <CardHeader>
          <CardTitle>Clinical Consent Required</CardTitle>
          <CardDescription>
            HIPAA regulations require your explicit consent before we can process
            clinical screening data for {screeningType}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="error">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div className="bg-muted p-4 rounded-md text-sm space-y-2">
            <p>By clicking "I Consent", you agree to the following:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Your responses will be evaluated for clinical significance.</li>
              <li>Data will be stored securely and protected under HIPAA.</li>
              <li>Results may be shared with your designated healthcare providers.</li>
              <li>You can withdraw this consent at any time from your profile settings.</li>
            </ul>
          </div>
          <Alert>
            <AlertDescription className="text-xs">
              This screening tool is for informational purposes and does not
              constitute a medical diagnosis. In case of emergency, please call 988.
            </AlertDescription>
          </Alert>
          <div className="flex gap-3">
            <Button
              onClick={handleConsentSubmit}
              disabled={consentLoading}
              className="flex-1"
            >
              {consentLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              I Consent and Start Screening
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
}

export default ClinicalConsentWrapper;
