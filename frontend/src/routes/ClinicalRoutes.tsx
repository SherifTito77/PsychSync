import React from 'react';
import { Routes, Route } from 'react-router-dom';
import ClinicalAssessments from '../pages/ClinicalAssessments';
import ClinicalConsent from '../pages/ClinicalConsent';
import ClinicalAssessment from '../pages/ClinicalAssessment';
import ClinicalResults from '../pages/ClinicalResults';
import ClinicalEmergency from '../pages/ClinicalEmergency';
import ClinicalDashboard from '../pages/ClinicalDashboard';
import DASS21Assessment from '../pages/clinical/DASS21Assessment';
import PCL5Assessment from '../pages/clinical/PCL5Assessment';
import AUDITAssessment from '../pages/clinical/AUDITAssessment';

const ClinicalRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Main Clinical Pages */}
      <Route path="/clinical-assessments" element={<ClinicalAssessments />} />
      <Route path="/clinical" element={<ClinicalAssessments />} />

      {/* Consent Flow */}
      <Route path="/clinical/consent" element={<ClinicalConsent />} />

      {/* Assessment Taking */}
      <Route path="/clinical/assessment/:tool/take" element={<ClinicalAssessment />} />
      <Route path="/clinical/assessment/:tool/start" element={<ClinicalConsent />} />
      <Route path="/clinical/assessment/:tool/complete" element={<ClinicalResults />} />

      {/* Specific Assessment Routes */}
      <Route path="/clinical/dass21" element={<DASS21Assessment />} />
      <Route path="/clinical/pcl5" element={<PCL5Assessment />} />
      <Route path="/clinical/audit" element={<AUDITAssessment />} />

      {/* Emergency Resources */}
      <Route path="/clinical/emergency" element={<ClinicalEmergency />} />

      {/* Admin/Clinician Pages */}
      <Route path="/clinical/dashboard" element={<ClinicalDashboard />} />

      {/* Placeholder routes for future implementation */}
      <Route path="/clinical/alerts" element={<div className="p-8"><h1>Alert Management - Coming Soon</h1></div>} />
      <Route path="/clinical/referrals" element={<div className="p-8"><h1>Referral Management - Coming Soon</h1></div>} />
      <Route path="/clinical/providers" element={<div className="p-8"><h1>Provider Directory - Coming Soon</h1></div>} />
      <Route path="/clinical/safety-plan" element={<div className="p-8"><h1>Safety Plan Creator - Coming Soon</h1></div>} />
      <Route path="/clinical/resources" element={<div className="p-8"><h1>Self-Help Resources - Coming Soon</h1></div>} />
      <Route path="/admin/clinical-analytics" element={<div className="p-8"><h1>Clinical Analytics - Coming Soon</h1></div>} />
    </Routes>
  );
};

export default ClinicalRoutes;
