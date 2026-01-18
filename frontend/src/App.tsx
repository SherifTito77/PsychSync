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
import { initializeGlobalErrorHandlers } from './utils/globalErrorHandlers';
// SECURITY: No longer using SecureTokenStorage - tokens in httpOnly cookies
import { pwaManager } from './utils/pwaManager';
import PWAInstaller from './components/PWAInstaller';
import OfflineStatusIndicator from './components/OfflineStatus';
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
const ToxicBehaviorDetection = React.lazy(() => import('./pages/ToxicBehaviorDetection'));
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

// Enhanced Clinical Assessments with advanced features
const EnhancedClinicalAssessments = React.lazy(() => import('./components/clinical/EnhancedClinicalAssessments'));

// Evidence-Based Clinical Screening Tools
const PHQ9Screening = React.lazy(() => import('./components/clinical/PHQ9Screening'));
const GAD7Screening = React.lazy(() => import('./components/clinical/GAD7Screening'));
const CSSRSScreening = React.lazy(() => import('./components/clinical/CSSRSScreening'));
const CrisisResources = React.lazy(() => import('./components/clinical/CrisisResources'));

// Advanced Clinical Assessments
const LSASScreening = React.lazy(() => import('./components/clinical/LSASScreening'));
const EAT26Screening = React.lazy(() => import('./components/clinical/EAT26Screening'));
const YBOCSScreening = React.lazy(() => import('./components/clinical/YBOCSScreening'));
const BDI2Screening = React.lazy(() => import('./components/clinical/BDI2Screening'));
const BAIScreening = React.lazy(() => import('./components/clinical/BAIScreening'));

// Additional Clinical Assessments
const DASS21Screening = React.lazy(() => import('./components/clinical/DASS21Screening'));
const PCL5Screening = React.lazy(() => import('./components/clinical/PCL5Screening'));
const AUDITScreening = React.lazy(() => import('./components/clinical/AUDITScreening'));
const PSS10Screening = React.lazy(() => import('./components/clinical/PSS10Screening'));
const ASRSScreening = React.lazy(() => import('./components/clinical/ASRSScreening'));
const ISIScreening = React.lazy(() => import('./components/clinical/ISIScreening'));
const CBIScreening = React.lazy(() => import('./components/clinical/CBIScreening'));
const MDQScreening = React.lazy(() => import('./components/clinical/MDQScreening'));
const DAST10Screening = React.lazy(() => import('./components/clinical/DAST10Screening'));
const AQ10Screening = React.lazy(() => import('./components/clinical/AQ10Screening'));
const ACEScreening = React.lazy(() => import('./components/clinical/ACEScreening'));
const IESRScreening = React.lazy(() => import('./components/clinical/IESRScreening'));
const IATScreening = React.lazy(() => import('./components/clinical/IATScreening'));

// Telehealth & AI Support
const VideoConsultation = React.lazy(() => import('./components/telehealth/VideoConsultation'));
const TelehealthScheduler = React.lazy(() => import('./components/telehealth/TelehealthScheduler'));
const MentalHealthChatbot = React.lazy(() => import('./components/ai/MentalHealthChatbot'));
const ClinicalAnalyticsDashboard = React.lazy(() => import('./components/analytics/ClinicalAnalyticsDashboard'));
const PopulationHealthDashboard = React.lazy(() => import('./components/analytics/PopulationHealthDashboard'));
const AutomatedAlertsCenter = React.lazy(() => import('./components/clinical/AutomatedAlertsCenter'));

// Security Dashboard (admin only)
const SecurityDashboard = React.lazy(() => import('./components/admin/SecurityDashboard'));

// Health Monitoring Routes
const EnhancedHealthDashboard = React.lazy(() => import('./components/health/EnhancedHealthDashboard'));
const ManagerDashboard = React.lazy(() => import('./components/health/ManagerDashboard'));

// Defensible IP Features
const BurnoutPrevention = React.lazy(() => import('./pages/BurnoutPrevention'));
const MultiFrameworkSynthesis = React.lazy(() => import('./pages/MultiFrameworkSynthesis'));
const AnonymousFeedback = React.lazy(() => import('./pages/AnonymousFeedback'));
const BehavioralAnalytics = React.lazy(() => import('./pages/BehavioralAnalytics'));

// --- Five Distinct Service Areas ---
const PersonalityAssessments = React.lazy(() => import('./pages/PersonalityAssessments'));
const BehavioralAnalysis = React.lazy(() => import('./pages/BehavioralAnalysis'));
const MentalHealthWellness = React.lazy(() => import('./pages/MentalHealthWellness'));
const TestWellnessForm = React.lazy(() => import('./components/clinical/TestWellnessForm'));
const StressAssessmentTest = React.lazy(() => import('./pages/StressAssessmentTest'));
const WellbeingAssessment = React.lazy(() => import('./pages/wellbeing-assessment'));
const EmailConnector = React.lazy(() => import('./pages/EmailConnector'));
const HRISConnector = React.lazy(() => import('./pages/HRISConnector'));

// Legal Rights & Equity Dashboards
const LegalRightsDashboard = React.lazy(() => import('./components/legal/LegalRightsDashboard'));
const EquityDashboard = React.lazy(() => import('./components/equity/EquityDashboard'));

// Overview pages for dropdown sections
const Services = React.lazy(() => import('./pages/Services'));
const Screening = React.lazy(() => import('./pages/Screening'));
const AnalyticsOverview = React.lazy(() => import('./pages/AnalyticsOverview'));
const CorporateIntegrationsPage = React.lazy(() => import('./pages/CorporateIntegrationsPage'));
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
  // Initialize PWA functionality and global error handlers
  useEffect(() => {
    // Initialize global error handlers first
    initializeGlobalErrorHandlers();

    // Then initialize PWA functionality
    pwaManager.initialize().catch((error) => {
      console.error('Failed to initialize PWA:', error);
    });

    // Cleanup on unmount
    return () => {
      pwaManager.cleanup();
    };
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
                <>
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
                              <AnalyticsOverview />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/analytics/dashboard"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Analytics Dashboard..." />}>
                              <Analytics />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/services"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Services..." />}>
                              <Services />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Screening..." />}>
                              <Screening />
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
                    path="/toxic-behavior-detection"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Toxic Behavior Detection..." />}>
                              <ToxicBehaviorDetection />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/burnout-prevention"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Burnout Prevention..." />}>
                              <BurnoutPrevention />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/multi-framework-synthesis"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Multi-Framework Synthesis..." />}>
                              <MultiFrameworkSynthesis />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/anonymous-feedback"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Anonymous Feedback..." />}>
                              <AnonymousFeedback />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/behavioral-analytics"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Behavioral Analytics..." />}>
                              <BehavioralAnalytics />
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

                  {/* Legal Rights & Equity Dashboards */}
                  <Route
                    path="/legal-rights"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Legal Rights Dashboard..." />}>
                              <LegalRightsDashboard />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  <Route
                    path="/equity"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Equity Dashboard..." />}>
                              <EquityDashboard />
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
                    path="/enhanced-assessments"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Enhanced Assessments..." />}>
                              <EnhancedClinicalAssessments />
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

                  {/* Evidence-Based Clinical Screening Routes */}
                  <Route
                    path="/screening/phq9"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading PHQ-9 Screening..." />}>
                              <PHQ9Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/gad7"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading GAD-7 Screening..." />}>
                              <GAD7Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/cssrs"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading C-SSRS Screening..." />}>
                              <CSSRSScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/crisis-resources"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Crisis Resources..." />}>
                              <CrisisResources />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Advanced Clinical Assessment Routes */}
                  <Route
                    path="/screening/lsas"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading LSAS Assessment..." />}>
                              <LSASScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/eat26"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading EAT-26 Assessment..." />}>
                              <EAT26Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/ybocs"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Y-BOCS Assessment..." />}>
                              <YBOCSScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/bdi2"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading BDI-II Assessment..." />}>
                              <BDI2Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/bai"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading BAI Assessment..." />}>
                              <BAIScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Additional Clinical Assessment Routes */}
                  <Route
                    path="/screening/dass21"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading DASS-21 Assessment..." />}>
                              <DASS21Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/pcl5"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading PCL-5 Assessment..." />}>
                              <PCL5Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/audit"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading AUDIT Assessment..." />}>
                              <AUDITScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Additional Clinical Assessment Routes */}
                  <Route
                    path="/screening/pss10"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading PSS-10 Assessment..." />}>
                              <PSS10Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/asrs"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading ASRS Assessment..." />}>
                              <ASRSScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/isi"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading ISI Assessment..." />}>
                              <ISIScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/cbi"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading CBI Assessment..." />}>
                              <CBIScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/mdq"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading MDQ Assessment..." />}>
                              <MDQScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/dast10"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading DAST-10 Assessment..." />}>
                              <DAST10Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/aq10"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading AQ-10 Assessment..." />}>
                              <AQ10Screening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/ace"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading ACE Assessment..." />}>
                              <ACEScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/iesr"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading IES-R Assessment..." />}>
                              <IESRScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/screening/iat"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading IAT Assessment..." />}>
                              <IATScreening />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Telehealth Routes */}
                  <Route
                    path="/telehealth/schedule"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Telehealth Scheduler..." />}>
                              <TelehealthScheduler />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/telehealth/session/:sessionId"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Connecting to video consultation..." />}>
                              <VideoConsultation sessionId="" userRole="patient" />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* AI Support Routes */}
                  <Route
                    path="/support/chat"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading chat support..." />}>
                              <MentalHealthChatbot />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Clinical Analytics Routes */}
                  <Route
                    path="/analytics/clinical"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading clinical analytics..." />}>
                              <ClinicalAnalyticsDashboard />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Population Health Analytics Route */}
                  <Route
                    path="/analytics/population-health"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading population health dashboard..." />}>
                              <PopulationHealthDashboard />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Automated Alerts Center Route */}
                  <Route
                    path="/clinical/alerts-center"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading alerts center..." />}>
                              <AutomatedAlertsCenter />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Health Monitoring Routes */}
                  <Route
                    path="/health"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Health Dashboard..." />}>
                              <EnhancedHealthDashboard />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/health-dashboard"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Health Dashboard..." />}>
                              <EnhancedHealthDashboard />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />
                  <Route
                    path="/team-health"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Team Health Analytics..." />}>
                              <ManagerDashboard />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* Corporate Integrations Routes */}
                  <Route
                    path="/integrations/corporate"
                    element={
                      <SecureRoute requireAuth>
                        <RequireAuth>
                          <DashboardLayout>
                            <Suspense fallback={<SecureFallback message="Loading Corporate Integrations..." />}>
                              <CorporateIntegrationsPage />
                            </Suspense>
                          </DashboardLayout>
                        </RequireAuth>
                      </SecureRoute>
                    }
                  />

                  {/* 404 - Redirect to Landing */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                </>
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
