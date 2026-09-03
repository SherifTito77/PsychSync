import api from './api';
import logger from '@/utils/logger';

export interface SettingsData {
  profile: {
    name: string;
    email: string;
    company: string;
    title: string;
    bio: string;
    avatar: string;
  };
  preferences: {
    emailNotifications: boolean;
    weeklyReports: boolean;
    teamUpdates: boolean;
    assessmentReminders: boolean;
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
  };
  privacy: {
    profileVisibility: 'public' | 'team' | 'private';
    shareAssessmentResults: boolean;
    dataSharing: boolean;
    twoFactorEnabled: boolean;
  };
  billing: {
    plan: 'free' | 'pro' | 'enterprise';
    billingEmail: string;
    nextBillingDate?: string;
    cancelAtPeriodEnd: boolean;
  };
}

export const settingsService = {
  async getSettings(): Promise<SettingsData> {
    logger.logApiCall('/settings', 'GET');
    try {
      const response = await api.get<SettingsData>('/settings');
      return response.data;
    } catch (error: any) {
      logger.logApiError('/settings', 'GET', error);
      throw error;
    }
  },

  async updateSettings(data: Partial<SettingsData>): Promise<void> {
    logger.logApiCall('/settings', 'PUT');
    try {
      await api.put('/settings', data);
      logger.info('Settings updated successfully');
    } catch (error: any) {
      logger.logApiError('/settings', 'PUT', error);
      throw error;
    }
  },

  async uploadAvatar(file: File): Promise<{ avatarUrl: string }> {
    logger.logApiCall('/settings/avatar', 'POST');
    try {
      const formData = new FormData();
      formData.append('avatar', file);
      const response = await api.post<{ avatarUrl: string }>('/settings/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      logger.logApiError('/settings/avatar', 'POST', error);
      throw error;
    }
  },
};
