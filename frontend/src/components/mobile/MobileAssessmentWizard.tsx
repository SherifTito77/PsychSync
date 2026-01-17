/**
 * Mobile Assessment Wizard Component
 *
 * A reusable, mobile-optimized assessment wizard with:
 * - One question per screen
 * - Large touch targets (44x44px minimum)
 * - Sticky bottom navigation
 * - Progress indicator
 * - Smooth animations
 * - Swipe gestures for navigation
 */

import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronLeft, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import Progress from '@/components/ui/progress';

interface Question {
  id: string;
  text: string;
  options: Array<{
    value: number;
    text: string;
  }>;
  category?: string;
}

interface MobileAssessmentWizardProps {
  title: string;
  description: string;
  questions: Question[];
  onSubmit: (responses: Record<string, number>) => Promise<void>;
  submitEndpoint: string;
  showCategory?: boolean;
}

export function MobileAssessmentWizard({
  title,
  description,
  questions,
  onSubmit,
  submitEndpoint,
  showCategory = false,
}: MobileAssessmentWizardProps) {
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [direction, setDirection] = useState(0);

  const currentQ = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;
  const isAnswered = responses[currentQ?.id] !== undefined;
  const canGoNext = isAnswered && currentQuestion < questions.length - 1;
  const canSubmit = isAnswered && currentQuestion === questions.length - 1;

  // Touch handling for swipe gestures
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);

  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(0);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;

    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && canGoNext) {
      handleNext();
    }
    if (isRightSwipe && currentQuestion > 0) {
      handlePrevious();
    }
  };

  const handleResponse = async (value: number) => {
    setResponses((prev) => ({
      ...prev,
      [currentQ.id]: value,
    }));

    // Auto-advance after a short delay for better UX
    if (currentQuestion < questions.length - 1) {
      setTimeout(() => {
        handleNext();
      }, 300);
    }
  };

  const handleNext = () => {
    if (canGoNext) {
      setDirection(1);
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setDirection(-1);
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;

    setIsSubmitting(true);
    try {
      await onSubmit(responses);
      setShowResult(true);
    } catch (error) {
      console.error('Submission error:', error);
      // Handle error appropriately
    } finally {
      setIsSubmitting(false);
    }
  };

  const variants = {
    enter: (direction: number) => ({
      x: direction > 0 ? '100%' : '-100%',
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction < 0 ? '100%' : '-100%',
      opacity: 0,
    }),
  };

  if (showResult) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 15 }}
          className="text-center"
        >
          <CheckCircle2 className="w-24 h-24 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Assessment Complete!</h2>
          <p className="text-gray-600 mb-6">Your responses have been submitted successfully.</p>
          <Button onClick={() => window.history.back()} size="lg" className="w-full max-w-sm">
            Return to Dashboard
          </Button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header with progress */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 sticky top-0 z-10">
        <div className="mb-2">
          <p className="text-sm font-medium text-gray-900 mb-1">
            Question {currentQuestion + 1} of {questions.length}
          </p>
          <Progress value={progress} className="h-2" />
        </div>
        {showCategory && currentQ.category && (
          <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
            {currentQ.category}
          </span>
        )}
      </div>

      {/* Question card */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <motion.div
          key={currentQuestion}
          custom={direction}
          variants={variants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{
            x: { type: 'spring', stiffness: 300, damping: 30 },
            opacity: { duration: 0.2 },
          }}
          className="max-w-lg mx-auto"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          <div className="bg-white rounded-2xl shadow-sm p-6 mb-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">{currentQ.text}</h2>
            <p className="text-sm text-gray-500">Select the option that best describes you</p>
          </div>

          {/* Options */}
          <div className="space-y-3">
            {currentQ.options.map((option) => {
              const isSelected = responses[currentQ.id] === option.value;

              return (
                <motion.button
                  key={option.value}
                  onClick={() => handleResponse(option.value)}
                  className={`w-full p-5 rounded-xl border-2 text-left transition-all min-h-[60px] flex items-center ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50/50'
                  }`}
                  whileTap={{ scale: 0.98 }}
                  disabled={isSubmitting}
                >
                  <span className="flex-1 text-base font-medium">{option.text}</span>
                  {isSelected && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center ml-3"
                    >
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    </motion.div>
                  )}
                </motion.button>
              );
            })}
          </div>

          {/* Swipe hint */}
          {canGoNext && !isSubmitting && (
            <p className="text-center text-sm text-gray-400 mt-6">
              Swipe left to continue →
            </p>
          )}
        </motion.div>
      </div>

      {/* Sticky bottom navigation */}
      <div className="bg-white border-t border-gray-200 px-4 py-4 safe-area-bottom">
        <div className="max-w-lg mx-auto flex gap-3">
          <Button
            variant="outline"
            size="lg"
            onClick={handlePrevious}
            disabled={currentQuestion === 0 || isSubmitting}
            className="flex-1 min-h-[52px]"
          >
            <ChevronLeft className="w-5 h-5 mr-1" />
            Previous
          </Button>

          {canSubmit ? (
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting}
              size="lg"
              className="flex-1 min-h-[52px] bg-blue-600 hover:bg-blue-700"
            >
              {isSubmitting ? 'Submitting...' : 'Submit'}
              <CheckCircle2 className="w-5 h-5 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={!canGoNext || isSubmitting}
              size="lg"
              className="flex-1 min-h-[52px] bg-blue-600 hover:bg-blue-700"
            >
              Next
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
