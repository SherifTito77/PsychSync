/**
 * Mock Data for Team Composition Optimizer
 *
 * Simulated team members and candidates for development/testing
 */

import { TeamMember } from '../types';

export const MOCK_TEAM_MEMBERS: TeamMember[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@company.com',
    role: 'Team Lead',
    department: 'Engineering',
    skills: ['Leadership', 'Communication', 'Technical'],
    skillLevels: { 'Leadership': 0.85, 'Communication': 0.9, 'Technical': 0.8 },
    personalityTraits: {
      'Openness': 0.75,
      'Conscientiousness': 0.85,
      'Extraversion': 0.7,
      'Agreeableness': 0.8,
      'Neuroticism': 0.25
    },
    performanceScore: 0.88,
    collaborationScore: 0.92,
    innovationScore: 0.78,
    leadershipPotential: 0.9,
    adaptabilityScore: 0.85,
    yearsOfExperience: 8,
    availability: true,
  },
  {
    id: '2',
    name: 'Michael Chen',
    email: 'michael.chen@company.com',
    role: 'Senior Developer',
    department: 'Engineering',
    skills: ['Technical', 'Problem Solving', 'Analytics'],
    skillLevels: { 'Technical': 0.9, 'Problem Solving': 0.85, 'Analytics': 0.8 },
    personalityTraits: {
      'Openness': 0.8,
      'Conscientiousness': 0.75,
      'Extraversion': 0.4,
      'Agreeableness': 0.7,
      'Neuroticism': 0.3
    },
    performanceScore: 0.85,
    collaborationScore: 0.75,
    innovationScore: 0.9,
    leadershipPotential: 0.65,
    adaptabilityScore: 0.88,
    yearsOfExperience: 6,
    availability: true,
  },
];

export const MOCK_CANDIDATES: TeamMember[] = [
  {
    id: '3',
    name: 'Emily Rodriguez',
    email: 'emily.rodriguez@company.com',
    role: 'UX Designer',
    department: 'Design',
    skills: ['Design', 'User Research', 'Communication'],
    skillLevels: { 'Design': 0.85, 'User Research': 0.8, 'Communication': 0.75 },
    personalityTraits: {
      'Openness': 0.9,
      'Conscientiousness': 0.7,
      'Extraversion': 0.6,
      'Agreeableness': 0.85,
      'Neuroticism': 0.2
    },
    performanceScore: 0.82,
    collaborationScore: 0.9,
    innovationScore: 0.95,
    leadershipPotential: 0.7,
    adaptabilityScore: 0.92,
    yearsOfExperience: 5,
    availability: true,
  },
  {
    id: '4',
    name: 'David Kim',
    email: 'david.kim@company.com',
    role: 'Data Analyst',
    department: 'Analytics',
    skills: ['Analytics', 'Statistics', 'Communication'],
    skillLevels: { 'Analytics': 0.88, 'Statistics': 0.9, 'Communication': 0.7 },
    personalityTraits: {
      'Openness': 0.6,
      'Conscientiousness': 0.9,
      'Extraversion': 0.3,
      'Agreeableness': 0.8,
      'Neuroticism': 0.15
    },
    performanceScore: 0.87,
    collaborationScore: 0.8,
    innovationScore: 0.65,
    leadershipPotential: 0.6,
    adaptabilityScore: 0.85,
    yearsOfExperience: 4,
    availability: true,
  },
  {
    id: '5',
    name: 'Lisa Wang',
    email: 'lisa.wang@company.com',
    role: 'Project Manager',
    department: 'Operations',
    skills: ['Leadership', 'Planning', 'Communication'],
    skillLevels: { 'Leadership': 0.8, 'Planning': 0.85, 'Communication': 0.88 },
    personalityTraits: {
      'Openness': 0.7,
      'Conscientiousness': 0.95,
      'Extraversion': 0.8,
      'Agreeableness': 0.9,
      'Neuroticism': 0.1
    },
    performanceScore: 0.9,
    collaborationScore: 0.95,
    innovationScore: 0.7,
    leadershipPotential: 0.85,
    adaptabilityScore: 0.88,
    yearsOfExperience: 7,
    availability: true,
  },
  {
    id: '6',
    name: 'James Wilson',
    email: 'james.wilson@company.com',
    role: 'DevOps Engineer',
    department: 'Engineering',
    skills: ['Technical', 'Infrastructure', 'Automation'],
    skillLevels: { 'Technical': 0.85, 'Infrastructure': 0.9, 'Automation': 0.8 },
    personalityTraits: {
      'Openness': 0.65,
      'Conscientiousness': 0.85,
      'Extraversion': 0.5,
      'Agreeableness': 0.6,
      'Neuroticism': 0.2
    },
    performanceScore: 0.83,
    collaborationScore: 0.7,
    innovationScore: 0.75,
    leadershipPotential: 0.55,
    adaptabilityScore: 0.9,
    yearsOfExperience: 5,
    availability: true,
  },
  {
    id: '7',
    name: 'Maria Garcia',
    email: 'maria.garcia@company.com',
    role: 'Business Analyst',
    department: 'Business',
    skills: ['Analysis', 'Requirements', 'Communication'],
    skillLevels: { 'Analysis': 0.88, 'Requirements': 0.82, 'Communication': 0.9 },
    personalityTraits: {
      'Openness': 0.75,
      'Conscientiousness': 0.8,
      'Extraversion': 0.7,
      'Agreeableness': 0.85,
      'Neuroticism': 0.25
    },
    performanceScore: 0.86,
    collaborationScore: 0.92,
    innovationScore: 0.7,
    leadershipPotential: 0.75,
    adaptabilityScore: 0.88,
    yearsOfExperience: 6,
    availability: true,
  },
];

export const DEFAULT_REQUIREMENTS = {
  teamSize: 5,
  requiredSkills: ['Leadership', 'Communication', 'Technical'],
  skillWeights: { 'Leadership': 0.3, 'Communication': 0.2, 'Technical': 0.25 },
  personalityBalance: {
    'Openness': [0.4, 0.8] as [number, number],
    'Conscientiousness': [0.5, 0.9] as [number, number],
    'Extraversion': [0.3, 0.7] as [number, number],
    'Agreeableness': [0.4, 0.8] as [number, number],
    'Neuroticism': [0.1, 0.4] as [number, number]
  },
  objectives: ['Performance', 'Collaboration', 'Innovation'],
  experienceDistribution: { 'Junior': 1, 'Mid': 3, 'Senior': 1 },
  budget: 500000,
  deadline: '2024-06-30',
  projectType: 'Digital Transformation'
};
