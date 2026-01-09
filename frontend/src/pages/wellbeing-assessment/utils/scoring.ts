/**
 * Wellbeing Scoring Utilities
 *
 * Functions to calculate wellbeing scores by category.
 */

import { WellbeingQuestion, CategoryScore } from '../types';

// Score mapping for answer options
const SCORE_MAP: Record<string, number> = {
  // Positive options (highest score)
  'Excellent': 4,
  'Very Good': 4,
  'Always': 4,
  'Very High': 4,
  'High Energy': 4,
  'Very Satisfied': 4,
  'Definitely Yes': 4,
  'Very Comfortable': 4,
  'Very Stable': 4,
  'Very Well': 4,
  'Strongly Agree': 4,
  'Very Secure': 4,
  'Very Clear': 4,
  'Daily': 4,
  '8+ hours': 4,
  'Yes, 6+ months': 4,
  'Energized': 4,

  // Good options (second highest score)
  'Good': 3,
  'Usually': 3,
  'High': 3,
  'Moderately High': 3,
  'Satisfied': 3,
  'Mostly Yes': 3,
  'Comfortable': 3,
  'Stable': 3,
  'Well': 3,
  'Agree': 3,
  'Secure': 3,
  'Clear': 3,
  'Several times a week': 3,
  '7-8 hours': 3,
  'Yes, 3-6 months': 3,
  'Mostly Energized': 3,
  'Several times a week': 3,

  // Fair options (middle score)
  'Fair': 2,
  'Sometimes': 2,
  'Moderate': 2,
  'Moderately': 2,
  'Neutral': 2,
  'Somewhat': 2,
  'Somewhat Comfortable': 2,
  'Somewhat Stable': 2,
  'Somewhat Clear': 2,
  'Occasionally': 2,
  'Somewhat Secure': 2,
  'Once a week': 2,
  '5-6 hours': 2,
  'Yes, less than 3 months': 2,
  'Often': 2,

  // Poor options (lowest score)
  'Poor': 1,
  'Rarely': 1,
  'Rarely/Never': 1,
  'Low': 1,
  'Low Energy': 1,
  'Dissatisfied': 1,
  'No': 1,
  'Uncomfortable': 1,
  'Unstable': 1,
  'Poorly': 1,
  'Disagree': 1,
  'Insecure': 1,
  'Unclear': 1,
  'Never': 1,
  'Less than 5 hours': 1,
  'Drained': 1,
};

/**
 * Calculate score for a single category
 */
export function calculateCategoryScore(
  questions: WellbeingQuestion[],
  responses: Record<string, string>
): CategoryScore {
  let totalScore = 0;
  let answeredQuestions = 0;

  questions.forEach((question) => {
    const answer = responses[question.id];
    if (answer) {
      totalScore += SCORE_MAP[answer] || 0;
      answeredQuestions++;
    }
  });

  const maxScore = questions.length * 4; // Max 4 points per question
  const percentage = answeredQuestions > 0 ? (totalScore / maxScore) * 100 : 0;

  let level: 'low' | 'medium' | 'high';
  if (percentage >= 70) {
    level = 'high';
  } else if (percentage >= 40) {
    level = 'medium';
  } else {
    level = 'low';
  }

  return {
    category: questions[0].category, // All questions in this group have same category
    score: totalScore,
    maxScore,
    percentage: Math.round(percentage),
    level,
  };
}

/**
 * Calculate overall wellbeing percentage
 */
export function calculateOverallPercentage(
  categoryScores: CategoryScore[]
): number {
  if (categoryScores.length === 0) return 0;

  const totalPercentage = categoryScores.reduce((sum, score) => sum + score.percentage, 0);
  return Math.round(totalPercentage / categoryScores.length);
}
