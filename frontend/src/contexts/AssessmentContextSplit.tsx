import React, { ReactNode } from 'react';
import { AssessmentDataProvider } from './AssessmentDataContext';
import { AssessmentUIProvider } from './AssessmentUIProvider';
import { AssessmentActionsProvider } from './AssessmentActionsContext';

/**
 * Combined Assessment Provider
 *
 * This provider composes all three focused contexts:
 * 1. AssessmentDataContext - Core data (assessment, questions, answers, results)
 * 2. AssessmentUIContext - UI state (loading, error, submitting)
 * 3. AssessmentActionsContext - Actions (handleAnswer, handleNext, handleSubmit, etc.)
 *
 * USAGE:
 *
 * import { AssessmentProvider } from '@/contexts/AssessmentContextSplit';
 *
 * function App() {
 *   return (
 *     <AssessmentProvider>
 *       <YourApp />
 *     </AssessmentProvider>
 *   );
 * }
 *
 * Then in components, choose the right hook for your needs:
 *
 * // For data only (won't re-render on loading/error changes)
 * const { assessment, answers } = useAssessmentData();
 *
 * // For UI state only (won't re-render on data changes)
 * const { isLoading, error } = useAssessmentUI();
 *
 * // For actions (stable references)
 * const { handleAnswer, handleSubmit } = useAssessmentActions();
 *
 * BENEFITS:
 * - Components only subscribe to state they actually use
 * - Prevents unnecessary re-renders across the component tree
 * - Better performance for large assessment interfaces
 */

interface AssessmentProviderProps {
  children: ReactNode;
}

export function AssessmentProvider({ children }: AssessmentProviderProps) {
  return (
    <AssessmentDataProvider>
      <AssessmentUIProvider>
        <AssessmentActionsProvider>
          {children}
        </AssessmentActionsProvider>
      </AssessmentUIProvider>
    </AssessmentDataProvider>
  );
}

/**
 * Convenience re-exports for backward compatibility
 *
 * If migrating from the old AssessmentContext, you can use these imports:
 * import {
 *   AssessmentProvider,
 *   useAssessmentData,
 *   useAssessmentUI,
 *   useAssessmentActions
 * } from '@/contexts/AssessmentContextSplit';
 */

export { useAssessmentData } from './AssessmentDataContext';
export { useAssessmentUI } from './AssessmentUIProvider';
export { useAssessmentActions } from './AssessmentActionsContext';

/**
 * MIGRATION GUIDE:
 *
 * Old way (single context):
 * import { useAssessment } from '@/contexts/AssessmentContext';
 * const { assessment, isLoading, handleAnswer } = useAssessment();
 *
 * New way (split contexts):
 * import { useAssessmentData, useAssessmentUI, useAssessmentActions } from '@/contexts/AssessmentContextSplit';
 *
 * // For data (won't re-render on UI state changes)
 * const { assessment, answers } = useAssessmentData();
 *
 * // For UI state (won't re-render on data changes)
 * const { isLoading, error } = useAssessmentUI();
 *
 * // For actions (stable references)
 * const { handleAnswer, handleSubmit } = useAssessmentActions();
 *
 * PERFORMANCE BENEFIT:
 *
 * Before: If isLoading changes, ALL components using useAssessment re-render
 * After:  Only components using useAssessmentUI re-render when isLoading changes
 *
 * This is especially important for large assessment interfaces with many components.
 */
