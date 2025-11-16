// frontend/src/services/teamService.ts
import api from './api';
export interface Team {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}
export interface TeamMember {
  id: number;
  team_id: number;
  user_id: number;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
  user: {
    id: number;
    email: string;
    full_name: string;
  };
}
export interface TeamWithMembers extends Team {
  members: TeamMember[];
  member_count: number;
}
export interface CreateTeamRequest {
  name: string;
  description?: string;
}
export interface UpdateTeamRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}
export interface AddMemberRequest {
  user_id: number;
  role?: 'owner' | 'admin' | 'member';
}
export interface UpdateMemberRequest {
  role: 'owner' | 'admin' | 'member';
}
export const teamService = {
  // Team CRUD
  async createTeam(data: CreateTeamRequest): Promise<Team> {
    const response = await api.post<Team>('/teams', data);
    return response.data;
  },
  async getTeams(myTeams: boolean = false): Promise<Team[]> {
    const response = await api.get<{ teams: Team[]; total: number }>('/teams', {
      params: { my_teams: myTeams },
    });
    return response.data.teams;
  },
  async getTeam(teamId: number): Promise<TeamWithMembers> {
    const response = await api.get<TeamWithMembers>(`/teams/${teamId}`);
    return response.data;
  },
  async updateTeam(teamId: number, data: UpdateTeamRequest): Promise<Team> {
    const response = await api.put<Team>(`/teams/${teamId}`, data);
    return response.data;
  },
  async deleteTeam(teamId: number): Promise<void> {
    await api.delete(`/teams/${teamId}`);
  },
  // Member Management
  async addMember(teamId: number, data: AddMemberRequest): Promise<TeamMember> {
    const response = await api.post<TeamMember>(`/teams/${teamId}/members`, data);
    return response.data;
  },
  async getMembers(teamId: number): Promise<TeamMember[]> {
    const response = await api.get<TeamMember[]>(`/teams/${teamId}/members`);
    return response.data;
  },
  async updateMemberRole(
    teamId: number,
    userId: number,
    data: UpdateMemberRequest
  ): Promise<TeamMember> {
    const response = await api.patch<TeamMember>(
      `/teams/${teamId}/members/${userId}`,
      data
    );
    return response.data;
  },
  async removeMember(teamId: number, userId: number): Promise<void> {
    await api.delete(`/teams/${teamId}/members/${userId}`);
  },
  async leaveTeam(teamId: number): Promise<void> {
    await api.post(`/teams/${teamId}/leave`);
  },
};
