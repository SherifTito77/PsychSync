// frontend/src/App.tsx
// Enhanced main application component with comprehensive security measures
import React, { memo, Suspense, lazy, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext';
import { TeamProvider } from './contexts/TeamContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssessmentProvider } from './contexts/AssessmentContext';
import RequireAuth from './components/RequireAuth';
import DashboardLayout from './components/layout/DashboardLayout';
import ErrorBoundary from './components/ErrorBoundary';
import { initializeSecurity, SecurityUtils } from './utils/securityUtils';
// SECURITY: No longer using SecureTokenStorage - tokens in httpOnly cookies
import { pwaManager } from './utils/pwaManager';
import PWAInstaller from './components/PWAInstaller';
import OfflineStatusIndicator from './components/OfflineStatus';
import './styles/pwa.css';
// --- Core Pages (loaded immediately) ---
import Login from './pages/Login';
import Register from './pages/Register';
// --- New Onboarding Components ---
import ImprovedLanding from './components/onboarding/ImprovedLanding';
import ProgressiveDashboard from './components/onboarding/ProgressiveDashboard';
import StreamlinedRegister from './components/onboarding/StreamlinedRegister';
import OnboardingNavigation from './components/OnboardingNavigation';
// --- Regular Import for Testing ---
import Dashboard from './pages/Dashboard';
const Profile = React.lazy(() => import('./pages/Profile'));
const Teams = React.lazy(() => import('./pages/Teams'));
const TeamDetail = React.lazy(() => import('./pages/TeamDetail'));
const AssessmentDetail = React.lazy(() => import('./pages/AssessmentDetail'));
const TakeAssessment = React.lazy(() => import('./pages/TakeAssessment'));
const ResponseResults = React.lazy(() => import('./pages/ResponseResults'));
const MyResponses = React.lazy(() => import('./pages/MyResponses'));
const TemplateBrowser = React.lazy(() => import('./pages/TemplateBrowser'));
const TeamOptimizer = React.lazy(() => import('./pages/TeamOptimizer'));
const PredictiveAnalytics = React.lazy(() => import('./pages/PredictiveAnalytics'));
const ReliabilityValidity = React.lazy(() => import('./pages/ReliabilityValidity'));
const EmployeeSafety = React.lazy(() => import('./pages/EmployeeSafety'));
const AssessmentStartPage = React.lazy(() => import('./pages/assessments/AssessmentStartPage'));
const AssessmentResultsPage = React.lazy(() => import('./pages/assessments/AssessmentResultsPage'));

// Specific Assessment Components
const MBTIAssessmentPage = React.lazy(() => import('./pages/assessments/types/MBTIAssessmentPage'));
const BigFiveAssessmentPage = React.lazy(() => import('./pages/assessments/types/BigFiveAssessmentPage'));
const EnneagramAssessmentPage = React.lazy(() => import('./pages/assessments/types/EnneagramAssessmentPage'));
const DISCAssessmentPage = React.lazy(() => import('./pages/assessments/types/DISCAssessmentPage'));
const SocialStylesPage = React.lazy(() => import('./pages/assessments/types/SocialStylesPage'));
const StrengthsFinderPage = React.lazy(() => import('./pages/assessments/types/StrengthsFinderPage'));
const PredictiveIndexPage = React.lazy(() => import('./pages/assessments/types/PredictiveIndexPage'));

// Clinical Assessment Components (loaded on demand due to sensitive nature)
const ClinicalAssessments = React.lazy(() => import('./pages/ClinicalAssessments'));
const ClinicalConsent = React.lazy(() => import('./pages/ClinicalConsent'));
const ClinicalAssessment = React.lazy(() => import('./pages/clinical-assessment'));
const AssessmentRouter = React.lazy(() => import('./pages/clinical/AssessmentRouter'));
const ClinicalResults = React.lazy(() => import('./pages/clinical-results'));
const ClinicalEmergency = React.lazy(() => import('./pages/ClinicalEmergency'));
const ClinicalDashboard = React.lazy(() => import('./pages/ClinicalDashboard'));
const ClinicalSelfHelp = React.lazy(() => import('./pages/ClinicalSelfHelp'));
const QuickAssessmentPage = React.lazy(() => import('./pages/QuickAssessment'));

// Security Dashboard (admin only)
const SecurityDashboard = React.lazy(() => import('./components/admin/SecurityDashboard'));

// --- Five Distinct Service Areas ---
const PersonalityAssessments = React.lazy(() => import('./pages/PersonalityAssessments'));
const BehavioralAnalysis = React.lazy(() => import('./pages/BehavioralAnalysis'));
const MentalHealthWellness = React.lazy(() => import('./pages/MentalHealthWellness'));
const TestWellnessForm = React.lazy(() => import('./components/clinical/TestWellnessForm'));
const StressAssessmentTest = React.lazy(() => import('./pages/StressAssessmentTest'));
const WellbeingAssessment = React.lazy(() => import('./pages/wellbeing-assessment'));
const EmailConnector = React.lazy(() => import('./pages/EmailConnector'));
const HRISConnector = React.lazy(() => import('./pages/HRISConnector'));
// --- Anonymous Feedback Components ---
import AnonymousFeedbackForm from './components/AnonymousFeedbackForm';
import AnonymousFeedbackStatus from './components/AnonymousFeedbackStatus';
import PublicLanding from './pages/PublicLanding';
// --- Actual Components ---
import VerifyEmail from './pages/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

// Security monitoring component
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
      SecurityUtils.storeSecurityMetrics({
        type: 'CSP_VIOLATION',
        timestamp: Date.now(),
        details: {
          blockedURI: event.blockedURI,
          violatedDirective: event.violatedDirective
        }
      });
    };

    // Listen for security policy violations
    document.addEventListener('securitypolicyviolation', handleSecurityViolation);

    // Monitor for suspicious activity
    const activityMonitor = setInterval(() => {
      const report = SecurityUtils.getSecurityReport();
      if (report.securityScore < 70) {
        console.warn('Security score low:', report);
        SecurityUtils.storeSecurityMetrics({
          type: 'SECURITY_SCORE_LOW',
          timestamp: Date.now(),
          score: report.securityScore,
          vulnerabilities: report.vulnerabilities
        });
      }
    }, 30000); // Check every 30 seconds

    return () => {
      document.removeEventListener('securitypolicyviolation', handleSecurityViolation);
      clearInterval(activityMonitor);
    };
  }, []);

  return <>{children}</>;
});

// Route protection wrapper with security checks
const SecureRoute: React.FC<{
  children: React.ReactNode;
  requireAuth?: boolean;
  allowedRoles?: string[];
}> = memo(({ children, requireAuth = false, allowedRoles }) => {
  useEffect(() => {
    // Clear any suspicious data from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const suspiciousParams = ['<script', 'javascript:', 'data:text/html', 'vbscript:'];

    urlParams.forEach((value, key) => {
      if (suspiciousParams.some(param => value.toLowerCase().includes(param))) {
        console.warn('Suspicious URL parameter detected:', key, value);
        // Remove the suspicious parameter
        urlParams.delete(key);
        const newUrl = `${window.location.pathname}${urlParams.toString() ? `?${urlParams.toString()}` : ''}`;
        window.history.replaceState({}, '', newUrl);
      }
    });

    // SECURITY: Token validation handled by backend via httpOnly cookies
    // Frontend only checks if user data exists in localStorage
    const userData = localStorage.getItem('user');
    if (requireAuth && !userData) {
      console.warn('No user session found, redirecting to login');
      window.location.href = '/login';
    }
  }, [requireAuth]);

  if (requireAuth) {
    const userData = localStorage.getItem('user');
    if (!userData) {
      return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
});

// Loading fallback component with security considerations
const SecureFallback: React.FC<{ message?: string }> = memo(({ message = "Loading..." }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
      <p className="text-gray-600">{SecurityUtils.sanitizeHTML(message)}</p>
    </div>
  </div>
));

const App: React.FC = memo(() => {
  // Initialize PWA functionality
  useEffect(() => {
    pwaManager.initialize().catch(console.error);
  }, []);

  // Show navigation helper in development
  const showDevNavigation = process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost';

  return (
    <ErrorBoundary
      enableErrorReporting={true}
      showRetry={true}
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
              {/* Public Routes */}
              <Route
                path="/test-wellness"
                element={
                  <Suspense fallback={<div>Loading test wellness form...</div>}>
                    <TestWellnessForm />
                  </Suspense>
                }
              />
              <Route
                path="/test-stress-assessment"
                element={
                  <Suspense fallback={<div>Loading Stress Assessment...</div>}>
                    <StressAssessmentTest />
                  </Suspense>
                }
              />
              <Route
                path="/test-wellbeing-assessment"
                element={
                  <Suspense fallback={<div>Loading Wellbeing Assessment...</div>}>
                    <WellbeingAssessment />
                  </Suspense>
                }
              />
              <Route
                path="/login"
                element={
                  <SecureRoute>
                    <Login />
                  </SecureRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <SecureRoute>
                    <Register />
                  </SecureRoute>
                }
              />
              <Route
                path="/verify-email"
                element={
                  <SecureRoute>
                    <VerifyEmail />
                  </SecureRoute>
                }
              />
              <Route
                path="/forgot-password"
                element={
                  <SecureRoute>
                    <ForgotPassword />
                  </SecureRoute>
                }
              />
              <Route
                path="/reset-password/:token"
                element={
                  <SecureRoute>
                    <ResetPassword />
                  </SecureRoute>
                }
              />

              {/* Anonymous Feedback Routes (Public) */}
              <Route
                path="/anonymous-feedback"
                element={
                  <SecureRoute>
                    <AnonymousFeedbackForm />
                  </SecureRoute>
                }
              />
              <Route
                path="/feedback-status"
                element={
                  <SecureRoute>
                    <AnonymousFeedbackStatus />
                  </SecureRoute>
                }
              />

              {/* Protected Routes with Dashboard Layout */}
              <Route
                path="/dashboard"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Dashboard />
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Profile..." />}>
                          <Profile />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/teams"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Teams..." />}>
                          <Teams />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/teams/:teamId"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Team Details..." />}>
                          <TeamDetail />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
                <Route
                path="/assessments/:assessmentId"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Assessment Details..." />}>
                          <AssessmentDetail />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/:assessmentId/take"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <Suspense fallback={<SecureFallback message="Loading Assessment..." />}>
                        <TakeAssessment />
                      </Suspense>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/responses/:responseId/results"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Results..." />}>
                          <ResponseResults />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/responses/my-responses"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Responses..." />}>
                          <MyResponses />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/analytics"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Analytics..." />}>
                          <Analytics />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <Suspense fallback={<SecureFallback message="Loading Settings..." />}>
                        <Settings />
                      </Suspense>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/templates"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Templates..." />}>
                          <TemplateBrowser />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/team-optimizer"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Team Optimizer..." />}>
                          <TeamOptimizer />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/predictive-analytics"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Predictive Analytics..." />}>
                          <PredictiveAnalytics />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/reliability-validity"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Reliability & Validity..." />}>
                          <ReliabilityValidity />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/employee-safety"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Employee Safety..." />}>
                          <EmployeeSafety />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/admin/security"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Security Dashboard..." />}>
                          <SecurityDashboard />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
                          {/* Specific Assessment Start Routes */}
              <Route
                path="/assessments/mbti/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading MBTI Assessment..." />}>
                          <MBTIAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/mbti"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading MBTI Assessment..." />}>
                          <MBTIAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/big-five/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Big Five Assessment..." />}>
                          <BigFiveAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/big-five"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Big Five Assessment..." />}>
                          <BigFiveAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/big_five/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Big Five Assessment..." />}>
                          <BigFiveAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/big_five"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Big Five Assessment..." />}>
                          <BigFiveAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/enneagram/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Enneagram Assessment..." />}>
                          <EnneagramAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/enneagram"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Enneagram Assessment..." />}>
                          <EnneagramAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/disc/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading DISC Assessment..." />}>
                          <DISCAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/disc"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading DISC Assessment..." />}>
                          <DISCAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/social/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Social Styles Assessment..." />}>
                          <SocialStylesPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/social"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Social Styles Assessment..." />}>
                          <SocialStylesPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/strengthsfinder/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading StrengthsFinder Assessment..." />}>
                          <StrengthsFinderPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/strengthsfinder"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading StrengthsFinder Assessment..." />}>
                          <StrengthsFinderPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/predictive-index/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Predictive Index Assessment..." />}>
                          <PredictiveIndexPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/predictive-index"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Predictive Index Assessment..." />}>
                          <PredictiveIndexPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/predictive_index/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Predictive Index Assessment..." />}>
                          <PredictiveIndexPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/predictive_index"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Predictive Index Assessment..." />}>
                          <PredictiveIndexPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              {/* Fallback for unknown assessments */}
              <Route
                path="/assessments/:id/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Assessment..." />}>
                          <AssessmentStartPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/:id/results"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Results..." />}>
                          <AssessmentResultsPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/assessments/:id/continue"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Assessment..." />}>
                          <AssessmentStartPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              
              {/* New Onboarding Routes - Value First */}
              <Route
                path="/"
                element={
                  <SecureRoute>
                    <ImprovedLanding onGetStarted={(role, challenge) => {
                      // Handle value preview completion
                      if (role && challenge) {
                        // Store in sessionStorage for onboarding
                        sessionStorage.setItem('onboarding_role', role);
                        sessionStorage.setItem('onboarding_challenge', challenge);
                        window.location.href = '/quick-start';
                      }
                    }} />
                  </SecureRoute>
                }
              />

              <Route
                path="/quick-start"
                element={
                  <SecureRoute>
                    <ProgressiveDashboard
                      initialRole={sessionStorage.getItem('onboarding_role') || ''}
                      initialChallenge={sessionStorage.getItem('onboarding_challenge') || ''}
                    />
                  </SecureRoute>
                }
              />

              {/* Alternative Quick Preview Route */}
              <Route
                path="/preview"
                element={
                  <SecureRoute>
                    <ImprovedLanding onGetStarted={(role, challenge) => {
                      if (role && challenge) {
                        sessionStorage.setItem('onboarding_role', role);
                        sessionStorage.setItem('onboarding_challenge', challenge);
                        window.location.href = '/register-streamlined';
                      }
                    }} />
                  </SecureRoute>
                }
              />

              {/* Streamlined Registration Route */}
              <Route
                path="/register-streamlined"
                element={
                  <SecureRoute>
                    <StreamlinedRegister
                      userRole={sessionStorage.getItem('onboarding_role') || ''}
                      challenge={sessionStorage.getItem('onboarding_challenge') || ''}
                      onSkip={() => window.location.href = '/'}
                    />
                  </SecureRoute>
                }
              />

              {/* Quick Assessment API Route */}
              <Route
                path="/quick-assessment"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Quick Assessment..." />}>
                          <QuickAssessmentPage />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />

              {/* Five Distinct Service Areas */}
              <Route
                path="/personality-assessments"
                element={
                  <DashboardLayout>
                    <Suspense fallback={<div>Loading Personality Assessments...</div>}>
                      <PersonalityAssessments />
                    </Suspense>
                  </DashboardLayout>
                }
              />

              <Route
                path="/behavioral-analysis"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Behavioral Analysis..." />}>
                          <BehavioralAnalysis />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />

              <Route
                path="/mental-health-wellness"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Mental Health & Wellness..." />}>
                          <MentalHealthWellness />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />

              <Route
                path="/email-connector"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Email Connector..." />}>
                          <EmailConnector />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />

              <Route
                path="/hris-connector"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading HRIS Connector..." />}>
                          <HRISConnector />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />

              {/* Clinical Assessment Routes */}
              <Route
                path="/clinical-assessments"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Mental Health Screening..." />}>
                          <ClinicalAssessments />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Mental Health Screening..." />}>
                          <ClinicalAssessments />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/consent"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Consent Form..." />}>
                          <ClinicalConsent />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/assessment/:tool/take"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Assessment..." />}>
                          <AssessmentRouter />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/assessment/:tool/start"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Assessment..." />}>
                          <AssessmentRouter />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/assessment/:tool/complete"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Results..." />}>
                          <ClinicalResults />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/emergency"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Emergency Resources..." />}>
                          <ClinicalEmergency />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/dashboard"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Clinical Dashboard..." />}>
                          <ClinicalDashboard />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />
              <Route
                path="/clinical/self-help"
                element={
                  <SecureRoute requireAuth>
                    <RequireAuth>
                      <DashboardLayout>
                        <Suspense fallback={<SecureFallback message="Loading Self-Help Resources..." />}>
                          <ClinicalSelfHelp />
                        </Suspense>
                      </DashboardLayout>
                    </RequireAuth>
                  </SecureRoute>
                }
              />

              {/* 404 - Redirect to Landing */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            </AssessmentProvider>
          </TeamProvider>
        </NotificationProvider>
      </SecurityMonitor>
    </ThemeProvider>
  </ErrorBoundary>
);  // End of return statement
});  // End of memo function

App.displayName = 'App';
export default App;