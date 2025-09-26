import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { AuthContextType, AuthProviderProps } from '../types/contexts';
import { User, ApiResponse, RegisterFormData } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // ... rest of your existing logic with proper typing
};
