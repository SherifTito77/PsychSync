//frontend/src/routes/AssessmentRoutes.tsx
import { Route, Routes } from "react-router-dom";
import AssessmentContinuePage from '@/pages/assessments/types/AssessmentContinuePage'
import MBTIAssessmentPage from '@/pages/assessments/types/MBTIAssessmentPage'
import BigFiveAssessmentPage from '@/pages/assessments/types/BigFiveAssessmentPage'
import EnneagramAssessmentPage from '@/pages/assessments/types/EnneagramAssessmentPage'
import DISCAssessmentPage from '@/pages/assessments/types/DISCAssessmentPage'
import StrengthsFinderPage from '@/pages/assessments/types/StrengthsFinderPage'
import PredictiveIndexPage from '@/pages/assessments/types/PredictiveIndexPage'
import SocialStylesPage from '@/pages/assessments/types/SocialStylesPage'
export default function AssessmentRoutes() {
  return (
    <Routes>
      <Route path="continue" element={<AssessmentContinuePage />} />
      <Route path="mbti/start" element={<MBTIAssessmentPage />} />
      <Route path="mbti" element={<MBTIAssessmentPage />} />
      <Route path="big-five/start" element={<BigFiveAssessmentPage />} />
      <Route path="big-five" element={<BigFiveAssessmentPage />} />
      <Route path="enneagram/start" element={<EnneagramAssessmentPage />} />
      <Route path="enneagram" element={<EnneagramAssessmentPage />} />
      <Route path="disc/start" element={<DISCAssessmentPage />} />
      <Route path="disc" element={<DISCAssessmentPage />} />
      <Route path="strengthsfinder/start" element={<StrengthsFinderPage />} />
      <Route path="strengthsfinder" element={<StrengthsFinderPage />} />
      <Route path="predictive-index/start" element={<PredictiveIndexPage />} />
      <Route path="predictive-index" element={<PredictiveIndexPage />} />
      <Route path="social-styles/start" element={<SocialStylesPage />} />
      <Route path="social-styles" element={<SocialStylesPage />} />
    </Routes>
  );
}
