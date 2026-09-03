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

// Helper function to get role badge styling
const getRoleBadgeStyles = (role?: string) => {
  switch (role) {
    case 'admin':
    case 'super_admin':
      return {
        bgColor: 'bg-purple-100',
        textColor: 'text-purple-800',
        borderColor: 'border-purple-300',
        label: 'Admin'
      };
    case 'hr':
      return {
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        borderColor: 'border-blue-300',
        label: 'HR'
      };
    case 'manager':
      return {
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        borderColor: 'border-green-300',
        label: 'Manager'
      };
    case 'employee':
    default:
      return {
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-700',
        borderColor: 'border-gray-300',
        label: 'Employee'
      };
  }
};

const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  const { user, logout } = useAuth();
  const roleStyles = getRoleBadgeStyles(user?.role);

  // Debug: Log user role to console
  React.useEffect(() => {
    if (user) {
      console.log('Current user:', user.full_name, 'Role:', user.role, 'IsSuperuser:', user.is_superuser);
    }
  }, [user]);

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

            {/* User info with role badge */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700 font-medium">
                  {user?.full_name || 'User'}
                </span>
                <span
                  className={`px-2.5 py-0.5 text-xs font-medium rounded-full border ${roleStyles.bgColor} ${roleStyles.textColor} ${roleStyles.borderColor}`}
                >
                  {roleStyles.label}
                </span>
              </div>
            </div>

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
