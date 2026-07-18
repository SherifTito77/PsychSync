// src/services/authService.ts
// Authentication service aligned with the FastAPI auth router
import apiClient from './api';
import { User, LoginCredentials, RegisterData } from '../types';
import logger from '../utils/logger';

// Define the expected shape of the login response from the backend
interface LoginResponse {
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
  user?: UserResponse;
  message?: string;
  timestamp?: number;
  requires_mfa?: boolean;
  mfa_challenge_token?: string;
}

// Define MFA Challenge response specifically
interface MFAChallenge {
  requires_mfa: true;
  mfa_challenge_token: string;
  message: string;
  user: UserResponse;
}

// Define the expected shape of the user data from the backend
interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  is_verified: boolean;
  is_superuser: boolean;
  avatar_url?: string;
  organization_id?: string | null;
  role?: string | null;
}

const normalizeUser = (userData: {
  id: string;
  email: string;
  full_name?: string | null;
  is_active?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  is_verified?: boolean;
  is_superuser?: boolean;
  avatar_url?: string | null;
  organization_id?: string | null;
  role?: string | null;
}): User => ({
  id: userData.id,
  email: userData.email,
  full_name: userData.full_name || '',
  is_active: userData.is_active ?? true,
  created_at: userData.created_at || new Date().toISOString(),
  updated_at: userData.updated_at || new Date().toISOString(),
  is_verified: userData.is_verified ?? true,
  is_superuser: userData.is_superuser ?? false,
  avatar_url: userData.avatar_url ?? undefined,
  organization_id: userData.organization_id ?? null,
  role: (userData.role as any) || 'employee',
});

const persistTokens = (tokens: Pick<LoginResponse, 'access_token' | 'refresh_token'>) => {
  if (tokens.access_token) {
    localStorage.setItem('access_token', tokens.access_token);
  }
  if (tokens.refresh_token) {
    localStorage.setItem('refresh_token', tokens.refresh_token);
  } else if (!tokens.access_token) {
    // If we're clearing tokens (e.g. login failed or MFA required)
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

// Function to handle user login
export const login = async (credentials: LoginCredentials): Promise<{ user?: User; tokens: LoginResponse; requires_mfa?: boolean; mfa_challenge_token?: string }> => {
  logger.logAuthEvent('Login attempt', {
    email: credentials.email,
    timestamp: new Date().toISOString()
  });

  try {
    // Use the real auth router and send OAuth2-compatible form data.
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    logger.logApiCall('auth/login', 'POST', {
      email: credentials.email
    });

    const response = await apiClient.post<LoginResponse>('auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const loginData = response.data;
    console.log('[DEBUG] Login Data:', loginData);

    // Check if MFA is required
    if (loginData.requires_mfa) {
      logger.logAuthEvent('MFA challenge issued', {
        email: credentials.email
      });

      return {
        requires_mfa: true,
        mfa_challenge_token: loginData.mfa_challenge_token,
        tokens: loginData
      };
    }

    // Normal login flow
    if (loginData.access_token) {
      persistTokens({
        access_token: loginData.access_token,
        refresh_token: loginData.refresh_token,
      });
    }

    // Fetch the authoritative profile from the auth router.
    let user: User;
    try {
      user = await getCurrentUser();
    } catch (error) {
      // Fallback to the login payload if /auth/me is temporarily unavailable.
      console.warn('Could not fetch full user profile, using basic data', error);
      if (loginData.user) {
        user = normalizeUser(loginData.user);
      } else {
        throw new Error('No user data available in login response');
      }
    }

    logger.logAuthEvent('Login successful', {
      user_id: user.id,
      email: user.email,
      timestamp: new Date().toISOString()
    });

    return {
      user,
      tokens: loginData
    };

  } catch (error: any) {
    // Log API errors with context
    if (error.response) {
      logger.logAuthFailure('Login failed - API error', error, {
        email: credentials.email,
        status_code: error.response.status,
        status_text: error.response.statusText
      });
    } else if (error.request) {
      logger.logAuthFailure('Login failed - network error', error, {
        email: credentials.email,
        reason: 'network_error'
      });
    } else {
      logger.logAuthFailure('Login failed - unexpected error', error, {
        email: credentials.email
      });
    }

    throw error;
  }
};
// Function to handle MFA verification completion
export const verifyMfa = async (mfaChallengeToken: string, totpCode: string): Promise<{ user: User; tokens: LoginResponse }> => {
  try {
    const formData = new URLSearchParams();
    formData.append('mfa_challenge_token', mfaChallengeToken);
    formData.append('totp_code', totpCode);

    const response = await apiClient.post<LoginResponse>('auth/login/mfa/verify', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const loginData = response.data;
    console.log('[DEBUG] Login Data:', loginData);

    if (loginData.access_token) {
      persistTokens({
        access_token: loginData.access_token,
        refresh_token: loginData.refresh_token,
      });
    }

    // Fetch the authoritative profile
    let user: User;
    try {
      user = await getCurrentUser();
    } catch (error) {
      console.warn('Could not fetch full user profile after MFA, using basic data', error);
      if (loginData.user) {
        user = normalizeUser(loginData.user);
      } else {
        throw new Error('No user data available in MFA response');
      }
    }

    // Store user in localStorage for persistence
    localStorage.setItem('user', JSON.stringify(user));

    return { user, tokens: loginData };
  } catch (error: any) {
    logger.logAuthFailure('MFA verification failed', error);
    throw error;
  }
};

// Function to handle user registration
export const register = async (userData: RegisterData): Promise<void> => {
  await apiClient.post<UserResponse>('auth/register', userData);
};
// Function to get the currently authenticated user's data
export const getCurrentUser = async (): Promise<User> => {
  try {
    const response = await apiClient.get<{
      id: string;
      email: string;
      full_name: string | null;
      role: string;
      is_active: boolean;
      is_verified: boolean;
      is_superuser: boolean;
      two_factor_enabled: boolean;
      created_at: string | null;
      updated_at: string | null;
      avatar_url: string | null;
      organization_id: string | null;
    }>('auth/me');

    const user = normalizeUser(response.data);

    localStorage.setItem('user', JSON.stringify(user));

    logger.logAuthEvent('Get current user successful', {
      user_id: user.id,
      email: user.email,
      organization_id: user.organization_id
    });

    return user;

  } catch (error: any) {
    // Silently handle expected auth states without logging errors
    // These are normal: user not logged in, token expired, etc.
    const message = error?.message || 'Unknown error';

    // Only log unexpected errors (not 401 unauthorized)
    if (error?.response?.status !== 401) {
      logger.logAuthFailure('Get current user failed - unexpected error', error, {});
    }

    throw error;
  }
};
// Function to handle user logout
export const logout = async (): Promise<void> => {
  logger.logAuthEvent('Logout attempt', {
    user_id: logger['userId'] || 'unknown'
  });

  // SECURITY: Call backend logout endpoint to clear httpOnly cookies
  let backend_logout_success = false;
  try {
    await apiClient.post('auth/logout', {}, { withCredentials: true });
    backend_logout_success = true;  // ✅ Track backend success
    logger.logAuthEvent('Logout successful - backend cleared', {});
  } catch (error) {
    logger.logAuthFailure('Backend logout failed - keeping local state', error, {
      fallback: 'backend_unavailable'
    });
    // ✅ SECURITY FIX: Do NOT clear local state if backend fails
    // If backend is unreachable, user remains logged in on server
    // This prevents session inconsistency where frontend shows logged out
    // but backend still has active session
  }

  // Only clear local storage if backend logout succeeded
  if (backend_logout_success) {
    // Clear local storage (non-sensitive user data only)
    localStorage.removeItem('user');

    // Clear any fallback tokens still in localStorage from before migration
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // SECURITY: Tokens in httpOnly cookies cleared by backend
    logger.logAuthEvent('Logout completed - local state cleared', {});
  } else {
    logger.logAuthEvent('Logout deferred - backend unavailable', {});
  }
};
