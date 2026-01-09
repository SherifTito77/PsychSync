/**
 * Authentication Query Hooks
 *
 * Custom React Query hooks for authentication-related API calls.
 * These hooks work alongside AuthContext for efficient user data fetching.
 *
 * Migration Strategy:
 * 1. Keep AuthContext for auth state (login/logout actions)
 * 2. Use React Query for user data fetching (currentUser, profile)
 * 3. This reduces Context size and improves performance
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, ApiResponse } from '../types';
import { queryKeys } from '../lib/queryClient';

// Import actual auth service
import { login as authServiceLogin, register as authServiceRegister, getCurrentUser as authServiceGetCurrentUser, logout as authServiceLogout } from '../services/authService';

// Type imports from authService
type LoginCredentials = import('../services/authService').LoginCredentials;
type RegisterData = import('../services/authService').RegisterData;

/**
 * Fetch current user
 *
 * This hook replaces fetching user data in AuthContext.
 * Returns null if not authenticated (not an error).
 *
 * @returns Query result with user data or null
 *
 * Example:
 * ```typescript
 * function ProfileHeader() {
 *   const { data: user, isLoading, error } = useCurrentUser();
 *
 *   if (isLoading) return <Skeleton />;
 *   if (!user) return <LoginPrompt />;
 *
 *   return <div>Welcome, {user.full_name}</div>;
 * }
 * ```
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.auth.currentUser(),

    // Connected to actual authService
    queryFn: async (): Promise<User | null> => {
      try {
        return await authServiceGetCurrentUser();
      } catch (error) {
        // If 401, user is not authenticated (return null, not error)
        return null;
      }
    },

    // Don't retry auth failures (401s)
    retry: false,

    // Consider data stale after 5 minutes (will refetch in background)
    staleTime: 5 * 60 * 1000,

    // Keep in cache for 10 minutes after user logs out
    gcTime: 10 * 60 * 1000,

    // Refetch on window focus (to check if session is still valid)
    refetchOnWindowFocus: true,
  });
}

/**
 * Fetch user profile
 *
 * Fetches detailed profile information for the current user.
 *
 * @returns Query result with profile data
 *
 * Example:
 * ```typescript
 * function ProfilePage() {
 *   const { data: profile, isLoading } = useUserProfile();
 *
 *   if (isLoading) return <LoadingSpinner />;
 *
 *   return <ProfileDisplay profile={profile} />;
 * }
 * ```
 */
export function useUserProfile() {
  return useQuery({
    queryKey: queryKeys.users.profile(),

    // Only run if user is authenticated
    enabled: !!localStorage.getItem('user'),

    // Connected to actual authService
    queryFn: async (): Promise<User> => {
      return await authServiceGetCurrentUser();
    },

    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Login mutation
 *
 * Performs login and invalidates current user query to trigger refetch.
 *
 * @returns Mutation function for login
 *
 * Example:
 * ```typescript
 * function LoginForm() {
 *   const loginMutation = useLogin();
 *
 *   const handleSubmit = async (credentials) => {
 *     const result = await loginMutation.mutateAsync(credentials);
 *     if (result.error) {
 *       showToast(result.error, 'error');
 *     } else {
 *       showToast('Welcome back!', 'success');
 *     }
 *   };
 *
 *   return <form onSubmit={handleSubmit}>...</form>;
 * }
 * ```
 */
export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginCredentials): Promise<ApiResponse<{ user: User }>> => {
      // Connected to actual authService
      const result = await authServiceLogin(credentials);
      return { success: true, data: result };
    },

    // On successful login, refetch current user
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.auth.currentUser(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.profile(),
      });
    },

    // Clear all queries on login (fresh start)
    onSettled: () => {
      queryClient.clear();
    },

    onError: (error: Error) => {
      return {
        success: false,
        error: error.message,
      };
    },
  });
}

/**
 * Register mutation
 *
 * Performs user registration.
 *
 * @returns Mutation function for registration
 *
 * Example:
 * ```typescript
 * function RegisterForm() {
 *   const registerMutation = useRegister();
 *
 *   const handleSubmit = async (userData) => {
 *     const result = await registerMutation.mutateAsync(userData);
 *     if (result.error) {
 *       showToast(result.error, 'error');
 *     } else {
 *       showToast('Account created!', 'success');
 *       router.push('/login');
 *     }
 *   };
 *
 *   return <form onSubmit={handleSubmit}>...</form>;
 * }
 * ```
 */
export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userData: RegisterData): Promise<ApiResponse> => {
      // Connected to actual authService
      await authServiceRegister(userData);
      return { success: true };
    },

    onError: (error: Error) => {
      return {
        success: false,
        error: error.message,
      };
    },
  });
}

/**
 * Logout mutation
 *
 * Performs logout and clears all cached data.
 *
 * @returns Mutation function for logout
 *
 * Example:
 * ```typescript
 * function LogoutButton() {
 *   const logoutMutation = useLogout();
 *
 *   const handleLogout = async () => {
 *     await logoutMutation.mutateAsync();
 *     router.push('/login');
 *   };
 *
 *   return <button onClick={handleLogout}>Logout</button>;
 * }
 * ```
 */
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<void> => {
      // Connected to actual authService
      await authServiceLogout();
    },

    // On logout, clear all queries from cache
    onSuccess: () => {
      queryClient.clear();
    },

    // Invalidate auth queries to trigger refetch (will return null)
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.auth.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.all,
      });
    },
  });
}

/**
 * Update user profile mutation
 *
 * Updates user profile information.
 *
 * @returns Mutation function for profile updates
 *
 * Example:
 * ```typescript
 * function ProfileEditor() {
 *   const updateProfileMutation = useUpdateProfile();
 *   const { data: user } = useCurrentUser();
 *
 *   const handleSave = async (updates) => {
 *     await updateProfileMutation.mutateAsync(updates);
 *   };
 *
 *   return <form onSubmit={handleSave}>...</form>;
 * }
 * ```
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    // TODO(human): Replace with actual API call
    mutationFn: async (
      updates: Partial<User>
    ): Promise<ApiResponse<User>> => {
      // Placeholder implementation
      // Replace this with: return authService.updateProfile(updates);

      try {
        await new Promise((resolve) => setTimeout(resolve, 500));

        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const updatedUser = { ...currentUser, ...updates };

        localStorage.setItem('user', JSON.stringify(updatedUser));

        return { success: true, data: updatedUser };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Update failed',
        };
      }
    },

    // Optimistic update
    onMutate: async (updates) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.auth.currentUser(),
      });

      const previousUser = queryClient.getQueryData<User>(
        queryKeys.auth.currentUser()
      );

      // Optimistically update user data
      queryClient.setQueryData<User>(
        queryKeys.auth.currentUser(),
        (old = {} as User) => ({ ...old, ...updates })
      );

      return { previousUser };
    },

    // Rollback on error
    onError: (error, variables, context) => {
      if (context?.previousUser) {
        queryClient.setQueryData(
          queryKeys.auth.currentUser(),
          context.previousUser
        );
      }
    },

    // Refetch to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.auth.currentUser(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.profile(),
      });
    },
  });
}

/**
 * Change password mutation
 *
 * Updates user password.
 *
 * @returns Mutation function for password changes
 */
export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation({
    // TODO(human): Replace with actual API call
    mutationFn: async (passwords: {
      currentPassword: string;
      newPassword: string;
    }): Promise<ApiResponse> => {
      // Placeholder implementation
      // Replace this with: return authService.changePassword(passwords);

      try {
        await new Promise((resolve) => setTimeout(resolve, 500));
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Password change failed',
        };
      }
    },

    // Don't refetch user on password change
  });
}

/**
 * Request password reset mutation
 *
 * Sends password reset email.
 *
 * @returns Mutation function for password reset requests
 */
export function useRequestPasswordReset() {
  return useMutation({
    // TODO(human): Replace with actual API call
    mutationFn: async (email: string): Promise<ApiResponse> => {
      // Placeholder implementation
      // Replace this with: return authService.requestPasswordReset(email);

      try {
        await new Promise((resolve) => setTimeout(resolve, 500));
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error:
            error instanceof Error ? error.message : 'Reset request failed',
        };
      }
    },
  });
}

/**
 * Reset password mutation
 *
 * Resets password with token from email.
 *
 * @returns Mutation function for password reset
 */
export function useResetPassword() {
  return useMutation({
    // TODO(human): Replace with actual API call
    mutationFn: async (data: {
      token: string;
      newPassword: string;
    }): Promise<ApiResponse> => {
      // Placeholder implementation
      // Replace this with: return authService.resetPassword(data);

      try {
        await new Promise((resolve) => setTimeout(resolve, 500));
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Password reset failed',
        };
      }
    },

    // On successful reset, clear auth queries
    onSuccess: () => {
      // User will need to login with new password
    },
  });
}
