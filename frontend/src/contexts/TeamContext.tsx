// // ===== TEAM CONTEXT FILE =====
// // src/contexts/TeamContext.tsx
// src/contexts/TeamContext.tsx - Team Management Context
import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode, useRef } from 'react';
import { Team, ApiResponse } from '../types';
import { useNotification } from './NotificationContext';
interface TeamContextType {
  teams: Team[];
  currentTeam: Team | null;
  loading: boolean;
  fetchTeams: () => Promise<void>;
  createTeam: (teamData: Omit<Team, 'id'>) => Promise<ApiResponse<Team>>;
  updateTeam: (teamId: number, updateData: Partial<Team>) => Promise<ApiResponse<Team>>;
  deleteTeam: (teamId: number) => Promise<ApiResponse>;
  selectTeam: (team: Team) => void;
}
const TeamContext = createContext<TeamContextType | undefined>(undefined);
export const useTeam = (): TeamContextType => {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error('useTeam must be used within a TeamProvider');
  }
  return context;
};
interface TeamProviderProps {
  children: ReactNode;
}
export const TeamProvider: React.FC<TeamProviderProps> = ({ children }) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // ✅ Store previous state for optimistic update rollback
  const previousTeamsRef = useRef<Team[]>([]);
  const previousCurrentTeamRef = useRef<Team | null>(null);
  const { showNotification } = useNotification();

  // ✅ MEMOIZED: Functions with useCallback
  const fetchTeams = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockTeams: Team[] = [
        { id: 1, name: 'Frontend Team', status: 'active', description: 'Web development team' },
        { id: 2, name: 'Backend Team', status: 'active', description: 'API development team' },
        { id: 3, name: 'QA Team', status: 'inactive', description: 'Quality assurance team' },
      ];
      setTeams(mockTeams);
    } catch (error) {
      showNotification('Failed to fetch teams', 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  const createTeam = useCallback(async (teamData: Omit<Team, 'id'>): Promise<ApiResponse<Team>> => {
    try {
      const newTeam: Team = { id: Date.now(), ...teamData, status: 'active' };
      setTeams((prev) => [...prev, newTeam]);
      showNotification('Team created successfully', 'success');
      return { success: true, data: newTeam };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  }, [showNotification]);

  // ✅ FIXED: Use functional updates to avoid stale closure for currentTeam
  // ✅ FIXED: Added optimistic update rollback on API failure
  const updateTeam = useCallback(async (teamId: number, updateData: Partial<Team>): Promise<ApiResponse<Team>> => {
    // Store previous state for rollback
    previousTeamsRef.current = teams;
    previousCurrentTeamRef.current = currentTeam;

    try {
      const updatedTeam: Team = { ...updateData, id: teamId } as Team;

      // ✅ Optimistic update with functional state
      setTeams((prev) => {
        // Store previous state before updating
        previousTeamsRef.current = prev;
        return prev.map((team) =>
          team.id === teamId ? { ...team, ...updatedTeam } : team
        );
      });

      // ✅ Use functional update for currentTeam too
      setCurrentTeam((prevCurrentTeam) => {
        // Store previous state before updating
        if (prevCurrentTeam?.id === teamId) {
          previousCurrentTeamRef.current = prevCurrentTeam;
        }
        // ✅ Check fresh state instead of closure-captured value
        if (prevCurrentTeam && prevCurrentTeam.id === teamId) {
          return { ...prevCurrentTeam, ...updatedTeam };
        }
        return prevCurrentTeam;
      });

      // ✅ TODO(human): Make actual API call here to persist the update
      // For now, we'll simulate a successful update
      // const response = await api.patch(`/teams/${teamId}`, updateData);
      // if (!response.ok) throw new Error('Failed to update team');

      showNotification('Team updated successfully', 'success');
      return { success: true, data: updatedTeam };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update team';

      // ✅ Rollback optimistic update on error
      setTeams(previousTeamsRef.current);
      setCurrentTeam(previousCurrentTeamRef.current);

      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  }, [teams, currentTeam, showNotification]); // ✅ Remove currentTeam from deps

  // ✅ FIXED: Use functional update to avoid stale closure for currentTeam
  const deleteTeam = useCallback(async (teamId: number): Promise<ApiResponse> => {
    try {
      setTeams((prev) => prev.filter((team) => team.id !== teamId));

      // ✅ Use functional update to avoid stale closure
      setCurrentTeam((prevCurrentTeam) => {
        if (prevCurrentTeam && prevCurrentTeam.id === teamId) {
          return null;
        }
        return prevCurrentTeam;
      });

      showNotification('Team deleted successfully', 'success');
      return { success: true };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  }, [showNotification]); // ✅ Remove currentTeam from deps

  const selectTeam = useCallback((team: Team): void => {
    setCurrentTeam(team);
  }, []);

  // ✅ MEMOIZED: Context value only changes when dependencies change
  const value: TeamContextType = useMemo(() => ({
    teams,
    currentTeam,
    loading,
    fetchTeams,
    createTeam,
    updateTeam,
    deleteTeam,
    selectTeam,
  }), [teams, currentTeam, loading, fetchTeams, createTeam, updateTeam, deleteTeam, selectTeam]);

  return <TeamContext.Provider value={value}>{children}</TeamContext.Provider>;
};
