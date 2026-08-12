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
export const SentimentAnalysis = lazy(() => import('../pages/SentimentAnalysis'));
export const ScheduledReports = lazy(() => import('../pages/ScheduledReports'));
export const HRISConnector = lazy(() => import('../pages/HRISConnector'));

// Admin
export const SecurityDashboard = lazy(() => import('../components/admin/SecurityDashboard'));
export const CorporatePsychologyDashboard = lazy(() => import('../components/admin/CorporatePsychologyDashboard'));
export const PerformanceMonitoring = lazy(() => import('../pages/PerformanceMonitoring'));

// Analytics Dashboards
export const PopulationHealthDashboard = lazy(() => import('../components/analytics/PopulationHealthDashboard'));

// Executive & Analytics
export const CEOExecutiveDashboard = lazy(() => import('../pages/CEOExecutiveDashboard'));
export const CEOBurnoutAnalytics = lazy(() => import('../components/executive/CEOBurnoutDashboard'));
export const AdminKPI = lazy(() => import('../pages/AdminKPI'));
export const AdvancedBurnoutAnalytics = lazy(() => import('../pages/AdvancedBurnoutAnalytics'));
export const BurnoutPredictionDashboard = lazy(() => import('../pages/BurnoutPredictionDashboard'));
export const BurnoutPrevention = lazy(() => import('../pages/BurnoutPrevention'));

// Risk Detection & Monitoring
export const RadarDashboard = lazy(() => import('../pages/RadarDashboard'));
export const BehavioralAnalytics = lazy(() => import('../pages/BehavioralAnalytics'));
export const ToxicBehaviorDetection = lazy(() => import('../pages/ToxicBehaviorDetection'));
export const AnomalyDetection = lazy(() => import('../pages/AnomalyDetection'));
export const TeamRiskDashboard = lazy(() => import('../pages/TeamRiskDashboard'));

// Core UI & Operations
export const IconGallery = lazy(() => import('../pages/IconGallery'));
export const ProductOperationsPage = lazy(() => import('../pages/ProductOperationsPage'));

// Clinical Screening
export const Screening = lazy(() => import('../pages/Screening'));
export const ScreeningRouter = lazy(() => import('../pages/ScreeningRouter'));

// HRIS Analytics
export const HRISAnalyticsDashboard = lazy(() => import('../pages/HRISAnalyticsDashboard'));
export const HRISConnectorPage = lazy(() => import('../pages/HRISConnector'));
export const WorkforceDemographics = lazy(() => import('../pages/hris/WorkforceDemographics'));
export const PerformanceAnalytics = lazy(() => import('../pages/hris/PerformanceAnalytics'));
export const TurnoverAnalysis = lazy(() => import('../pages/hris/TurnoverAnalysis'));
export const CompensationAnalysis = lazy(() => import('../pages/hris/CompensationAnalysis'));
export const EngagementAnalytics = lazy(() => import('../pages/hris/EngagementAnalytics'));
export const LearningAndDevelopment = lazy(() => import('../pages/hris/LearningAndDevelopment'));
export const SuccessionPlanning = lazy(() => import('../pages/hris/SuccessionPlanning'));

// Teams Analytics (additional)
export const MultiFrameworkSynthesis = lazy(() => import('../pages/MultiFrameworkSynthesis'));

// Services & Connectors
export const CorporateIntegrationsPage = lazy(() => import('../pages/CorporateIntegrationsPage'));
export const HealthDashboard = lazy(() => import('../components/health/HealthDashboard'));
export const TeamCompositionAnalytics = lazy(() => import('../pages/TeamCompositionAnalytics'));

// AI Chat Support
export const AIChatSupport = lazy(() => import('../pages/AIChatSupport'));

// Behavioral Intelligence
export const BehavioralIntelligenceDashboard = lazy(() => import('../pages/BehavioralIntelligenceDashboard'));

// Organizational Network Analysis
export const OrganizationalNetworkDashboard = lazy(() => import('../pages/OrganizationalNetworkDashboard'));

// Work Systems Integration
export const WorkSystemsIntegration = lazy(() => import('../pages/WorkSystemsIntegration'));

// AI Behavioral Coach
export const AIBehavioralCoach = lazy(() => import('../pages/AIBehavioralCoach'));

// Calendar Integration
export const CalendarIntegration = lazy(() => import('../pages/CalendarIntegration'));

// Communication Analytics
export const CommunicationAnalytics = lazy(() => import('../pages/CommunicationAnalytics'));

// Clinical Components (used as pages)
export const TelehealthScheduler = lazy(() => import('../components/telehealth/TelehealthScheduler'));
export const ClinicalAnalyticsDashboard = lazy(() => import('../components/analytics/ClinicalAnalyticsDashboard'));
export const AutomatedAlertsCenter = lazy(() => import('../components/clinical/AutomatedAlertsCenter'));
export const ClinicalResourcesPage = lazy(() => import('../components/clinical/ClinicalResources'));
export const EnhancedClinicalAssessments = lazy(() => import('../components/clinical/EnhancedClinicalAssessments'));

// Compliance & Legal
export const LegalRightsDashboard = lazy(() => import('../components/legal/LegalRightsDashboard'));
export const EquityDashboard = lazy(() => import('../components/equity/EquityDashboard'));

// Test & Demo Pages
export const TestWellnessForm = lazy(() => import('../components/clinical/TestWellnessForm'));
export const StressAssessmentTest = lazy(() => import('../pages/StressAssessmentTest'));
export const QuickAssessmentPage = lazy(() => import('../pages/QuickAssessment'));
