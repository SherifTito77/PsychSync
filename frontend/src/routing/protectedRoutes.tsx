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
  CEOExecutiveDashboard,
  AdminKPI,
  AdvancedBurnoutAnalytics,
  BurnoutPredictionDashboard,
  BurnoutPrevention,
  PopulationHealthDashboard,
  IconGallery,
  ProductOperationsPage,
  RadarDashboard,
  BehavioralAnalytics,
  ToxicBehaviorDetection,
  AnomalyDetection,
  TeamRiskDashboard,
  Screening,
  ScreeningRouter,
  SentimentAnalysis,
  ScheduledReports,
  HRISAnalyticsDashboard,
  HRISConnectorPage,
  WorkforceDemographics,
  PerformanceAnalytics,
  TurnoverAnalysis,
  CompensationAnalysis,
  EngagementAnalytics,
  LearningAndDevelopment,
  SuccessionPlanning,
  CEOBurnoutAnalytics,
  CorporatePsychologyDashboard,
  PerformanceMonitoring,
  ClinicalAssessments,
  ClinicalEmergency,
  ClinicalDashboard,
  ClinicalSelfHelp,
  WellbeingAssessment,
  StressAssessmentTest,
  TelehealthScheduler,
  ClinicalAnalyticsDashboard,
  AutomatedAlertsCenter,
  ClinicalResourcesPage,
  EnhancedClinicalAssessments,
  AIChatSupport,
  CorporateIntegrationsPage,
  HealthDashboard,
  BiometricIntegrations,
  TeamCompositionAnalytics,
  MultiFrameworkSynthesis,
  LegalRightsDashboard,
  EquityDashboard,
  BehavioralIntelligenceDashboard,
  OrganizationalNetworkDashboard,
  CollaborationSurvey,
  CommunityMap,
  NetworkEvolution,
  PersonalityNetwork,
  WorkSystemsIntegration,
  AIBehavioralCoach,
  CalendarIntegration,
  CommunicationAnalytics,
  ExecutiveIntelligence,
  OrganizationalPulse,
  OrganizationalDigitalTwin,
  ManagerIntelligence,
  OKRDashboard,
  PeerRecognition,
  EmailMetadataDashboard,
  SlackMetadataDashboard,
  TeamsMetadataDashboard,
  ComputerUsageDashboard,
  BadgeAccessDashboard,
  PTOPatternsDashboard,
  ActionPlansDashboard,
  Feedback360Dashboard,
  MeetingEffectiveness,
  ExternalBenchmarks,
  OnboardingAnalytics,
  NudgeBotDashboard,
  GitMetadataDashboard,
  ToxicityBurnoutDashboard,
  VideoConferenceMetadataDashboard,
  KnowledgeBaseAnalyticsDashboard,
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
    {createProtectedRoute('/admin/corporate-psychology', <CorporatePsychologyDashboard />)}
    {createProtectedRoute('/admin/performance', <PerformanceMonitoring />)}

    {/* Executive & Analytics */}
    {createProtectedRoute('/executive/burnout', <CEOExecutiveDashboard />)}
    {createProtectedRoute('/ceo-burnout-analytics', <CEOBurnoutAnalytics />)}
    {createProtectedRoute('/analytics/population-health', <PopulationHealthDashboard />)}
    {createProtectedRoute('/analytics/kpi', <AdminKPI />)}
    {createProtectedRoute('/advanced-burnout', <AdvancedBurnoutAnalytics />)}
    {createProtectedRoute('/burnout-prediction', <BurnoutPredictionDashboard />)}
    {createProtectedRoute('/burnout-prevention', <BurnoutPrevention />)}

    {/* Core UI & Operations */}
    {createProtectedRoute('/icon-gallery', <IconGallery />)}
    {createProtectedRoute('/product-operations', <ProductOperationsPage />)}

    {/* Risk Detection & Monitoring */}
    {createProtectedRoute('/radar', <RadarDashboard />)}
    {createProtectedRoute('/behavioral-analytics', <BehavioralAnalytics />)}
    {createProtectedRoute('/toxic-behavior-detection', <ToxicBehaviorDetection />)}
    {createProtectedRoute('/anomaly-detection', <AnomalyDetection />)}
    {createProtectedRoute('/team-dashboard', <TeamRiskDashboard />)}

    {/* Email Monitoring */}
    {createProtectedRoute('/email-connector', <EmailConnector />)}
    {createProtectedRoute('/email-metadata', <EmailMetadataDashboard />)}
    {createProtectedRoute('/slack-metadata', <SlackMetadataDashboard />)}
    {createProtectedRoute('/teams-metadata', <TeamsMetadataDashboard />)}
    {createProtectedRoute('/computer-usage', <ComputerUsageDashboard />)}
    {createProtectedRoute('/badge-access', <BadgeAccessDashboard />)}
    {createProtectedRoute('/pto-patterns', <PTOPatternsDashboard />)}
    {createProtectedRoute('/git-metadata', <GitMetadataDashboard />)}
    {createProtectedRoute('/sentiment-analysis', <SentimentAnalysis />)}
    {createProtectedRoute('/scheduled-reports', <ScheduledReports />)}

    {/* HRIS Analytics */}
    {createProtectedRoute('/hris-analytics', <HRISAnalyticsDashboard />)}
    {createProtectedRoute('/hris-connector', <HRISConnectorPage />)}
    {createProtectedRoute('/hris/demographics', <WorkforceDemographics />)}
    {createProtectedRoute('/hris/performance', <PerformanceAnalytics />)}
    {createProtectedRoute('/hris/turnover', <TurnoverAnalysis />)}
    {createProtectedRoute('/hris/compensation', <CompensationAnalysis />)}
    {createProtectedRoute('/hris/engagement', <EngagementAnalytics />)}
    {createProtectedRoute('/hris/learning', <LearningAndDevelopment />)}
    {createProtectedRoute('/hris/succession', <SuccessionPlanning />)}

    {/* Teams Analytics (sidebar alias routes) */}
    {createProtectedRoute('/team-optimizer', <TeamOptimizer />)}
    {createProtectedRoute('/team-composition', <TeamCompositionAnalytics />)}
    {createProtectedRoute('/multi-framework-synthesis', <MultiFrameworkSynthesis />)}
    {createProtectedRoute('/analytics/dashboard', <Analytics />)}

    {/* Services & Connectors */}
    {createProtectedRoute('/integrations/corporate', <CorporateIntegrationsPage />)}
    {createProtectedRoute('/health', <HealthDashboard />)}
    {createProtectedRoute('/biometric/integrations', <BiometricIntegrations />)}
    {createProtectedRoute('/biometric/metrics', <BiometricIntegrations />)}
    {createProtectedRoute('/biometric/sleep', <BiometricIntegrations />)}
    {createProtectedRoute('/biometric/stress', <BiometricIntegrations />)}
    {createProtectedRoute('/team-health', <TeamCompositionAnalytics />)}
    {createProtectedRoute('/behavioral-analysis', <BehavioralAnalysis />)}

    {/* Clinical Services */}
    {createProtectedRoute('/support/chat', <AIChatSupport />)}
    {createProtectedRoute('/telehealth/schedule', <TelehealthScheduler />)}
    {createProtectedRoute('/analytics/clinical', <ClinicalAnalyticsDashboard />)}
    {createProtectedRoute('/clinical/alerts-center', <AutomatedAlertsCenter />)}
    {createProtectedRoute('/clinical-assessments', <ClinicalAssessments />)}
    {createProtectedRoute('/clinical/assessment/wellbeing/take', <WellbeingAssessment />)}
    {createProtectedRoute('/clinical/assessment/stress/take', <StressAssessmentTest />)}
    {createProtectedRoute('/clinical/self-help', <ClinicalSelfHelp />)}
    {createProtectedRoute('/clinical/resources', <ClinicalResourcesPage />)}
    {createProtectedRoute('/clinical/emergency', <ClinicalEmergency />)}
    {createProtectedRoute('/clinical/dashboard', <ClinicalDashboard />)}
    {createProtectedRoute('/enhanced-assessments', <EnhancedClinicalAssessments />)}
    {createProtectedRoute('/mental-health-wellness', <MentalHealthWellness />)}
    {createProtectedRoute('/personality-assessments', <PersonalityAssessments />)}

    {/* Clinical Screening */}
    {createProtectedRoute('/screening', <Screening />)}
    {createProtectedRoute('/screening/:toolId', <ScreeningRouter />)}

    {/* Behavioral Intelligence */}
    {createProtectedRoute('/behavioral-intelligence', <BehavioralIntelligenceDashboard />)}
    {createProtectedRoute('/organizational-network', <OrganizationalNetworkDashboard />)}
    {createProtectedRoute('/collaboration-survey', <CollaborationSurvey />)}
    {createProtectedRoute('/community-map', <CommunityMap />)}
    {createProtectedRoute('/network-evolution', <NetworkEvolution />)}
    {createProtectedRoute('/personality-network', <PersonalityNetwork />)}
    {createProtectedRoute('/work-systems', <WorkSystemsIntegration />)}
    {createProtectedRoute('/ai-coach', <AIBehavioralCoach />)}
    {createProtectedRoute('/calendar-intelligence', <CalendarIntegration />)}
    {createProtectedRoute('/communication-analytics', <CommunicationAnalytics />)}

    {/* Executive Intelligence */}
    {createProtectedRoute('/executive-intelligence', <ExecutiveIntelligence />)}

    {/* Organizational Pulse */}
    {createProtectedRoute('/organizational-pulse', <OrganizationalPulse />)}

    {/* Organizational Digital Twin */}
    {createProtectedRoute('/org-digital-twin', <OrganizationalDigitalTwin />)}

    {/* Manager Intelligence */}
    {createProtectedRoute('/manager-intelligence', <ManagerIntelligence />)}

    {/* OKR & Recognition */}
    {createProtectedRoute('/okr', <OKRDashboard />)}
    {createProtectedRoute('/recognition', <PeerRecognition />)}

    {/* Corporate Enhancement Layer */}
    {createProtectedRoute('/action-plans', <ActionPlansDashboard />)}
    {createProtectedRoute('/feedback-360', <Feedback360Dashboard />)}
    {createProtectedRoute('/meeting-effectiveness', <MeetingEffectiveness />)}
    {createProtectedRoute('/external-benchmarks', <ExternalBenchmarks />)}
    {createProtectedRoute('/onboarding-analytics', <OnboardingAnalytics />)}
    {createProtectedRoute('/nudge-bot', <NudgeBotDashboard />)}

    {/* Video Conferencing & Knowledge Base Analytics */}
    {createProtectedRoute('/video-conference-metadata', <VideoConferenceMetadataDashboard />)}
    {createProtectedRoute('/knowledge-base-metadata', <KnowledgeBaseAnalyticsDashboard />)}

    {/* Toxicity & Burnout Intelligence */}
    {createProtectedRoute('/toxicity-burnout', <ToxicityBurnoutDashboard />)}

    {/* Compliance & Legal */}
    {createProtectedRoute('/legal-rights', <LegalRightsDashboard />)}
    {createProtectedRoute('/equity', <EquityDashboard />)}
  </>
);
