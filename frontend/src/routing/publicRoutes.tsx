/**
 * Public Routes Configuration
 *
 * Routes accessible without authentication
 */

import { Route } from 'react-router-dom';
import { Suspense } from 'react';

// Direct imports (non-lazy for critical paths)
import Login from '../pages/Login';
import Register from '../pages/Register';
import VerifyEmail from '../pages/VerifyEmail';
import ForgotPassword from '../pages/ForgotPassword';
import ResetPassword from '../pages/ResetPassword';

// Lazy imports
import { TestWellnessForm, StressAssessmentTest, WellbeingAssessment } from './lazyImports';

// Components
import AnonymousFeedbackForm from '../components/AnonymousFeedbackForm';
import AnonymousFeedbackStatus from '../components/AnonymousFeedbackStatus';
import PublicLanding from '../pages/PublicLanding';

// Custom SecureRoute wrapper (if needed)
const SecureRoute = ({ children }: { children: React.ReactNode }) => <>{children}</>;

export const publicRoutes = (
  <>
    {/* Test Routes */}
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

    {/* Authentication Routes */}
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

    {/* Anonymous Feedback Routes */}
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

    {/* Public Landing */}
    <Route path="/public" element={<PublicLanding />} />
  </>
);
