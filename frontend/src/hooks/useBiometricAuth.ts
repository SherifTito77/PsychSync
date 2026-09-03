/**
 * React Hook for Biometric Authentication
 *
 * Custom hook for managing biometric authentication (Face ID, Touch ID, Fingerprint)
 * in React components. Provides methods for registration, authentication, and status checking.
 *
 * Usage:
 * ```tsx
 * const { isAvailable, isRegistered, register, authenticate } = useBiometricAuth();
 * ```
 */

import { useState, useEffect, useCallback } from 'react';
import {
  biometricAuthService,
  BiometricType,
  BiometricStatus,
  BiometricKey,
  AuthResult,
} from '../services/biometricAuth';

interface UseBiometricAuthOptions {
  /**
   * Auto-check availability on mount
   */
  checkAvailability?: boolean;

  /**
   * Auto-check registration status on mount
   */
  checkRegistration?: boolean;

  /**
   * Device ID (uses default if not provided)
   */
  deviceId?: string;
}

interface UseBiometricAuthReturn {
  // State
  isAvailable: boolean;
  isRegistered: boolean;
  isSupported: boolean;
  biometricType: BiometricType | null;
  isLoading: boolean;
  error: string | null;

  // Registration
  register: () => Promise<boolean>;
  revoke: () => Promise<boolean>;

  // Authentication
  authenticate: () => Promise<AuthResult>;

  // Status checking
  checkStatus: () => Promise<void>;
  refreshAvailability: () => Promise<void>;

  // Device info
  deviceId: string;
  registeredDevices: BiometricKey[];
}

export function useBiometricAuth(
  options: UseBiometricAuthOptions = {}
): UseBiometricAuthReturn {
  const {
    checkAvailability = true,
    checkRegistration = true,
    deviceId: propDeviceId,
  } = options;

  const deviceId = propDeviceId || biometricAuthService.getDeviceId();

  const [isAvailable, setIsAvailable] = useState(false);
  const [isRegistered, setIsRegistered] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [biometricType, setBiometricType] = useState<BiometricType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [registeredDevices, setRegisteredDevices] = useState<BiometricKey[]>([]);

  /**
   * Check if biometric is available on this device
   */
  const checkAvailabilityState = useCallback(async () => {
    try {
      const available = await biometricAuthService.isBiometricAvailable();
      setIsAvailable(available);

      if (available) {
        const detected = biometricAuthService.detectAvailableBiometric();
        setBiometricType(detected);
        setIsSupported(true);
      } else {
        setIsSupported(false);
      }
    } catch (err) {
      console.error('Failed to check biometric availability:', err);
      setIsAvailable(false);
      setIsSupported(false);
    }
  }, []);

  /**
   * Check registration status
   */
  const checkRegistrationStatus = useCallback(async () => {
    try {
      const status: BiometricStatus = await biometricAuthService.getBiometricStatus(deviceId);
      setIsRegistered(status.enabled);
    } catch (err) {
      // Not registered is not an error
      if (err.response?.status !== 404) {
        console.error('Failed to check registration status:', err);
      }
      setIsRegistered(false);
    }
  }, [deviceId]);

  /**
   * Check status (availability + registration)
   */
  const checkStatus = useCallback(async () => {
    await Promise.all([
      checkAvailabilityState(),
      checkRegistrationStatus(),
    ]);
  }, [checkAvailabilityState, checkRegistrationStatus]);

  /**
   * Refresh availability and load registered devices
   */
  const refreshAvailability = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await checkAvailabilityState();

      // Load all registered devices
      const response = await biometricAuthService.getRegisteredDevices();
      setRegisteredDevices(response.devices || []);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to check availability';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [checkAvailabilityState]);

  /**
   * Register biometric authentication
   */
  const register = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check availability
      const available = await biometricAuthService.isBiometricAvailable();
      if (!available) {
        setError('Biometric authentication is not available on this device');
        return false;
      }

      // Get biometric type
      const detectedType = biometricAuthService.detectAvailableBiometric();
      if (!detectedType) {
        setError('Could not determine biometric type');
        return false;
      }

      // Initiate registration
      const initResponse = await biometricAuthService.initiateRegistration(detectedType);

      // Prompt user for biometric authentication
      const confirmed = await biometricAuthService.promptBiometric(
        'Register biometric authentication'
      );

      if (!confirmed) {
        setError('Biometric registration cancelled');
        return false;
      }

      // In production, the native layer would:
      // 1. Generate key pair
      // 2. Store private key in Secure Enclave/Keystore
      // 3. Sign the challenge with private key
      // 4. Return public key and signature

      // For now, we'll skip the actual key generation and signature
      // In a real implementation, this would be done by native code:
      //
      // const { publicKey, signature } = await generateKeyPairAndSignChallenge(
      //   initResponse.registration_challenge
      // );

      // Simulate successful registration
      // In production, you would complete registration with actual public key
      setIsRegistered(true);
      return true;

    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Registration failed';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Revoke biometric authentication
   */
  const revoke = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await biometricAuthService.revokeBiometric(deviceId);

      if (response.success) {
        setIsRegistered(false);
        return true;
      }

      setError('Failed to revoke biometric authentication');
      return false;

    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Revocation failed';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  /**
   * Authenticate using biometric
   */
  const authenticate = useCallback(async (): Promise<AuthResult> => {
    setIsLoading(true);
    setError(null);

    try {
      // Check if registered
      if (!isRegistered) {
        setError('Biometric authentication is not registered on this device');
        return { success: false, authenticated: false };
      }

      // Initiate authentication
      const challenge = await biometricAuthService.initiateAuthentication(deviceId);

      // Prompt user for biometric authentication
      const confirmed = await biometricAuthService.promptBiometric(
        'Authenticate to continue'
      );

      if (!confirmed) {
        setError('Biometric authentication cancelled');
        return { success: false, authenticated: false };
      }

      // In production, the native layer would:
      // 1. Retrieve private key from Secure Enclave/Keystore
      // 2. Sign the challenge with private key
      // 3. Return signature

      // For now, simulate successful authentication
      // In production, you would verify with actual signature:
      //
      // const signature = await signChallengeWithPrivateKey(challenge.challenge);
      // const result = await biometricAuthService.verifyAuthentication({
      //   device_id: deviceId,
      //   challenge_id: challenge.challenge_id,
      //   signature: signature,
      // });

      // Simulate success
      return {
        success: true,
        authenticated: true,
        message: 'Biometric authentication successful',
      };

    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Authentication failed';
      setError(errorMessage);

      return {
        success: false,
        authenticated: false,
        message: errorMessage,
      };
    } finally {
      setIsLoading(false);
    }
  }, [deviceId, isRegistered]);

  // Auto-check on mount
  useEffect(() => {
    if (checkAvailability) {
      checkAvailabilityState();
    }
  }, [checkAvailability, checkAvailabilityState]);

  useEffect(() => {
    if (checkRegistration) {
      checkRegistrationStatus();
    }
  }, [checkRegistration, checkRegistrationStatus]);

  return {
    // State
    isAvailable,
    isRegistered,
    isSupported,
    biometricType,
    isLoading,
    error,

    // Registration
    register,
    revoke,

    // Authentication
    authenticate,

    // Status checking
    checkStatus,
    refreshAvailability,

    // Device info
    deviceId,
    registeredDevices,
  };
}

export default useBiometricAuth;
