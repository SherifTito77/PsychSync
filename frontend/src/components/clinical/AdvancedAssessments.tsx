/**
 * Advanced Clinical Assessments Index
 *
 * Exports all advanced clinical assessment components:
 * - LSAS (Social Anxiety)
 * - EAT-26 (Eating Disorders)
 * - Y-BOCS (OCD)
 *
 * Usage:
 *   import { LSASScreening, EAT26Screening, YBOCSScreening } from '@/components/clinical/AdvancedAssessments';
 */

export { LSASScreening } from './LSASScreening';
export { EAT26Screening } from './EAT26Screening';
export { YBOCSScreening } from './YBOCSScreening';

/**
 * Assessment Metadata for Routing/Display
 */
export const ADVANCED_ASSESSMENTS = {
  LSAS: {
    id: 'lsas',
    name: 'Social Anxiety Assessment',
    component: 'LSASScreening',
    description: 'Liebowitz Social Anxiety Scale - 24 items assessing fear and avoidance',
    duration: '~10 minutes',
    icon: 'Brain',
    color: 'blue',
    reliability: 'α = 0.95',
  },
  EAT26: {
    id: 'eat26',
    name: 'Eating Attitudes Assessment',
    component: 'EAT26Screening',
    description: 'Eating Attitudes Test - 26 items screening for eating disorders',
    duration: '~8 minutes',
    icon: 'Apple',
    color: 'green',
    reliability: 'α = 0.83',
  },
  YBOCS: {
    id: 'ybocs',
    name: 'OCD Severity Assessment',
    component: 'YBOCSScreening',
    description: 'Yale-Brown Obsessive Compulsive Scale - 10 items for OCD severity',
    duration: '~10 minutes',
    icon: 'RefreshCw',
    color: 'purple',
    reliability: 'α = 0.98',
  },
} as const;

export type AdvancedAssessmentType = keyof typeof ADVANCED_ASSESSMENTS;
