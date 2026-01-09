/**
 * Display Helper Utilities
 *
 * Functions for formatting and styling scores and metrics
 */

/**
 * Get color class for score text based on value
 */
export const getScoreColor = (score: number): string => {
  if (score >= 0.9) return 'text-green-600';
  if (score >= 0.7) return 'text-blue-600';
  if (score >= 0.5) return 'text-yellow-600';
  return 'text-red-600';
};

/**
 * Get background color class for score based on value
 */
export const getScoreBgColor = (score: number): string => {
  if (score >= 0.9) return 'bg-green-100';
  if (score >= 0.7) return 'bg-blue-100';
  if (score >= 0.5) return 'bg-yellow-100';
  return 'bg-red-100';
};
