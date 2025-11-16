// src/services/authService.ts
import apiClient from './api';
import { User, LoginCredentials, RegisterData } from '../types';
// Define the expected shape of the login response from the backend
interface LoginResponse {
  access_token: string;
  token_type: string;
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
}
// Function to handle user login
export const login = async (credentials: LoginCredentials): Promise<{ user: User; tokens: LoginResponse }> => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);   // or credentials.username
  formData.append('password', credentials.password);
  // Use correct token endpoint
  const response = await apiClient.post<LoginResponse>('/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  const loginData = response.data;
  // Store the token in localStorage
  localStorage.setItem('access_token', loginData.access_token);
  // Our backend returns user data in the login response
  const user = loginData.user;
  // Store user data in localStorage for persistence
  localStorage.setItem('user', JSON.stringify(user));
  return {
    user,
    tokens: {
      access_token: loginData.access_token,
      token_type: loginData.token_type,
      user: loginData.user
    }
  };
};
// Function to handle user registration
export const register = async (userData: RegisterData): Promise<void> => {
  // Use correct register endpoint
  await apiClient.post<UserResponse>('/register', userData);
};
// Function to get the currently authenticated user's data
export const getCurrentUser = async (): Promise<User> => {
  // Use correct user profile endpoint
  const response = await apiClient.get<UserResponse>('/me');
  return response.data as User;
};
// Function to handle user logout
export const logout = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};