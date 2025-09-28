// // // // // // // // src/types/contexts.ts

// src/types/contexts.ts - Fixed context type definitions

import { User, Team, Notification, ApiResponse, RegisterFormData } from './index';

// ===== AUTH CONTEXT TYPES =====

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<ApiResponse>;
  register: (userData: RegisterFormData) => Promise<ApiResponse>;
  logout: () => void;
}

// ===== NOTIFICATION CONTEXT TYPES =====

export interface NotificationContextType {
  notifications: Notification[];
  showNotification: (message: string, type?: Notification['type'], duration?: number) => void;
  removeNotification: (id: number) => void;
}

// ===== TEAM CONTEXT TYPES =====

export interface TeamContextType {
  teams: Team[];
  currentTeam: Team | null;
  loading: boolean;
  fetchTeams: () => Promise<void>;
  createTeam: (teamData: Omit<Team, 'id'>) => Promise<ApiResponse<Team>>;
  updateTeam: (teamId: number, updateData: Partial<Team>) => Promise<ApiResponse<Team>>;
  deleteTeam: (teamId: number) => Promise<ApiResponse>;
  selectTeam: (team: Team) => void;
}


// // src/types/contexts.ts - Fixed context type definitions

// import { User, Team, Notification, ApiResponse, RegisterFormData } from './index';

// // ===== AUTH CONTEXT TYPES =====

// export interface AuthContextType {
//   user:any; //User | null;
//   // isLoading: boolean;
//   // login: (email: string, password: string) => Promise<ApiResponse>;
//   // register: (userData: RegisterFormData) => Promise<ApiResponse>;
//   setUser: (user: any) => void;
//   // logout: () => void;
// }

// export interface AuthProviderProps {
//   children: React.ReactNode;
// }


// // ===== NOTIFICATION CONTEXT TYPES =====

// export interface NotificationContextType {
//   notifications: Notification[];
//   showNotification: (message: string, type?: Notification['type'], duration?: number) => void;
//   removeNotification: (id: number) => void;
// }

// // ===== TEAM CONTEXT TYPES =====

// export interface TeamContextType {
//   teams: Team[];
//   currentTeam: Team | null;
//   loading: boolean;
//   fetchTeams: () => Promise<void>;
//   createTeam: (teamData: Omit<Team, 'id'>) => Promise<ApiResponse<Team>>;
//   updateTeam: (teamId: number, updateData: Partial<Team>) => Promise<ApiResponse<Team>>;
//   deleteTeam: (teamId: number) => Promise<ApiResponse>;
//   selectTeam: (team: Team) => void;
// }

// // // src/types/contexts.ts

// // import { User, RegisterFormData, ApiResponse, AppNotification, Team } from "./index";
// // import React, { ReactNode } from "react";

// // // Auth Context
// // export interface AuthContextType {
// //   user: User | null;
// //   isLoading: boolean;
// //   setUser: React.Dispatch<React.SetStateAction<User | null>>;
// //   login: (email: string, password: string) => Promise<ApiResponse<User>>;
// //   register: (userData: RegisterFormData) => Promise<ApiResponse<User>>;
// //   logout: () => void;
// // }

// // export interface AuthProviderProps {
// //   children: ReactNode;
// // }

// // // Notification Context
// // export interface NotificationContextType {
// //   notifications: AppNotification[];
// //   addNotification: (notification: AppNotification) => void;
// //   removeNotification: (id: string) => void;
// // }

// // // Team Context
// // export interface TeamContextType {
// //   teams: Team[];
// //   setTeams: React.Dispatch<React.SetStateAction<Team[]>>;
// //   addTeam: (team: Team) => void;
// //   removeTeam: (id: number) => void;
// // }




// // // // import { User, Team, Notification, ApiResponse } from ".";
// // // import { RegisterFormData, User, ApiResponse } from "./index";


// // // // Auth context
// // // export interface AuthContextType {
// // //   user: User | null;
// // //   setUser: React.Dispatch<React.SetStateAction<User | null>>; // added setUser
// // //   isLoading: boolean;
// // //   login: (email: string, password: string) => Promise<ApiResponse>;
// // //   register: (userData: RegisterFormData) => Promise<ApiResponse<User>>;

// // //   // register: (userData: { name: string; email: string; password: string }) => Promise<ApiResponse>;
// // //   logout: () => void;
// // // }

// // // // Notification context
// // // export interface NotificationContextType {
// // //   notifications: Notification[];
// // //   showNotification: (message: string, type?: Notification["type"], duration?: number) => void;
// // //   removeNotification: (id: number) => void;
// // // }

// // // // Team context
// // // export interface TeamContextType {
// // //   teams: Team[];
// // //   currentTeam: Team | null;
// // //   loading: boolean;
// // //   fetchTeams: () => void;
// // //   createTeam: (teamData: Omit<Team, "id">) => Promise<ApiResponse<Team>>;
// // //   updateTeam: (teamId: number, updateData: Partial<Team>) => Promise<ApiResponse<Team>>; // use number, not string
// // //   deleteTeam: (teamId: number) => Promise<ApiResponse<null>>; // use number
// // //   selectTeam: (team: Team) => void;
// // // }

// // // export interface AuthProviderProps {
// // //   children: React.ReactNode;
// // // }

// // // export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => { ... }



// // // // import {
// // // //   User,
// // // //   Team,
// // // //   ApiResponse,
// // // //   RegisterFormData,
// // // //   LoginFormData,
// // // // } from "./index";

// // // // // ===== Auth Context =====
// // // // export interface AuthContextType {
// // // //   user: User | null;
// // // //   setUser: React.Dispatch<React.SetStateAction<User | null>>;
// // // //   isLoading: boolean;
// // // //   login: (email: string, password: string) => Promise<ApiResponse<User>>;
// // // //   register: (userData: RegisterFormData) => Promise<ApiResponse<User>>;
// // // //   logout: () => void;
// // // // }

// // // // export interface AuthProviderProps {
// // // //   children: React.ReactNode;
// // // // }

// // // // // ===== Team Context =====
// // // // export interface TeamContextType {
// // // //   teams: Team[];
// // // //   currentTeam: Team | null;
// // // //   createTeam: (teamData: Omit<Team, "id">) => Promise<ApiResponse<Team>>;
// // // //   updateTeam: (
// // // //     id: string,
// // // //     teamData: Partial<Team>,
// // // //   ) => Promise<ApiResponse<Team>>;
// // // //   deleteTeam: (id: string) => Promise<ApiResponse<null>>;
// // // // }

// // // // // // src/types/contexts.ts
// // // // // import {
// // // // //   User,
// // // // //   Team,
// // // // //   Notification,
// // // // //   ApiResponse,
// // // // //   RegisterFormData,
// // // // //   LoginFormData,
// // // // // } from "./index";

// // // // // // ===== Auth Context =====
// // // // // export interface AuthContextType {
// // // // //   user: User | null;
// // // // //   setUser: React.Dispatch<React.SetStateAction<User | null>>;
// // // // //   isLoading: boolean;
// // // // //   login: (email: string, password: string) => Promise<ApiResponse<User>>;
// // // // //   register: (userData: RegisterFormData) => Promise<ApiResponse<User>>;
// // // // //   logout: () => void;
// // // // // }

// // // // // export interface AuthProviderProps {
// // // // //   children: React.ReactNode;
// // // // // }

// // // // // // ===== Team Context =====
// // // // // export interface TeamContextType {
// // // // //   teams: Team[];
// // // // //   currentTeam: Team | null;
// // // // //   createTeam: (teamData: Omit<Team, "id">) => Promise<ApiResponse<Team>>;
// // // // //   updateTeam: (
// // // // //     id: string,
// // // // //     teamData: Partial<Team>,
// // // // //   ) => Promise<ApiResponse<Team>>;
// // // // //   deleteTeam: (id: string) => Promise<ApiResponse<null>>;
// // // // // }

// // // // // // import { User, Team, Notification, ApiResponse, LoginFormData, RegisterFormData } from "./index";

// // // // // // // src/types/contexts.ts

// // // // // // export interface User {
// // // // // //   id: string | number;
// // // // // //   name: string;
// // // // // //   email: string;
// // // // // // }

// // // // // // export interface Team {
// // // // // //   id: number;
// // // // // //   name: string;
// // // // // //   status: "active" | "inactive" | "archived";
// // // // // // }

// // // // // // export interface Notification {
// // // // // //   id: string;
// // // // // //   message: string;
// // // // // //   type: "success" | "error" | "info";
// // // // // // }

// // // // // // export interface ApiResponse<T = any> {
// // // // // //   success: boolean;
// // // // // //   data?: T;
// // // // // //   error?: string;
// // // // // // }

// // // // // // export interface RegisterFormData {
// // // // // //   name: string;
// // // // // //   email: string;
// // // // // //   password: string;
// // // // // // }

// // // // // // export interface LoginFormData {
// // // // // //   email: string;
// // // // // //   password: string;
// // // // // // }

// // // // // // // For context providers
// // // // // // export interface AuthProviderProps {
// // // // // //   children: React.ReactNode;
// // // // // // }

// // // // // // // Auth context type
// // // // // // export interface AuthContextType {
// // // // // //   user: User | null;
// // // // // //   setUser: React.Dispatch<React.SetStateAction<User | null>>;
// // // // // //   isLoading: boolean;
// // // // // //   login: (email: string, password: string) => Promise<ApiResponse<any>>;
// // // // // //   register: (userData: RegisterFormData) => Promise<ApiResponse<any>>;
// // // // // //   logout: () => void;
// // // // // // }

// // // // // // // Team form type (single definition, no duplicates)
// // // // // // export type TeamFormData = Omit<Team, "id"> & {
// // // // // //   status?: "active" | "inactive"; // Optional for forms
// // // // // // };

// // // // // // // src/types/contexts.ts
// // // // // // export interface TeamContextType {
// // // // // //   teams: Team[];
// // // // // //   currentTeam: Team | null; // ✅ add this
// // // // // //   createTeam: (teamData: Omit<Team, "id">) => Promise<ApiResponse<Team>>;
// // // // // //   updateTeam: (
// // // // // //     id: string,
// // // // // //     teamData: Partial<Team>
// // // // // //   ) => Promise<ApiResponse<Team>>;
// // // // // //   deleteTeam: (id: string) => Promise<ApiResponse<null>>;
// // // // // // }

// // // // // // // // Team context type
// // // // // // // export interface TeamContextType {
// // // // // // //   teams: Team[];
// // // // // // //   createTeam: (teamData: TeamFormData) => Promise<ApiResponse<Team>>;
// // // // // // //   updateTeam: (id: string, teamData: Partial<TeamFormData>) => Promise<ApiResponse<Team>>;
// // // // // // //   deleteTeam: (id: string) => Promise<ApiResponse<null>>;
// // // // // // // }

// // // // // // // // REMOVE TeamFormData from this import line
// // // // // // // import { User, Team, Notification, ApiResponse, LoginFormData, RegisterFormData } from './index';
// // // // // // // // import React from 'react';

// // // // // // // // ===== AUTH CONTEXT TYPES =====

// // // // // // // export interface AuthContextType {
// // // // // // //   user: User | null;
// // // // // // //   isLoading: boolean;
// // // // // // //   login: (email: string, password: string) => Promise<ApiResponse>;
// // // // // // //   register: (userData: RegisterFormData) => Promise<ApiResponse>;
// // // // // // //   logout: () => void;
// // // // // // // }

// // // // // // // // ===== NOTIFICATION CONTEXT TYPES =====

// // // // // // // export interface NotificationContextType {
// // // // // // //   notifications: Notification[];
// // // // // // //   showNotification: (message: string, type?: Notification['type'], duration?: number) => void;
// // // // // // //   removeNotification: (id: number) => void;
// // // // // // // }

// // // // // // // // ===== TEAM CONTEXT TYPES =====

// // // // // // // export interface TeamContextType {
// // // // // // //   teams: Team[];
// // // // // // //   currentTeam: Team | null;
// // // // // // //   loading: boolean;
// // // // // // //   fetchTeams: () => Promise<void>;
// // // // // // //   createTeam: (teamData: TeamFormData) => Promise<ApiResponse<Team>>;
// // // // // // //   updateTeam: (teamId: number, updateData: Partial<Team>) => Promise<ApiResponse<Team>>;
// // // // // // //   deleteTeam: (teamId: number) => Promise<ApiResponse>;
// // // // // // //   selectTeam: (team: Team) => void;
// // // // // // // }

// // // // // // // // src/types/contexts.ts
// // // // // // // export type TeamFormData = Omit<Team, "id" | "status"> & {
// // // // // // //   status?: "active" | "inactive";
// // // // // // // };

// // // // // // // // src/types/contexts.ts
// // // // // // // export interface AuthProviderProps {
// // // // // // //   children: React.ReactNode;
// // // // // // // }

// // // // // // // // src/types/contexts.ts
// // // // // // // export type TeamFormData = Omit<Team, "id">; // simplest fix

// // // // // // // // OR, if form should not send "archived"
// // // // // // // export type TeamFormData = Omit<Team, "id"> & {
// // // // // // //   status?: "active" | "inactive"; // optional
// // // // // // // };

// // // // // // // // src/types/contexts.ts
// // // // // // // export interface AuthProviderProps {
// // // // // // //   children: React.ReactNode;
// // // // // // // }

// // // // // // // // src/types/contexts.ts
// // // // // // // export interface AuthContextType {
// // // // // // //   user: User | null;
// // // // // // //   setUser: React.Dispatch<React.SetStateAction<User | null>>;
// // // // // // //   login?: (email: string, password: string) => Promise<boolean>;
// // // // // // //   logout?: () => void;
// // // // // // // }

// // // // // // // // export interface NotificationProviderProps {
// // // // // // // //   children: React.ReactNode;
// // // // // // // // }
// // // // // // // // export interface TeamProviderProps {
// // // // // // // //   children: React.ReactNode;
// // // // // // // // }

// // // // // // // // export type LoginFormData = {

// // // // // // // //   email: string;
// // // // // // // //   password: string;
// // // // // // // // };
// // // // // // // // export type RegisterFormData = {
// // // // // // // //   name: string;
// // // // // // // //   email: string;
// // // // // // // //   password: string;
// // // // // // // //   confirmPassword: string;
// // // // // // // // };
// // // // // // // // export interface ApiResponse<T = any> {
// // // // // // // //   success: boolean;
// // // // // // // //   message: string;
// // // // // // // //   data?: T;
// // // // // // // // }
// // // // // // // // export interface User {
// // // // // // // //   id: number;
