import { describe, it, expect } from 'vitest';
import {
  calculateAveragePersonality,
  calculateTeamStats,
  getScoreColor,
  getRecommendedTeam,
  generateCompatibilityHeatmap,
  preparePersonalityRadarData,
  prepareSkillCoverageData,
} from '../teamMetrics';
import { TeamMember, TeamRequirement } from '../../types';

describe('teamMetrics utilities', () => {
  const mockTeam: TeamMember[] = [
    {
      id: '1',
      name: 'Alice',
      email: 'alice@example.com',
      role: 'Developer',
      department: 'Engineering',
      skills: ['React', 'TypeScript'],
      skillLevels: { React: 90, TypeScript: 85 },
      personalityTraits: {
        Openness: 80,
        Conscientiousness: 70,
        Extraversion: 60,
        Agreeableness: 90,
        Neuroticism: 20,
      },
      performanceScore: 0.9,
      collaborationScore: 0.85,
      innovationScore: 0.8,
      leadershipPotential: 0.7,
      adaptabilityScore: 0.75,
      yearsOfExperience: 5,
      availability: true,
    },
    {
      id: '2',
      name: 'Bob',
      email: 'bob@example.com',
      role: 'Designer',
      department: 'Product',
      skills: ['Figma', 'UI/UX'],
      skillLevels: { Figma: 95, 'UI/UX': 90 },
      personalityTraits: {
        Openness: 90,
        Conscientiousness: 60,
        Extraversion: 80,
        Agreeableness: 70,
        Neuroticism: 30,
      },
      performanceScore: 0.85,
      collaborationScore: 0.9,
      innovationScore: 0.95,
      leadershipPotential: 0.6,
      adaptabilityScore: 0.8,
      yearsOfExperience: 3,
      availability: true,
    },
  ];

  describe('calculateAveragePersonality', () => {
    it('should calculate the average of personality traits correctly', () => {
      const result = calculateAveragePersonality(mockTeam);
      expect(result.Openness).toBe(85);
      expect(result.Conscientiousness).toBe(65);
      expect(result.Extraversion).toBe(70);
      expect(result.Agreeableness).toBe(80);
      expect(result.Neuroticism).toBe(25);
    });

    it('should return an empty object for an empty team', () => {
      expect(calculateAveragePersonality([])).toEqual({});
    });
  });

  describe('calculateTeamStats', () => {
    it('should calculate average performance, skills, and experience correctly', () => {
      const result = calculateTeamStats(mockTeam);
      // Performance: (0.9 + 0.85) / 2 * 100 = 87.5
      expect(result.averagePerformance).toBe(87.5);
      // Skills: (2 + 2) / 2 = 2
      expect(result.averageSkills).toBe(2);
      // Experience: (5 + 3) / 2 = 4
      expect(result.averageExperience).toBe(4);
    });

    it('should return zeros for an empty team', () => {
      const result = calculateTeamStats([]);
      expect(result).toEqual({
        averagePerformance: 0,
        averageSkills: 0,
        averageExperience: 0,
      });
    });
  });

  describe('getScoreColor', () => {
    it('should return green for high scores', () => {
      expect(getScoreColor(0.9)).toBe('text-green-600');
      expect(getScoreColor(0.8)).toBe('text-green-600');
    });

    it('should return yellow for medium-high scores', () => {
      expect(getScoreColor(0.7)).toBe('text-yellow-600');
      expect(getScoreColor(0.6)).toBe('text-yellow-600');
    });

    it('should return orange for medium-low scores', () => {
      expect(getScoreColor(0.5)).toBe('text-orange-600');
      expect(getScoreColor(0.4)).toBe('text-orange-600');
    });

    it('should return red for low scores', () => {
      expect(getScoreColor(0.3)).toBe('text-red-600');
      expect(getScoreColor(0.1)).toBe('text-red-600');
    });
  });

  describe('getRecommendedTeam', () => {
    const candidates: TeamMember[] = [
      { id: '3', name: 'Charlie' } as TeamMember,
      { id: '4', name: 'David' } as TeamMember,
      { id: '5', name: 'Eve' } as TeamMember,
    ];

    it('should combine current team with selected candidates up to teamSize', () => {
      const result = getRecommendedTeam(mockTeam, candidates, ['3', '4'], 3);
      expect(result.length).toBe(3);
      expect(result[0].id).toBe('1');
      expect(result[1].id).toBe('2');
      expect(result[2].id).toBe('3');
    });

    it('should handle recommended candidates not in available list', () => {
      const result = getRecommendedTeam(mockTeam, candidates, ['3', '99'], 4);
      expect(result.length).toBe(3);
      expect(result[2].id).toBe('3');
    });
  });

  describe('generateCompatibilityHeatmap', () => {
    it('should generate a square matrix of compatibility scores', () => {
      const result = generateCompatibilityHeatmap(mockTeam);
      expect(result.length).toBe(mockTeam.length);
      expect(result[0].name).toBe('Alice');
      expect(result[0].member0).toBeDefined();
      expect(result[0].member1).toBeDefined();
      expect(typeof result[0].member0).toBe('number');
    });

    it('should calculate different scores for different pairings', () => {
      const result = generateCompatibilityHeatmap(mockTeam);
      // member0 vs member0 (self) should be the same as member1 vs member1 (self) if traits are same
      // but here we just want to see it's calculated
      expect(result[0].member1).toBeGreaterThan(0);
      expect(result[1].member0).toBe(result[0].member1); // Should be symmetric
    });

    it('should return an empty array for an empty team', () => {
      expect(generateCompatibilityHeatmap([])).toEqual([]);
    });
  });

  describe('preparePersonalityRadarData', () => {
    const requirements: TeamRequirement = {
      personalityBalance: {
        Openness: [70, 90],
        Conscientiousness: [60, 80],
      },
    } as any;

    it('should map traits correctly with optimal value being average of range', () => {
      const result = preparePersonalityRadarData(mockTeam, requirements);
      const opennessData = result.find(d => d.trait === 'Openness');
      expect(opennessData?.current).toBe(85); // (80+90)/2
      expect(opennessData?.optimal).toBe(80); // (70+90)/2
    });

    it('should use default values if trait is missing in requirements', () => {
      const result = preparePersonalityRadarData(mockTeam, requirements);
      const neuroticismData = result.find(d => d.trait === 'Neuroticism');
      expect(neuroticismData?.current).toBe(25);
      expect(neuroticismData?.optimal).toBe(0.5);
    });
  });

  describe('prepareSkillCoverageData', () => {
    const requirements: TeamRequirement = {
      skillWeights: {
        React: 0.8,
        TypeScript: 0.6,
        Figma: 0.4,
      },
    } as any;

    const optimizationResult = {
      skillCoverage: {
        React: 0.9,
        TypeScript: 0.7,
      },
    };

    it('should map skill coverage data correctly', () => {
      const result = prepareSkillCoverageData(requirements, optimizationResult);
      expect(result.length).toBe(3);
      const reactData = result.find(d => d.skill === 'React');
      expect(reactData?.coverage).toBe(0.9);
      expect(reactData?.weight).toBe(0.8);
    });

    it('should default coverage to 0 if missing in result', () => {
      const result = prepareSkillCoverageData(requirements, optimizationResult);
      const figmaData = result.find(d => d.skill === 'Figma');
      expect(figmaData?.coverage).toBe(0);
      expect(figmaData?.weight).toBe(0.4);
    });
  });
});
