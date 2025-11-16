// // src/components/layout/Header.tsx - Application Header
// File: src/components/layout/Header.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Search } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';
interface HeaderProps {
  onMenuToggle: () => void;
}
const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  const { user, logout } = useAuth();
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={onMenuToggle}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              aria-label="Toggle sidebar"
            >
              ☰
            </button>
            <h1 className="ml-4 text-xl font-semibold text-gray-900">
              PsychSync
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            {/* Anonymous Feedback Links */}
            <div className="hidden md:flex items-center space-x-3 border-r border-gray-300 pr-4">
              <Link
                to="/anonymous-feedback"
                className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              >
                <Shield className="w-4 h-4 mr-1" />
                <span className="hidden lg:inline">Anonymous Feedback</span>
              </Link>
              <Link
                to="/feedback-status"
                className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-md transition-colors"
              >
                <Search className="w-4 h-4 mr-1" />
                <span className="hidden lg:inline">Check Status</span>
              </Link>
            </div>
            <span className="text-sm text-gray-600">
              Welcome, {user?.full_name || 'User'}
            </span>
            <Button onClick={logout} variant="danger">
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};
export default Header;
