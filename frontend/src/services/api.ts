
// src/services/api.ts
import { User, Team, ApiResponse, LoginFormData, RegisterFormData } from '../types';

// Get API URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('authToken');

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.message || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error occurred',
      };
    }
  }

  // Authentication endpoints
  async login(credentials: LoginFormData): Promise<ApiResponse<{ access_token: string; user: User }>> {
    // Mock implementation - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      success: true,
      data: {
        access_token: 'mock-token-' + Date.now(),
        user: {
          id: 1,
          name: 'Demo User',
          email: credentials.email,
        },
      },
    };

    // Real implementation (uncomment when backend is ready):
    // return this.request<{ access_token: string; user: User }>('/auth/login', {
    //   method: 'POST',
    //   body: JSON.stringify(credentials),
    // });
  }

  async register(userData: RegisterFormData): Promise<ApiResponse<User>> {
    // Mock implementation - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      success: true,
      data: {
        id: Date.now(),
        name: userData.name,
        email: userData.email,
      },
    };

    // Real implementation (uncomment when backend is ready):
    // return this.request<User>('/auth/register', {
    //   method: 'POST',
    //   body: JSON.stringify(userData),
    // });
  }

  async refreshToken(): Promise<ApiResponse<{ access_token: string }>> {
    return this.request<{ access_token: string }>('/auth/refresh', {
      method: 'POST',
    });
  }

  // Team endpoints
  async getTeams(): Promise<ApiResponse<Team[]>> {
    // Mock implementation - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      data: [
        { id: 1, name: 'Frontend Team', status: 'active', description: 'Web development team' },
        { id: 2, name: 'Backend Team', status: 'active', description: 'API development team' },
        { id: 3, name: 'QA Team', status: 'inactive', description: 'Quality assurance team' },
      ],
    };

    // Real implementation (uncomment when backend is ready):
    // return this.request<Team[]>('/teams');
  }

  async createTeam(teamData: Omit<Team, 'id'>): Promise<ApiResponse<Team>> {
    // Mock implementation - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      data: {
        id: Date.now(),
        ...teamData,
        status: 'active',
      },
    };

    // Real implementation (uncomment when backend is ready):
    // return this.request<Team>('/teams', {
    //   method: 'POST',
    //   body: JSON.stringify(teamData),
    // });
  }

  async updateTeam(teamId: number, updateData: Partial<Team>): Promise<ApiResponse<Team>> {
    // Mock implementation - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      data: {
        ...updateData,
        id: teamId,
      } as Team,
    };

    // Real implementation (uncomment when backend is ready):
    // return this.request<Team>(`/teams/${teamId}`, {
    //   method: 'PUT',
    //   body: JSON.stringify(updateData),
    // });
  }

  async deleteTeam(teamId: number): Promise<ApiResponse<void>> {
    // Mock implementation - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return { success: true };

    // Real implementation (uncomment when backend is ready):
    // return this.request<void>(`/teams/${teamId}`, {
    //   method: 'DELETE',
    // });
  }

  // Health check endpoint
  async healthCheck(): Promise<ApiResponse<{ status: string; version: string }>> {
    return this.request<{ status: string; version: string }>('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient(API_BASE_URL);

// Export individual service functions for convenience
export const authService = {
  login: (credentials: LoginFormData) => apiClient.login(credentials),
  register: (userData: RegisterFormData) => apiClient.register(userData),
  refreshToken: () => apiClient.refreshToken(),
};

export const teamService = {
  getTeams: () => apiClient.getTeams(),
  createTeam: (teamData: Omit<Team, 'id'>) => apiClient.createTeam(teamData),
  updateTeam: (teamId: number, updateData: Partial<Team>) => apiClient.updateTeam(teamId, updateData),
  deleteTeam: (teamId: number) => apiClient.deleteTeam(teamId),
};