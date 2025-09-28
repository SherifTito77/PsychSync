// // // // src/types/index.ts

// src/types/index.ts - Fixed type definitions

export interface User {
  id: number;
  name: string;
  email: string;
  createdAt?: string;
  updatedAt?: string;
  role?: 'admin' | 'manager' | 'member';
}

export interface Team {
  id: number;
  name: string;
  status: 'active' | 'inactive' | 'archived'; // Added status property
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

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string; // Added error property
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

// // src/types/index.ts

// export interface User {
//   id: number;
//   name: string;
//   email: string;
//   // Add other fields if needed
// }

// export interface RegisterFormData {
//   name: string;
//   email: string;
//   password: string;
//   confirmPassword: string;
// }

// export interface ApiResponse<T = any> {
//   success: boolean;
//   data?: T;
//   message?: string;
// }

// // Rename custom Notification to avoid conflict with browser Notification
// export interface AppNotification {
//   id: string;
//   message: string;
//   type: "success" | "error" | "info";
//   duration?: number;
// }

// // Team type
// export interface Team {
//   id: number;
//   name: string;
//   members: User[];
//   createdAt: string;
// }



// // export interface User {
// //   id: number;
// //   name: string;
// //   email: string;
// //   createdAt?: string;
// //   updatedAt?: string;
// //   role?: "admin" | "manager" | "member";
// // }

// // export interface Team {
// //   id: number;
// //   name: string;
// //   status: "active" | "inactive" | "archived";
// //   description: string;
// //   createdAt?: string;
// //   updatedAt?: string;
// // }

// // export interface Notification {
// //   id: number;
// //   message: string;
// //   type: "success" | "error" | "warning" | "info";
// //   duration: number;
// // }

// // export interface ApiResponse<T = any> {
// //   success: boolean;
// //   data?: T;
// //   error?: string;
// // }

// // export interface RegisterFormData {
// //   name: string;
// //   email: string;
// //   password: string;
// //   confirmPassword: string;
// // }

// // export interface DashboardData {
// //   totalTeams: number;
// //   totalAssessments: number;
// //   avgCompatibility: number;
// //   predictedVelocity: number;
// // }

// // export interface LoginFormData {
// //   email: string;
// //   password: string;
// // }

// // // // types/index.ts
// // export interface AppNotification {
// //   id: string;
// //   message: string;
// //   type: "success" | "error" | "info";
// //   duration?: number;
// // }

// // // // types/contexts.ts
// // notifications: AppNotification[];
// // // // setNotifications: React.Dispatch<React.SetStateAction<AppNotification[]>>;

// // // // For context providers
// // // export interface AuthProviderProps {
// // //   children: React.ReactNode;
// // // }

// // // export interface AuthContextType {
// // //   user: User | null;
// // //   setUser: React.Dispatch<React.SetStateAction<User | null>>;
// // //   isLoading: boolean;
// // //   login: (email: string, password: string) => Promise<ApiResponse<any>>;
// // //   register: (userData: RegisterFormData) => Promise<ApiResponse<any>>;
// // //   logout: () => void;
// // // }

// // // export interface TeamContextType {
// // //   teams: Team[];
// // //   selectedTeam: Team | null;
// // //   loading: boolean;
// // //   fetchTeams: () => Promise<void>;
// // //   createTeam: (teamData: Partial<Team>) => Promise<ApiResponse<Team>>;
// // //   updateTeam: (id: number, teamData: Partial<Team>) => Promise<ApiResponse<Team>>; // ensure id is number
// // //   deleteTeam: (id: number) => Promise<ApiResponse<null>>; // ensure id is number
// // //   selectTeam: (team: Team | null) => void;
// // // }

// // // export interface NotificationContextType {
// // //   notifications: AppNotification[];
// // //   addNotification: (notification: Omit<AppNotification, "id">) => void;
// // //   removeNotification: (id: string) => void;
// // // }

// // // // ===== Component Props ===== 


// // // // ===== Core Models =====
// // // export interface User {
// // //   id: number; // enforce consistency
// // //   name: string;
// // //   email: string;
// // // }

// // // export interface Team {
// // //   id: number;
// // //   name: string;
// // //   description: string; // ✅ required field
// // //   status: "active" | "inactive" | "archived";
// // // }

// // // export interface Notification {
// // //   id: string;
// // //   message: string;
// // //   type: "success" | "error" | "info";
// // // }

// // // export interface ApiResponse<T = any> {
// // //   success: boolean;
// // //   data?: T;
// // //   error?: string;
// // // }

// // // // ===== Form Data =====
// // // export interface RegisterFormData {
// // //   name: string;
// // //   email: string;
// // //   password: string;
// // // }

// // // export interface LoginFormData {
// // //   email: string;
// // //   password: string;
// // // }

// // // // // ===== CORE ENTITY INTERFACES =====

// // // // export interface User {
// // // //   id: number;
// // // //   name: string;
// // // //   email: string;
// // // //   createdAt?: string;
// // // //   updatedAt?: string;
// // // //   role?: 'admin' | 'manager' | 'member';
// // // //   profilePicture?: string;
// // // // }

// // // // export interface Team {
// // // //   id: number;
// // // //   name: string;
// // // //   status: 'active' | 'inactive' | 'archived';
// // // //   description: string;
// // // //   createdAt?: string;
// // // //   updatedAt?: string;
// // // //   memberCount?: number;
// // // //   ownerId?: number;
// // // // }

// // // // export interface Notification {
// // // //   id: number;
// // // //   message: string;
// // // //   type: 'success' | 'error' | 'warning' | 'info';
// // // //   duration: number;
// // // //   createdAt?: string;
// // // //   isRead?: boolean;
// // // // }

// // // // // ===== API RESPONSE INTERFACES =====

// // // // export interface ApiResponse<T = any> {
// // // //   success: boolean;
// // // //   data?: T;
// // // //   error?: string;
// // // //   message?: string;
// // // // }

// // // // export interface LoginResponse {
// // // //   access_token: string;
// // // //   user: User;
// // // //   expires_in?: number;
// // // // }

// // // // export interface DashboardData {
// // // //   totalTeams: number;
// // // //   totalAssessments: number;
// // // //   avgCompatibility: number;
// // // //   predictedVelocity: number;
// // // // }

// // // // // ===== FORM DATA INTERFACES =====

// // // // export interface LoginFormData {
// // // //   email: string;
// // // //   password: string;
// // // // }

// // // // export interface RegisterFormData {
// // // //   name: string;
// // // //   email: string;
// // // //   password: string;
// // // //   confirmPassword: string;
// // // // }

// // // // export interface TeamFormData {
// // // //   name: string;
// // // //   description: string;
// // // //   status?: 'active' | 'inactive';
// // // // }
