/**
 * ClinicalAssessment Component (Refactored)
 *
 * Clinical assessment interface for PHQ-9, GAD-7, and PSS tools.
 *
 * This is a refactored version that imports data and types from separate modules,
 * making the code more maintainable and easier to test.
 *
 * @version 2.0.0 - Refactored for modularity
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';

// Import from modular files
import type { AssessmentData, AssessmentQuestion } from './types';
import { getPHQ9Questions } from './data/phq9Questions';
import { GAD7_QUESTIONS } from './data/gad7Questions';
import { PSS_QUESTIONS } from './data/pssQuestions';
import styles from './ClinicalAssessment.module.css';

// Assessment configurations with dynamic question generation
const assessments: Record<string, AssessmentData> = {
  phq9: {
    title: 'PHQ-9 Depression Screening',
    description: 'Patient Health Questionnaire-9 - Enhanced Assessment',
    instructions: 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
    questions: [], // Will be populated dynamically
    scoring: {
      min: 0,
      max: 27,
      levels: [
        { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no depression symptoms' },
        { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild depression symptoms' },
        { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate depression symptoms' },
        { range: [15, 19], label: 'Moderately Severe', color: 'red', description: 'Moderately severe depression symptoms' },
        { range: [20, 27], label: 'Severe', color: 'red', description: 'Severe depression symptoms' },
      ],
    },
  },
  gad7: {
    title: 'GAD-7 Anxiety Screening',
    description: 'Generalized Anxiety Disorder-7',
    instructions: 'Over the last 2 weeks, how often have you been bothered by the following problems?',
    questions: GAD7_QUESTIONS,
    scoring: {
      min: 0,
      max: 21,
      levels: [
        { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no anxiety symptoms' },
        { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild anxiety symptoms' },
        { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate anxiety symptoms' },
        { range: [15, 21], label: 'Severe', color: 'red', description: 'Severe anxiety symptoms' },
      ],
    },
  },
  stress: {
    title: 'Perceived Stress Scale (PSS)',
    description: 'Perceived Stress Scale - Stress Assessment',
    instructions: 'In the last month, how often have you felt the following ways?',
    questions: PSS_QUESTIONS,
    scoring: {
      min: 0,
      max: 40,
      levels: [
        { range: [0, 13], label: 'Minimal', color: 'green', description: 'Low perceived stress' },
        { range: [14, 20], label: 'Mild', color: 'yellow', description: 'Mild perceived stress' },
        { range: [21, 27], label: 'Moderate', color: 'orange', description: 'Moderate perceived stress' },
        { range: [28, 40], label: 'Severe', color: 'red', description: 'High perceived stress' },
      ],
    },
  },
};

const ClinicalAssessment: React.FC = () => {
  const { tool, action } = useParams<{ tool: string; action: string }>();
  const navigate = useNavigate();

  // Inject CSS to fix input blocking issues
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      ${styles.inputFix}
    `;
    document.head.appendChild(styleElement);

    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null);
  const [showCrisisWarning, setShowCrisisWarning] = useState(false);

  useEffect(() => {
    const loadAssessmentData = async () => {
      console.log('ClinicalAssessment: Loading assessment for tool:', tool);

      // Add timeout to prevent infinite loading
      const timeoutId = setTimeout(() => {
        console.warn('ClinicalAssessment: Loading timeout, forcing loading to false');
        setLoading(false);
      }, 5000);

      try {
        if (tool && assessments[tool as keyof typeof assessments]) {
          const baseAssessment = assessments[tool as keyof typeof assessments];

          // Dynamically generate questions for PHQ-9
          if (tool === 'phq9') {
            const randomQuestions = getPHQ9Questions(9);
            const enhancedAssessment = {
              ...baseAssessment,
              questions: randomQuestions
            };
            console.log('ClinicalAssessment: Enhanced assessment created');
            setAssessmentData(enhancedAssessment);
          } else {
            console.log('ClinicalAssessment: Using base assessment for', tool);
            setAssessmentData(baseAssessment);
          }
        } else {
          console.error('ClinicalAssessment: Invalid tool or assessment not found:', tool);
          setLoading(false);
        }
      } catch (error) {
        console.error('ClinicalAssessment: Error loading assessment data:', error);
        setLoading(false);
      } finally {
        clearTimeout(timeoutId);
      }

      console.log('ClinicalAssessment: Loading completed');
      setLoading(false);
    };

    loadAssessmentData();
  }, [tool]);

  const handleResponse = (questionId: number | string, answer: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: answer
    }));

    // Check for crisis indicators
    if (typeof answer === 'string' && answer.toLowerCase().includes('nearly every day')) {
      setShowCrisisWarning(true);
    }
  };

  const handleNext = () => {
    if (assessmentData && currentQuestion < assessmentData.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      console.log('Submitting assessment:', tool, 'responses:', responses);

      // Calculate score
      if (assessmentData) {
        const score = calculateScore(responses, assessmentData.questions);
        const level = getScoreLevel(score, assessmentData.scoring);

        console.log('Assessment score:', score, 'Level:', level);

        // Navigate to results
        setTimeout(() => {
          navigate(`/clinical/results/${tool}`, {
            state: { responses, score, level, assessmentData }
          });
        }, 1000);
      }
    } catch (error) {
      console.error('Error submitting assessment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const calculateScore = (responses: Record<string, string>, questions: AssessmentQuestion[]): number => {
    return questions.reduce((total, question) => {
      const answer = responses[question.id];
      if (!answer) return total;

      const answerIndex = question.options.indexOf(answer);
      return total + answerIndex;
    }, 0);
  };

  const getScoreLevel = (score: number, scoring: any) => {
    return scoring.levels.find((level: any) =>
      score >= level.range[0] && score <= level.range[1]
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className={styles.loadingSpinner}></div>
          <p className="text-gray-600 mt-4">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (!assessmentData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <Alert variant="error" title="Assessment Not Found">
              The requested assessment could not be loaded. Please try again or contact support.
            </Alert>
            <Button onClick={() => navigate('/clinical')} className="mt-4">
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentQuestionData = assessmentData.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / assessmentData.questions.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{assessmentData.title}</h1>
          <p className="text-gray-600">{assessmentData.description}</p>
        </div>

        {/* Crisis Warning */}
        {showCrisisWarning && (
          <div className={styles.crisisWarning}>
            <div className={styles.crisisWarningTitle}>⚠️ Support Available</div>
            <div className={styles.crisisWarningText}>
              If you're experiencing a crisis, please reach out for help:
              <br />• National Suicide Prevention Lifeline: 988
              <br />• Crisis Text Line: Text HOME to 741741
            </div>
          </div>
        )}

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {assessmentData.questions.length}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-label={`Assessment progress: ${Math.round(progress)}%`}
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>

        {/* Question Card */}
        <Card className={styles.questionCard}>
          <CardContent className="pt-6">
            <p className="text-lg text-gray-800 mb-6">{currentQuestionData.text}</p>

            <div className={`space-y-3 ${styles.inputFix}`}>
              {currentQuestionData.options.map((option) => {
                const isSelected = responses[currentQuestionData.id] === option;
                return (
                  <button
                    key={option}
                    onClick={() => handleResponse(currentQuestionData.id, option)}
                    className={`${styles.optionButton} ${isSelected ? styles.optionButton.selected : ''}`}
                    aria-pressed={isSelected}
                  >
                    <span className="ml-2">{option}</span>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className={styles.navButton}
          >
            Previous
          </Button>

          {currentQuestion < assessmentData.questions.length - 1 ? (
            <Button
              variant="default"
              onClick={handleNext}
              disabled={!responses[currentQuestionData.id]}
              className={styles.navButton}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="default"
              onClick={handleSubmit}
              disabled={submitting || Object.keys(responses).length < assessmentData.questions.length}
              className={styles.navButton}
            >
              {submitting ? 'Submitting...' : 'Submit Assessment'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClinicalAssessment;
