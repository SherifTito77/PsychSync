/**
 * Wellbeing Assessment Hook
 *
 * Custom hook for managing wellbeing assessment flow and scoring.
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { WELLBEING_QUESTIONS, QUESTIONS_BY_CATEGORY, CATEGORIES, QUESTIONS_PER_GROUP } from '../constants/questions';
import { calculateCategoryScore, calculateOverallPercentage } from '../utils/scoring';
import { CategoryScore, StoredAssessmentResult } from '../types';

interface UseWellbeingAssessmentReturn {
  currentCategoryIndex: number;
  currentGroupIndex: number;
  responses: Record<string, string>;
  showResults: boolean;
  currentQuestions: typeof WELLBEING_QUESTIONS;
  categoryScores: CategoryScore[];
  overallPercentage: number;
  handleResponseChange: (questionId: string, answer: string) => void;
  handleNext: () => void;
  handlePrevious: () => void;
  handleComplete: () => void;
  canProgress: () => boolean;
  getCategoryProgress: () => { current: number; total: number };
}

/**
 * Hook to manage wellbeing assessment flow
 */
export function useWellbeingAssessment(): UseWellbeingAssessmentReturn {
  const navigate = useNavigate();

  const [currentCategoryIndex, setCurrentCategoryIndex] = useState(0);
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [showResults, setShowResults] = useState(false);
  const [categoryScores, setCategoryScores] = useState<CategoryScore[]>([]);
  const [overallPercentage, setOverallPercentage] = useState(0);

  // Calculate scores when showing results
  useEffect(() => {
    if (showResults) {
      const scores: CategoryScore[] = CATEGORIES.map((category) => {
        const categoryQuestions = QUESTIONS_BY_CATEGORY[category];
        return calculateCategoryScore(categoryQuestions, responses);
      });

      setCategoryScores(scores);
      setOverallPercentage(calculateOverallPercentage(scores));

      // Save to localStorage
      const result: StoredAssessmentResult = {
        id: `wb_${Date.now()}`,
        date: new Date().toISOString(),
        overallPercentage: calculateOverallPercentage(scores),
        categoryScores: scores,
      };

      // Save to wellnessStorage (would import from utils)
      try {
        const history = JSON.parse(localStorage.getItem('wellbeingAssessmentHistory') || '[]');
        history.push(result);
        localStorage.setItem('wellbeingAssessmentHistory', JSON.stringify(history));
      } catch (error) {
        console.error('Failed to save assessment:', error);
      }
    }
  }, [showResults, responses]);

  const handleResponseChange = useCallback((questionId: string, answer: string) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  }, []);

  const handleNext = useCallback(() => {
    const currentCategory = CATEGORIES[currentCategoryIndex];
    const categoryQuestions = QUESTIONS_BY_CATEGORY[currentCategory];
    const totalGroups = Math.ceil(categoryQuestions.length / QUESTIONS_PER_GROUP);

    if (currentGroupIndex < totalGroups - 1) {
      // More questions in current category
      setCurrentGroupIndex((prev) => prev + 1);
    } else if (currentCategoryIndex < CATEGORIES.length - 1) {
      // Move to next category
      setCurrentCategoryIndex((prev) => prev + 1);
      setCurrentGroupIndex(0);
    } else {
      // Assessment complete
      setShowResults(true);
    }
  }, [currentCategoryIndex, currentGroupIndex]);

  const handlePrevious = useCallback(() => {
    if (currentGroupIndex > 0) {
      setCurrentGroupIndex((prev) => prev - 1);
    } else if (currentCategoryIndex > 0) {
      setCurrentCategoryIndex((prev) => prev - 1);
      const prevCategory = CATEGORIES[currentCategoryIndex - 1];
      const prevCategoryQuestions = QUESTIONS_BY_CATEGORY[prevCategory];
      const totalGroups = Math.ceil(prevCategoryQuestions.length / QUESTIONS_PER_GROUP);
      setCurrentGroupIndex(totalGroups - 1);
    }
  }, [currentCategoryIndex, currentGroupIndex]);

  const handleComplete = useCallback(() => {
    setShowResults(true);
  }, []);

  const canProgress = useCallback((): boolean => {
    const currentCategory = CATEGORIES[currentCategoryIndex];
    const categoryQuestions = QUESTIONS_BY_CATEGORY[currentCategory];
    const startIndex = currentGroupIndex * QUESTIONS_PER_GROUP;
    const endIndex = Math.min(startIndex + QUESTIONS_PER_GROUP, categoryQuestions.length);
    const currentQuestions = categoryQuestions.slice(startIndex, endIndex);

    return currentQuestions.every((q) => responses[q.id]);
  }, [currentCategoryIndex, currentGroupIndex, responses]);

  const getCategoryProgress = useCallback(() => {
    const currentCategory = CATEGORIES[currentCategoryIndex];
    const categoryQuestions = QUESTIONS_BY_CATEGORY[currentCategory];
    const startIndex = currentGroupIndex * QUESTIONS_PER_GROUP;
    const totalGroups = Math.ceil(categoryQuestions.length / QUESTIONS_PER_GROUP);

    return {
      current: currentCategoryIndex * 10 + currentGroupIndex + 1,
      total: CATEGORIES.length * 10, // Approximate
    };
  }, [currentCategoryIndex, currentGroupIndex]);

  // Get current questions to display
  const currentCategory = CATEGORIES[currentCategoryIndex];
  const categoryQuestions = QUESTIONS_BY_CATEGORY[currentCategory];
  const startIndex = currentGroupIndex * QUESTIONS_PER_GROUP;
  const endIndex = Math.min(startIndex + QUESTIONS_PER_GROUP, categoryQuestions.length);
  const currentQuestions = categoryQuestions.slice(startIndex, endIndex);

  return {
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
    getCategoryProgress,
  };
}
