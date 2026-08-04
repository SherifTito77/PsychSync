import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';

/**
 * AssessmentUIContext - UI state management for assessments
 */

interface AssessmentUIContextValue {
  // UI State only
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;

  // UI State setters
  setIsLoading: (loading: boolean) => void;
  setIsSubmitting: (submitting: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const AssessmentUIContext = createContext<AssessmentUIContextValue | undefined>(undefined);

interface AssessmentUIProviderProps {
  children: ReactNode;
}

export function AssessmentUIProvider({ children }: AssessmentUIProviderProps) {
  // UI state only - separated from data
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clear error helper
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Memoized context value - only changes when UI state actually changes
  const value: AssessmentUIContextValue = useMemo(() => ({
    // UI State
    isLoading,
    isSubmitting,
    error,

    // UI State setters
    setIsLoading,
    setIsSubmitting,
    setError,
    clearError,
  }), [
    isLoading,
    isSubmitting,
    error,
    setIsLoading,
    setIsSubmitting,
    setError,
    clearError,
  ]);

  return (
    <AssessmentUIContext.Provider value={value}>
      {children}
    </AssessmentUIContext.Provider>
  );
}

/**
 * Hook to use assessment UI context
 * Throws error if used outside of AssessmentUIProvider
 */
export function useAssessmentUI() {
  const context = useContext(AssessmentUIContext);
  if (context === undefined) {
    throw new Error('useAssessmentUI must be used within an AssessmentUIProvider');
  }
  return context;
}
