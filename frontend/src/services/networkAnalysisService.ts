// frontend/src/services/networkAnalysisService.ts
import axios from '../api/axios';

export interface CollaborationNomination {
  nominee_id: string;
  network_type: 'advice' | 'trust' | 'energy' | 'collaboration';
  strength: number;
}

export interface CollaborationSurveySubmit {
  nominations: CollaborationNomination[];
  survey_round?: string;
}

export interface TemporalSnapshot {
  date: string;
  total_nodes: number;
  total_edges: number;
  density: number;
  avg_degree_centrality: number;
  num_communities: number | null;
  num_isolates: number | null;
  num_influencers: number | null;
  num_bridges: number | null;
}

export interface PersonalityNetworkInsight {
  type: string;
  user_id: string;
  name: string;
  message: string;
}

export interface CommunityProfile {
  community_id: number;
  size: number;
  avg_personality: Record<string, number>;
  dominant_trait: string;
}

export interface SurveyNetworkResponse {
  network_type: string;
  survey_round: string | null;
  total_respondents: number;
  total_nominees: number;
  edges: Array<{ source: string; target: string; strength: number; network_type: string }>;
  top_nominated: Array<{ user_id: string; name: string; nominations: number }>;
}

const BASE = '/api/v1/organizational-network';

export const networkAnalysisService = {
  analyzeNetwork: (orgId: string, lookbackDays = 60) =>
    axios.get(`${BASE}/analyze/${orgId}`, { params: { lookback_days: lookbackDays } }),

  getTemporalEvolution: (orgId: string, days = 90) =>
    axios.get<TemporalSnapshot[]>(`${BASE}/temporal/${orgId}`, { params: { days } }),

  submitCollaborationSurvey: (orgId: string, data: CollaborationSurveySubmit) =>
    axios.post(`${BASE}/survey/${orgId}`, data),

  getSurveyNetwork: (orgId: string, networkType?: string, surveyRound?: string) =>
    axios.get<SurveyNetworkResponse>(`${BASE}/survey/${orgId}/results`, {
      params: { network_type: networkType, survey_round: surveyRound },
    }),

  getPersonalityNetworkInsights: (orgId: string, lookbackDays = 60) =>
    axios.get<{
      insights: PersonalityNetworkInsight[];
      node_personality: any[];
      community_profiles: CommunityProfile[];
    }>(`${BASE}/personality/${orgId}`, { params: { lookback_days: lookbackDays } }),
};
