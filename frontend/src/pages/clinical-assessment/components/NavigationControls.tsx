/**
 * Navigation Controls Component
 *
 * Provides Next/Previous navigation buttons for assessment flow.
 */

import React from 'react';
import { Button } from '@/components/ui/Button';

interface NavigationControlsProps {
  currentQuestion: number;
  totalQuestions: number;
  canProgress: boolean;
  onNext: () => void;
  onPrevious: () => void;
  onSubmit: () => void;
  submitting: boolean;
}

export const NavigationControls: React.FC<NavigationControlsProps> = ({
  currentQuestion,
  totalQuestions,
  canProgress,
  onNext,
  onPrevious,
  onSubmit,
  submitting,
}) => {
  const isLastQuestion = currentQuestion === totalQuestions - 1;
  const isFirstQuestion = currentQuestion === 0;

  return (
    <div className="flex justify-between items-center mt-6 max-w-3xl mx-auto">
      <Button
        variant="outline"
        onClick={onPrevious}
        disabled={isFirstQuestion}
      >
        Previous
      </Button>

      {isLastQuestion ? (
        <Button
          onClick={onSubmit}
          disabled={!canProgress || submitting}
          className="px-8"
        >
          {submitting ? 'Submitting...' : 'Submit Assessment'}
        </Button>
      ) : (
        <Button
          onClick={onNext}
          disabled={!canProgress}
        >
          Next
        </Button>
      )}
    </div>
  );
};
