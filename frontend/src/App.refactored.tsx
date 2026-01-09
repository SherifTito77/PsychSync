/**
 * App Component - Main Orchestrator
 *
 * Central application routing and provider setup
 *
 * SPLIT from 1,103 lines → ~200 lines (82% reduction)
 */

import { memo, useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Providers
import { NotificationProvider } from './contexts/NotificationContext';
import { TeamProvider } from './contexts/TeamContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssessmentProvider } from './contexts/AssessmentContext';

// Routing Configuration
import { publicRoutes } from './routing/publicRoutes';
import { protectedRoutes } from './routing/protectedRoutes';
import { clinicalRoutes } from './routing/clinicalRoutes';

// Components
import ErrorBoundary from './components/ErrorBoundary';
import { initializeSecurity } from './utils/securityUtils';
import { pwaManager } from './utils/pwaManager';
import PWAInstaller from './components/PWAInstaller';
import OfflineStatusIndicator from './components/OfflineStatus';

// Onboarding Components
import ImprovedLanding from './components/onboarding/ImprovedLanding';
import ProgressiveDashboard from './components/onboarding/ProgressiveDashboard';
import StreamlinedRegister from './components/onboarding/StreamlinedRegister';
import OnboardingNavigation from './components/OnboardingNavigation';

/**
 * Security Monitor Component
 */
const SecurityMonitor: React.FC<{ children: React.ReactNode }> = memo(({ children }) => {
  useEffect(() => {
    // Initialize security measures on app startup
    initializeSecurity();

    // Monitor for security violations
    const handleSecurityViolation = (event: SecurityPolicyViolationEvent) => {
      console.warn('Security Policy Violation:', {
        blockedURI: event.blockedURI,
        violatedDirective: event.violatedDirective,
        originalPolicy: event.originalPolicy,
        documentURI: event.documentURI,
      });

      // Report to monitoring service
      if (typeof window !== 'undefined' && (window as any).reportError) {
        (window as any).reportError(event);
      }
    };

    // Listen for security violations
    if (typeof document !== 'undefined') {
      document.addEventListener('securitypolicyviolation', handleSecurityViolation as EventListener);
    }

    return () => {
      if (typeof document !== 'undefined') {
        document.removeEventListener('securitypolicyviolation', handleSecurityViolation as EventListener);
      }
    };
  }, []);

  return <>{children}</>;
});

SecurityMonitor.displayName = 'SecurityMonitor';

/**
 * Main App Component
 */
const App: React.FC = () => {
  const [showDevNavigation] = useState(true);

  useEffect(() => {
    // Initialize PWA
    pwaManager.register();

    // Cleanup on unmount
    return () => {
      pwaManager.unregister();
    };
  }, []);

  return (
    <ErrorBoundary
      showErrorDetails={true}
      maxRetries={3}
      customMessage="Something went wrong. Our team has been notified."
    >
      <ThemeProvider>
        <SecurityMonitor>
          <NotificationProvider>
            <TeamProvider>
              <AssessmentProvider>
                {showDevNavigation && <OnboardingNavigation />}

                <PWAInstaller
                  onInstallComplete={() => console.log('PWA installed successfully')}
                  onInstallDismissed={() => console.log('PWA install dismissed')}
                />
                <OfflineStatusIndicator showDetailedInfo={true} />

                <Routes>
                  {/* Redirect root to landing */}
                  <Route path="/" element={<Navigate to="/landing" replace />} />

                  {/* Onboarding Flow */}
                  <Route path="/landing" element={<ImprovedLanding />} />
                  <Route path="/onboard/dashboard" element={<ProgressiveDashboard />} />
                  <Route path="/onboard/register" element={<StreamlinedRegister />} />

                  {/* Public Routes */}
                  {publicRoutes}

                  {/* Protected Routes with Dashboard Layout */}
                  {protectedRoutes}

                  {/* Clinical Routes (Protected) */}
                  {clinicalRoutes}

                  {/* Catch-all - redirect to landing */}
                  <Route path="*" element={<Navigate to="/landing" replace />} />
                </Routes>
              </AssessmentProvider>
            </TeamProvider>
          </NotificationProvider>
        </SecurityMonitor>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default memo(App);
