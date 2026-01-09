/**
 * Clinical Actions Hook
 *
 * Custom hook for handling clinical result actions (save, share, print, navigate).
 * Separates action logic from the main results display component.
 */

import { useNavigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { AssessmentResult } from '../types';

interface UseClinicalActionsReturn {
  saving: boolean;
  handleSave: (result: AssessmentResult, tool: string | undefined) => Promise<void>;
  handleShareWithProvider: (result: AssessmentResult) => void;
  handleRetakeAssessment: (tool: string | undefined) => void;
  handleBackToAssessments: () => void;
}

/**
 * Hook to handle clinical results actions
 *
 * @returns Object containing action handlers and loading states
 *
 * @example
 * ```typescript
 * const { saving, handleSave, handleShareWithProvider } = useClinicalActions();
 *
 * <Button onClick={() => handleSave(result, tool)} disabled={saving}>
 *   {saving ? 'Saving...' : 'Save Results'}
 * </Button>
 * ```
 */
export function useClinicalActions(): UseClinicalActionsReturn {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const handleSave = useCallback(async (result: AssessmentResult, tool: string | undefined) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      await fetch('/api/v1/clinical/screenings/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          tool,
          result,
        }),
      });
    } catch (error) {
      console.error('Error saving results:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const handleShareWithProvider = useCallback((result: AssessmentResult) => {
    navigate('/clinical/referrals/new', { state: { assessmentResult: result } });
  }, [navigate]);

  const handleRetakeAssessment = useCallback((tool: string | undefined) => {
    if (tool) {
      navigate(`/clinical/assessment/${tool}/take`);
    }
  }, [navigate]);

  const handleBackToAssessments = useCallback(() => {
    navigate('/clinical-assessments');
  }, [navigate]);

  return {
    saving,
    handleSave,
    handleShareWithProvider,
    handleRetakeAssessment,
    handleBackToAssessments,
  };
}
