import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';

/**
 * AssessmentDataContext - Core assessment data management
 *
 * This context ONLY manages assessment data:
 * - Assessment configuration
 * - Current question index
 * - User answers
 * - Results
 *
 * UI state (loading, error) is in AssessmentUIContext
 * Actions are in AssessmentActionsContext
 *
 * This split prevents unnecessary re-renders when UI state changes.
 */

// Generic interfaces for assessment data
interface AssessmentQuestion {
  id: number;
  question_text: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface Assessment<T extends AssessmentQuestion> {
  id: string;
  title: string;
  description: string;
  questions: T[];
}

interface AssessmentDataContextValue<T extends AssessmentQuestion> {
  // Data only - no UI state
  assessment: Assessment<T> | null;
  currentQuestion: number;
  answers: Record<number, string>;
  results: any;

  // Setters only - for actions context
  setAssessment: (assessment: Assessment<T> | null | ((prev: Assessment<T> | null) => Assessment<T> | null)) => void;
  setCurrentQuestion: (index: number | ((prev: number) => number)) => void;
  setAnswers: (answers: Record<number, string> | ((prev: Record<number, string>) => Record<number, string>)) => void;
  setResults: (results: any | ((prev: any) => any)) => void;
}

const AssessmentDataContext = createContext<AssessmentDataContextValue<any> | undefined>(undefined);

interface AssessmentDataProviderProps {
  children: ReactNode;
}

export function AssessmentDataProvider<T extends AssessmentQuestion>({ children }: AssessmentDataProviderProps) {
  // Core assessment data - separate from UI state
  const [assessment, setAssessment] = useState<Assessment<T> | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [results, setResults] = useState<any>(null);

  // Memoized context value - only changes when data actually changes
  const value: AssessmentDataContextValue<T> = useMemo(() => ({
    // Data
    assessment,
    currentQuestion,
    answers,
    results,

    // Setters (for use by actions context)
    setAssessment,
    setCurrentQuestion,
    setAnswers,
    setResults,
  }), [
    assessment,
    currentQuestion,
    answers,
    results,
    setAssessment,
    setCurrentQuestion,
    setAnswers,
    setResults,
  ]);

  return (
    <AssessmentDataContext.Provider value={value}>
      {children}
    </AssessmentDataContext.Provider>
  );
}

/**
 * Hook to use assessment data context
 * Throws error if used outside of AssessmentDataProvider
 */
export function useAssessmentData<T extends AssessmentQuestion>() {
  const context = useContext(AssessmentDataContext);
  if (context === undefined) {
    throw new Error('useAssessmentData must be used within an AssessmentDataProvider');
  }
  return context as AssessmentDataContextValue<T>;
}
