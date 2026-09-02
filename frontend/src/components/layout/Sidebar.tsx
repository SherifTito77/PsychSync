// // // src/components/layout/Sidebar.tsx - Sidebar Component with Role-Based Navigation
// src/components/layout/Sidebar.tsx - Fixed with React Router
import React, { useState, memo, useMemo } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useRoleNavigation } from '../../hooks/useRoleNavigation';

interface MenuItem {
  name: string;
  path: string;
  icon: string;
  requiredRoles?: string[];
}

interface SubMenuItem {
  name: string;
  path: string;
  icon: string;
  description?: string;
}

interface MenuSection {
  name: string;
  path: string;
  icon: string;
  items?: SubMenuItem[];
  requiredRoles?: string[]; // Add role requirements
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}
// ⚡️ PERFORMANCE: Memoized to prevent unnecessary re-renders
const Sidebar = memo(({ isOpen, onToggle }: SidebarProps) => {
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isHR, isAdmin, filterItems } = useRoleNavigation();

  const userRole = user?.role || 'user';

  // Core navigation items - Main navigation always visible
  const coreItems: MenuItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Product Operations', path: '/product-operations', icon: '📈' },
    { name: 'Icon Gallery', path: '/icon-gallery', icon: '🎨' },
    { name: 'Settings', path: '/settings', icon: '⚙️' }
  ];

  // Filter core items based on role
  const visibleCoreItems = useMemo(() => {
    return coreItems.filter(item => {
      // All users can see core items
      return true;
    });
  }, [userRole]);

  // Executive & Business Analytics Section
  const executiveAnalyticsSection: MenuSection = {
    name: 'Executive Analytics',
    path: '/executive-analytics',
    icon: '📊',
    items: [
      {
        name: 'CEO Executive Dashboard',
        path: '/executive/burnout',
        icon: '🎯',
        description: 'Executive burnout risk, department analytics, 90-day trends'
      },
      {
        name: 'KPI Dashboard',
        path: '/analytics/kpi',
        icon: '📈',
        description: 'Business KPIs, performance metrics, goal tracking'
      },
      {
        name: 'Predictive Analytics',
        path: '/predictive-analytics',
        icon: '🔮',
        description: 'AI predictions, forecasting, risk models'
      },
      {
        name: 'Population Health',
        path: '/analytics/population-health',
        icon: '🏥',
        description: 'Population-wide health metrics, epidemiological data'
      },
      {
        name: 'Executive Intelligence',
        path: '/executive-intelligence',
        icon: '🧠',
        description: 'BI + ONA + HRIS integration into team narratives & trend alerts'
      },
      {
        name: 'Organizational Pulse',
        path: '/organizational-pulse',
        icon: '💓',
        description: 'Predictive intelligence — 7 key questions answered before you ask them'
      },
      {
        name: 'Org Digital Twin',
        path: '/org-digital-twin',
        icon: '🏗',
        description: 'Living organizational model with 7 dimensions & what-if simulation'
      },
      {
        name: 'OKR Dashboard',
        path: '/okr',
        icon: '🎯',
        description: 'Objectives & Key Results tracking with health indicators'
      },
      {
        name: 'External Benchmarks',
        path: '/external-benchmarks',
        icon: '📊',
        description: 'Compare against anonymized industry peers with differential privacy'
      }
    ]
  };

  // ⚡ EARLY WARNING & RISK SECTION - Critical Features (Promoted to Top)
  const earlyWarningSection: MenuSection = {
    name: 'Early Warning & Risk',
    path: '/early-warning',
    icon: '⚡',
    requiredRoles: ['hr', 'admin', 'super_admin', 'manager'], // HR/Manager only
    items: [
      { name: 'Organizational Pulse', path: '/organizational-pulse', icon: '💓', description: 'Predictive intelligence — 7 key questions answered before you ask them' },
      { name: 'Manager Intelligence', path: '/manager-intelligence', icon: '👔', description: 'Your team pulse, member risks, action items & coaching prompts' },
      { name: 'Behavioral Intelligence', path: '/behavioral-intelligence', icon: '🧠', description: 'Team Health, Collaboration, Psych Safety, Friction & Change Readiness scores' },
      { name: 'Org Network Analysis', path: '/organizational-network', icon: '🕸', description: 'Hidden influencers, isolated employees, cross-team bridges & manager dependency' },
      { name: 'Radar Dashboard', path: '/radar', icon: '📡', description: '360° organizational health monitoring system' },
      { name: 'Advanced Burnout Analytics', path: '/advanced-burnout', icon: '🎯', description: '14-day early warning with Z-scores & trend detection' },
      { name: 'Burnout Prevention', path: '/burnout-prevention', icon: '🔥', description: '7-90 day burnout prediction & prevention' },
      { name: 'Behavioral Analytics', path: '/behavioral-analytics', icon: '🧠', description: 'Communication patterns & sentiment analysis' },
      { name: 'Toxic Behavior Detection', path: '/toxic-behavior-detection', icon: '🛡️', description: 'Harassment & toxic pattern monitoring' },
      { name: 'Employee Safety', path: '/employee-safety', icon: '⚠️', description: 'Workplace safety & incident tracking' },
      { name: 'Anomaly Detection', path: '/anomaly-detection', icon: '🚨', description: 'ML-powered pattern detection & alerts' },
      { name: 'Team Risk Dashboard', path: '/team-dashboard', icon: '👥', description: 'Team-level risk indicators & heatmap' },
      { name: 'Burnout Prediction', path: '/burnout-prediction', icon: '🔮', description: 'AI-powered risk prediction & analytics' },
      { name: 'Action Plans', path: '/action-plans', icon: '📋', description: 'Track interventions from Pulse, Manager Intelligence & manual creation' },
      { name: 'Onboarding Analytics', path: '/onboarding-analytics', icon: '👋', description: 'New hire health composite from existing signals' },
      { name: 'Toxicity & Burnout', path: '/toxicity-burnout', icon: '☣️', description: 'Passive detection of toxic patterns & burnout from infrastructure metadata' }
    ]
  };

  // Metadata Intelligence Section
  const metadataIntelligenceSection: MenuSection = {
    name: 'Metadata Intelligence',
    path: '/metadata-intelligence',
    icon: '🔍',
    requiredRoles: ['hr', 'admin', 'super_admin', 'manager'],
    items: [
      { name: 'Email Metadata', path: '/email-metadata', icon: '📧', description: 'Behavioral signals from email metadata — timestamps, volumes, response times' },
      { name: 'Slack Metadata', path: '/slack-metadata', icon: '💬', description: 'Channel breadth, DM ratio, context switching, presence patterns' },
      { name: 'Teams Metadata', path: '/teams-metadata', icon: '🟣', description: 'Chat counts, call duration, meeting fatigue, presence timeline' },
      { name: 'Calendar Analytics', path: '/calendar-intelligence', icon: '📅', description: 'Meeting load, focus time, after-hours meetings, fragmentation score' },
      { name: 'Computer Usage', path: '/computer-usage', icon: '🖥', description: 'Activity levels, session duration, break frequency, idle patterns' },
      { name: 'Badge Access', path: '/badge-access', icon: '🏢', description: 'Office entry/exit times, long days, weekend presence, hours trend' },
      { name: 'PTO Patterns', path: '/pto-patterns', icon: '🏖', description: 'Vacation avoidance, sick day trends, recovery deficit — strongest early predictor' },
      { name: 'Git/GitHub', path: '/git-metadata', icon: '🐙', description: 'Commit patterns, PR lifecycle, review bottlenecks, after-hours coding' },
      { name: 'Video Conferencing', path: '/video-conference-metadata', icon: '📹', description: 'Camera engagement, meeting fatigue, back-to-back density, join latency' },
      { name: 'Knowledge Base', path: '/knowledge-base-metadata', icon: '📚', description: 'Doc creation, contributor concentration, stale content, knowledge sharing' },
      { name: 'Email Connector', path: '/email-connector', icon: '🔗', description: 'Email integration services' },
      { name: 'Scheduled Reports', path: '/scheduled-reports', icon: '📅', description: 'Automated weekly/monthly email reports' },
      { name: 'Anomaly Detection', path: '/anomaly-detection', icon: '🚨', description: 'ML-powered pattern detection & alerts' }
    ]
  };

  // HRIS Analytics Section
  const hrisSection: MenuSection = {
    name: 'HRIS Analytics',
    path: '/hris-analytics',
    icon: '📊',
    requiredRoles: ['hr', 'admin', 'super_admin', 'manager'], // HR/Manager only
    items: [
      {
        name: 'Analytics Dashboard',
        path: '/hris-analytics',
        icon: '📈',
        description: '7 charts, KPIs, custom reports with real-time updates'
      },
      {
        name: 'HRIS Connector',
        path: '/hris-connector',
        icon: '🔗',
        description: 'Connect Workday, BambooHR, ADP & 30+ HR systems'
      },
      {
        name: 'Workforce Demographics',
        path: '/hris/demographics',
        icon: '👥',
        description: 'Employee composition, diversity analysis, age distribution & tenure trends'
      },
      {
        name: 'Performance Analytics',
        path: '/hris/performance',
        icon: '⭐',
        description: 'Performance reviews, goals completion, top performers & trends'
      },
      {
        name: 'Turnover Analysis',
        path: '/hris/turnover',
        icon: '📉',
        description: 'Turnover patterns, retention risks, exit reasons & predictions'
      },
      {
        name: 'Compensation Analysis',
        path: '/hris/compensation',
        icon: '💰',
        description: 'Pay equity, salary benchmarks, compensation gaps & total rewards'
      },
      {
        name: 'Engagement Analytics',
        path: '/hris/engagement',
        icon: '😊',
        description: 'Employee satisfaction, engagement scores, sentiment & workplace pulse'
      },
      {
        name: 'Learning & Development',
        path: '/hris/learning',
        icon: '📚',
        description: 'Training effectiveness, skill gaps, certifications & development programs'
      },
      {
        name: 'Succession Planning',
        path: '/hris/succession',
        icon: '🎯',
        description: 'Leadership pipeline, readiness scores, key positions & successors'
      }
    ]
  };

  // Admin Section
  const adminSection: MenuSection = {
    name: 'Admin & Executive',
    path: '/admin',
    icon: '🔐',
    requiredRoles: ['admin', 'super_admin'],
    items: [
      {
        name: 'CEO Burnout Analytics',
        path: '/ceo-burnout-analytics',
        icon: '📊',
        description: 'Organization-level burnout risk, ROI tracking & cost-benefit analysis'
      },
      {
        name: 'Advanced Burnout Analytics',
        path: '/advanced-burnout',
        icon: '🎯',
        description: '14-day early warning with Z-scores, cognitive load & fatigue tracking'
      },
      {
        name: 'Corporate Psychology',
        path: '/admin/corporate-psychology',
        icon: '🧠',
        description: 'System-level organizational psychology intelligence for executives'
      },
      {
        name: 'Security Dashboard',
        path: '/admin/security',
        icon: '🛡️',
        description: 'Security monitoring and threat intelligence'
      },
      {
        name: 'Performance Monitoring',
        path: '/admin/performance',
        icon: '⚡',  // Options: 📊 📈 ⚡ 🎯 🔧 🖥️ 📉
        description: 'Real-time system performance metrics and health'
      }
    ]
  };

  // Clinical Screening Section - Assessment Tools Only
  const clinicalSection: MenuSection = {
    name: 'Clinical Screening',
    path: '/screening',
    icon: '🏥',
    items: [
      {
        name: 'Depression Screening (PHQ-9)',
        path: '/screening/phq9',
        icon: '💙',
        description: 'Evidence-based depression screening (α=0.89)'
      },
      {
        name: 'Anxiety Screening (GAD-7)',
        path: '/screening/gad7',
        icon: '💛',
        description: 'Comprehensive anxiety assessment (α=0.92)'
      },
      {
        name: 'Suicide Risk (C-SSRS)',
        path: '/screening/cssrs',
        icon: '🚨',
        description: 'Columbia-Suicide Severity Rating Scale (AUC=0.83)'
      },
      {
        name: 'Crisis Resources',
        path: '/screening/crisis-resources',
        icon: '🆘',
        description: '24/7 crisis support and emergency resources'
      },
      {
        name: 'Social Anxiety (LSAS)',
        path: '/screening/lsas',
        icon: '😰',
        description: 'Liebowitz Social Anxiety Scale (α=0.95)'
      },
      {
        name: 'Eating Attitudes (EAT-26)',
        path: '/screening/eat26',
        icon: '🍎',
        description: 'Eating disorder screening (α=0.90)'
      },
      {
        name: 'OCD Severity (Y-BOCS)',
        path: '/screening/ybocs',
        icon: '🔄',
        description: 'Yale-Brown Obsessive Compulsive Scale (α=0.90)'
      },
      {
        name: 'Depression (BDI-II)',
        path: '/screening/bdi2',
        icon: '😢',
        description: 'Beck Depression Inventory-II (α=0.91)'
      },
      {
        name: 'Anxiety (BAI)',
        path: '/screening/bai',
        icon: '😰',
        description: 'Beck Anxiety Inventory (α=0.92)'
      },
      {
        name: 'DASS-21 (Depression/Anxiety/Stress)',
        path: '/screening/dass21',
        icon: '📊',
        description: '21-item multi-symptom assessment (α=0.84-0.91)'
      },
      {
        name: 'PCL-5 (PTSD Checklist)',
        path: '/screening/pcl5',
        icon: '🎯',
        description: 'PTSD screening for DSM-5 (α=0.94)'
      },
      {
        name: 'AUDIT (Alcohol Use)',
        path: '/screening/audit',
        icon: '🍺',
        description: 'Alcohol Use Disorders Identification Test (α=0.92)'
      },
      {
        name: 'PSS-10 (Perceived Stress)',
        path: '/screening/pss10',
        icon: '😰',
        description: 'Perceived Stress Scale (α=0.78)'
      },
      {
        name: 'ISI (Insomnia Severity)',
        path: '/screening/isi',
        icon: '😴',
        description: 'Insomnia Severity Index (α=0.91)'
      },
      {
        name: 'CBI (Burnout Inventory)',
        path: '/screening/cbi',
        icon: '🔥',
        description: 'Copenhagen Burnout Inventory (α=0.87)'
      },
      {
        name: 'MDQ (Mood Disorder)',
        path: '/screening/mdq',
        icon: '🌈',
        description: 'Bipolar disorder screening (Sens=0.73, Spec=0.90)'
      },
      {
        name: 'DAST-10 (Drug Abuse)',
        path: '/screening/dast10',
        icon: '💊',
        description: 'Drug Abuse Screening Test (α=0.92)'
      },
      {
        name: 'AQ-10 (Autism Spectrum)',
        path: '/screening/aq10',
        icon: '🧩',
        description: 'Autism Spectrum Quotient (Sens=0.88, Spec=0.91)'
      },
      {
        name: 'ACE (Adverse Childhood Experiences)',
        path: '/screening/ace',
        icon: '👶',
        description: 'Childhood trauma screening (10 items)'
      },
      {
        name: 'IES-R (Impact of Event)',
        path: '/screening/iesr',
        icon: '💔',
        description: 'PTSD symptom assessment (α=0.96)'
      },
      {
        name: 'IAT (Internet Addiction)',
        path: '/screening/iat',
        icon: '📱',
        description: 'Internet Addiction Test (α=0.90)'
      },
      {
        name: 'ADHD Screening (ASRS)',
        path: '/screening/asrs',
        icon: '⚡',
        description: 'Adult ADHD Self-Report Scale v1.1 (Sens=68.7%, Spec=72.1%)'
      }
    ]
  };

  // Clinical Services & Resources Section
  const telehealthSection: MenuSection = {
    name: 'Clinical Services & Resources',
    path: '/telehealth/schedule',
    icon: '🏥',
    items: [
      {
        name: 'Telehealth - Schedule Consultation',
        path: '/telehealth/schedule',
        icon: '📹',
        description: 'Schedule video consultation with clinician'
      },
      {
        name: 'AI Chat Support',
        path: '/support/chat',
        icon: '🤖',
        description: '24/7 AI-powered mental health support'
      },
      {
        name: 'AI Behavioral Coach',
        path: '/ai-coach',
        icon: '🧬',
        description: 'Personalized coaching, Digital Twin & team fit simulation'
      },
      {
        name: 'Clinical Analytics',
        path: '/analytics/clinical',
        icon: '📊',
        description: 'Population health insights dashboard'
      },
      {
        name: 'Population Health',
        path: '/analytics/population-health',
        icon: '🏥',
        description: 'Population metrics and high-risk identification'
      },
      {
        name: 'Alerts Center',
        path: '/clinical/alerts-center',
        icon: '🚨',
        description: 'Manage clinical alerts and notifications'
      },
      {
        name: 'Screening Home',
        path: '/clinical-assessments',
        icon: '🏠',
        description: 'Main mental health assessment portal'
      },
      {
        name: 'Wellbeing Check',
        path: '/clinical/assessment/wellbeing/take',
        icon: '🌟',
        description: 'Overall wellbeing assessment'
      },
      {
        name: 'Stress Assessment',
        path: '/clinical/assessment/stress/take',
        icon: '😰',
        description: 'Perceived stress level evaluation'
      },
      {
        name: 'Self-Help Library',
        path: '/clinical/self-help',
        icon: '📚',
        description: 'Comprehensive coping strategies'
      },
      {
        name: 'Clinical Resources',
        path: '/clinical/resources',
        icon: '🏥',
        description: 'Therapists, support groups & mental health tools'
      },
      {
        name: 'Emergency Resources',
        path: '/clinical/emergency',
        icon: '🚨',
        description: '24/7 crisis support hotline'
      },
      {
        name: 'Clinical Dashboard',
        path: '/clinical/dashboard',
        icon: '👨‍⚕️',
        description: 'Professional tools for clinicians'
      },
      {
        name: '✨ Enhanced Assessments',
        path: '/enhanced-assessments',
        icon: '⭐',
        description: 'Advanced assessments with dark mode, animations & offline support'
      },
      {
        name: 'Mental Health',
        path: '/mental-health-wellness',
        icon: '🧘',
        description: 'Mental health and wellness resources'
      },
      {
        name: 'Personality Assessments',
        path: '/personality-assessments',
        icon: '🧠',
        description: 'Personality tests and profiles'
      }
    ]
  };

  // Service Areas Section - Collapsible
  const servicesSection: MenuSection = {
    name: 'Services & Connectors',
    path: '/services',
    icon: '🔧',
    requiredRoles: ['hr', 'admin', 'super_admin', 'manager'], // HR/Manager only
    items: [
      {
        name: 'Corporate Integrations',
        path: '/integrations/corporate',
        icon: '🔗',
        description: 'Connect 30+ data sources including Slack, HRIS, and more'
      },
      {
        name: 'Work Systems (Jira/DevOps)',
        path: '/work-systems',
        icon: '🔌',
        description: 'Jira, Azure DevOps, Asana, Monday.com integration & behavioral signals'
      },
      {
        name: 'Calendar Intelligence',
        path: '/calendar-intelligence',
        icon: '📅',
        description: 'Meeting load, focus time, after-hours & fragmentation analysis'
      },
      {
        name: 'Communication Analytics',
        path: '/communication-analytics',
        icon: '💬',
        description: 'Slack & Teams messaging patterns, sentiment & after-hours analysis'
      },
      {
        name: 'Health Dashboard',
        path: '/health',
        icon: '❤️',
        description: 'Personal health monitoring and stress tracking'
      },
      {
        name: 'Team Health Analytics',
        path: '/team-health',
        icon: '📊',
        description: 'Manager view of team wellness (anonymized)'
      },
      {
        name: 'Behavioral Analysis',
        path: '/behavioral-analysis',
        icon: '📊',
        description: 'Behavioral pattern analysis'
      },
      {
        name: 'Nudge Bot',
        path: '/nudge-bot',
        icon: '🤖',
        description: 'Proactive outbound nudges via Slack/Teams'
      }
    ]
  };

  // Network & Collaboration Section - Dedicated ONA
  const networkSection: MenuSection = {
    name: 'Network & Collaboration',
    path: '/organizational-network',
    icon: '🕸',
    requiredRoles: ['hr', 'admin', 'super_admin', 'manager'],
    items: [
      {
        name: 'Network Dashboard',
        path: '/organizational-network',
        icon: '🕸',
        description: 'Influencers, bridges, isolated employees & network health'
      },
      {
        name: 'Collaboration Survey',
        path: '/collaboration-survey',
        icon: '📋',
        description: 'Advice, trust & energy network mapping via self-report'
      },
      {
        name: 'Community Map',
        path: '/community-map',
        icon: '🏘',
        description: 'Detected communities, clusters & silo analysis'
      },
      {
        name: 'Network Evolution',
        path: '/network-evolution',
        icon: '📈',
        description: 'Temporal trends in connectivity, density & communities'
      },
      {
        name: 'Personality Overlay',
        path: '/personality-network',
        icon: '🧠',
        description: 'Big Five traits overlaid on network positions'
      }
    ]
  };

  // Teams Analytics Section - Collapsible
  const featuresSection: MenuSection = {
    name: 'Teams Analytics',
    path: '/analytics',
    icon: '🤖',
    items: [
      {
        name: 'Teams',
        path: '/teams',
        icon: '👥',
        description: 'Manage and view your teams'
      },
      {
        name: 'Team Optimizer',
        path: '/team-optimizer',
        icon: '⚡',
        description: 'AI team composition with OCEAN, EI, cognitive traits, role presets & conflict analysis'
      },
      {
        name: 'Team Composition',
        path: '/team-composition',
        icon: '🧩',
        description: 'Personality-based team analytics and insights'
      },
      {
        name: 'Peer Recognition',
        path: '/recognition',
        icon: '🏆',
        description: 'Give & view peer-to-peer recognitions, org-wide recognition stats'
      },
      {
        name: '360 Feedback',
        path: '/feedback-360',
        icon: '🔄',
        description: 'Multi-rater feedback with privacy-safe aggregation & blind spot detection'
      },
      {
        name: 'Meeting Effectiveness',
        path: '/meeting-effectiveness',
        icon: '📹',
        description: 'Rate meetings to build org-wide meeting health signals'
      },
      {
        name: 'Multi-Framework Synthesis',
        path: '/multi-framework-synthesis',
        icon: '🧬',
        description: 'Cross-framework synthesis: Big Five, MBTI, Enneagram, DISC, Belbin, Holland & more'
      },
      {
        name: 'Reliability & Validity',
        path: '/reliability-validity',
        icon: '🔬',
        description: 'Research metrics and validation'
      },
      {
        name: 'General Analytics',
        path: '/analytics/dashboard',
        icon: '📈',
        description: 'Overall analytics dashboard'
      }
    ]
  };

  // Biometric Integrations Section
  const biometricSection: MenuSection = {
    name: 'Biometric Integrations',
    path: '/biometric',
    icon: '⌚',
    items: [
      {
        name: 'Device Connections',
        path: '/biometric/integrations',
        icon: '📱',
        description: 'Connect Apple Health, Fitbit, Garmin, Oura, WHOOP & Google Fit'
      },
      {
        name: 'Live Metrics',
        path: '/biometric/metrics',
        icon: '❤️',
        description: 'Real-time heart rate, HRV, sleep quality & stress levels'
      },
      {
        name: 'Sleep & Recovery',
        path: '/biometric/sleep',
        icon: '🌙',
        description: 'Sleep stages, recovery scores & readiness trends'
      },
      {
        name: 'Stress Biometrics',
        path: '/biometric/stress',
        icon: '⚡',
        description: 'Physiological stress signals, body battery & strain tracking'
      }
    ]
  };

  // Compliance & Legal Section - Collapsible
  const complianceSection: MenuSection = {
    name: 'Compliance & Legal',
    path: '/compliance',
    icon: '⚖️',
    items: [
      {
        name: 'Legal Rights Dashboard',
        path: '/legal-rights',
        icon: '⚖️',
        description: 'Employee legal rights information and resources'
      },
      {
        name: 'Equity & Transparency',
        path: '/equity',
        icon: '🤝',
        description: 'Workplace equity metrics and transparency reports'
      }
    ]
  };

  const toggleSection = (sectionName: string) => {
    setExpandedSections(prev =>
      prev.includes(sectionName)
        ? prev.filter(name => name !== sectionName)
        : [...prev, sectionName]
    );
  };

  // Check if any route in a section is active
  const isClinicalActive = clinicalSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isTelehealthActive = telehealthSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isServicesActive = servicesSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isExecutiveAnalyticsActive = executiveAnalyticsSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isFeaturesActive = featuresSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isMetadataIntelligenceActive = metadataIntelligenceSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isHRISActive = hrisSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isEarlyWarningActive = earlyWarningSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isBiometricActive = biometricSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isNetworkActive = networkSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isComplianceActive = complianceSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  // Helper function to check if section should be visible based on role
  const isSectionVisible = (section: MenuSection): boolean => {
    // Admin and superuser see everything
    if (isAdmin || user?.is_superuser) {
      return true;
    }
    if (!section.requiredRoles || section.requiredRoles.length === 0) {
      return true; // No role requirements = visible to all
    }
    // Check if user has any of the required roles
    return section.requiredRoles.some(role => userRole.toLowerCase().includes(role.toLowerCase()));
  };

  return (
    <aside
      className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-40 flex flex-col ${
        isOpen ? 'w-48' : 'w-14'
      } ${
        !isOpen ? '-translate-x-full md:translate-x-0' : ''
      }`}
    >
      {/* Toggle Button - Always Visible */}
      <button
        onClick={onToggle}
        className="absolute top-4 right-2 z-50 p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-white transition-colors"
        aria-label="Toggle sidebar"
      >
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          )}
        </svg>
      </button>

      <div className="p-4 flex-shrink-0">
        <div className={`flex items-center ${isOpen ? 'justify-between' : 'justify-center'}`}>
          {isOpen && <span className="text-lg font-semibold">PsychSync</span>}
        </div>
      </div>
      <nav className="mt-8 flex-1 overflow-y-auto overflow-x-hidden px-2">
        {/* Core Routes */}
        <div className="mb-8">
          {isOpen && (
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider flex items-center justify-between">
              <span>Core</span>
              {/* Role Badge */}
              {isAdmin && (
                <span className="px-2 py-0.5 text-xs bg-orange-500/20 text-orange-400 rounded-full">
                  Admin
                </span>
              )}
              {isHR && !isAdmin && (
                <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">
                  HR
                </span>
              )}
            </div>
          )}
          {visibleCoreItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
                ${isActive ? 'bg-gray-800 text-white border-r-2 border-blue-500' : ''}
              `}
            >
              <span className="text-xl">{item.icon}</span>
              {isOpen && <span className="ml-3">{item.name}</span>}
            </NavLink>
          ))}
        </div>

        {/* 📊 VISUAL SEPARATOR - Executive Analytics */}
        <div className="relative flex items-center py-4">
          <div className="flex-grow border-t border-blue-500/30"></div>
          {isOpen && (
            <span className="flex-shrink-0 mx-4 text-blue-400 text-xs font-semibold uppercase tracking-wider">
              📊 Executive
            </span>
          )}
          <div className="flex-grow border-t border-blue-500/30"></div>
        </div>

        {/* Executive Analytics Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => toggleSection('executive-analytics-section')}
            className={`
              w-full flex items-center px-4 py-3 text-blue-400 hover:bg-blue-900/20 hover:text-blue-300 transition-colors cursor-pointer text-left rounded-lg
              ${isExecutiveAnalyticsActive ? 'bg-blue-900/30 text-blue-300 border-r-2 border-blue-400' : ''}
            `}
          >
            <span className="text-2xl">{executiveAnalyticsSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left font-semibold">{executiveAnalyticsSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSection('executive-analytics-section');
                  }}
                  className="p-1 hover:bg-blue-900/40 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle executive analytics section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('executive-analytics-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {expandedSections.includes('executive-analytics-section') && isOpen && (
            <div className="mt-2 space-y-1">
              {executiveAnalyticsSection.items?.map((item, index) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-800 text-white border-r-2 border-blue-500' : ''}
                    ${index !== executiveAnalyticsSection.items!.length - 1 ? 'border-b border-blue-500/10' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-xl">{item.icon}</span>
                  {isOpen && <span className="ml-3">{item.name}</span>}
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* ⚡ VISUAL SEPARATOR - Early Warning & Risk */}
        {isSectionVisible(earlyWarningSection) && (
          <>
            <div className="relative flex items-center py-4">
              <div className="flex-grow border-t border-yellow-500/30"></div>
              {isOpen && (
                <span className="flex-shrink-0 mx-4 text-yellow-400 text-xs font-semibold uppercase tracking-wider">
                  ⚡ Risk Detection
                </span>
              )}
              <div className="flex-grow border-t border-yellow-500/30"></div>
            </div>

            {/* Early Warning & Risk Section - Collapsible */}
            <div className="mb-8">
          <button
            onClick={() => toggleSection('early-warning-section')}
            className={`
              w-full flex items-center px-4 py-3 text-yellow-400 hover:bg-yellow-900/20 hover:text-yellow-300 transition-colors cursor-pointer text-left rounded-lg
              ${isEarlyWarningActive ? 'bg-yellow-900/30 text-yellow-300 border-r-2 border-yellow-400' : ''}
            `}
          >
            <span className="text-2xl">{earlyWarningSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left font-semibold">{earlyWarningSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSection('early-warning-section');
                  }}
                  className="p-1 hover:bg-yellow-900/40 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle early warning section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('early-warning-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Early Warning Sub-items */}
          {isOpen && expandedSections.includes('early-warning-section') && (
            <div className="mt-2 bg-yellow-900/10 border-l-2 border-yellow-500 rounded-lg overflow-hidden">
              {earlyWarningSection.items?.map((item, index) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-3 pl-8 text-sm text-gray-300 hover:bg-yellow-900/20 hover:text-white transition-colors
                    ${isActive ? 'bg-yellow-900/30 text-yellow-200 border-l-4 border-yellow-400' : ''}
                    ${index !== earlyWarningSection.items!.length - 1 ? 'border-b border-yellow-500/10' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-xl mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div className="font-medium">{item.name}</div>
                    {item.description && isOpen && (
                      <div className="text-xs text-gray-400 mt-0.5">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>
          </>
        )}

        {/* 📧 VISUAL SEPARATOR - Integrations */}
        <div className="relative flex items-center py-3">
          <div className="flex-grow border-t border-gray-700"></div>
        </div>

        {/* Clinical Screening Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => toggleSection('clinical-screening')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isClinicalActive ? 'bg-gray-800 text-white border-r-2 border-green-500' : ''}
            `}
          >
            <span className="text-xl text-yellow-400">{clinicalSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{clinicalSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('clinical-screening');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle clinical screening section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('clinical-screening') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Clinical Screening Sub-items */}
          {isOpen && expandedSections.includes('clinical-screening') && (
            <div className="bg-gray-800 border-l-2 border-green-500">
              {clinicalSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* Email Monitoring Section - Collapsible */}
        {isSectionVisible(metadataIntelligenceSection) && (
          <div className="mb-8">
          <button
            onClick={() => toggleSection('email-monitoring')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isMetadataIntelligenceActive ? 'bg-gray-800 text-white border-r-2 border-indigo-500' : ''}
            `}
          >
            <span className="text-xl text-indigo-400">{metadataIntelligenceSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{metadataIntelligenceSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('email-monitoring');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle email monitoring section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('email-monitoring') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Email Monitoring Sub-items */}
          {isOpen && expandedSections.includes('email-monitoring') && (
            <div className="bg-gray-800 border-l-2 border-indigo-500">
              {metadataIntelligenceSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>
        )}

        {/* HRIS Analytics Section - Collapsible */}
        {isSectionVisible(hrisSection) && (
          <div className="mb-8">
          <button
            onClick={() => toggleSection('hris-analytics-section')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isHRISActive ? 'bg-gray-800 text-white border-r-2 border-cyan-500' : ''}
            `}
          >
            <span className="text-xl text-cyan-400">{hrisSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{hrisSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('hris-analytics-section');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle HRIS analytics section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('hris-analytics-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible HRIS Analytics Sub-items */}
          {isOpen && expandedSections.includes('hris-analytics-section') && (
            <div className="bg-gray-800 border-l-2 border-cyan-500">
              {hrisSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>
        )}

        {/* Admin & Executive Section - Collapsible */}
        {isSectionVisible(adminSection) && (
          <div className="mb-8">
            <button
              onClick={() => toggleSection('admin-section')}
              className={`
                w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
                ${location.pathname.startsWith('/admin') ? 'bg-gray-800 text-white border-r-2 border-orange-500' : ''}
              `}
            >
              <span className="text-xl text-orange-400">{adminSection.icon}</span>
              {isOpen && (
                <>
                  <span className="ml-3 flex-1 text-left font-medium">{adminSection.name}</span>
                  <span className="ml-2">
                    <svg
                      className={`w-4 h-4 transition-transform ${expandedSections.includes('admin-section') ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </>
              )}
            </button>

            {/* Collapsible Admin Sub-items */}
            {isOpen && expandedSections.includes('admin-section') && (
              <div className="bg-gray-800 border-l-2 border-orange-500">
                {adminSection.items?.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) => `
                      flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                      ${isActive ? 'bg-gray-700 text-white' : ''}
                    `}
                    title={item.description}
                  >
                    <span className="text-lg mr-3">{item.icon}</span>
                    <div className="flex-1">
                      <div>{item.name}</div>
                      {item.description && (
                        <div className="text-xs text-gray-500">{item.description}</div>
                      )}
                    </div>
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Telehealth Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => toggleSection('telehealth-section')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isTelehealthActive ? 'bg-gray-800 text-white border-r-2 border-blue-400' : ''}
            `}
          >
            <span className="text-xl text-blue-400">{telehealthSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{telehealthSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('telehealth-section');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle telehealth section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('telehealth-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Telehealth Sub-items */}
          {isOpen && expandedSections.includes('telehealth-section') && (
            <div className="bg-gray-800 border-l-2 border-blue-400">
              {telehealthSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => console.log('[Sidebar] Clicked navigation item:', item.name, 'path:', item.path)}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* Services & Connectors Section - Collapsible */}
        {isSectionVisible(servicesSection) && (
          <>
          <div className="mb-8">
          <button
            onClick={() => toggleSection('services-section')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isServicesActive ? 'bg-gray-800 text-white border-r-2 border-blue-500' : ''}
            `}
          >
            <span className="text-xl text-purple-400">{servicesSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{servicesSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('services-section');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle services section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('services-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Services Sub-items */}
          {isOpen && expandedSections.includes('services-section') && (
            <div className="bg-gray-800 border-l-2 border-purple-500">
              {servicesSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>
        </>
        )}

        {/* Biometric Integrations Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => toggleSection('biometric-section')}
            className={`
              w-full flex items-center px-4 py-3 text-emerald-400 hover:bg-emerald-900/20 hover:text-emerald-300 transition-colors cursor-pointer text-left rounded-lg
              ${isBiometricActive ? 'bg-emerald-900/30 text-emerald-300 border-r-2 border-emerald-400' : ''}
            `}
          >
            <span className="text-2xl">{biometricSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left font-semibold">{biometricSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSection('biometric-section');
                  }}
                  className="p-1 hover:bg-emerald-900/40 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle biometric integrations section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('biometric-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {isOpen && expandedSections.includes('biometric-section') && (
            <div className="mt-2 bg-emerald-900/10 border-l-2 border-emerald-500 rounded-lg overflow-hidden">
              {biometricSection.items?.map((item, index) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-3 pl-8 text-sm text-gray-300 hover:bg-emerald-900/20 hover:text-white transition-colors
                    ${isActive ? 'bg-emerald-900/30 text-emerald-200 border-l-4 border-emerald-400' : ''}
                    ${index !== biometricSection.items!.length - 1 ? 'border-b border-emerald-500/10' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-xl mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div className="font-medium">{item.name}</div>
                    {item.description && isOpen && (
                      <div className="text-xs text-gray-400 mt-0.5">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* Network & Collaboration Section */}
        {isSectionVisible(networkSection) && (
          <div className="mb-8">
            <button
              onClick={() => toggleSection('network-section')}
              className={`
                w-full flex items-center px-4 py-3 text-teal-400 hover:bg-teal-900/20 hover:text-teal-300 transition-colors cursor-pointer text-left rounded-lg
                ${isNetworkActive ? 'bg-teal-900/30 text-teal-300 border-r-2 border-teal-400' : ''}
              `}
            >
              <span className="text-2xl">{networkSection.icon}</span>
              {isOpen && (
                <>
                  <span className="ml-3 flex-1 text-left font-semibold">{networkSection.name}</span>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSection('network-section');
                    }}
                    className="p-1 hover:bg-teal-900/40 rounded cursor-pointer"
                    role="button"
                    aria-label="Toggle network section"
                    tabIndex={0}
                  >
                    <svg
                      className={`w-4 h-4 transition-transform ${
                        expandedSections.includes('network-section') ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </>
              )}
            </button>

            {isOpen && expandedSections.includes('network-section') && (
              <div className="mt-2 bg-teal-900/10 border-l-2 border-teal-500 rounded-lg overflow-hidden">
                {networkSection.items?.map((item, index) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) => `
                      flex items-center px-4 py-3 pl-8 text-sm text-gray-300 hover:bg-teal-900/20 hover:text-white transition-colors
                      ${isActive ? 'bg-teal-900/30 text-teal-200 border-l-4 border-teal-400' : ''}
                      ${index !== networkSection.items!.length - 1 ? 'border-b border-teal-500/10' : ''}
                    `}
                    title={item.description}
                  >
                    <span className="text-xl mr-3">{item.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium">{item.name}</div>
                      {item.description && isOpen && (
                        <div className="text-xs text-gray-400 mt-0.5">{item.description}</div>
                      )}
                    </div>
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Analytics & AI Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => toggleSection('features-section')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isFeaturesActive ? 'bg-gray-800 text-white border-r-2 border-orange-500' : ''}
            `}
          >
            <span className="text-xl text-orange-400">{featuresSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{featuresSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('features-section');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle analytics section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('features-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Features Sub-items */}
          {isOpen && expandedSections.includes('features-section') && (
            <div className="bg-gray-800 border-l-2 border-orange-500">
              {featuresSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* Compliance & Legal Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => toggleSection('compliance-section')}
            className={`
              w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors cursor-pointer text-left
              ${isComplianceActive ? 'bg-gray-800 text-white border-r-2 border-blue-500' : ''}
            `}
          >
            <span className="text-xl text-blue-400">{complianceSection.icon}</span>
            {isOpen && (
              <>
                <span className="ml-3 flex-1 text-left">{complianceSection.name}</span>
                <span
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent double toggle
                    toggleSection('compliance-section');
                  }}
                  className="p-1 hover:bg-gray-700 rounded cursor-pointer"
                  role="button"
                  aria-label="Toggle compliance section"
                  tabIndex={0}
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSections.includes('compliance-section') ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </>
            )}
          </button>

          {/* Collapsible Compliance Sub-items */}
          {isOpen && expandedSections.includes('compliance-section') && (
            <div className="bg-gray-800 border-l-2 border-blue-500">
              {complianceSection.items?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-4 py-2 pl-8 text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors
                    ${isActive ? 'bg-gray-700 text-white' : ''}
                  `}
                  title={item.description}
                >
                  <span className="text-lg mr-3">{item.icon}</span>
                  <div className="flex-1">
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* Public Access Routes */}
        <div className="border-t border-gray-700 pt-4">
          {isOpen && (
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider">
              Public Access
            </div>
          )}
          <NavLink
            to="/anonymous-feedback"
            className={({ isActive }) => `
              flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
              ${isActive ? 'bg-gray-800 text-white border-r-2 border-green-500' : ''}
            `}
          >
            <span className="text-xl">🛡️</span>
            {isOpen && <span className="ml-3">Anonymous Feedback</span>}
          </NavLink>
          <NavLink
            to="/feedback-status"
            className={({ isActive }) => `
              flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
              ${isActive ? 'bg-gray-800 text-white border-r-2 border-green-500' : ''}
            `}
          >
            <span className="text-xl">🔍</span>
            {isOpen && <span className="ml-3">Check Status</span>}
          </NavLink>
        </div>
      </nav>
    </aside>
  );
});

Sidebar.displayName = 'Sidebar';

export default Sidebar;
