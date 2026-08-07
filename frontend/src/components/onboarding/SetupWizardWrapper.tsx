// src/components/onboarding/SetupWizardWrapper.tsx - Wrapper to trigger setup wizard
import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import QuickSetupWizard from './QuickSetupWizard';

const SetupWizardWrapper: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showWizard, setShowWizard] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkWizardStatus = () => {
      // Don't show wizard on auth pages
      const authPages = ['/login', '/register', '/verify-email'];
      if (authPages.includes(location.pathname)) {
        setShowWizard(false);
        setIsLoading(false);
        return;
      }

      // Check if wizard was already completed
      const wizardCompleted = localStorage.getItem('setupWizardCompleted');
      const wizardDate = localStorage.getItem('setupWizardDate');

      if (wizardCompleted) {
        // If completed more than 30 days ago, optionally show again
        if (wizardDate) {
          const daysSinceCompletion = Math.floor(
            (Date.now() - new Date(wizardDate).getTime()) / (1000 * 60 * 60 * 24)
          );

          // Don't show again if completed within last 30 days
          if (daysSinceCompletion < 30) {
            setShowWizard(false);
            setIsLoading(false);
            return;
          }
        }
      }

      // Check if user is new (created within last 24 hours)
      if (user?.created_at) {
        const userAge = Math.floor(
          (Date.now() - new Date(user.created_at).getTime()) / (1000 * 60 * 60)
        );

        if (userAge < 24 && !wizardCompleted) {
          // New user - show wizard
          setShowWizard(true);
          setIsLoading(false);
          return;
        }
      }

      setShowWizard(false);
      setIsLoading(false);
    };

    checkWizardStatus();
  }, [user, location.pathname]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (showWizard) {
    return <QuickSetupWizard />;
  }

  // If wizard shouldn't be shown, render nothing (children will be rendered by Route)
  return null;
};

export default SetupWizardWrapper;
