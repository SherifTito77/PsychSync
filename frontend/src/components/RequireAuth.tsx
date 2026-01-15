// src/components/RequireAuth.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './common/LoadingSpinner';
interface RequireAuthProps {
  children: React.ReactNode;
}
const RequireAuth: React.FC<RequireAuthProps> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

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
    // Save the intended destination in state
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  // If there is a user, render the child components
  return <>{children}</>;
};
export default RequireAuth;