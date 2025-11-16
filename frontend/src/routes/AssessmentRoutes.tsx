//frontend/src/routes/AssessmentRoutes.tsx
import { Route, Routes } from "react-router-dom";
import AssessmentContinuePage from '@/pages/assessments/types/AssessmentContinuePage'
import MBTIAssessmentPage from '@/pages/assessments/types/MBTIAssessmentPage'
import BigFiveAssessmentPage from '@/pages/assessments/types/BigFiveAssessmentPage'
import EnneagramAssessmentPage from '@/pages/assessments/types/EnneagramAssessmentPage'
import DISCAssessmentPage from '@/pages/assessments/types/DISCAssessmentPage'
import StrengthsFinderPage from '@/pages/assessments/types/StrengthsFinderPage'
import PredictiveIndexPage from '@/pages/assessments/types/PredictiveIndexPage'
export default function AssessmentRoutes() {
  return (
    <Routes>
      <Route path="continue" element={<AssessmentContinuePage />} />
      <Route path="mbti" element={<MBTIAssessmentPage />} />
      <Route path="bigfive" element={<BigFiveAssessmentPage />} />
      <Route path="enneagram" element={<EnneagramAssessmentPage />} />
      <Route path="disc" element={<DISCAssessmentPage />} />
      <Route path="strengths" element={<StrengthsFinderPage />} />
      <Route path="predictive" element={<PredictiveIndexPage />} />
    </Routes>
  );
}
