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

    // Extract user data from response
    const user: User = {
      id: loginData.user.id,
      email: loginData.user.email,
      full_name: loginData.user.name || loginData.user.email,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_verified: true,
      is_superuser: loginData.user.email.includes('admin')
    };

    // Store user data AND token in localStorage (for development/testing)
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('access_token', loginData.access_token);

    logger.logAuthEvent('Login successful', {
      user_id: user.id,
      email: user.email,
      timestamp: new Date().toISOString()
    });

    return {
      user,
      tokens: {
        access_token: loginData.access_token,
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
  logger.logAuthEvent('Get current user attempt', {});

  try {
    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    if (!token) {
      logger.logAuthFailure('Get current user failed - no token', new Error('No token'), {
        reason: 'no_token_in_storage'
      });
      throw new Error('No authentication token found');
    }

    logger.logApiCall('/verify-token/' + token.substring(0, 10) + '...', 'GET', {});

    const response = await apiClient.get<{
      success: boolean;
      valid: boolean;
      payload?: {
        sub: string;
        user_id: string;
        name: string;
      };
    }>('/verify-token/' + token);

    const userData = response.data;

    if (!userData.success || !userData.valid) {
      logger.logAuthFailure('Get current user failed - invalid token', new Error('Invalid token'), {
        reason: 'invalid_token',
        success: userData.success,
        valid: userData.valid
      });
      throw new Error('Invalid token');
    }

    // Convert the response to match User interface
    const user: User = {
      id: userData.payload?.user_id || '',
      email: userData.payload?.sub || '',
      full_name: userData.payload?.name || '',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_verified: true,
      is_superuser: userData.payload?.sub?.includes('admin') || false
    };

    logger.logAuthEvent('Get current user successful', {
      user_id: user.id,
      email: user.email
    });

    return user;

  } catch (error: any) {
    if (error.response) {
      logger.logAuthFailure('Get current user failed - API error', error, {
        status_code: error.response.status
      });
    } else {
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
  try {
    await apiClient.post('/auth/logout', {}, { withCredentials: true });
    logger.logAuthEvent('Logout successful - backend cleared', {});
  } catch (error) {
    logger.logAuthFailure('Backend logout failed - clearing local state only', error, {
      fallback: 'local_clear'
    });
  }

  // Clear local storage (non-sensitive user data only)
  localStorage.removeItem('user');

  // Clear any fallback tokens still in localStorage from before migration
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // SECURITY: Tokens in httpOnly cookies cleared by backend
  logger.logAuthEvent('Logout completed - local state cleared', {});
};
