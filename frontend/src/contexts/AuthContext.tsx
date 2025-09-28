// // // // // // src/contexts/AuthContext.tsx

// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { AuthContextType } from '../types/contexts';
import { User, ApiResponse, RegisterFormData } from '../types';
import { authService } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async (): Promise<void> => {
    try {
      const token = localStorage.getItem('authToken');
      if (token) {
        // Simulate API call to validate token and get user data
        // In real implementation, call your backend to validate token
        const userData: User = {
          id: 1,
          name: 'Demo User',
          email: 'demo@example.com'
        };
        setUser(userData);
      }
    } catch (error) {
      localStorage.removeItem('authToken');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<ApiResponse> => {
    try {
      setIsLoading(true);
      
      // Use the API service for login
      const result = await authService.login({ email, password });
      
      if (result.success && result.data) {
        localStorage.setItem('authToken', result.data.access_token);
        setUser(result.data.user);
        return { success: true };
      } else {
        return {
          success: false,
          error: result.error || 'Login failed'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Login failed'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterFormData): Promise<ApiResponse> => {
    try {
      setIsLoading(true);
      
      // Use the API service for registration
      const result = await authService.register(userData);
      
      if (result.success) {
        return {
          success: true,
          data: result.data
        };
      } else {
        return {
          success: false,
          error: result.error || 'Registration failed'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Registration failed'
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
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};




// import { AuthContextType, AuthProviderProps } from "../types/contexts";
// import { User, ApiResponse, RegisterFormData } from "../types";

// import React, { createContext, useContext, useState, useEffect } from "react";


// const AuthContext = createContext<AuthContextType | undefined>(undefined);

// export const useAuth = () => {
//   const ctx = useContext(AuthContext);
//   if (!ctx) throw new Error("useAuth must be used within AuthProvider");
//   return ctx;
// };

// export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
//   const [user, setUser] = useState<User | null>(null);
//   const [isLoading] = useState(false);

//   const value: AuthContextType = {
//     user,
//     setUser,
//     isLoading,
//     login: async (email, password) => {
//       const mockUser: User = { id: 1, name: "Demo", email };
//       setUser(mockUser);
//       return { success: true, data: mockUser } as ApiResponse<User>;
//     },
//     register: async (data: RegisterFormData) => {
//       const newUser: User = {
//         id: Date.now(),
//         name: data.name,
//         email: data.email,
//       };
//       setUser(newUser);
//       return { success: true, data: newUser } as ApiResponse<User>;
//     },
//     logout: () => setUser(null),
//   };

//   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// };



// // // src/contexts/AuthContext.tsx
// // import React, { createContext, useContext, useState } from "react";
// // import { AuthContextType, AuthProviderProps } from "../types/contexts";
// // import { User } from "../types";

// // const AuthContext = createContext<AuthContextType | undefined>(undefined);

// // export const useAuth = () => {
// //   const ctx = useContext(AuthContext);
// //   if (!ctx) throw new Error("useAuth must be used within AuthProvider");
// //   return ctx;
// // };

// // export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
// //   const [user, setUser] = useState<User | null>(null);
// //   const [isLoading] = useState(false);

// //   const value: AuthContextType = {
// //     user,
// //     setUser,
// //     isLoading,
// //     login: async (email, password) => {
// //       const mockUser: User = { id: 1, name: "Demo", email };
// //       setUser(mockUser);
// //       return { success: true, data: mockUser };
// //     },
// //     register: async (data) => {
// //       const newUser: User = {
// //         id: Date.now(),
// //         name: data.name,
// //         email: data.email,
// //       };
// //       setUser(newUser);
// //       return { success: true, data: newUser };
// //     },
// //     logout: () => setUser(null),
// //   };

// //   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// // };

// // // // src/contexts/AuthContext.tsx
// // // import React, { createContext, useContext, useState } from "react";
// // // import { AuthContextType, AuthProviderProps, User } from "../types/contexts";

// // // export const AuthContext = createContext<AuthContextType | undefined>(
// // //   undefined
// // // );

// // // export const useAuth = () => {
// // //   const ctx = useContext(AuthContext);
// // //   if (!ctx) throw new Error("useAuth must be used within AuthProvider");
// // //   return ctx;
// // // };

// // // export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
// // //   const [user, setUser] = useState<User | null>(null);

// // //   const value: AuthContextType = {
// // //     user,
// // //     setUser,
// // //     isLoading: false,
// // //     login: async () => ({ success: true }),
// // //     register: async () => ({ success: true }),
// // //     logout: () => setUser(null),
// // //   };

// // //   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// // // };

// // // // import React, { createContext, useState, useContext } from "react";
// // // // import { AuthContextType, AuthProviderProps } from "../types/contexts";
// // // // import { User } from "../types";

// // // // const AuthContext = createContext<AuthContextType | undefined>(undefined);

// // // // export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
// // // //   const [user, setUser] = useState<User | null>(null);
// // // //   const [isLoading, setIsLoading] = useState(false);

// // // //   const login = async (email: string, password: string) => {
// // // //     setIsLoading(true);
// // // //     try {
// // // //       // TODO: call API
// // // //       return { success: true, data: { id: "1", email } } as any;
// // // //     } finally {
// // // //       setIsLoading(false);
// // // //     }
// // // //   };

// // // //   const register = async () => {
// // // //     // TODO: implement register
// // // //     return { success: true, data: {} } as any;
// // // //   };

// // // //   const logout = () => {
// // // //     setUser(null);
// // // //   };

// // // //   const value: AuthContextType = {
// // // //     user,
// // // //     setUser,
// // // //     isLoading,
// // // //     login,
// // // //     register,
// // // //     logout,
// // // //   };

// // // //   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// // // // };

// // // // export const useAuth = (): AuthContextType => {
// // // //   const ctx = useContext(AuthContext);
// // // //   if (!ctx) throw new Error("useAuth must be used within AuthProvider");
// // // //   return ctx;
// // // // };

// // // // // import React, { createContext, useState, useContext } from "react";
// // // // // import { AuthContextType, AuthProviderProps } from "../types/contexts";

// // // // // const AuthContext = createContext<AuthContextType | undefined>(undefined);

// // // // // export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
// // // // //   const [user, setUser] = useState(null);

// // // // //   const value: AuthContextType = { user, setUser };
// // // // //   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// // // // // };
// // // // // // export const useAuth = (): AuthContextType => {
// // // // // //   const context = useContext(AuthContext);

// // // // // // import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';
// // // // // // import { AuthContextType, AuthProviderProps } from '../types/contexts';
// // // // // // import { User, ApiResponse, RegisterFormData } from '../types';

// // // // // // const AuthContext = createContext<AuthContextType | undefined>(undefined);

// // // // // // export const useAuth = (): AuthContextType => {
// // // // // //   const context = useContext(AuthContext);
// // // // // //   if (!context) {
// // // // // //     throw new Error('useAuth must be used within an AuthProvider');
// // // // // //   }
// // // // // //   return context;
// // // // // // };

// // // // // // export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
// // // // // //   const [user, setUser] = useState<User | null>(null);
// // // // // //   const [isLoading, setIsLoading] = useState<boolean>(true);

// // // // // //   // ... rest of your existing logic with proper typing
// // // // // // };
