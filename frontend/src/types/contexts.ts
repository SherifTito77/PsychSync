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
