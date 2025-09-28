// src/contexts/AuthContext.tsx - Authentication Context

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, ApiResponse, RegisterFormData } from '../types';

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
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async (): Promise<void> => {
    try {
      const token = localStorage.getItem('authToken');
      if (token) {
        // Simulate API call - replace with actual API
        const userData: User = {
          id: 1,
          name: 'Demo User',
          email: 'demo@example.com',
        };
        setUser(userData);
      }
    } catch (error) {
      localStorage.removeItem('authToken');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<ApiResponse> => {
    try {
      setIsLoading(true);
      // Simulate API call - replace with actual API
      const mockResponse = {
        access_token: 'mock-token-' + Date.now(),
        user: { id: 1, name: 'Demo User', email: email },
      };

      localStorage.setItem('authToken', mockResponse.access_token);
      setUser(mockResponse.user);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Login failed',
      };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterFormData): Promise<ApiResponse> => {
    try {
      setIsLoading(true);
      // Simulate API call - replace with actual API
      const response = { id: Date.now(), ...userData };
      return { success: true, data: response };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Registration failed',
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (): void => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};