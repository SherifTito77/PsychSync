// // // src/components/layout/Sidebar.tsx - Sidebar Component
// src/components/layout/Sidebar.tsx - Fixed with React Router
import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';

interface MenuItem {
  name: string;
  path: string;
  icon: string;
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
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}
const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const [expandedSections, setExpandedSections] = useState<string[]>(['clinical-screening']);
  const location = useLocation();
  const navigate = useNavigate();

  // Auto-collapse all sections when sidebar is closed, re-expand when opened
  React.useEffect(() => {
    if (!isOpen) {
      setExpandedSections([]);
    } else {
      // Re-expand clinical screening section when sidebar opens
      setExpandedSections(['clinical-screening']);
    }
  }, [isOpen]);

  const coreItems: MenuItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Teams', path: '/teams', icon: '👥' },
    { name: 'Toxic Behavior Detection', path: '/toxic-behavior-detection', icon: '🛡️' },
    { name: 'Burnout Prevention', path: '/burnout-prevention', icon: '🔥' },
    { name: 'Anonymous Feedback', path: '/anonymous-feedback', icon: '🔒' },
    { name: 'Behavioral Analytics', path: '/behavioral-analytics', icon: '🧠' },
    { name: 'Multi-Framework Synthesis', path: '/multi-framework-synthesis', icon: '🧩' },
    { name: 'Legal Rights', path: '/legal-rights', icon: '⚖️' },
    { name: 'Equity Dashboard', path: '/equity', icon: '📈' },
    { name: 'Settings', path: '/settings', icon: '⚙️' }
  ];

  // Clinical Screening Section with Enhanced Tools
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
      },
      {
        name: 'Telehealth',
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
      }
    ]
  };

  // Service Areas Section - Collapsible
  const servicesSection: MenuSection = {
    name: 'Services & Connectors',
    path: '/services',
    icon: '🔧',
    items: [
      {
        name: 'Corporate Integrations',
        path: '/integrations/corporate',
        icon: '🔗',
        description: 'Connect 30+ data sources for behavioral intelligence'
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
      },
      {
        name: 'Behavioral Analysis',
        path: '/behavioral-analysis',
        icon: '📊',
        description: 'Behavioral pattern analysis'
      },
      {
        name: 'Email Connector',
        path: '/email-connector',
        icon: '📧',
        description: 'Email integration services'
      },
      {
        name: 'HRIS Connector',
        path: '/hris-connector',
        icon: '🏢',
        description: 'HR system integration'
      }
    ]
  };

  // Analytics & Features Section - Collapsible
  const featuresSection: MenuSection = {
    name: 'Analytics & AI',
    path: '/analytics',
    icon: '🤖',
    items: [
      {
        name: 'Team Optimizer',
        path: '/team-optimizer',
        icon: '⚡',
        description: 'Optimize team dynamics'
      },
      {
        name: 'Predictive Analytics',
        path: '/predictive-analytics',
        icon: '🤖',
        description: 'AI-powered predictions'
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

  const isServicesActive = servicesSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  const isFeaturesActive = featuresSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );
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
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider">
              Core
            </div>
          )}
          {coreItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
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

        {/* Clinical Screening Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => {
              // Navigate to section page AND toggle expansion
              navigate(clinicalSection.path);
              toggleSection('clinical-screening');
            }}
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

        {/* Services & Connectors Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => {
              // Navigate to section page AND toggle expansion
              navigate(servicesSection.path);
              toggleSection('services-section');
            }}
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

        {/* Analytics & AI Section - Collapsible */}
        <div className="mb-8">
          <button
            onClick={() => {
              // Navigate to section page AND toggle expansion
              navigate(featuresSection.path);
              toggleSection('features-section');
            }}
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
};
export default Sidebar;
