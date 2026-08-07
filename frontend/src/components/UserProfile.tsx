// src/components/UserProfile.tsx
//
// FIXED: Memory leak from async operation without mounted check
// Now uses useAsyncEffect hook for proper cleanup

import React, { useState } from 'react';
import apiClient from '../api/axios';
import { User } from '../types';
import { useAsyncEffect } from '../hooks/useAsyncEffect';

const UserProfile: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // FIXED: Uses useAsyncEffect with automatic cleanup and mounted checks
  useAsyncEffect(async (signal, isMounted) => {
    try {
      // This request will now automatically include the Authorization header
      // and will be cancelled if component unmounts during fetch
      const response = await apiClient.get<User>('/api/v1/auth/me', {
        signal, // Pass AbortSignal to enable cancellation
      });

      // Only update state if component is still mounted
      if (isMounted()) {
        setUser(response.data);
        setLoading(false);
      }
    } catch (err) {
      // Only update state if component is still mounted and error wasn't abort
      if (isMounted() && err instanceof Error && err.name !== 'AbortError') {
        console.error('Failed to fetch user data', err);
        setError('Failed to load user profile.');
        setLoading(false);
      }
      // The response interceptor in axios.ts will handle the 401 redirect
    }
  }, []);
  if (loading) {
    return <div>Loading profile...</div>;
  }
  if (error) {
    return <div>{error}</div>;
  }
  return (
    <div>
      <h2>User Profile</h2>
      {user ? (
        <div>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Full Name:</strong> {user.full_name}</p>
          <p><strong>User ID:</strong> {user.id}</p>
        </div>
      ) : (
        <p>No user data found.</p>
      )}
    </div>
  );
};
export default UserProfile;
