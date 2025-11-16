// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, ApiResponse, RegisterFormData } from '../types';
import { login as authServiceLogin, register, getCurrentUser, logout as authServiceLogout } from '../services/authService';
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<ApiResponse>;
  register: (userData: RegisterFormData) => Promise<ApiResponse>;
  logout: () => void;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined);
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
interface AuthProviderProps {
  children: ReactNode;
}
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true); // Start with true to check for auth status
  // --- AUTO-LOGIN LOGIC ---
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // If authenticated, get the current user from real service
          const currentUser = await getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
          }
        } catch (error) {
          // If fetching fails, log the user out.
          console.error('Invalid token, logging out.');
          handleLogout();
        }
      }
      // Set loading to false after the check is complete
      setIsLoading(false);
    };
    initAuth();
  }, []); // This runs only once when the component mounts
  const handleLogin = async (email: string, password: string): Promise<ApiResponse> => {
    try {
      // Use the real authentication service
      const { user: loggedInUser } = await authServiceLogin({ email, password });
      setUser(loggedInUser);
      return { success: true };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  };
  const handleRegister = async (userData: RegisterFormData): Promise<ApiResponse> => {
    try {
      await register({
        email: userData.email,
        full_name: userData.full_name,
        password: userData.password,
      });
      return { success: true };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };
  const handleLogout = (): void => {
    // Use the real logout service
    authServiceLogout();
    setUser(null);
  };
  const value: AuthContextType = {
    user,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};