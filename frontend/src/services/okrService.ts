import api from '../api/axios';

export interface OKRObjective {
  id: string;
  title: string;
  progress: number;
  status: string;
  key_results_count: number;
}

export interface OKRSummary {
  period: string;
  year: number;
  team: string | null;
  overall_health: 'green' | 'yellow' | 'red';
  objectives: {
    total: number;
    completed: number;
    completion_rate: number;
  };
  key_results: {
    total: number;
    achieved: number;
    on_track: number;
    at_risk: number;
    off_track: number;
    achievement_rate: number;
  };
  objectives_list: OKRObjective[];
}

export interface CreateObjectivePayload {
  title: string;
  objective_type: string;
  period: string;
  year: number;
  start_date: string;
  end_date: string;
  organization_id?: string;
  team?: string;
  description?: string;
  strategic_priority?: string;
}

export interface CreateKeyResultPayload {
  objective_id: string;
  title: string;
  target_value: number;
  unit_of_measure: string;
  start_date: string;
  end_date: string;
  baseline_value?: number;
  description?: string;
  weight?: number;
}

export interface UpdateKRProgressPayload {
  current_value: number;
  notes?: string;
  blockers?: string;
  next_steps?: string;
  confidence_level?: 'high' | 'medium' | 'low';
  sentiment?: 'positive' | 'neutral' | 'negative';
}

export async function getOKRSummary(
  period: string,
  year: number,
  organizationId?: string,
  team?: string,
): Promise<OKRSummary> {
  const params: Record<string, string | number> = { period, year };
  if (organizationId) params.organization_id = organizationId;
  if (team) params.team = team;
  const { data } = await api.get<OKRSummary>('/api/v1/okr/summary', { params });
  return data;
}

export async function createObjective(payload: CreateObjectivePayload) {
  const { data } = await api.post('/api/v1/okr/objectives', payload);
  return data;
}

export async function createKeyResult(payload: CreateKeyResultPayload) {
  const { data } = await api.post('/api/v1/okr/key-results', payload);
  return data;
}

export async function updateKRProgress(krId: string, payload: UpdateKRProgressPayload) {
  const { data } = await api.patch(`/api/v1/okr/key-results/${krId}/progress`, payload);
  return data;
}
