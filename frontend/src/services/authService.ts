// src/services/authService.ts
// Authentication service with httpOnly cookie-based security
import apiClient from './api';
import { User, LoginCredentials, RegisterData } from '../types';
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
  // Use the secure token-fixed endpoint with httpOnly cookies
  const formData = new FormData();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);

  const response = await apiClient.post<{message: string; user: any}>('/auth/token-fixed', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    // SECURITY: Enable credentials to send/receive cookies
    withCredentials: true
  });

  const loginData = response.data;

  // Check if login was successful
  if (loginData.message !== 'Login successful') {
    throw new Error(loginData.message || 'Login failed');
  }

  // SECURITY: Tokens are now stored in httpOnly cookies by the backend
  // We do NOT store them in localStorage anymore to prevent XSS token theft

  // Extract user data from response
  const user: User = {
    id: loginData.user.id,
    email: loginData.user.email,
    full_name: loginData.user.full_name || loginData.user.email,
    is_active: loginData.user.is_active ?? true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_verified: true,
    is_superuser: loginData.user.role === 'admin'
  };

  // Store ONLY non-sensitive user data in localStorage (no tokens!)
  localStorage.setItem('user', JSON.stringify(user));

  return {
    user,
    tokens: {
      access_token: '',  // Empty - tokens are in httpOnly cookies
      token_type: 'bearer',
      user: user,
      expires_in: 1800
    } as LoginResponse
  };
};
// Function to handle user registration
export const register = async (userData: RegisterData): Promise<void> => {
  // Use correct register endpoint
  await apiClient.post<UserResponse>('/register', userData);
};
// Function to get the currently authenticated user's data
export const getCurrentUser = async (): Promise<User> => {
  // SECURITY: Tokens are in httpOnly cookies, sent automatically with withCredentials
  const response = await apiClient.get<{user: any}>('/auth/me-fixed', {
    withCredentials: true
  });
  const userData = response.data;

  // Convert the response to match User interface
  return {
    id: userData.user?.id || userData.id,
    email: userData.user?.email || userData.email,
    full_name: userData.user?.name || userData.name || userData.email,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_verified: true,
    is_superuser: userData.user?.email?.includes('admin') || false
  };
};
// Function to handle user logout
export const logout = async (): Promise<void> => {
  // SECURITY: Call backend logout endpoint to clear httpOnly cookies
  try {
    await apiClient.post('/auth/logout', {}, { withCredentials: true });
  } catch (error) {
    console.warn('Backend logout failed, clearing local state only');
  }

  // Clear local storage (non-sensitive user data only)
  localStorage.removeItem('user');

  // Clear any fallback tokens still in localStorage from before migration
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // SECURITY: Tokens in httpOnly cookies cleared by backend
};