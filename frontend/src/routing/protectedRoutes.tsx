/**
 * Protected Routes Configuration
 *
 * Routes requiring authentication with DashboardLayout
 */

import { Route } from 'react-router-dom';
import { Suspense } from 'react';

// Direct imports
import Dashboard from '../pages/Dashboard';
import Analytics from '../pages/Analytics';
import Settings from '../pages/Settings';

// Lazy imports
import {
  Profile,
  Teams,
  TeamDetail,
  AssessmentDetail,
  TakeAssessment,
  ResponseResults,
  MyResponses,
  TemplateBrowser,
  TeamOptimizer,
  PredictiveAnalytics,
  ReliabilityValidity,
  EmployeeSafety,
  AssessmentStartPage,
  AssessmentResultsPage,
  MBTIAssessmentPage,
  BigFiveAssessmentPage,
  EnneagramAssessmentPage,
  DISCAssessmentPage,
  SocialStylesPage,
  StrengthsFinderPage,
  PredictiveIndexPage,
  PersonalityAssessments,
  BehavioralAnalysis,
  MentalHealthWellness,
  EmailConnector,
  HRISConnector,
  SecurityDashboard,
} from './lazyImports';

// Layout
import DashboardLayout from '../components/layout/DashboardLayout';
import RequireAuth from '../components/RequireAuth';

const createProtectedRoute = (path: string, element: React.ReactNode) => (
  <Route
    path={path}
    element={
      <RequireAuth>
        <DashboardLayout>
          <Suspense fallback={<div>Loading...</div>}>
            {element}
          </Suspense>
        </DashboardLayout>
      </RequireAuth>
    }
  />
);

export const protectedRoutes = (
  <>
    {createProtectedRoute('/', <Dashboard />)}
    {createProtectedRoute('/dashboard', <Dashboard />)}
    {createProtectedRoute('/profile', <Profile />)}
    {createProtectedRoute('/teams', <Teams />)}
    {createProtectedRoute('/teams/:id', <TeamDetail />)}
    {createProtectedRoute('/assessments', <AssessmentDetail />)}
    {createProtectedRoute('/assessments/take', <TakeAssessment />)}
    {createProtectedRoute('/assessments/results', <ResponseResults />)}
    {createProtectedRoute('/responses', <MyResponses />)}
    {createProtectedRoute('/templates', <TemplateBrowser />)}
    {createProtectedRoute('/optimizer', <TeamOptimizer />)}
    {createProtectedRoute('/analytics', <Analytics />)}
    {createProtectedRoute('/predictive-analytics', <PredictiveAnalytics />)}
    {createProtectedRoute('/reliability-validity', <ReliabilityValidity />)}
    {createProtectedRoute('/employee-safety', <EmployeeSafety />)}
    {createProtectedRoute('/settings', <Settings />)}

    {/* Assessment Start */}
    {createProtectedRoute('/assessments/start/:templateId', <AssessmentStartPage />)}
    {createProtectedRoute('/assessments/results/:responseId', <AssessmentResultsPage />)}

    {/* Personality Assessment Types */}
    {createProtectedRoute('/assessments/mbti', <MBTIAssessmentPage />)}
    {createProtectedRoute('/assessments/big-five', <BigFiveAssessmentPage />)}
    {createProtectedRoute('/assessments/enneagram', <EnneagramAssessmentPage />)}
    {createProtectedRoute('/assessments/disc', <DISCAssessmentPage />)}
    {createProtectedRoute('/assessments/social-styles', <SocialStylesPage />)}
    {createProtectedRoute('/assessments/strengths', <StrengthsFinderPage />)}
    {createProtectedRoute('/assessments/predictive-index', <PredictiveIndexPage />)}

    {/* Service Areas */}
    {createProtectedRoute('/personality', <PersonalityAssessments />)}
    {createProtectedRoute('/behavioral', <BehavioralAnalysis />)}
    {createProtectedRoute('/wellness', <MentalHealthWellness />)}

    {/* Integrations */}
    {createProtectedRoute('/integrations/email', <EmailConnector />)}
    {createProtectedRoute('/integrations/hris', <HRISConnector />)}

    {/* Admin Only */}
    {createProtectedRoute('/admin/security', <SecurityDashboard />)}
  </>
);
