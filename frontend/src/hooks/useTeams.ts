/**
 * Team Query Hooks
 *
 * Custom React Query hooks for team-related API calls.
 * These hooks handle caching, background refetching, error handling, and loading states.
 *
 * Usage:
 * ```typescript
 * function TeamList() {
 *   const { data: teams, isLoading, error } = useTeams();
 *
 *   if (isLoading) return <LoadingSpinner />;
 *   if (error) return <ErrorDisplay error={error} />;
 *
 *   return <ul>{teams?.map(team => <li key={team.id}>{team.name}</li>)}</ul>;
 * }
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryClient';
import { teamService } from '../services/teamService';

// Types from teamService
type Team = import('../services/teamService').Team;
type TeamMember = import('../services/teamService').TeamMember;
type CreateTeamRequest = import('../services/teamService').CreateTeamRequest;
type UpdateTeamRequest = import('../services/teamService').UpdateTeamRequest;

/**
 * Fetch all teams
 *
 * @returns Query result with teams array
 *
 * Example:
 * ```typescript
 * const { data: teams, isLoading, error } = useTeams();
 * ```
 */
export function useTeams(myTeams: boolean = false) {
  return useQuery({
    queryKey: queryKeys.teams.lists(),
    queryFn: async (): Promise<Team[]> => {
      // Connected to actual teamService
      return teamService.getTeams(myTeams);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetch a single team by ID
 *
 * @param teamId - The team ID to fetch
 * @returns Query result with team data
 *
 * Example:
 * ```typescript
 * const { data: team, isLoading, error } = useTeam(123);
 * ```
 */
export function useTeam(teamId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.teams.detail(teamId || 0),
    enabled: !!teamId,
    queryFn: async (): Promise<Team> => {
      if (!teamId) throw new Error('Team ID is required');
      // Connected to actual teamService
      return teamService.getTeam(teamId);
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Fetch team members
 *
 * @param teamId - The team ID to fetch members for
 * @returns Query result with members array
 *
 * Example:
 * ```typescript
 * const { data: members, isLoading, error } = useTeamMembers(123);
 * ```
 */
export function useTeamMembers(teamId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.teams.members(teamId || 0),
    enabled: !!teamId,
    queryFn: async (): Promise<TeamMember[]> => {
      if (!teamId) throw new Error('Team ID is required');
      // Connected to actual teamService
      return teamService.getMembers(teamId);
    },
    staleTime: 2 * 60 * 1000, // 2 minutes (members change more frequently)
  });
}

/**
 * Create a new team
 *
 * @returns Mutation function for creating teams
 *
 * Example:
 * ```typescript
 * const createTeamMutation = useCreateTeam();
 *
 * const handleCreate = async (teamData) => {
 *   const result = await createTeamMutation.mutateAsync(teamData);
 *   if (result.error) {
 *     // Handle error
 *   } else {
 *     // Success - teams list is automatically refetched
 *   }
 * };
 * ```
 */
export function useCreateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (teamData: CreateTeamRequest): Promise<Team> => {
      // Connected to actual teamService
      return teamService.createTeam(teamData);
    },

    // On success, invalidate and refetch teams list
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.teams.lists(),
      });
    },

    onError: (error) => {
      console.error('Failed to create team:', error);
    },
  });
}

/**
 * Update an existing team
 *
 * @returns Mutation function for updating teams
 *
 * Example:
 * ```typescript
 * const updateTeamMutation = useUpdateTeam();
 *
 * const handleUpdate = async (teamId, updates) => {
 *   await updateTeamMutation.mutateAsync({ teamId, updates });
 * };
 * ```
 */
export function useUpdateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      teamId,
      data,
    }: {
      teamId: number;
      data: UpdateTeamRequest;
    }): Promise<Team> => {
      // Connected to actual teamService
      return teamService.updateTeam(teamId, data);
    },

    // Optimistic update - update UI immediately, rollback on error
    onMutate: async ({ teamId, data }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.teams.lists() });

      const previousTeams = queryClient.getQueryData<Team[]>(queryKeys.teams.lists());

      // Optimistically update the cache
      queryClient.setQueryData<Team[]>(
        queryKeys.teams.lists(),
        (old = []) =>
          old.map((team) =>
            team.id === teamId ? { ...team, ...data } : team
          )
      );

      return { previousTeams };
    },

    // Rollback on error
    onError: (error, variables, context) => {
      if (context?.previousTeams) {
        queryClient.setQueryData(
          queryKeys.teams.lists(),
          context.previousTeams
        );
      }
      console.error('Failed to update team:', error);
    },

    // Refetch to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.teams.lists(),
      });
    },
  });
}

/**
 * Delete a team
 *
 * @returns Mutation function for deleting teams
 *
 * Example:
 * ```typescript
 * const deleteTeamMutation = useDeleteTeam();
 *
 * const handleDelete = async (teamId) => {
 *   await deleteTeamMutation.mutateAsync(teamId);
 * };
 * ```
 */
export function useDeleteTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (teamId: number): Promise<void> => {
      // Connected to actual teamService
      return teamService.deleteTeam(teamId);
    },

    // Optimistic update - remove from cache immediately
    onMutate: async (teamId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.teams.lists() });

      const previousTeams = queryClient.getQueryData<Team[]>(queryKeys.teams.lists());

      // Optimistically remove the team from cache
      queryClient.setQueryData<Team[]>(
        queryKeys.teams.lists(),
        (old = []) => old.filter((team) => team.id !== teamId)
      );

      return { previousTeams };
    },

    // Rollback on error
    onError: (error, variables, context) => {
      if (context?.previousTeams) {
        queryClient.setQueryData(
          queryKeys.teams.lists(),
          context.previousTeams
        );
      }
      console.error('Failed to delete team:', error);
    },

    // Refetch to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.teams.lists(),
      });
    },
  });
}

/**
 * Select a team (for team switching)
 *
 * @returns Mutation function for selecting current team
 */
export function useSelectTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (team: Team): Promise<void> => {
      // Store selected team in localStorage
      localStorage.setItem('selectedTeamId', team.id.toString());
      return;
    },

    onSuccess: () => {
      // Refetch queries that depend on selected team
      queryClient.invalidateQueries({
        queryKey: queryKeys.teams.members,
      });
    },
  });
}
