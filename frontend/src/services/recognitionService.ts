import api from '../api/axios';

export interface Recognition {
  id: string;
  type: string;
  message: string | null;
  created_at: string;
}

export interface RecognitionStats {
  total_recognitions: number;
  unique_givers: number;
  unique_receivers: number;
  type_breakdown: Record<string, number>;
  period_days: number;
}

export interface GiveRecognitionPayload {
  recipient_id: string;
  recognition_type: string;
  message?: string;
  team_id?: string;
  is_public?: boolean;
}

export async function giveRecognition(payload: GiveRecognitionPayload) {
  const { data } = await api.post('/api/v1/recognition', payload);
  return data;
}

export async function getReceivedRecognitions(days = 90) {
  const { data } = await api.get<{ count: number; recognitions: Recognition[] }>(
    '/api/v1/recognition/received',
    { params: { days } },
  );
  return data;
}

export async function getTeamFeed(teamId: string, days = 30) {
  const { data } = await api.get<{ team_id: string; count: number; feed: Recognition[] }>(
    `/api/v1/recognition/team/${teamId}/feed`,
    { params: { days } },
  );
  return data;
}

export async function getRecognitionStats(organizationId: string, days = 90) {
  const { data } = await api.get<RecognitionStats>(
    `/api/v1/recognition/stats/${organizationId}`,
    { params: { days } },
  );
  return data;
}
