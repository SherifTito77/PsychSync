// src/pages/IconGallery.tsx - Complete Icon Gallery Page (Updated for Current Sidebar)
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../components/common/Icon';

interface IconItem {
  name: string;
  path: string;
  icon: string;
  description?: string;
}

interface IconSection {
  title: string;
  icon: string;
  color: string;
  items: IconItem[];
}

const IconGallery: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Core Items - Updated to match current sidebar
  const coreItems: IconItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊', description: 'Overview of teams, assessments, and analytics' },
    { name: 'Product Operations', path: '/product-operations', icon: '📈', description: 'Product operations and management dashboard' },
    { name: 'Icon Gallery', path: '/icon-gallery', icon: '🎨', description: 'Browse all available UI icons and emojis' },
    { name: 'Teams', path: '/teams', icon: '👥', description: 'Manage and view your teams' },
    { name: 'Settings', path: '/settings', icon: '⚙️', description: 'Manage your preferences' }
  ];

  // Executive Analytics Section
  const executiveAnalyticsItems: IconItem[] = [
    { name: 'CEO Executive Dashboard', path: '/executive/burnout', icon: '🎯', description: 'Executive burnout risk, department analytics, 90-day trends' },
    { name: 'KPI Dashboard', path: '/analytics/kpi', icon: '📈', description: 'Business KPIs, performance metrics, goal tracking' },
    { name: 'Predictive Analytics', path: '/predictive-analytics', icon: '🔮', description: 'AI predictions, forecasting, risk models' },
    { name: 'Population Health', path: '/analytics/population-health', icon: '🏥', description: 'Population-wide health metrics, epidemiological data' }
  ];

  // Early Warning & Risk Section
  const earlyWarningItems: IconItem[] = [
    { name: 'Radar Dashboard', path: '/radar', icon: '📡', description: '360° organizational health monitoring system' },
    { name: 'Advanced Burnout Analytics', path: '/advanced-burnout', icon: '🎯', description: '14-day early warning with Z-scores & trend detection' },
    { name: 'Burnout Prevention', path: '/burnout-prevention', icon: '🔥', description: '7-90 day burnout prediction & prevention' },
    { name: 'Behavioral Analytics', path: '/behavioral-analytics', icon: '🧠', description: 'Communication patterns & sentiment analysis' },
    { name: 'Toxic Behavior Detection', path: '/toxic-behavior-detection', icon: '🛡️', description: 'Harassment & toxic pattern monitoring' },
    { name: 'Employee Safety', path: '/employee-safety', icon: '⚠️', description: 'Workplace safety & incident tracking' },
    { name: 'Anomaly Detection', path: '/anomaly-detection', icon: '🚨', description: 'ML-powered pattern detection & alerts' },
    { name: 'Team Risk Dashboard', path: '/team-dashboard', icon: '👥', description: 'Team-level risk indicators & heatmap' },
    { name: 'Burnout Prediction', path: '/burnout-prediction', icon: '🔮', description: 'AI-powered risk prediction & analytics' }
  ];

  // Clinical Screening Section
  const clinicalScreeningItems: IconItem[] = [
    { name: 'Depression Screening (PHQ-9)', path: '/screening/phq9', icon: '💙', description: 'Evidence-based depression screening (α=0.89)' },
    { name: 'Anxiety Screening (GAD-7)', path: '/screening/gad7', icon: '💛', description: 'Comprehensive anxiety assessment (α=0.92)' },
    { name: 'Suicide Risk (C-SSRS)', path: '/screening/cssrs', icon: '🚨', description: 'Columbia-Suicide Severity Rating Scale (AUC=0.83)' },
    { name: 'Crisis Resources', path: '/screening/crisis-resources', icon: '🆘', description: '24/7 crisis support and emergency resources' },
    { name: 'Social Anxiety (LSAS)', path: '/screening/lsas', icon: '😰', description: 'Liebowitz Social Anxiety Scale (α=0.95)' },
    { name: 'Eating Attitudes (EAT-26)', path: '/screening/eat26', icon: '🍎', description: 'Eating disorder screening (α=0.90)' },
    { name: 'OCD Severity (Y-BOCS)', path: '/screening/ybocs', icon: '🔄', description: 'Yale-Brown Obsessive Compulsive Scale (α=0.90)' },
    { name: 'Depression (BDI-II)', path: '/screening/bdi2', icon: '😢', description: 'Beck Depression Inventory-II (α=0.91)' },
    { name: 'Anxiety (BAI)', path: '/screening/bai', icon: '😟', description: 'Beck Anxiety Inventory (α=0.92)' },
    { name: 'DASS-21 (Depression/Anxiety/Stress)', path: '/screening/dass21', icon: '📊', description: '21-item multi-symptom assessment (α=0.84-0.91)' },
    { name: 'PCL-5 (PTSD Checklist)', path: '/screening/pcl5', icon: '🎯', description: 'PTSD screening for DSM-5 (α=0.94)' },
    { name: 'AUDIT (Alcohol Use)', path: '/screening/audit', icon: '🍺', description: 'Alcohol Use Disorders Identification Test (α=0.92)' },
    { name: 'PSS-10 (Perceived Stress)', path: '/screening/pss10', icon: '😰', description: 'Perceived Stress Scale (α=0.78)' },
    { name: 'ISI (Insomnia Severity)', path: '/screening/isi', icon: '😴', description: 'Insomnia Severity Index (α=0.91)' },
    { name: 'CBI (Burnout Inventory)', path: '/screening/cbi', icon: '🔥', description: 'Copenhagen Burnout Inventory (α=0.87)' },
    { name: 'MDQ (Mood Disorder)', path: '/screening/mdq', icon: '🌈', description: 'Bipolar disorder screening (Sens=0.73, Spec=0.90)' },
    { name: 'DAST-10 (Drug Abuse)', path: '/screening/dast10', icon: '💊', description: 'Drug Abuse Screening Test (α=0.92)' },
    { name: 'AQ-10 (Autism Spectrum)', path: '/screening/aq10', icon: '🧩', description: 'Autism Spectrum Quotient (Sens=0.88, Spec=0.91)' },
    { name: 'ACE (Adverse Childhood Experiences)', path: '/screening/ace', icon: '👶', description: 'Childhood trauma screening (10 items)' },
    { name: 'IES-R (Impact of Event)', path: '/screening/iesr', icon: '💔', description: 'PTSD symptom assessment (α=0.96)' },
    { name: 'IAT (Internet Addiction)', path: '/screening/iat', icon: '📱', description: 'Internet Addiction Test (α=0.90)' },
    { name: 'ADHD Screening (ASRS)', path: '/screening/asrs', icon: '⚡', description: 'Adult ADHD Self-Report Scale v1.1 (Sens=68.7%, Spec=72.1%)' }
  ];

  // Email Monitoring Section
  const emailMonitoringItems: IconItem[] = [
    { name: 'Email Connector', path: '/email-connector', icon: '🔗', description: 'Email integration services' },
    { name: 'Sentiment Analysis', path: '/sentiment-analysis', icon: '😊', description: 'Email tone and emotion analysis' },
    { name: 'Scheduled Reports', path: '/scheduled-reports', icon: '📅', description: 'Automated weekly/monthly email reports' },
    { name: 'Anomaly Detection', path: '/anomaly-detection', icon: '🚨', description: 'ML-powered pattern detection & alerts' },
    { name: 'Team Dashboard', path: '/team-dashboard', icon: '👥', description: 'Team analytics & performance metrics' }
  ];

  // HRIS Analytics Section
  const hrisItems: IconItem[] = [
    { name: 'Analytics Dashboard', path: '/hris-analytics', icon: '📈', description: '7 charts, KPIs, custom reports with real-time updates' },
    { name: 'HRIS Connector', path: '/hris-connector', icon: '🔗', description: 'Connect Workday, BambooHR, ADP & 30+ HR systems' },
    { name: 'Workforce Demographics', path: '/hris/demographics', icon: '👥', description: 'Employee composition, diversity analysis, age distribution & tenure trends' },
    { name: 'Performance Analytics', path: '/hris/performance', icon: '⭐', description: 'Performance reviews, goals completion, top performers & trends' },
    { name: 'Turnover Analysis', path: '/hris/turnover', icon: '📉', description: 'Turnover patterns, retention risks, exit reasons & predictions' },
    { name: 'Compensation Analysis', path: '/hris/compensation', icon: '💰', description: 'Pay equity, salary benchmarks, compensation gaps & total rewards' },
    { name: 'Engagement Analytics', path: '/hris/engagement', icon: '😊', description: 'Employee satisfaction, engagement scores, sentiment & workplace pulse' },
    { name: 'Learning & Development', path: '/hris/learning', icon: '📚', description: 'Training effectiveness, skill gaps, certifications & development programs' },
    { name: 'Succession Planning', path: '/hris/succession', icon: '🎯', description: 'Leadership pipeline, readiness scores, key positions & successors' }
  ];

  // Clinical Services & Resources Section
  const clinicalServicesItems: IconItem[] = [
    { name: 'Telehealth - Schedule Consultation', path: '/telehealth/schedule', icon: '📹', description: 'Schedule video consultation with clinician' },
    { name: 'AI Chat Support', path: '/support/chat', icon: '🤖', description: '24/7 AI-powered mental health support' },
    { name: 'Clinical Analytics', path: '/analytics/clinical', icon: '📊', description: 'Population health insights dashboard' },
    { name: 'Population Health', path: '/analytics/population-health', icon: '🏥', description: 'Population metrics and high-risk identification' },
    { name: 'Alerts Center', path: '/clinical/alerts-center', icon: '🚨', description: 'Manage clinical alerts and notifications' },
    { name: 'Screening Home', path: '/clinical-assessments', icon: '🏠', description: 'Main mental health assessment portal' },
    { name: 'Wellbeing Check', path: '/clinical/assessment/wellbeing/take', icon: '🌟', description: 'Overall wellbeing assessment' },
    { name: 'Stress Assessment', path: '/clinical/assessment/stress/take', icon: '😰', description: 'Perceived stress level evaluation' },
    { name: 'Self-Help Library', path: '/clinical/self-help', icon: '📚', description: 'Comprehensive coping strategies' },
    { name: 'Clinical Resources', path: '/clinical/resources', icon: '🏥', description: 'Therapists, support groups & mental health tools' },
    { name: 'Emergency Resources', path: '/clinical/emergency', icon: '🚨', description: '24/7 crisis support hotline' },
    { name: 'Clinical Dashboard', path: '/clinical/dashboard', icon: '👨‍⚕️', description: 'Professional tools for clinicians' },
    { name: '✨ Enhanced Assessments', path: '/enhanced-assessments', icon: '⭐', description: 'Advanced assessments with dark mode, animations & offline support' },
    { name: 'Mental Health', path: '/mental-health-wellness', icon: '🧘', description: 'Mental health and wellness resources' },
    { name: 'Personality Assessments', path: '/personality-assessments', icon: '🧠', description: 'Personality tests and profiles' }
  ];

  // Admin & Executive Section
  const adminItems: IconItem[] = [
    { name: 'CEO Burnout Analytics', path: '/ceo-burnout-analytics', icon: '📊', description: 'Organization-level burnout risk, ROI tracking & cost-benefit analysis' },
    { name: 'Advanced Burnout Analytics', path: '/advanced-burnout', icon: '🎯', description: '14-day early warning with Z-scores, cognitive load & fatigue tracking' },
    { name: 'Corporate Psychology', path: '/admin/corporate-psychology', icon: '🧠', description: 'System-level organizational psychology intelligence for executives' },
    { name: 'Security Dashboard', path: '/admin/security', icon: '🛡️', description: 'Security monitoring and threat intelligence' },
    { name: 'Performance Monitoring', path: '/admin/performance', icon: '⚡', description: 'Real-time system performance metrics and health' }
  ];

  // Services & Connectors Section
  const servicesItems: IconItem[] = [
    { name: 'Corporate Integrations', path: '/integrations/corporate', icon: '🔗', description: 'Connect 30+ data sources including Slack, HRIS, and more' },
    { name: 'Health Dashboard', path: '/health', icon: '❤️', description: 'Personal health monitoring and stress tracking' },
    { name: 'Team Health Analytics', path: '/team-health', icon: '📊', description: 'Manager view of team wellness (anonymized)' },
    { name: 'Behavioral Analysis', path: '/behavioral-analysis', icon: '📊', description: 'Behavioral pattern analysis' }
  ];

  // Analytics & AI Section
  const analyticsItems: IconItem[] = [
    { name: 'Team Optimizer', path: '/team-optimizer', icon: '⚡', description: 'Optimize team dynamics with department filtering' },
    { name: 'Team Composition', path: '/team-composition', icon: '🧩', description: 'Personality-based team analytics and insights' },
    { name: 'Multi-Framework Synthesis', path: '/multi-framework-synthesis', icon: '🧩', description: 'AI-powered synthesis across personality frameworks' },
    { name: 'Predictive Analytics', path: '/predictive-analytics', icon: '🤖', description: 'AI-powered predictions' },
    { name: 'Reliability & Validity', path: '/reliability-validity', icon: '🔬', description: 'Research metrics and validation' },
    { name: 'General Analytics', path: '/analytics/dashboard', icon: '📈', description: 'Overall analytics dashboard' }
  ];

  // Compliance & Legal Section
  const complianceItems: IconItem[] = [
    { name: 'Legal Rights Dashboard', path: '/legal-rights', icon: '⚖️', description: 'Employee legal rights information and resources' },
    { name: 'Equity & Transparency', path: '/equity', icon: '🤝', description: 'Workplace equity metrics and transparency reports' }
  ];

  // Public Access Section
  const publicItems: IconItem[] = [
    { name: 'Anonymous Feedback', path: '/anonymous-feedback', icon: '🛡️', description: 'Secure anonymous feedback system' },
    { name: 'Check Status', path: '/feedback-status', icon: '🔍', description: 'Check feedback status' }
  ];

  const sections: IconSection[] = [
    { title: 'Core Navigation', icon: '📊', color: 'bg-blue-50 border-blue-200', items: coreItems },
    { title: 'Executive Analytics', icon: '📊', color: 'bg-indigo-50 border-indigo-200', items: executiveAnalyticsItems },
    { title: 'Early Warning & Risk', icon: '⚡', color: 'bg-yellow-50 border-yellow-200', items: earlyWarningItems },
    { title: 'Clinical Screening', icon: '🏥', color: 'bg-green-50 border-green-200', items: clinicalScreeningItems },
    { title: 'Email Monitoring', icon: '📧', color: 'bg-indigo-50 border-indigo-200', items: emailMonitoringItems },
    { title: 'HRIS Analytics', icon: '📊', color: 'bg-cyan-50 border-cyan-200', items: hrisItems },
    { title: 'Clinical Services', icon: '🏥', color: 'bg-blue-50 border-blue-200', items: clinicalServicesItems },
    { title: 'Admin & Executive', icon: '🔐', color: 'bg-red-50 border-red-200', items: adminItems },
    { title: 'Services & Connectors', icon: '🔧', color: 'bg-purple-50 border-purple-200', items: servicesItems },
    { title: 'Analytics & AI', icon: '🤖', color: 'bg-orange-50 border-orange-200', items: analyticsItems },
    { title: 'Compliance & Legal', icon: '⚖️', color: 'bg-gray-50 border-gray-200', items: complianceItems },
    { title: 'Public Access', icon: '🌐', color: 'bg-green-50 border-green-200', items: publicItems }
  ];

  // Filter sections and items based on search
  const filteredSections = sections.map(section => ({
    ...section,
    items: section.items.filter(item =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchQuery.toLowerCase()))
    )
  })).filter(section =>
    selectedCategory === 'all' || section.title === selectedCategory
  ).filter(section => section.items.length > 0);

  const handleIconClick = (path: string) => {
    navigate(path);
  };

  const allIcons = sections.flatMap(s => s.items);
  const uniqueIcons = new Set(allIcons.map(item => item.icon)).size;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mobile-text-responsive">
              Icon Gallery
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              All navigation icons from the sidebar • {allIcons.length} total items across {sections.length} categories
            </p>
          </div>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors mobile-touch-target"
          >
            ← Back
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search icons, names, descriptions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <Icon size="md" className="absolute left-4 top-3 text-gray-400">🔍</Icon>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 mt-4">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              selectedCategory === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Categories ({sections.length})
          </button>
          {sections.map((section) => (
            <button
              key={section.title}
              onClick={() => setSelectedCategory(section.title)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                selectedCategory === section.title
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <span>{section.icon}</span>
              <span className="hidden sm:inline">{section.title}</span>
              <span className="text-xs bg-white/20 px-1.5 rounded-full">{section.items.length}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        {sections.map((section) => (
          <div
            key={section.title}
            className={`${section.color} border-2 rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer`}
            onClick={() => setSelectedCategory(section.title)}
          >
            <div className="text-3xl mb-2">{section.icon}</div>
            <div className="text-2xl sm:text-3xl font-bold text-gray-900">{section.items.length}</div>
            <div className="text-xs text-gray-700 mt-1">{section.title}</div>
          </div>
        ))}
      </div>

      {/* Icons Grid */}
      {filteredSections.map((section, sectionIndex) => (
        <div key={sectionIndex} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
          <div className="flex items-center justify-between mb-4 pb-2 border-b-2 border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <span className="text-2xl">{section.icon}</span>
              {section.title}
              <span className="text-sm font-normal text-gray-500">({section.items.length} items)</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
            {section.items.map((item, index) => (
              <div
                key={index}
                onClick={() => handleIconClick(item.path)}
                className={`
                  rounded-lg border-2 cursor-pointer p-4 transition-all duration-200
                  ${section.color}
                  hover:shadow-lg hover:scale-105
                  focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                  mobile-touch-target
                `}
              >
                <div className="flex flex-col items-center text-center">
                  {/* Icon */}
                  <div className="text-4xl sm:text-5xl mb-3 transform transition-transform duration-300 hover:scale-110">
                    {item.icon}
                  </div>

                  {/* Name */}
                  <h3 className="font-semibold text-gray-900 mb-2 text-sm leading-tight">
                    {item.name}
                  </h3>

                  {/* Description (if available) */}
                  {item.description && (
                    <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                      {item.description}
                    </p>
                  )}

                  {/* Path */}
                  <p className="text-xs text-indigo-600 font-mono bg-white/70 px-2 py-1 rounded w-full overflow-hidden text-ellipsis">
                    {item.path}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* No Results */}
      {filteredSections.every(s => s.items.length === 0) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Icon size="lg" className="mb-4">🔍</Icon>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No icons found</h3>
          <p className="text-gray-600">Try adjusting your search query or category filter</p>
        </div>
      )}

      {/* Footer Info */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <p className="text-sm text-indigo-800 text-center">
          <strong>💡 Tip:</strong> Click on any icon card to navigate to that page • Use keyboard shortcut <kbd className="px-1.5 py-0.5 bg-white border rounded mx-1">⌘K</kbd> to search from anywhere
        </p>
      </div>
    </div>
  );
};

export default IconGallery;
