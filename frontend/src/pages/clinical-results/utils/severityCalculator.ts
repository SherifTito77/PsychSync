/**
 * Severity Calculator Utility
 *
 * Calculates severity information based on assessment severity levels.
 * Maps severity levels to UI-friendly labels, colors, and descriptions.
 */

import { SeverityInfo } from '../types';

/**
 * Get severity information based on severity level
 *
 * @param severityLevel - The severity level string (e.g., "Minimal", "Mild", "Moderate", "Severe")
 * @returns SeverityInfo object with label, color, and description
 *
 * @example
 * ```typescript
 * const severity = getSeverityInfo('Moderate');
 * // Returns: { label: 'Moderate Symptoms', color: 'orange', description: '...' }
 * ```
 */
export function getSeverityInfo(severityLevel: string): SeverityInfo {
  const severityMap: Record<string, SeverityInfo> = {
    'Minimal': {
      label: 'Minimal Symptoms',
      color: 'green',
      description: 'Little to no symptoms detected'
    },
    'Mild': {
      label: 'Mild Symptoms',
      color: 'yellow',
      description: 'Mild symptoms that may benefit from self-care'
    },
    'Moderate': {
      label: 'Moderate Symptoms',
      color: 'orange',
      description: 'Moderate symptoms - consider professional support'
    },
    'Moderately Severe': {
      label: 'Moderately Severe',
      color: 'red',
      description: 'Significant symptoms - professional treatment recommended'
    },
    'Severe': {
      label: 'Severe Symptoms',
      color: 'red',
      description: 'Severe symptoms - immediate professional help needed'
    },
    'Low': {
      label: 'Low Wellbeing',
      color: 'yellow',
      description: 'Some areas for improvement identified'
    },
    'High Risk': {
      label: 'High Risk',
      color: 'red',
      description: 'High-risk pattern requiring immediate attention'
    }
  };

  return severityMap[severityLevel] || severityMap['Minimal'];
}

/**
 * Get Tailwind CSS color class for severity level
 *
 * @param severityLevel - The severity level string
 * @returns Tailwind CSS color class name
 *
 * @example
 * ```typescript
 * const colorClass = getSeverityColorClass('Moderate');
 * // Returns: 'bg-orange-500'
 * ```
 */
export function getSeverityColorClass(severityLevel: string): string {
  const severity = getSeverityInfo(severityLevel);

  const colorMap: Record<string, string> = {
    'green': 'bg-green-500',
    'yellow': 'bg-yellow-500',
    'orange': 'bg-orange-500',
    'red': 'bg-red-500',
  };

  return colorMap[severity.color] || 'bg-gray-500';
}

/**
 * Check if severity level indicates crisis/high severity
 *
 * @param severityLevel - The severity level string
 * @returns true if severity is "Severe" or "Moderately Severe"
 */
export function isCrisisSeverity(severityLevel: string): boolean {
  return severityLevel === 'Severe' || severityLevel === 'Moderately Severe';
}
