// src/components/layout/Header.tsx - Application Header

import React from 'react';
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
            <span className="text-sm text-gray-600">
              Welcome, {user?.name}
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