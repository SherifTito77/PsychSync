/**
 * Wellbeing Assessment Page
 *
 * Main orchestrator component for comprehensive wellbeing assessment.
 * This page has been split from a monolithic 1,373-line component into
 * manageable, focused sub-components and utilities.
 *
 * Architecture:
 * - Constants: 54 wellbeing questions organized by category
 * - Hooks: Assessment flow and scoring management
 * - Components: Question display, progress, results
 * - This file: Coordinates everything together
 *
 * Before: 1,373 lines in one file
 * After: <200 lines in this file + focused sub-components
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';

// Constants
import { CATEGORIES } from './constants/questions';

// Hooks
import { useWellbeingAssessment } from './hooks/useWellbeingAssessment';

// Components
import { QuestionCard } from './components/QuestionCard';
import { CategoryProgress } from './components/CategoryProgress';
import { ResultsDisplay } from './components/ResultsDisplay';

// Types
import { WellbeingQuestion } from './types';

/**
 * Main Wellbeing Assessment Component
 */
const WellbeingAssessment: React.FC = () => {
  const navigate = useNavigate();

  // Assessment flow hook
  const {
    currentCategoryIndex,
    currentGroupIndex,
    responses,
    showResults,
    currentQuestions,
    categoryScores,
    overallPercentage,
    handleResponseChange,
    handleNext,
    handlePrevious,
    handleComplete,
    canProgress,
  } = useWellbeingAssessment();

  // Show results if assessment complete
  if (showResults) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="mb-6">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="mb-4"
            >
              ← Back to Dashboard
            </Button>
            <h1 className="text-3xl font-bold text-gray-900">
              Wellbeing Assessment Results
            </h1>
          </div>

          <ResultsDisplay
            overallPercentage={overallPercentage}
            categoryScores={categoryScores}
            onRetake={() => window.location.reload()}
            onDashboard={() => navigate('/')}
          />
        </div>
      </div>
    );
  }

  const currentCategory = CATEGORIES[currentCategoryIndex];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4"
          >
            ← Back to Dashboard
          </Button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Comprehensive Wellbeing Assessment
          </h1>
          <p className="text-gray-600">
            Answer questions about your wellbeing across 7 key areas of life.
            This should take approximately 10-15 minutes.
          </p>
        </div>

        {/* Info Alert */}
        <Alert variant="info" className="mb-6">
          <p className="text-sm">
            <strong>Tip:</strong> Answer honestly based on how you've been feeling
            over the past few weeks. There are no right or wrong answers.
          </p>
        </Alert>

        {/* Category Progress */}
        <CategoryProgress
          currentCategoryIndex={currentCategoryIndex}
          currentGroupIndex={currentGroupIndex}
          totalCategories={CATEGORIES.length}
          categoryName={currentCategory}
        />

        {/* Question Cards */}
        <div className="space-y-4 mb-6">
          {currentQuestions.map((question, index) => {
            const questionNumber =
              currentCategoryIndex * 10 + currentGroupIndex * 3 + index + 1;

            return (
              <QuestionCard
                key={question.id}
                question={question}
                selectedAnswer={responses[question.id]}
                onResponseChange={(answer) => handleResponseChange(question.id, answer)}
                questionNumber={questionNumber}
              />
            );
          })}
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center max-w-3xl mx-auto">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentCategoryIndex === 0 && currentGroupIndex === 0}
          >
            Previous
          </Button>

          {currentCategoryIndex === CATEGORIES.length - 1 &&
          currentGroupIndex ===
            Math.ceil(
              (currentQuestions.length / 3) * 3 || currentQuestions.length
            ) /
              3 -
              1 ? (
            <Button onClick={handleComplete} disabled={!canProgress()}>
              View Results
            </Button>
          ) : (
            <Button onClick={handleNext} disabled={!canProgress()}>
              Next
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default WellbeingAssessment;
