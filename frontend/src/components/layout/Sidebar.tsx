// // // src/components/layout/Sidebar.tsx - Sidebar Component
// src/components/layout/Sidebar.tsx - Fixed with React Router
import React from 'react';
import { NavLink } from 'react-router-dom';
interface MenuItem {
  name: string;
  path: string;
  icon: string;
}
interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}
const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  const menuItems: MenuItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Teams', path: '/teams', icon: '👥' },
    { name: 'Assessments', path: '/assessments', icon: '📋' },
    { name: 'Optimizer', path: '/optimizer', icon: '⚡' },
    { name: 'Analytics', path: '/analytics', icon: '📈' },
    { name: 'Settings', path: '/settings', icon: '⚙️' }
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
        {/* Authenticated Routes */}
        <div className="mb-8">
          {isOpen && (
            <div className="px-4 py-2 text-xs text-gray-500 uppercase tracking-wider">
              Main Menu
            </div>
          )}
          {menuItems.map((item) => (
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
