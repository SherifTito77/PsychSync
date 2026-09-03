/**
 * Team Metrics Utilities
 *
 * Functions for calculating team composition metrics and statistics
 */

import { TeamMember, TeamRequirement, PersonalityRadarData, SkillCoverageData } from '../types';

/**
 * Calculate personality compatibility between two team members
 * Based on complementary and similar traits
 */
const calculatePersonalityCompatibility = (
  traits1: Record<string, number>,
  traits2: Record<string, number>
): number => {
  // Complementary traits (opposites attract for work)
  const complementaryScore =
    Math.abs((traits1.extraversion || 0) - (traits2.extraversion || 0)) / 100 * 0.25 +
    Math.abs((traits1.openness || 0) - (traits2.openness || 0)) / 100 * 0.25;

  // Similar traits (should be aligned)
  const similarScore =
    (100 - Math.abs((traits1.conscientiousness || 0) - (traits2.conscientiousness || 0))) / 100 * 0.25 +
    (100 - Math.abs((traits1.agreeableness || 0) - (traits2.agreeableness || 0))) / 100 * 0.25;

  // Low neuroticism is generally better (penalty factor)
  const neuroticismPenalty = ((traits1.neuroticism || 0) + (traits2.neuroticism || 0)) / 200;

  return Math.max(0, Math.min(1, complementaryScore + similarScore - (neuroticismPenalty * 0.25)));
};

/**
 * Calculate average personality traits for a team
 */
export const calculateAveragePersonality = (team: TeamMember[]): Record<string, number> => {
  if (team.length === 0) return {};

  const traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism'];
  const averages: Record<string, number> = {};

  traits.forEach(trait => {
    const sum = team.reduce((total, member) => total + (member.personalityTraits[trait] || 0), 0);
    averages[trait] = sum / team.length;
  });

  return averages;
};

/**
 * Prepare data for personality radar chart
 */
export const preparePersonalityRadarData = (
  currentTeam: TeamMember[],
  requirements: TeamRequirement,
  optimizationResult?: any
): PersonalityRadarData[] => {
  const traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism'];
  const currentAvg = calculateAveragePersonality(currentTeam);

  return traits.map(trait => ({
    trait,
    current: currentTeam.length > 0 ? (currentAvg[trait] || 0.5) : 0.5,
    optimal: requirements.personalityBalance[trait]
      ? (requirements.personalityBalance[trait][0] + requirements.personalityBalance[trait][1]) / 2
      : 0.5,
    optimized: optimizationResult?.personalityBalance?.[trait] || 0.5,
  }));
};

/**
 * Prepare data for skill coverage chart
 */
export const prepareSkillCoverageData = (
  requirements: TeamRequirement,
  optimizationResult?: any
): SkillCoverageData[] => {
  const skills = Object.keys(requirements.skillWeights);

  return skills.map(skill => ({
    skill,
    coverage: optimizationResult?.skillCoverage?.[skill] || 0,
    weight: requirements.skillWeights[skill] || 0,
  }));
};

/**
 * Calculate team statistics
 */
export const calculateTeamStats = (team: TeamMember[]) => {
  if (team.length === 0) {
    return {
      averagePerformance: 0,
      averageSkills: 0,
      averageExperience: 0,
    };
  }

  const totalPerformance = team.reduce((sum, member) => sum + member.performanceScore, 0);
  const totalSkills = team.reduce((sum, member) => sum + member.skills.length, 0);
  const totalExperience = team.reduce((sum, member) => sum + member.yearsOfExperience, 0);

  return {
    averagePerformance: (totalPerformance / team.length) * 100,
    averageSkills: totalSkills / team.length,
    averageExperience: totalExperience / team.length,
  };
};

/**
 * Generate compatibility heatmap data
 */
export const generateCompatibilityHeatmap = (team: TeamMember[]) => {
  if (team.length === 0) return [];

  return team.map((member1, i) => {
    const row: any = { name: member1.name, id: member1.id };
    team.forEach((member2, j) => {
      // TODO(human): Replace with actual backend compatibility calculation
      // Calculate compatibility based on personality traits
      const comp = calculatePersonalityCompatibility(
        member1.personalityTraits || {},
        member2.personalityTraits || {}
      );
      row[`member${j}`] = Number((comp * 100).toFixed(1));
    });
    return row;
  });
};

/**
 * Get recommended team composition
 */
export const getRecommendedTeam = (
  currentTeam: TeamMember[],
  availableCandidates: TeamMember[],
  recommendedMemberIds: string[],
  teamSize: number
): TeamMember[] => {
  const selectedCandidates = availableCandidates.filter(c =>
    recommendedMemberIds.includes(c.id)
  );

  return [...currentTeam, ...selectedCandidates].slice(0, teamSize);
};

/**
 * Get color based on score value
 */
export const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.6) return 'text-yellow-600';
  if (score >= 0.4) return 'text-orange-600';
  return 'text-red-600';
};
