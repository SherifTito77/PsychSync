/**
 * Succession Planning Hook
 *
 * Manages succession planning data and state
 */

import { useState } from 'react';
import { PipelineAnalysis, SuccessionCandidate, SuccessionScenario } from '../types';

export const useSuccessionPlanning = () => {
  const [activeTab, setActiveTab] = useState('pipeline');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [selectedRole, setSelectedRole] = useState('all');
  const [timeHorizon, setTimeHorizon] = useState('24');

  // Mock data - would come from API
  const [pipelineAnalysis, setPipelineAnalysis] = useState<PipelineAnalysis[]>([
    {
      pipeline_level: 'Executive',
      total_positions: 5,
      ready_candidates: 2,
      gap_percentage: 60,
      bench_strength: 40,
      risk_level: 'HIGH',
      development_recommendations: [
        'Accelerated leadership program',
        'Executive coaching initiatives',
        'Cross-functional exposure'
      ]
    },
    {
      pipeline_level: 'Senior Management',
      total_positions: 12,
      ready_candidates: 7,
      gap_percentage: 42,
      bench_strength: 58,
      risk_level: 'MEDIUM',
      development_recommendations: [
        'Strategic thinking workshops',
        'Mentorship programs',
        'External training initiatives'
      ]
    },
    {
      pipeline_level: 'Middle Management',
      total_positions: 28,
      ready_candidates: 22,
      gap_percentage: 21,
      bench_strength: 79,
      risk_level: 'LOW',
      development_recommendations: [
        'Leadership fundamentals training',
        'Team development programs',
        'Performance management skills'
      ]
    },
    {
      pipeline_level: 'Team Lead',
      total_positions: 45,
      ready_candidates: 38,
      gap_percentage: 16,
      bench_strength: 84,
      risk_level: 'LOW',
      development_recommendations: [
        'First-time manager training',
        'Communication skills development',
        'Project management certification'
      ]
    }
  ]);

  const [successionCandidates, setSuccessionCandidates] = useState<SuccessionCandidate[]>([
    {
      candidate: {
        user_id: 'user_001',
        current_role: 'Senior Engineering Manager',
        readiness_level: 'READY_1_2_YEARS',
        readiness_score: 85,
        leadership_potential: 0.92,
        mobility_score: 0.9,
        risk_score: 15,
        promotion_timeline: 18,
        retention_risk: 20
      },
      target_role: {
        role_name: 'Director of Engineering',
        level: 'Senior Management',
        department: 'Technology'
      },
      match_score: 88,
      success_probability: 0.85,
      gap_analysis: {
        strategic_thinking: 15,
        financial_acumen: 25,
        stakeholder_management: 10
      }
    },
    {
      candidate: {
        user_id: 'user_002',
        current_role: 'Director of Product',
        readiness_level: 'READY_NOW',
        readiness_score: 95,
        leadership_potential: 0.96,
        mobility_score: 0.8,
        risk_score: 8,
        promotion_timeline: 0,
        retention_risk: 15
      },
      target_role: {
        role_name: 'VP of Product',
        level: 'Executive',
        department: 'Product'
      },
      match_score: 94,
      success_probability: 0.92,
      gap_analysis: {
        board_relations: 12,
        investor_relations: 18
      }
    },
    {
      candidate: {
        user_id: 'user_003',
        current_role: 'Senior Manager',
        readiness_level: 'READY_3_5_YEARS',
        readiness_score: 72,
        leadership_potential: 0.85,
        mobility_score: 0.95,
        risk_score: 28,
        promotion_timeline: 36,
        retention_risk: 35
      },
      target_role: {
        role_name: 'Director of Operations',
        level: 'Senior Management',
        department: 'Operations'
      },
      match_score: 76,
      success_probability: 0.68,
      gap_analysis: {
        strategic_thinking: 22,
        change_management: 18,
        financial_acumen: 30
      }
    }
  ]);

  const [scenarios, setScenarios] = useState<SuccessionScenario[]>([
    {
      scenario_name: 'CEO Transition',
      timeline_months: 12,
      readiness_status: 'AT_RISK',
      business_impact: {
        continuity_risk: 75,
        market_confidence: -15,
        team_stability: -20
      },
      financial_risk: 0.65,
      operational_risk: 0.72,
      required_actions: [
        'Accelerate successor development',
        'Implement interim leadership plan',
        'Enhance board communication'
      ]
    }
  ]);

  return {
    activeTab,
    setActiveTab,
    selectedLevel,
    setSelectedLevel,
    selectedRole,
    setSelectedRole,
    timeHorizon,
    setTimeHorizon,
    pipelineAnalysis,
    successionCandidates,
    scenarios,
  };
};
