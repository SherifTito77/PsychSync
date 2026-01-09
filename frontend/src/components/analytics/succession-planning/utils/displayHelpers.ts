/**
 * Display Helper Utilities
 *
 * Functions for formatting and styling succession planning data
 */

export const getReadinessColor = (level: string): string => {
  switch (level) {
    case 'READY_NOW':
      return 'bg-green-100 text-green-800';
    case 'READY_1_2_YEARS':
      return 'bg-blue-100 text-blue-800';
    case 'READY_3_5_YEARS':
      return 'bg-yellow-100 text-yellow-800';
    case 'NOT_READY':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const getRiskColor = (level: string): string => {
  switch (level) {
    case 'LOW':
      return 'text-green-600 bg-green-50';
    case 'MEDIUM':
      return 'text-yellow-600 bg-yellow-50';
    case 'HIGH':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

export const getReadinessLabel = (level: string): string => {
  switch (level) {
    case 'READY_NOW':
      return 'Ready Now';
    case 'READY_1_2_YEARS':
      return 'Ready 1-2 Years';
    case 'READY_3_5_YEARS':
      return 'Ready 3-5 Years';
    case 'NOT_READY':
      return 'Not Ready';
    default:
      return level;
  }
};

export const getGapColor = (percentage: number): string => {
  if (percentage < 20) return 'text-green-600';
  if (percentage < 40) return 'text-yellow-600';
  if (percentage < 60) return 'text-orange-600';
  return 'text-red-600';
};
