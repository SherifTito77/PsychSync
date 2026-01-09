/**
 * Lazy Import Configuration
 *
 * Centralizes all lazy-loaded components for code splitting
 */

import { lazy } from 'react';

// Core Pages
export const Profile = lazy(() => import('../pages/Profile'));
export const Teams = lazy(() => import('../pages/Teams'));
export const TeamDetail = lazy(() => import('../pages/TeamDetail'));
export const AssessmentDetail = lazy(() => import('../pages/AssessmentDetail'));
export const TakeAssessment = lazy(() => import('../pages/TakeAssessment'));
export const ResponseResults = lazy(() => import('../pages/ResponseResults'));
export const MyResponses = lazy(() => import('../pages/MyResponses'));
export const TemplateBrowser = lazy(() => import('../pages/TemplateBrowser'));

// Analytics & Optimization
export const TeamOptimizer = lazy(() => import('../pages/TeamOptimizer'));
export const PredictiveAnalytics = lazy(() => import('../pages/PredictiveAnalytics'));
export const ReliabilityValidity = lazy(() => import('../pages/ReliabilityValidity'));
export const EmployeeSafety = lazy(() => import('../pages/EmployeeSafety'));

// Assessment Pages
export const AssessmentStartPage = lazy(() => import('../pages/assessments/AssessmentStartPage'));
export const AssessmentResultsPage = lazy(() => import('../pages/assessments/AssessmentResultsPage'));

// Personality Assessment Types
export const MBTIAssessmentPage = lazy(() => import('../pages/assessments/types/MBTIAssessmentPage'));
export const BigFiveAssessmentPage = lazy(() => import('../pages/assessments/types/BigFiveAssessmentPage'));
export const EnneagramAssessmentPage = lazy(() => import('../pages/assessments/types/EnneagramAssessmentPage'));
export const DISCAssessmentPage = lazy(() => import('../pages/assessments/types/DISCAssessmentPage'));
export const SocialStylesPage = lazy(() => import('../pages/assessments/types/SocialStylesPage'));
export const StrengthsFinderPage = lazy(() => import('../pages/assessments/types/StrengthsFinderPage'));
export const PredictiveIndexPage = lazy(() => import('../pages/assessments/types/PredictiveIndexPage'));

// Clinical Assessments (lazy for sensitive data)
export const ClinicalAssessments = lazy(() => import('../pages/ClinicalAssessments'));
export const ClinicalConsent = lazy(() => import('../pages/ClinicalConsent'));
export const ClinicalAssessment = lazy(() => import('../pages/clinical-assessment'));
export const AssessmentRouter = lazy(() => import('../pages/clinical/AssessmentRouter'));
export const ClinicalResults = lazy(() => import('../pages/clinical-results'));
export const ClinicalEmergency = lazy(() => import('../pages/ClinicalEmergency'));
export const ClinicalDashboard = lazy(() => import('../pages/ClinicalDashboard'));
export const ClinicalSelfHelp = lazy(() => import('../pages/ClinicalSelfHelp'));

// Service Areas
export const PersonalityAssessments = lazy(() => import('../pages/PersonalityAssessments'));
export const BehavioralAnalysis = lazy(() => import('../pages/BehavioralAnalysis'));
export const MentalHealthWellness = lazy(() => import('../pages/MentalHealthWellness'));
export const WellbeingAssessment = lazy(() => import('../pages/wellbeing-assessment'));

// Integrations
export const EmailConnector = lazy(() => import('../pages/EmailConnector'));
export const HRISConnector = lazy(() => import('../pages/HRISConnector'));

// Admin
export const SecurityDashboard = lazy(() => import('../components/admin/SecurityDashboard'));

// Test & Demo Pages
export const TestWellnessForm = lazy(() => import('../components/clinical/TestWellnessForm'));
export const StressAssessmentTest = lazy(() => import('../pages/StressAssessmentTest'));
export const QuickAssessmentPage = lazy(() => import('../pages/QuickAssessment'));
