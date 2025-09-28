
// ===== TEAM CONTEXT FILE =====
// src/contexts/TeamContext.tsx
import React, { createContext, useContext, useState } from 'react';
import { TeamContextType } from '../types/contexts';
import { Team, ApiResponse } from '../types';
import { useNotification } from './NotificationContext';

const TeamContext = createContext<TeamContextType | undefined>(undefined);

export const useTeam = (): TeamContextType => {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error('useTeam must be used within a TeamProvider');
  }
  return context;
};

export const TeamProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { showNotification } = useNotification();

  const fetchTeams = async (): Promise<void> => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockTeams: Team[] = [
        { id: 1, name: 'Frontend Team', status: 'active', description: 'Web development team' },
        { id: 2, name: 'Backend Team', status: 'active', description: 'API development team' },
        { id: 3, name: 'QA Team', status: 'inactive', description: 'Quality assurance team' }
      ];
      setTeams(mockTeams);
    } catch (error) {
      showNotification('Failed to fetch teams', 'error');
    } finally {
      setLoading(false);
    }
  };

  const createTeam = async (teamData: Omit<Team, 'id'>): Promise<ApiResponse<Team>> => {
    try {
      const newTeam: Team = {
        id: Date.now(),
        ...teamData,
        status: 'active'
      };
      setTeams(prev => [...prev, newTeam]);
      showNotification('Team created successfully', 'success');
      return { success: true, data: newTeam };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  };

  const updateTeam = async (teamId: number, updateData: Partial<Team>): Promise<ApiResponse<Team>> => {
    try {
      const updatedTeam: Team = { ...updateData, id: teamId } as Team;
      setTeams(prev => prev.map(team =>
        team.id === teamId ? { ...team, ...updatedTeam } : team
      ));
      if (currentTeam && currentTeam.id === teamId) {
        setCurrentTeam({ ...currentTeam, ...updatedTeam });
      }
      showNotification('Team updated successfully', 'success');
      return { success: true, data: updatedTeam };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  };

  const deleteTeam = async (teamId: number): Promise<ApiResponse> => {
    try {
      setTeams(prev => prev.filter(team => team.id !== teamId));
      if (currentTeam && currentTeam.id === teamId) {
        setCurrentTeam(null);
      }
      showNotification('Team deleted successfully', 'success');
      return { success: true };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  };

  const selectTeam = (team: Team): void => {
    setCurrentTeam(team);
  };

  const value: TeamContextType = {
    teams,
    currentTeam,
    loading,
    fetchTeams,
    createTeam,
    updateTeam,
    deleteTeam,
    selectTeam
  };

  return (
    <TeamContext.Provider value={value}>
      {children}
    </TeamContext.Provider>
  );
};
