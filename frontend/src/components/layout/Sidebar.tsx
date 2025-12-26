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
const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  const [expandedSections, setExpandedSections] = useState<string[]>(['clinical-screening']);
  const location = useLocation();
  const navigate = useNavigate();

  const coreItems: MenuItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Teams', path: '/teams', icon: '👥' },
    { name: 'Settings', path: '/settings', icon: '⚙️' }
  ];

  // Clinical Screening Section with Enhanced Tools
  const clinicalSection: MenuSection = {
    name: 'Clinical Screening',
    path: '/clinical-assessments',
    icon: '🏥',
    items: [
      {
        name: 'Screening Home',
        path: '/clinical-assessments',
        icon: '🏠',
        description: 'Main mental health assessment portal'
      },
      {
        name: 'Depression (PHQ-9)',
        path: '/clinical/assessment/phq9/take',
        icon: '💙',
        description: 'Evidence-based depression screening tool'
      },
      {
        name: 'Anxiety (GAD-7)',
        path: '/clinical/assessment/gad7/take',
        icon: '💛',
        description: 'Comprehensive anxiety assessment'
      },
      {
        name: 'Wellbeing Check',
        path: '/clinical/wellbeing/take',
        icon: '🌟',
        description: 'Overall wellbeing assessment'
      },
      {
        name: 'Stress Assessment',
        path: '/clinical/stress/take',
        icon: '😰',
        description: 'Perceived stress level evaluation'
      },
      {
        name: 'Sleep Quality',
        path: '/clinical/sleep/take',
        icon: '😴',
        description: 'Sleep pattern and quality assessment'
      },
      {
        name: 'Self-Help Library',
        path: '/clinical/self-help',
        icon: '📚',
        description: 'Comprehensive coping strategies'
      },
      {
        name: 'Meditation Tools',
        path: '/clinical/meditation',
        icon: '🧘',
        description: 'Guided meditation exercises'
      },
      {
        name: 'Emergency Resources',
        path: '/clinical/emergency',
        icon: '🚨',
        description: '24/7 crisis support hotline'
      },
      {
        name: 'Support Groups',
        path: '/clinical/support',
        icon: '👥',
        description: 'Peer support communities'
      },
      {
        name: 'Resource Center',
        path: '/clinical/resources',
        icon: '📖',
        description: 'Educational materials and guides'
      },
      {
        name: 'Progress Tracker',
        path: '/clinical/progress',
        icon: '📈',
        description: 'Track your mental health journey'
      },
      {
        name: 'Clinical Dashboard',
        path: '/clinical/dashboard',
        icon: '👨‍⚕️',
        description: 'Professional tools for clinicians'
      }
    ]
  };

  // Other service areas (including original mental health link)
  const serviceAreas: MenuItem[] = [
    { name: 'Mental Health', path: '/mental-health-wellness', icon: '🧘' },
    { name: 'Personality Assessments', path: '/personality-assessments', icon: '🧠' },
    { name: 'Behavioral Analysis', path: '/behavioral-analysis', icon: '📊' },
    { name: 'Email Connector', path: '/email-connector', icon: '📧' },
    { name: 'HRIS Connector', path: '/hris-connector', icon: '🏢' }
  ];

  const toggleSection = (sectionName: string) => {
    setExpandedSections(prev =>
      prev.includes(sectionName)
        ? prev.filter(name => name !== sectionName)
        : [...prev, sectionName]
    );
  };

  // Check if any clinical screening route is active
  const isClinicalActive = clinicalSection.items?.some(item =>
    location.pathname.startsWith(item.path)
  );

  // Additional features
  const featureItems: MenuItem[] = [
    { name: 'Team Optimizer', path: '/team-optimizer', icon: '⚡' },
    { name: 'Predictive Analytics', path: '/predictive-analytics', icon: '🤖' },
    { name: 'Reliability & Validity', path: '/reliability-validity', icon: '🔬' },
    { name: 'General Analytics', path: '/analytics', icon: '📈' }
  ];
  // Public access items (available without authentication)
  const publicItems: MenuItem[] = [
    { name: 'Anonymous Feedback', path: '/anonymous-feedback', icon: '🛡️' },
    { name: 'Check Status', path: '/feedback-status', icon: '🔍' }
  ];
  return (
    <aside 
      className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-40 ${
        isOpen ? 'w-64' : 'w-16'
      }`}
    >
      <div className="p-4">
        <div className={`flex items-center ${isOpen ? 'justify-between' : 'justify-center'}`}>
          {isOpen && <span className="text-lg font-semibold">PsychSync</span>}
        </div>
      </div>
      <nav className="mt-8">
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
              // Navigate to assessments page using React Router
              navigate(clinicalSection.path);
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
                <button
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent navigation when clicking arrow
                    toggleSection('clinical-screening');
                  }}
                  className="p-1 hover:bg-gray-700 rounded"
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
                </button>
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

        {/* Other Service Areas */}
        <div className="mb-8">
          {isOpen && (
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider">
              Service Areas
            </div>
          )}
          {serviceAreas.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
                ${isActive ? 'bg-gray-800 text-white border-r-2 border-purple-500' : ''}
              `}
            >
              <span className="text-xl">{item.icon}</span>
              {isOpen && <span className="ml-3">{item.name}</span>}
            </NavLink>
          ))}
        </div>

        {/* Additional Features */}
        <div className="mb-8">
          {isOpen && (
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider">
              Features
            </div>
          )}
          {featureItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
                ${isActive ? 'bg-gray-800 text-white border-r-2 border-indigo-500' : ''}
              `}
            >
              <span className="text-xl">{item.icon}</span>
              {isOpen && <span className="ml-3">{item.name}</span>}
            </NavLink>
          ))}
        </div>

        {/* Public Access Routes */}
        <div className="border-t border-gray-700 pt-4">
          {isOpen && (
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider">
              Anonymous Feedback
            </div>
          )}
          {publicItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
                ${isActive ? 'bg-gray-800 text-white border-r-2 border-green-500' : ''}
              `}
            >
              <span className="text-xl">{item.icon}</span>
              {isOpen && <span className="ml-3">{item.name}</span>}
            </NavLink>
          ))}
        </div>
      </nav>
    </aside>
  );
};
export default Sidebar;
