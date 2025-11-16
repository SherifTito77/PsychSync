// src/components/RequireAuth.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './common/LoadingSpinner';
interface RequireAuthProps {
  children: React.ReactNode;
}
const RequireAuth: React.FC<RequireAuthProps> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    // You can render a loading spinner or a full-page loader here
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }
  if (!user) {
    // If not loading and no user, redirect to the login page
    return <Navigate to="/login" replace />;
  }
  // If there is a user, render the child components
  return <>{children}</>;
};
export default RequireAuth;