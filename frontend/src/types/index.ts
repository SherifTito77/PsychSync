
// ===== CORE ENTITY INTERFACES =====

export interface User {
  id: number;
  name: string;
  email: string;
  createdAt?: string;
  updatedAt?: string;
  role?: 'admin' | 'manager' | 'member';
  profilePicture?: string;
}

export interface Team {
  id: number;
  name: string;
  status: 'active' | 'inactive' | 'archived';
  description: string;
  createdAt?: string;
  updatedAt?: string;
  memberCount?: number;
  ownerId?: number;
}

export interface Notification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration: number;
  createdAt?: string;
  isRead?: boolean;
}

// ===== API RESPONSE INTERFACES =====

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
  expires_in?: number;
}

export interface DashboardData {
  totalTeams: number;
  totalAssessments: number;
  avgCompatibility: number;
  predictedVelocity: number;
}

// ===== FORM DATA INTERFACES =====

export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface TeamFormData {
  name: string;
  description: string;
  status?: 'active' | 'inactive';
}