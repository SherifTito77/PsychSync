/**
 * Biometric Authentication Service
 *
 * Manages Face ID, Touch ID, and fingerprint authentication for mobile apps.
 * Integrates with native biometric APIs and provides secure authentication flow.
 *
 * Features:
 * - Biometric registration with public-key cryptography
 * - Challenge-response authentication
 * - Device management
 * - Security monitoring
 *
 * Platform Support:
 * - iOS: Face ID, Touch ID (via LocalAuthentication)
 * - Android: Fingerprint, Face Unlock (via BiometricPrompt)
 */

import api from './api';

// =============================================================================
// Types
// =============================================================================

export type BiometricType =
  | 'face_id'          // iOS Face ID
  | 'touch_id'         // iOS Touch ID
  | 'fingerprint'      // Android Fingerprint
  | 'iris'             // Samsung Iris Scan
  | 'face_unlock';     // Android Face Unlock

export interface DeviceInfo {
  platform: 'ios' | 'android';
  device_id: string;
  device_model?: string;
  os_version?: string;
  app_version?: string;
}

export interface BiometricRegistrationRequest {
  device_id: string;
  biometric_type: BiometricType;
  device_info?: DeviceInfo;
}

export interface CompleteRegistrationRequest {
  device_id: string;
  public_key: string;
  challenge_signature: string;
  key_id?: string;
}

export interface BiometricAuthRequest {
  device_id: string;
}

export interface VerifyAuthRequest {
  device_id: string;
  challenge_id: string;
  signature: string;
}

export interface BiometricKey {
  device_id: string;
  key_id: string;
  biometric_type: string;
  registered_at: string;
  last_used_at: string;
}

export interface BiometricStatus {
  enabled: boolean;
  biometric_type?: string;
  registered_at?: string;
  last_used_at?: string;
  message?: string;
}

export interface AuthChallenge {
  challenge: string;
  challenge_id: string;
  expires_in: number;
  key_id: string;
}

export interface AuthResult {
  success: boolean;
  authenticated: boolean;
  auth_token?: string;
  token_type?: string;
  expires_in?: number;
  message?: string;
}

export interface BiometricTypeInfo {
  type: BiometricType;
  name: string;
  platform: 'ios' | 'android';
  description: string;
  min_version: string;
}

// =============================================================================
// Service Class
// =============================================================================

class BiometricAuthService {
  private registeredKeys: Map<string, BiometricKey> = new Map();

  /**
   * Get unique device identifier
   * In production, this should come from the native layer
   */
  getDeviceId(): string {
    // Try to get from localStorage first
    const stored = localStorage.getItem('biometric_device_id');
    if (stored) {
      return stored;
    }

    // Generate new device ID
    const deviceId = `device_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    localStorage.setItem('biometric_device_id', deviceId);
    return deviceId;
  }

  /**
   * Get device information
   */
  getDeviceInfo(): DeviceInfo {
    const userAgent = navigator.userAgent;

    // Detect platform
    const isIOS = /iPad|iPhone|iPod/.test(userAgent) && !(window as any).MSStream;
    const isAndroid = /android/.test(userAgent.toLowerCase());

    const platform: 'ios' | 'android' = isIOS ? 'ios' : isAndroid ? 'android' : 'ios';

    return {
      platform,
      device_id: this.getDeviceId(),
      device_model: this.getDeviceModel(),
      os_version: this.getOSVersion(),
      app_version: process.env.REACT_APP_VERSION || '1.0.0',
    };
  }

  /**
   * Detect device model
   */
  private getDeviceModel(): string | undefined {
    const userAgent = navigator.userAgent;

    if (/iphone/.test(userAgent)) {
      return 'iPhone';
    } else if (/ipad/.test(userAgent)) {
      return 'iPad';
    } else if (/android/.test(userAgent)) {
      // Try to extract Android device model
      const match = userAgent.match(/Android\s([^\s]+)\s/);
      return match ? match[1] : 'Android Device';
    }

    return undefined;
  }

  /**
   * Detect OS version
   */
  private getOSVersion(): string {
    const userAgent = navigator.userAgent;
    let osVersion = 'Unknown';

    if (/iphone|ipad|ipod/.test(userAgent)) {
      const match = userAgent.match(/OS\s([\d_]+)\s/);
      osVersion = match ? match[1].replace(/_/g, '.') : 'iOS';
    } else if (/android/.test(userAgent)) {
      const match = userAgent.match(/Android\s([\d.]+)/);
      osVersion = match ? match[1] : 'Android';
    }

    return osVersion;
  }

  /**
   * Detect available biometric type
   */
  detectAvailableBiometric(): BiometricType | null {
    const platform = this.getDeviceInfo().platform;

    // In a real app, this would call native code to check:
    // - iOS: canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)
    // - Android: BiometricManager.canAuthenticate()

    // For now, return based on platform
    if (platform === 'ios') {
      // Assume Face ID for iOS (would check actual device in production)
      return 'face_id';
    } else {
      // Assume fingerprint for Android
      return 'fingerprint';
    }
  }

  /**
   * Initiate biometric registration
   */
  async initiateRegistration(
    biometricType: BiometricType
  ): Promise<{ registration_challenge: string; challenge_expires_in: number }> {
    try {
      const deviceInfo = this.getDeviceInfo();

      const response = await api.post('/biometric-auth/register/initiate', {
        device_id: deviceInfo.device_id,
        biometric_type: biometricType,
        device_info: deviceInfo,
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to initiate biometric registration:', error);
      throw error;
    }
  }

  /**
   * Complete biometric registration
   */
  async completeRegistration(request: CompleteRegistrationRequest): Promise<{
    success: boolean;
    key_id: string;
    registered_at: string;
    message: string;
  }> {
    try {
      const response = await api.post('/biometric-auth/register/complete', request);

      // Cache the key info
      if (response.data.success) {
        this.registeredKeys.set(request.device_id, {
          device_id: request.device_id,
          key_id: response.data.key_id,
          biometric_type: 'biometric',
          registered_at: response.data.registered_at,
          last_used_at: response.data.registered_at,
        });
      }

      return response.data;
    } catch (error: any) {
      console.error('Failed to complete biometric registration:', error);
      throw error;
    }
  }

  /**
   * Initiate biometric authentication
   */
  async initiateAuthentication(deviceId?: string): Promise<AuthChallenge> {
    try {
      const response = await api.post('/biometric-auth/authenticate/initiate', {
        device_id: deviceId || this.getDeviceId(),
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to initiate biometric authentication:', error);
      throw error;
    }
  }

  /**
   * Verify biometric authentication
   */
  async verifyAuthentication(request: VerifyAuthRequest): Promise<AuthResult> {
    try {
      const response = await api.post('/biometric-auth/authenticate/verify', request);

      // Update last used timestamp
      const key = this.registeredKeys.get(request.device_id);
      if (key && response.data.success) {
        key.last_used_at = new Date().toISOString();
        this.registeredKeys.set(request.device_id, key);
      }

      return response.data;
    } catch (error: any) {
      console.error('Failed to verify biometric authentication:', error);
      throw error;
    }
  }

  /**
   * Revoke biometric authentication
   */
  async revokeBiometric(deviceId?: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post('/biometric-auth/revoke', {
        device_id: deviceId || this.getDeviceId(),
      });

      // Remove from cache
      const id = deviceId || this.getDeviceId();
      this.registeredKeys.delete(id);

      return response.data;
    } catch (error: any) {
      console.error('Failed to revoke biometric authentication:', error);
      throw error;
    }
  }

  /**
   * Get registered devices
   */
  async getRegisteredDevices(): Promise<{ devices: BiometricKey[]; total: number }> {
    try {
      const response = await api.get('/biometric-auth/devices');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get registered devices:', error);
      throw error;
    }
  }

  /**
   * Get biometric status for current device
   */
  async getBiometricStatus(deviceId?: string): Promise<BiometricStatus> {
    try {
      const id = deviceId || this.getDeviceId();
      const response = await api.get(`/api/v1/biometric-auth/status?device_id=${id}`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to get biometric status:', error);
      throw error;
    }
  }

  /**
   * Get supported biometric types
   */
  async getSupportedTypes(): Promise<{ biometric_types: BiometricTypeInfo[]; total_types: number }> {
    try {
      const response = await api.get('/biometric-auth/types');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get supported biometric types:', error);
      throw error;
    }
  }

  /**
   * Check if biometric is available on this device
   * This would call native code in production
   */
  async isBiometricAvailable(): Promise<boolean> {
    // In production, this would:
    // - iOS: LAContext.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)
    // - Android: BiometricManager.fromContext(context).canAuthenticate()

    // For now, return true if we can detect a biometric type
    return this.detectAvailableBiometric() !== null;
  }

  /**
   * Prompt user for biometric authentication
   * This would trigger native biometric prompt in production
   */
  async promptBiometric(reason: string = 'Authenticate to continue'): Promise<boolean> {
    // In production, this would:
    // - iOS: LAContext.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, reason)
    // - Android: BiometricPrompt.authenticate(promptInfo)

    // For web testing, simulate prompt
    return new Promise((resolve) => {
      const confirmed = window.confirm(`${reason}\n\n(Simulated biometric prompt - would use Face ID/Touch ID/Fingerprint in production)`);
      resolve(confirmed);
    });
  }
}

// =============================================================================
// Export singleton instance
// =============================================================================

export const biometricAuthService = new BiometricAuthService();

// Export types
export default biometricAuthService;
