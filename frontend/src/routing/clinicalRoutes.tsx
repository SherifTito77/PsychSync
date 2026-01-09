/**
 * Clinical Routes Configuration
 *
 * Special handling for clinical/mental health assessments
 */

import { Route } from 'react-router-dom';
import { Suspense } from 'react';

// Lazy imports (sensitive data - always lazy)
import {
  ClinicalAssessments,
  ClinicalConsent,
  ClinicalAssessment,
  AssessmentRouter,
  ClinicalResults,
  ClinicalEmergency,
  ClinicalDashboard,
  ClinicalSelfHelp,
  QuickAssessmentPage,
} from './lazyImports';

// Layout
import DashboardLayout from '../components/layout/DashboardLayout';
import RequireAuth from '../components/RequireAuth';

const createClinicalRoute = (path: string, element: React.ReactNode) => (
  <Route
    path={path}
    element={
      <RequireAuth>
        <DashboardLayout>
          <Suspense fallback={<div>Loading clinical assessment...</div>}>
            {element}
          </Suspense>
        </DashboardLayout>
      </RequireAuth>
    }
  />
);

export const clinicalRoutes = (
  <>
    {createClinicalRoute('/clinical', <ClinicalAssessments />)}
    {createClinicalRoute('/clinical/consent', <ClinicalConsent />)}
    {createClinicalRoute('/clinical/assessment', <ClinicalAssessment />)}
    {createClinicalRoute('/clinical/router', <AssessmentRouter />)}
    {createClinicalRoute('/clinical/results/:tool', <ClinicalResults />)}
    {createClinicalRoute('/clinical/emergency', <ClinicalEmergency />)}
    {createClinicalRoute('/clinical/dashboard', <ClinicalDashboard />)}
    {createClinicalRoute('/clinical/self-help', <ClinicalSelfHelp />)}
    {createClinicalRoute('/clinical/quick', <QuickAssessmentPage />)}
  </>
);
