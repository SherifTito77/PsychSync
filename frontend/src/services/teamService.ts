// frontend/src/services/teamService.ts
import api from './api';
import logger from '@/utils/logger';
export interface Team {
  id: string; // Changed from number to string (UUID)
  name: string;
  description?: string;
  is_active: boolean;
  created_by_id: string; // Changed from number to string (UUID)
  created_at: string;
  updated_at: string;
}
export interface TeamMember {
  id: string; // Changed from number to string (UUID)
  team_id: string; // Changed from number to string (UUID)
  user_id: string; // Changed from number to string (UUID)
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
  user: {
    id: string; // Changed from number to string (UUID)
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
  user_id: string; // Changed from number to string (UUID)
  role?: 'owner' | 'admin' | 'member';
}
export interface UpdateMemberRequest {
  role: 'owner' | 'admin' | 'member';
}
export const teamService = {
  // Team CRUD
  async createTeam(data: CreateTeamRequest): Promise<Team> {
    logger.logApiCall('/teams', 'POST', {
      name: data.name,
    });

    try {
      const response = await api.post<Team>('/teams', data);

      logger.info('Team created successfully', {
        team_id: response.data.id,
        name: response.data.name,
      });

      return response.data;
    } catch (error: any) {
      logger.logApiError('/teams', 'POST', error, {
        name: data.name,
      });

      throw error;
    }
  },
  async getTeams(myTeams: boolean = false): Promise<Team[]> {
    logger.logApiCall('/teams', 'GET', {
      my_teams: myTeams,
    });

    try {
      const response = await api.get<{ teams: Team[]; total: number }>('/teams', {
        params: { my_teams: myTeams },
      });

      logger.info('Teams retrieved successfully', {
        count: response.data.teams.length,
        total: response.data.total,
        myTeams,
      });

      return response.data.teams;
    } catch (error: any) {
      logger.logApiError('/teams', 'GET', error, {
        myTeams,
      });

      throw error;
    }
  },
  async getTeam(teamId: string): Promise<TeamWithMembers> {  // Changed number to string (UUID)
    const response = await api.get<TeamWithMembers>(`/teams/${teamId}`);
    return response.data;
  },
  async updateTeam(teamId: string, data: UpdateTeamRequest): Promise<Team> {  // Changed number to string (UUID)
    const response = await api.put<Team>(`/teams/${teamId}`, data);
    return response.data;
  },
  async deleteTeam(teamId: string): Promise<void> {  // Changed number to string (UUID)
    await api.delete(`/teams/${teamId}`);
  },
  // Member Management
  async addMember(teamId: string, data: AddMemberRequest): Promise<TeamMember> {  // Changed number to string (UUID)
    const response = await api.post<TeamMember>(`/teams/${teamId}/members`, data);
    return response.data;
  },
  async getMembers(teamId: string): Promise<TeamMember[]> {  // Changed number to string (UUID)
    const response = await api.get<TeamMember[]>(`/teams/${teamId}/members`);
    return response.data;
  },
  async updateMemberRole(
    teamId: string,  // Changed number to string (UUID)
    userId: string,  // Changed number to string (UUID)
    data: UpdateMemberRequest
  ): Promise<TeamMember> {
    const response = await api.patch<TeamMember>(
      `/teams/${teamId}/members/${userId}`,
      data
    );
    return response.data;
  },
  async removeMember(teamId: string, userId: string): Promise<void> {  // Changed both to string (UUID)
    await api.delete(`/teams/${teamId}/members/${userId}`);
  },
  async leaveTeam(teamId: string): Promise<void> {  // Changed number to string (UUID)
    await api.post(`/teams/${teamId}/leave`);
  },
};
