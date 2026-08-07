// src/services/authService.ts
// Authentication service with httpOnly cookie-based security
import apiClient from './api';
import { User, LoginCredentials, RegisterData } from '../types';
import logger from '../utils/logger';
// SECURITY: No longer using SecureTokenStorage - tokens in httpOnly cookies
// Define the expected shape of the login response from the backend
interface LoginResponse {
  success?: boolean;
  access_token: string;
  token_type: string;
  expires_in?: number;
  user?: UserResponse;
  message?: string;
  timestamp?: number;
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
}
// Function to handle user login
export const login = async (credentials: LoginCredentials): Promise<{ user: User; tokens: LoginResponse }> => {
  logger.logAuthEvent('Login attempt', {
    email: credentials.email,
    timestamp: new Date().toISOString()
  });

  try {
    // Use the simple-login endpoint (no CSRF token required)
    // Use URLSearchParams for application/x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    logger.logApiCall('/simple-login', 'POST', {
      email: credentials.email
    });

    const response = await apiClient.post<{
      success: boolean;
      access_token: string;
      token_type: string;
      user: {
        id: string;
        email: string;
        name: string;
        role?: string;
        is_superuser?: boolean;
      };
    }>('/simple-login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const loginData = response.data;

    // Check if login was successful
    if (!loginData.success) {
      logger.logAuthFailure('Login failed - invalid credentials', new Error('Login failed'), {
        email: credentials.email,
        reason: 'invalid_credentials'
      });
      throw new Error('Login failed');
    }

    // Extract basic user data from response
    const basicUser: any = {
      id: loginData.user.id,
      email: loginData.user.email,
      full_name: loginData.user.name || loginData.user.full_name || loginData.user.email,
      is_active: loginData.user.is_active ?? true,
      created_at: loginData.user.created_at || new Date().toISOString(),
      updated_at: loginData.user.updated_at || new Date().toISOString(),
      is_verified: loginData.user.is_verified ?? true,
      is_superuser: loginData.user.is_superuser || false,
      role: loginData.user.role || 'employee',
      organization_id: loginData.user.organization_id || null
    };

    localStorage.setItem('access_token', loginData.access_token);
    if (loginData.refresh_token) {
      localStorage.setItem('refresh_token', loginData.refresh_token);
    }

    // ✅ Fetch complete user profile from /users/me to get organization_id
    let user: User;
    try {
      user = await getCurrentUser();
    } catch (error) {
      // Fallback to basic user data if /users/me fails
      console.warn('Could not fetch full user profile, using basic data', error);
      user = basicUser;
    }

    logger.logAuthEvent('Login successful', {
      user_id: user.id,
      email: user.email,
      timestamp: new Date().toISOString()
    });

    return {
      user,
      tokens: {
        access_token: loginData.access_token,
        refresh_token: loginData.refresh_token,
        token_type: loginData.token_type,
        user: user,
        expires_in: 86400 // 24 hours
      } as LoginResponse
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
// Function to handle user registration
export const register = async (userData: RegisterData): Promise<void> => {
  // Use correct register endpoint
  await apiClient.post<UserResponse>('/register', userData);
};
// Function to get the currently authenticated user's data
export const getCurrentUser = async (): Promise<User> => {
  try {
    // Use the /users/me endpoint which returns the full user profile including organization_id
    const response = await apiClient.get<{
      id: string;
      email: string;
      full_name: string | null;
      role: string;  // ✅ Include role from backend
      is_active: boolean;
      is_verified: boolean;
      is_superuser: boolean;
      two_factor_enabled: boolean;
      created_at: string | null;
      updated_at: string | null;
      avatar_url: string | null;
      organization_id: string | null;
    }>('/users/me');

    // Backend wraps response in {success, data, message} envelope
    const userData = (response.data as any).data ?? response.data;

    // Convert the response to match User interface
    const user: User = {
      id: userData.id,
      email: userData.email,
      full_name: userData.full_name || '',
      is_active: userData.is_active,
      created_at: userData.created_at || new Date().toISOString(),
      updated_at: userData.updated_at || new Date().toISOString(),
      is_verified: userData.is_verified,
      is_superuser: userData.is_superuser,
      avatar_url: userData.avatar_url,
      organization_id: userData.organization_id, // ✅ Include organization_id
      role: userData.role as any || 'employee' // ✅ Use role from backend
    };

    // Store updated user data in localStorage
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
    await apiClient.post('/logout', {}, { withCredentials: true });
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
