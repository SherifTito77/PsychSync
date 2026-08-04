/**
 * Trigger Psychology Analysis Button
 *
 * Add this button anywhere to trigger corporate psychology analysis
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { RefreshCw, AlertCircle } from 'lucide-react';
import corporatePsychologyService from '@/services/corporatePsychologyService';

interface PsychologyAnalysisButtonProps {
  organizationId: string;
  onAnalysisComplete?: (result: any) => void;
}

export const PsychologyAnalysisButton: React.FC<PsychologyAnalysisButtonProps> = ({
  organizationId,
  onAnalysisComplete
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const runAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const result = await corporatePsychologyService.runAnalysis({
        organization_id: organizationId,
        measurement_period_days: 30, // Analyze last 30 days
        include_culture_metrics: true,
        include_wellness_metrics: true,
        include_behavioral_metrics: true,
        include_communication_metrics: true,
      });

      setSuccess(true);

      // Call completion callback
      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }

      // Show success message
      alert(`✅ Analysis Complete!\n\nSignals Generated: ${result.signals_generated}\nInterventions Recommended: ${result.interventions_recommended}`);
    } catch (err: any) {
      setError(err.message || 'Failed to run analysis');
      console.error('Analysis failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={runAnalysis}
        disabled={isLoading}
        className="w-full"
        size="large"
      >
        {isLoading ? (
          <>
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            Running Analysis...
          </>
        ) : (
          <>
            <RefreshCw className="mr-2 h-4 w-4" />
            Run Corporate Psychology Analysis
          </>
        )}
      </Button>

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 text-green-600 text-sm bg-green-50 p-3 rounded">
          <RefreshCw className="h-4 w-4" />
          <span>Analysis complete! Check the dashboard for results.</span>
        </div>
      )}

      <p className="text-xs text-gray-500">
        Analyzes organizational patterns across communication, collaboration, and wellness metrics.
        Generates early-warning signals and intervention recommendations.
      </p>
    </div>
  );
};

export default PsychologyAnalysisButton;
