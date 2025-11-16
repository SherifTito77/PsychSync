// src/components/UserProfile.tsx
import React, { useState, useEffect } from 'react';
import apiClient from '../api/axios'; // This import should now work
import { User } from '../types'; // Import the User type
const UserProfile: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // This request will now automatically include the Authorization header
        const response = await apiClient.get<User>('/api/v1/auth/me'); // Specify the expected response type
        setUser(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch user data', err);
        setError('Failed to load user profile.');
        setLoading(false);
        // The response interceptor in axios.ts will handle the 401 redirect
      }
    };
    fetchUserData();
  }, []); // The empty dependency array ensures this runs only once when the component mounts
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