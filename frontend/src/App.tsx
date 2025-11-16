// frontend/src/App.tsx
import React, { memo, Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext';
import { TeamProvider } from './contexts/TeamContext';
import RequireAuth from './components/RequireAuth';
import DashboardLayout from './components/layout/DashboardLayout';
import { createLazyComponent } from './components/OptimizedComponent';
// --- Core Pages (loaded immediately) ---
import Login from './pages/Login';
import Register from './pages/Register';
// --- Lazy Loaded Pages for Performance ---
const Dashboard = createLazyComponent(() => import('./pages/Dashboard'), <div>Loading Dashboard...</div>, 'Dashboard');
const Profile = createLazyComponent(() => import('./pages/Profile'), <div>Loading Profile...</div>, 'Profile');
const Teams = createLazyComponent(() => import('./pages/Teams'), <div>Loading Teams...</div>, 'Teams');
const TeamDetail = createLazyComponent(() => import('./pages/TeamDetail'), <div>Loading Team Details...</div>, 'TeamDetail');
const Assessments = createLazyComponent(() => import('./pages/Assessments'), <div>Loading Assessments...</div>, 'Assessments');
const AssessmentDetail = createLazyComponent(() => import('./pages/AssessmentDetail'), <div>Loading Assessment Details...</div>, 'AssessmentDetail');
const TakeAssessment = createLazyComponent(() => import('./pages/TakeAssessment'), <div>Loading Assessment...</div>, 'TakeAssessment');
const ResponseResults = createLazyComponent(() => import('./pages/ResponseResults'), <div>Loading Results...</div>, 'ResponseResults');
const MyResponses = createLazyComponent(() => import('./pages/MyResponses'), <div>Loading Responses...</div>, 'MyResponses');
const TemplateBrowser = createLazyComponent(() => import('./pages/TemplateBrowser'), <div>Loading Templates...</div>, 'TemplateBrowser');
const TeamOptimizer = createLazyComponent(() => import('./pages/TeamOptimizer'), <div>Loading Team Optimizer...</div>, 'TeamOptimizer');
const AssessmentStartPage = createLazyComponent(() => import("@/pages/assessments/AssessmentStartPage"), <div>Loading Assessment...</div>, 'AssessmentStartPage');
const AssessmentResultsPage = createLazyComponent(() => import("@/pages/assessments/AssessmentResultsPage"), <div>Loading Results...</div>, 'AssessmentResultsPage');
const AssessmentRoutes = createLazyComponent(() => import("@/routes/AssessmentRoutes"), <div>Loading Assessment Routes...</div>, 'AssessmentRoutes');
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
const App: React.FC = memo(() => {
  return (
    // The <BrowserRouter> wrapper has been removed from here.
    // It now lives exclusively in main.tsx to fix the router error.
    <NotificationProvider>
      <TeamProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password/:token" element={<ResetPassword />} />
          {/* Anonymous Feedback Routes (Public) */}
          <Route path="/anonymous-feedback" element={<AnonymousFeedbackForm />} />
          <Route path="/feedback-status" element={<AnonymousFeedbackStatus />} />
          {/* Protected Routes with Dashboard Layout */}
          <Route path="/dashboard" element={<RequireAuth><DashboardLayout><Dashboard /></DashboardLayout></RequireAuth>} />
          <Route path="/profile" element={<RequireAuth><DashboardLayout><Profile /></DashboardLayout></RequireAuth>} />
          <Route path="/teams" element={<RequireAuth><DashboardLayout><Teams /></DashboardLayout></RequireAuth>} />
          <Route path="/teams/:teamId" element={<RequireAuth><DashboardLayout><TeamDetail /></DashboardLayout></RequireAuth>} />
          <Route path="/assessments" element={<RequireAuth><DashboardLayout><Assessments /></DashboardLayout></RequireAuth>} />
          <Route path="/assessments/:assessmentId" element={<RequireAuth><DashboardLayout><AssessmentDetail /></DashboardLayout></RequireAuth>} />
          <Route path="/assessments/:assessmentId/take" element={<RequireAuth><TakeAssessment /></RequireAuth>} />
          <Route path="/responses/:responseId/results" element={<RequireAuth><DashboardLayout><ResponseResults /></DashboardLayout></RequireAuth>} />
          <Route path="/responses/my-responses" element={<RequireAuth><DashboardLayout><MyResponses /></DashboardLayout></RequireAuth>} />
          <Route path="/analytics" element={<RequireAuth><DashboardLayout><Analytics /></DashboardLayout></RequireAuth>} />
          <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
          <Route path="/templates" element={<RequireAuth><DashboardLayout><TemplateBrowser /></DashboardLayout></RequireAuth>} />
          <Route path="/team-optimizer" element={<RequireAuth><DashboardLayout><TeamOptimizer /></DashboardLayout></RequireAuth>} />
          <Route path="/assessments/:id/start" element={<AssessmentStartPage />} />
          <Route path="/assessments/:id/results" element={<AssessmentResultsPage />} />
          <Route path="/assessments/:id/continue" element={<AssessmentStartPage />} />
          <Route path="/assessments/*" element={<AssessmentRoutes />} />
          {/* Root Landing Page */}
          <Route path="/" element={<PublicLanding />} />
          {/* 404 - Redirect to Landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </TeamProvider>
    </NotificationProvider>
  );
});
App.displayName = 'App';
export default App;